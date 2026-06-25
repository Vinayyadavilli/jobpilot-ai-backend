from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
import os
import httpx

from app.dependencies.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.resume import Resume
from app.schemas.resume import ResumeResponse, ResumeListResponse, EnhanceUrlRequest
from app.core.resume_parser import extract_text
from app.core.resume_generator import generate_docx_from_text
from app.services.ai_service import AIService
from app.repositories.resume_repository import ResumeRepository

router = APIRouter(prefix="/resumes", tags=["AI Resume Enhancer"])


def _build_response(resume: Resume, request: Request) -> ResumeResponse:
    """Helper to dynamically populate the download URL field in the schema."""
    # Convert Request.base_url to string and build clean path
    base_url_str = str(request.base_url)
    download_url = f"{base_url_str}api/v1/resumes/{resume.id}/download"
    return ResumeResponse(
        id=str(resume.id),
        original_url=resume.original_url,
        raw_text=resume.raw_text,
        enhanced_text=resume.enhanced_text,
        download_url=download_url,
        created_at=resume.created_at
    )


# ─── Enhance Uploaded File ──────────────────────────────────────────────────

@router.post("/enhance-file", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def enhance_file(
    request: Request,
    file: UploadFile = File(..., description="Upload a PDF, DOCX, or TXT resume file"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a resume file, parse it, enhance with AI, and return download links."""
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file appears to be empty."
        )

    # 1. Parse content to plain text
    try:
        raw_text = extract_text(content, file.filename)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    if not raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract readable text from the uploaded file."
        )

    # 2. Enhance text via AI LLM Service
    ai_service = AIService()
    try:
        enhanced_text = await ai_service.enhance_resume(raw_text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI Enhancement failed: {str(e)}"
        )

    # 3. Log/Save to database
    repo = ResumeRepository(db)
    resume = Resume(
        user_id=current_user.id,
        raw_text=raw_text,
        enhanced_text=enhanced_text
    )
    saved_resume = repo.create(resume)

    return _build_response(saved_resume, request)


# ─── Enhance From URL ───────────────────────────────────────────────────────

@router.post("/enhance-url", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def enhance_url(
    request: Request,
    data: EnhanceUrlRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download a resume from a public URL link, parse it, enhance with AI, and save/log it."""
    # 1. Download file content from URL
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(data.url, follow_redirects=True, timeout=20.0)
            r.raise_for_status()
            content = r.content
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to retrieve file from URL: {str(e)}"
            )

    # Guess filename from URL or default to TXT
    filename = os.path.basename(data.url.split("?")[0]) or "resume.txt"
    if not filename.endswith((".pdf", ".docx", ".doc", ".txt", ".md", ".rtf")):
        filename += ".txt"

    # 2. Parse content to plain text
    try:
        raw_text = extract_text(content, filename)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    if not raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The retrieved file content is empty or unparseable."
        )

    # 3. Enhance text via AI LLM Service
    ai_service = AIService()
    try:
        enhanced_text = await ai_service.enhance_resume(raw_text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI Enhancement failed: {str(e)}"
        )

    # 4. Log/Save to database
    repo = ResumeRepository(db)
    resume = Resume(
        user_id=current_user.id,
        original_url=data.url,
        raw_text=raw_text,
        enhanced_text=enhanced_text
    )
    saved_resume = repo.create(resume)

    return _build_response(saved_resume, request)


# ─── Download File (.docx) ──────────────────────────────────────────────────

@router.get("/{id}/download")
def download_resume(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate and download the AI-enhanced resume as an editable Word (.docx) document."""
    repo = ResumeRepository(db)
    resume = repo.get_by_id(id, current_user.id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume record not found."
        )

    try:
        docx_bytes = generate_docx_from_text(resume.enhanced_text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate DOCX document: {str(e)}"
        )

    # Stream the bytes as a file download attachment
    return StreamingResponse(
        io.BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": "attachment; filename=Enhanced_Resume.docx",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )


# ─── List Logs ──────────────────────────────────────────────────────────────

@router.get("", response_model=ResumeListResponse)
def list_resumes(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve history of all user resume enhancements."""
    repo = ResumeRepository(db)
    resumes = repo.get_all_for_user(current_user.id)
    
    responses = [_build_response(r, request) for r in resumes]
    return ResumeListResponse(total=len(responses), resumes=responses)
