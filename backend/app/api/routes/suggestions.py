"""
Task suggestion endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_active_user
from app.config import settings
from app.core.database import get_db
from app.models import Task, TaskStateEnum, User
from app.schemas import SuggestionRequest, SuggestionResponse, TaskResponse
from app.services.scoring.registry import get_strategy_registry
from app.services.scoring.service import TaskScoringService

router = APIRouter()


@router.post("/next", response_model=SuggestionResponse)
async def get_next_suggestion(
    request: SuggestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get the next task suggestion using fuzzy weighting algorithm.

    Uses stochastic selection with weighted probabilities based on
    task impact, urgency, strategic nudge, rejection dampening, and
    daily priorities.

    Args:
        request: Suggestion request (optionally include in-progress tasks)
        db: Database session
        current_user: Authenticated user

    Returns:
        SuggestionResponse with selected task and reason

    Raises:
        HTTPException: 404 if no tasks available
    """
    # Query Ready tasks (optionally include In Progress)
    if request.include_in_progress:
        states = [TaskStateEnum.READY, TaskStateEnum.IN_PROGRESS]
    else:
        states = [TaskStateEnum.READY]

    tasks = (
        db.query(Task)
        .filter(
            Task.user_id == current_user.id,
            Task.state.in_(states),
        )
        .all()
    )

    if not tasks:
        raise HTTPException(status_code=404, detail="No tasks available")

    # Get strategy and scoring service
    registry = get_strategy_registry()
    strategy = registry.get_default()  # Future: allow user to specify strategy
    service = TaskScoringService(strategy, settings.SCORING_CONFIG)

    # Select stochastically
    selected_task, reason = service.select_stochastic(tasks, current_user.id, db)

    # Return suggestion
    return SuggestionResponse(
        task=TaskResponse.model_validate(selected_task), reason=reason
    )


@router.get("/strategies")
async def list_scoring_strategies(
    current_user: User = Depends(get_current_active_user),
):
    """List available scoring strategies (for future user selection).

    Args:
        current_user: Authenticated user

    Returns:
        Dictionary with list of available strategies
    """
    registry = get_strategy_registry()
    return {"strategies": registry.list_strategies()}


@router.get("/planning/ranked-tasks")
async def get_ranked_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all Ready tasks ranked by weighted score for morning planning.

    Provides deterministic ranking showing which tasks have highest scores,
    with transparency about scoring factors.

    Args:
        db: Database session
        current_user: Authenticated user

    Returns:
        Dictionary with ranked list of tasks, scores, and reasons
    """
    tasks = (
        db.query(Task)
        .filter(
            Task.user_id == current_user.id,
            Task.state == TaskStateEnum.READY,
        )
        .all()
    )

    registry = get_strategy_registry()
    strategy = registry.get_default()
    service = TaskScoringService(strategy, settings.SCORING_CONFIG)

    ranked = service.rank_tasks(tasks, current_user.id, db)

    return {
        "tasks": [
            {
                "task": TaskResponse.model_validate(task),
                "score": score,
                "reason": reason,
            }
            for task, score, reason in ranked
        ]
    }


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


@router.post("/reject")
async def reject_suggestion(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Apply rejection dampening to a task.

    When a user rejects a suggestion, this endpoint creates a
    RejectionDampening record that reduces the task's weight in
    future suggestions until the next break or evening review.

    Args:
        task_id: ID of the task being rejected
        db: Database session
        current_user: Authenticated user

    Returns:
        Success message

    Raises:
        HTTPException: 404 if task not found or doesn't belong to user
    """
    from app.models import RejectionDampening
    from datetime import datetime, timezone

    # Verify task exists and belongs to user
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    # Check if dampening already exists for this task
    existing = db.query(RejectionDampening).filter(
        RejectionDampening.user_id == current_user.id,
        RejectionDampening.task_id == task_id
    ).first()

    if not existing:
        # Create new dampening record
        dampening = RejectionDampening(
            user_id=current_user.id,
            task_id=task_id,
            rejected_at=datetime.now(timezone.utc),
            expires_at="next_break"  # Cleared on break or evening review
        )
        db.add(dampening)
        db.commit()

    return {"message": "Task rejected", "task_id": task_id}


@router.post("/break")
async def take_break(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Clear all rejection dampening for the current user session.

    When a user takes a break, this resets all rejection dampening,
    allowing previously rejected tasks to be suggested again.

    Args:
        db: Database session
        current_user: Authenticated user

    Returns:
        Success message with count of cleared records
    """
    from app.models import RejectionDampening

    # Delete all rejection dampening records for this user
    deleted_count = db.query(RejectionDampening).filter(
        RejectionDampening.user_id == current_user.id
    ).delete()

    db.commit()

    return {
        "message": "Break taken, rejection dampening cleared",
        "cleared_count": deleted_count
    }
