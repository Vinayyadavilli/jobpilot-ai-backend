from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict

from app.schemas.dashboard import DashboardSummaryResponse, DashboardTimelineResponse
from app.dependencies.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.repositories.dashboard_repository import DashboardRepository
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _get_service(db: Session) -> DashboardService:
    return DashboardService(DashboardRepository(db))


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve all computed dashboard summary metrics (success/interview rates, activity, breakdowns)."""
    return _get_service(db).get_summary(current_user.id)


@router.get("/timeline", response_model=DashboardTimelineResponse)
def get_timeline(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve application timeline data points grouped by date."""
    return _get_service(db).get_timeline(current_user.id)


@router.get("/by-status", response_model=Dict[str, int])
def get_by_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve count of job applications grouped by status."""
    summary = _get_service(db).get_summary(current_user.id)
    return summary.status_breakdown
