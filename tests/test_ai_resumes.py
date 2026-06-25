import sys
import httpx
from datetime import datetime, timedelta
from app.database.session import SessionLocal
from app.repositories.user_repository import UserRepository
from app.repositories.resume_repository import ResumeRepository


def test_ai_resume_flow():
    base_url = "http://localhost:8000/api/v1"
    test_email = "ai_test@example.com"
    test_password = "Password123!"

    print("--- Starting AI Resume Enhancer Integration Tests ---")

    # 1. Clean up existing test data
    db = SessionLocal()
    try:
        user_repo = UserRepository(db)
        existing_user = user_repo.get_by_email(test_email)
        if existing_user:
            db.delete(existing_user)
            db.commit()
            print("Cleaned up existing test user.")
    except Exception as e:
        print(f"Error during cleanup: {e}")
    finally:
        db.close()

    # 2. Register
    print("Registering test user...")
    r = httpx.post(
        f"{base_url}/auth/register",
        json={"name": "AI Resume Tester", "email": test_email, "password": test_password}
    )
    assert r.status_code == 201, r.text
    
    # 3. Retrieve token and verify email
    db = SessionLocal()
    user_repo = UserRepository(db)
    user = user_repo.get_by_email(test_email)
    token = user.email_verification_token
    db.close()

    print("Verifying email...")
    r = httpx.get(f"{base_url}/auth/verify-email?token={token}")
    assert r.status_code == 200, r.text

    # 4. Login to get tokens
    print("Logging in...")
    r = httpx.post(
        f"{base_url}/auth/login",
        json={"email": test_email, "password": test_password}
    )
    assert r.status_code == 200, r.text
    tokens = r.json()
    access_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # 5. Check empty history
    print("Checking empty resumes history...")
    r = httpx.get(f"{base_url}/resumes", headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["total"] == 0

    # 6. Test enhance-file endpoint with a plain text file
    print("Testing enhance-file endpoint...")
    file_content = (
        "John Doe\n"
        "Software Engineer\n"
        "Experience: 2 years writing python scripts at Tech Corp.\n"
        "Skills: Python, Git."
    )
    files = {"file": ("resume.txt", file_content.encode("utf-8"), "text/plain")}
    
    r = httpx.post(f"{base_url}/resumes/enhance-file", files=files, headers=headers)
    print(f"Enhance file status: {r.status_code}")
    assert r.status_code == 201, r.text
    res_data = r.json()
    
    assert res_data["id"] is not None
    assert "download" in res_data["download_url"]
    assert "John Doe" in res_data["raw_text"]
    assert "Professional Resume" in res_data["enhanced_text"]
    resume_id = res_data["id"]

    # 7. Test download-resume endpoint (must return DOCX file with magic ZIP headers)
    print("Testing download endpoint...")
    download_url = res_data["download_url"]
    r = httpx.get(download_url, headers=headers)
    print(f"Download status: {r.status_code}")
    assert r.status_code == 200, r.text
    
    # Assert standard Word document zip signature magic bytes (PK\x03\x04)
    docx_bytes = r.content
    assert docx_bytes.startswith(b"PK\x03\x04")
    print("Verified download is a valid DOCX file!")

    # 8. Test enhance-url endpoint with a dummy test file from github raw contents
    print("Testing enhance-url endpoint...")
    # Use a highly reliable text URL that contains a sample readme
    test_url = "https://raw.githubusercontent.com/pypa/sampleproject/main/README.md"
    r = httpx.post(
        f"{base_url}/resumes/enhance-url",
        json={"url": test_url},
        headers=headers,
        timeout=30.0
    )
    print(f"Enhance URL status: {r.status_code}")
    assert r.status_code == 201, r.text
    url_res_data = r.json()
    assert url_res_data["original_url"] == test_url
    assert "A sample Python project" in url_res_data["raw_text"]

    # 9. Verify history lists 2 items
    print("Verifying resumes list history...")
    r = httpx.get(f"{base_url}/resumes", headers=headers)
    assert r.status_code == 200, r.text
    list_data = r.json()
    assert list_data["total"] == 2
    urls = [res["original_url"] for res in list_data["resumes"]]
    assert test_url in urls
    assert None in urls or "" in urls

    # 10. Clean up test user
    db = SessionLocal()
    try:
        user_repo = UserRepository(db)
        user = user_repo.get_by_email(test_email)
        if user:
            db.delete(user)
            db.commit()
            print("Cleaned up test user successfully.")
    finally:
        db.close()

    print("✅ All AI Resume Enhancer integration tests PASSED successfully!")


if __name__ == "__main__":
    test_ai_resume_flow()
