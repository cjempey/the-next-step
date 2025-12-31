"""
Task suggestion endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import SuggestionRequest, SuggestionResponse

router = APIRouter()


@router.post("/next", response_model=SuggestionResponse)
async def get_next_suggestion(
    request: SuggestionRequest, db: Session = Depends(get_db)
):
    """Get the next task suggestion using fuzzy weighting algorithm."""
    # TODO: Implement scoring algorithm and stochastic selection
    pass


@router.post("/suggest-importance")
async def suggest_importance(task_title: str, db: Session = Depends(get_db)):
    """Use AI to suggest task importance based on title and values."""
    # TODO: Implement OpenAI integration
    pass


@router.post("/suggest-urgency")
async def suggest_urgency(task_title: str, db: Session = Depends(get_db)):
    """Use AI to suggest task urgency based on title and due date."""
    # TODO: Implement OpenAI integration
    pass
