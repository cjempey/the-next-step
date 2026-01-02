"""
Task suggestion endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import SuggestionRequest, SuggestionResponse
from app.models import User
from app.auth import get_current_active_user

router = APIRouter()


@router.post("/next", response_model=SuggestionResponse)
async def get_next_suggestion(
    request: SuggestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get the next task suggestion using fuzzy weighting algorithm."""
    # TODO: Implement scoring algorithm and stochastic selection
    # Filter by current_user.id
    pass


@router.post("/suggest-impact")
async def suggest_impact(
    task_title: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Use AI to suggest task impact based on title and values."""
    # TODO: Implement OpenAI integration
    pass


@router.post("/suggest-urgency")
async def suggest_urgency(
    task_title: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Use AI to suggest task urgency based on title and due date."""
    # TODO: Implement OpenAI integration
    pass
