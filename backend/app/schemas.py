"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ImpactEnum(str, Enum):
    """Task impact levels."""

    A = "A"
    B = "B"
    C = "C"
    D = "D"


class UrgencyEnum(int, Enum):
    """Task urgency levels."""

    IMMEDIATE = 1
    SOON = 2
    CAN_DEFER = 3
    LONGTERM = 4


class TaskStateEnum(str, Enum):
    """Task states."""

    READY = "Ready"
    IN_PROGRESS = "In Progress"
    BLOCKED = "Blocked"
    PARKED = "Parked"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class RecurrenceEnum(str, Enum):
    """Recurrence patterns."""

    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"


# Task schemas
class TaskCreate(BaseModel):
    """Create task request."""

    title: str
    description: Optional[str] = None
    value_ids: list[int] = Field(default_factory=list)
    impact: Optional[ImpactEnum] = None
    urgency: Optional[UrgencyEnum] = None
    due_date: Optional[datetime] = None
    recurrence: RecurrenceEnum = RecurrenceEnum.NONE


class TaskUpdate(BaseModel):
    """Update task request."""

    title: Optional[str] = None
    description: Optional[str] = None
    impact: Optional[ImpactEnum] = None
    urgency: Optional[UrgencyEnum] = None
    state: Optional[TaskStateEnum] = None
    due_date: Optional[datetime] = None
    completion_percentage: Optional[int] = None
    notes: Optional[str] = None


class TaskResponse(BaseModel):
    """Task response."""

    id: int
    title: str
    description: Optional[str]
    value_ids: list[int]
    impact: ImpactEnum
    urgency: UrgencyEnum
    state: TaskStateEnum
    due_date: Optional[datetime]
    completion_percentage: Optional[int]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Value schemas
class ValueCreate(BaseModel):
    """Create value request."""

    statement: str


class ValueResponse(BaseModel):
    """Value response."""

    id: int
    statement: str
    archived: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Suggestion schemas
class SuggestionRequest(BaseModel):
    """Request for next task suggestion."""

    include_in_progress: bool = False


class SuggestionResponse(BaseModel):
    """Single task suggestion."""

    task: TaskResponse
    reason: str  # Human-readable explanation


# Review schemas
class ReviewCardsRequest(BaseModel):
    """Request to generate review cards."""

    pass


class ReviewCard(BaseModel):
    """Generic review card."""

    id: str
    card_type: str  # "completion", "rejection", "in_progress", "blocked", "recurring"
    content: str
    responses: list[dict]  # [{"option": "str", "action": "handler_key"}, ...]
