"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Annotated
from pydantic import BaseModel, Field, BeforeValidator, PlainSerializer


def ensure_utc_timezone(v: Optional[datetime]) -> Optional[datetime]:
    """Ensure datetime has UTC timezone for proper serialization.

    SQLite DateTime columns return naive datetimes. This validator adds
    UTC timezone info so they serialize correctly with timezone suffix.
    Converts non-UTC aware datetimes to UTC.
    """
    if v is None:
        return None
    if not isinstance(v, datetime):
        raise TypeError(f"Expected datetime or None, got {type(v).__name__}")
    # If naive, assume UTC
    if v.tzinfo is None:
        return v.replace(tzinfo=timezone.utc)
    # If already aware but not UTC, convert to UTC
    if v.tzinfo != timezone.utc:
        return v.astimezone(timezone.utc)
    return v


def serialize_datetime_with_z(v: Optional[datetime]) -> Optional[str]:
    """Serialize datetime as ISO 8601 string with timezone info.

    Uses second precision for consistent formatting.
    Returns format like '2026-01-04T07:08:00Z' for UTC times.
    """
    if v is None:
        return None
    # Ensure UTC timezone (defensive, should already be handled by validator)
    if v.tzinfo is None:
        v = v.replace(tzinfo=timezone.utc)
    elif v.tzinfo != timezone.utc:
        v = v.astimezone(timezone.utc)
    # Serialize with second precision and Z suffix for UTC
    return v.isoformat(timespec="seconds").replace("+00:00", "Z")


# Custom datetime type that always serializes with timezone
AwareDatetime = Annotated[
    datetime,
    BeforeValidator(ensure_utc_timezone),
    PlainSerializer(serialize_datetime_with_z, return_type=str, when_used="json"),
]


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


class ReviewCardTypeEnum(str, Enum):
    """Review card types."""

    COMPLETION = "completion"
    REJECTION = "rejection"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    RECURRING = "recurring"


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
    value_ids: Optional[list[int]] = None
    impact: Optional[ImpactEnum] = None
    urgency: Optional[UrgencyEnum] = None
    state: Optional[TaskStateEnum] = None
    due_date: Optional[datetime] = None
    completion_percentage: Optional[int] = None
    notes: Optional[str] = None


class TaskTransition(BaseModel):
    """Task state transition request."""

    new_state: TaskStateEnum
    notes: Optional[str] = None
    completion_percentage: Optional[int] = None


class TaskResponse(BaseModel):
    """Task response."""

    id: int
    title: str
    description: Optional[str]
    value_ids: list[int]
    impact: ImpactEnum
    urgency: UrgencyEnum
    state: TaskStateEnum
    due_date: Optional[AwareDatetime]
    recurrence: RecurrenceEnum
    completion_percentage: Optional[int]
    notes: Optional[str]
    created_at: AwareDatetime
    updated_at: AwareDatetime
    completed_at: Optional[AwareDatetime] = None

    class Config:
        from_attributes = True


class TaskTransitionResponse(BaseModel):
    """Response from task state transition."""

    task: TaskResponse
    next_instance: Optional[TaskResponse] = None


# Value schemas
class ValueCreate(BaseModel):
    """Create value request."""

    statement: str


class ValueResponse(BaseModel):
    """Value response.

    Returns both the computed 'archived' boolean (for client convenience)
    and the 'archived_at' timestamp (source of truth for archive status).
    """

    id: int
    statement: str
    archived: bool  # Computed from archived_at via hybrid property
    created_at: AwareDatetime
    archived_at: Optional[AwareDatetime] = None  # NULL for active values

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


class RejectionResponse(BaseModel):
    """Response for task rejection."""

    message: str
    task_id: int


class BreakResponse(BaseModel):
    """Response for taking a break."""

    message: str
    cleared_count: int


# Review schemas
class ReviewCardsRequest(BaseModel):
    """Request to generate review cards."""

    pass


class ReviewCardResponse(BaseModel):
    """Review card response."""

    id: int
    type: ReviewCardTypeEnum
    task_id: Optional[int]
    content: str
    responses: list[dict]  # [{"option": "str", "action": "handler_key"}, ...]
    generated_at: AwareDatetime

    class Config:
        from_attributes = True


class ReviewCard(BaseModel):
    """Generic review card (legacy, for backward compatibility)."""

    id: str
    card_type: str  # "completion", "rejection", "in_progress", "blocked", "recurring"
    content: str
    responses: list[dict]  # [{"option": "str", "action": "handler_key"}, ...]


# Auth schemas
class UserCreate(BaseModel):
    """User registration request."""

    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    """User login request."""

    username: str
    password: str


class UserResponse(BaseModel):
    """User response (public data only)."""

    id: int
    username: str
    email: str
    is_active: bool
    created_at: AwareDatetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
