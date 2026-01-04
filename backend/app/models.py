"""
SQLAlchemy ORM models.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Table,
    Enum,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
import enum

from app.core.database import Base


class ImpactEnum(str, enum.Enum):
    """Task impact levels."""

    A = "A"
    B = "B"
    C = "C"
    D = "D"


class UrgencyEnum(int, enum.Enum):
    """Task urgency levels."""

    IMMEDIATE = 1
    SOON = 2
    CAN_DEFER = 3
    LONGTERM = 4


class TaskStateEnum(str, enum.Enum):
    """Task states."""

    READY = "Ready"
    IN_PROGRESS = "In Progress"
    BLOCKED = "Blocked"
    PARKED = "Parked"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class RecurrenceEnum(str, enum.Enum):
    """Recurrence patterns."""

    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"


class ReviewCardTypeEnum(str, enum.Enum):
    """Review card types."""

    COMPLETION = "completion"
    REJECTION = "rejection"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    RECURRING = "recurring"


# Association table for tasks and values
task_value_association = Table(
    "task_value_association",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id")),
    Column("value_id", Integer, ForeignKey("values.id")),
)


class Task(Base):
    """Task model."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    impact = Column(Enum(ImpactEnum), nullable=False, default=ImpactEnum.B)
    urgency = Column(Enum(UrgencyEnum), nullable=False, default=UrgencyEnum.CAN_DEFER)
    state = Column(Enum(TaskStateEnum), nullable=False, default=TaskStateEnum.READY)
    due_date = Column(DateTime, nullable=True)
    recurrence = Column(
        Enum(RecurrenceEnum), nullable=False, default=RecurrenceEnum.NONE
    )
    completion_percentage = Column(Integer, nullable=True, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    completed_at = Column(DateTime, nullable=True)
    parent_task_id = Column(
        Integer, ForeignKey("tasks.id"), nullable=True
    )  # For recurring instances

    # Relationships
    values = relationship(
        "Value", secondary=task_value_association, back_populates="tasks"
    )
    parent_task = relationship("Task", remote_side=[id], backref="recurrence_instances")
    user = relationship("User", backref="tasks")


class Value(Base):
    """User-defined value model.

    The archived state is tracked via the archived_at timestamp:
    - archived_at = NULL: value is active
    - archived_at != NULL: value is archived (with timestamp of when it was archived)

    The hybrid property 'archived' provides a convenient boolean interface
    for Python code and SQL queries, computed from archived_at.
    """

    __tablename__ = "values"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    statement = Column(String(255), nullable=False)
    archived_at = Column(DateTime, nullable=True)  # NULL = active, NOT NULL = archived
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    # Computed property for backward compatibility and ergonomics
    @hybrid_property
    def archived(self) -> bool:
        """Return True if value is archived (has archived_at timestamp).

        This provides a convenient boolean interface in Python code:
            if value.archived: ...
        """
        return self.archived_at is not None

    @archived.expression
    def archived(cls):
        """SQL expression for filtering by archived status.

        This enables filtering in queries:
            query.filter(~Value.archived)  # active values only
            query.filter(Value.archived)   # archived values only
        """
        return cls.archived_at.isnot(None)

    # Relationships
    tasks = relationship(
        "Task", secondary=task_value_association, back_populates="values"
    )
    user = relationship("User", backref="values")


class RejectionDampening(Base):
    """Track task rejection dampening for suggestion algorithm."""

    __tablename__ = "rejection_dampening"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    rejected_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(String(50), nullable=False)  # "next_break" or "next_review"


class DailyPriority(Base):
    """Track daily task priorities set during morning planning."""

    __tablename__ = "daily_priorities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    priority_date = Column(
        DateTime, nullable=False
    )  # Date for which this is a priority
    expires_at = Column(DateTime, nullable=False)  # Evening review time


class ReviewHistory(Base):
    """Track review events for journaling."""

    __tablename__ = "review_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    review_date = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    action = Column(
        String(50), nullable=False
    )  # "completed", "blocked", "parked", etc.
    notes = Column(Text, nullable=True)


class ReviewCard(Base):
    """Review card for evening review flow (v2 feature)."""

    __tablename__ = "review_cards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(Enum(ReviewCardTypeEnum), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    content = Column(Text, nullable=False)
    responses = Column(JSON, nullable=False)  # Array of {option: str, action: str}
    generated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class User(Base):
    """User model for authentication."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
