"""
Value endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import ValueCreate, ValueResponse

router = APIRouter()


@router.get("/", response_model=list[ValueResponse])
async def list_values(db: Session = Depends(get_db)):
    """List all values."""
    # TODO: Implement
    return []


@router.post("/", response_model=ValueResponse)
async def create_value(value: ValueCreate, db: Session = Depends(get_db)):
    """Create a new value."""
    # TODO: Implement
    pass


@router.put("/{value_id}", response_model=ValueResponse)
async def update_value(
    value_id: int, value: ValueCreate, db: Session = Depends(get_db)
):
    """Update a value."""
    # TODO: Implement
    pass


@router.delete("/{value_id}")
async def delete_value(value_id: int, db: Session = Depends(get_db)):
    """Delete a value (archive)."""
    # TODO: Implement
    pass
