"""
Value endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Value
from app.schemas import ValueCreate, ValueResponse

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


@router.post("/", response_model=ValueResponse, status_code=201)
async def create_value(value: ValueCreate, db: Session = Depends(get_db)):
    """Create a new value."""
    validated_statement = validate_statement(value.statement)

    # Create new value
    db_value = Value(statement=validated_statement, archived=False)
    db.add(db_value)
    db.commit()
    db.refresh(db_value)
    return db_value


@router.get("/", response_model=list[ValueResponse])
async def list_values(db: Session = Depends(get_db)):
    """List all active values (non-archived)."""
    values = db.query(Value).filter(~Value.archived).all()
    return values


@router.put("/{value_id}", response_model=ValueResponse)
async def update_value(
    value_id: int, value: ValueCreate, db: Session = Depends(get_db)
):
    """Update a value statement."""
    validated_statement = validate_statement(value.statement)

    # Find the value
    db_value = db.query(Value).filter(Value.id == value_id).first()
    if not db_value:
        raise HTTPException(status_code=404, detail="Value not found")

    # Update the statement
    db_value.statement = validated_statement  # type: ignore[assignment]
    db.commit()
    db.refresh(db_value)
    return db_value


@router.patch("/{value_id}/archive", response_model=ValueResponse)
async def archive_value(value_id: int, db: Session = Depends(get_db)):
    """Archive/deactivate a value. Does not affect existing task-value links."""
    # Find the value
    db_value = db.query(Value).filter(Value.id == value_id).first()
    if not db_value:
        raise HTTPException(status_code=404, detail="Value not found")

    # Archive the value
    db_value.archived = True  # type: ignore[assignment]
    db.commit()
    db.refresh(db_value)
    return db_value
