"""
Value endpoints.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Value, User
from app.schemas import ValueCreate, ValueResponse
from app.auth import get_current_active_user

router = APIRouter()

# Maximum length for value statement (matches database column definition)
MAX_STATEMENT_LENGTH = 255


def validate_statement(statement: str) -> str:
    """
    Validate and normalize a value statement.

    Args:
        statement: The value statement to validate

    Returns:
        The trimmed statement

    Raises:
        HTTPException: If validation fails
    """
    if not statement or not statement.strip():
        raise HTTPException(status_code=400, detail="Value statement cannot be empty")

    trimmed = statement.strip()
    if len(trimmed) > MAX_STATEMENT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Value statement must not exceed {MAX_STATEMENT_LENGTH} characters",
        )

    return trimmed


@router.get("/", response_model=list[ValueResponse])
async def list_values(
    include_archived: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List values for the authenticated user.

    By default, returns only active (non-archived) values.
    Set include_archived=true to include archived values in results.

    Args:
        include_archived: If True, includes archived values in the response.
                         If False (default), returns only active values.
        db: Database session
        current_user: Authenticated user

    Returns:
        List of values for the authenticated user
    """
    query = db.query(Value).filter(Value.user_id == current_user.id)

    if not include_archived:
        query = query.filter(~Value.archived)

    values = query.all()
    return values


@router.post("/", response_model=ValueResponse, status_code=status.HTTP_201_CREATED)
async def create_value(
    value_data: ValueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new value for the authenticated user."""
    validated_statement = validate_statement(value_data.statement)

    new_value = Value(
        user_id=current_user.id,
        statement=validated_statement,
    )
    db.add(new_value)
    db.commit()
    db.refresh(new_value)
    return new_value


@router.put("/{value_id}", response_model=ValueResponse)
async def update_value(
    value_id: int,
    value_data: ValueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a value statement for the authenticated user."""
    validated_statement = validate_statement(value_data.statement)

    value = (
        db.query(Value)
        .filter(Value.id == value_id, Value.user_id == current_user.id)
        .first()
    )

    if not value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Value not found"
        )

    value.statement = validated_statement
    db.commit()
    db.refresh(value)
    return value


@router.patch("/{value_id}/archive", response_model=ValueResponse)
async def archive_value(
    value_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Archive a value for the authenticated user.

    Archiving makes a value part of "Your Journey", showing when you focused
    on this value. Archived values do not affect existing task-value links.

    This endpoint is idempotent: archiving an already-archived value succeeds
    without error and preserves the original archived_at timestamp. This allows
    the UI to safely call archive multiple times without losing historical data.

    To focus on this value again, create a new active value with the same
    statement (UI provides "Revisit" button for this).

    Args:
        value_id: ID of the value to archive
        db: Database session
        current_user: Authenticated user

    Returns:
        The archived value with archived_at timestamp

    Raises:
        HTTPException: 404 if value not found or doesn't belong to user
    """
    value = (
        db.query(Value)
        .filter(Value.id == value_id, Value.user_id == current_user.id)
        .first()
    )

    if not value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Value not found"
        )

    # Idempotent: only set archived_at if not already set
    # This preserves the original archive date for historical accuracy
    if not value.archived:
        value.archived_at = datetime.utcnow()
        db.commit()
        db.refresh(value)

    # Return value whether newly archived or already archived
    return value
