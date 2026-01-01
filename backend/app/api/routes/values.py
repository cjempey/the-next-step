"""
Value endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import ValueCreate, ValueResponse
from app.models import Value, User
from app.auth import get_current_active_user

router = APIRouter()


@router.get("/", response_model=list[ValueResponse])
async def list_values(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """List all values for the authenticated user."""
    values = db.query(Value).filter(Value.user_id == current_user.id).all()
    return values


@router.post("/", response_model=ValueResponse, status_code=status.HTTP_201_CREATED)
async def create_value(
    value_data: ValueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new value for the authenticated user."""
    new_value = Value(
        user_id=current_user.id,
        statement=value_data.statement,
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
    """Update a value for the authenticated user."""
    value = (
        db.query(Value)
        .filter(Value.id == value_id, Value.user_id == current_user.id)
        .first()
    )

    if not value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Value not found"
        )

    value.statement = value_data.statement
    db.commit()
    db.refresh(value)
    return value


@router.delete("/{value_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_value(
    value_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a value (archive) for the authenticated user."""
    value = (
        db.query(Value)
        .filter(Value.id == value_id, Value.user_id == current_user.id)
        .first()
    )

    if not value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Value not found"
        )

    value.archived = True
    db.commit()
