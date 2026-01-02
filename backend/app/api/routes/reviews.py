"""
Evening review endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import ReviewCardsRequest, ReviewCard
from app.models import User
from app.auth import get_current_active_user

router = APIRouter()


@router.post("/cards", response_model=list[ReviewCard])
async def generate_review_cards(
    request: ReviewCardsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate review cards for evening review based on day's activity."""
    # TODO: Implement card generation logic:
    # - Completion summary
    # - Rejection/skip cards (>=3 rejections)
    # - In-progress cards
    # - Blocked cards (>7 days)
    # - Recurring task cards
    # Filter by current_user.id
    pass


@router.post("/cards/{card_id}/respond")
async def respond_to_card(
    card_id: str,
    response_option: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Process user response to a review card."""
    # TODO: Implement response handlers for each card type
    # Each handler updates task state, creates new tasks (for breakdown), etc.
    # Verify card belongs to current_user
    pass


@router.get("/history")
async def get_review_history(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get review history for journaling."""
    # TODO: Implement
    # Filter by current_user.id
    pass
