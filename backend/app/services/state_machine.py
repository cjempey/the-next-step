"""
Task state machine and transition validation.

Implements the 6-state model with validation per MVP Requirements section 9.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.models import Task, TaskStateEnum, RecurrenceEnum


# Define allowed state transitions based on MVP Requirements section 9
ALLOWED_TRANSITIONS: dict[TaskStateEnum, set[TaskStateEnum]] = {
    TaskStateEnum.READY: {
        TaskStateEnum.IN_PROGRESS,
        TaskStateEnum.BLOCKED,
        TaskStateEnum.PARKED,
        TaskStateEnum.CANCELLED,
    },
    TaskStateEnum.IN_PROGRESS: {
        TaskStateEnum.COMPLETED,
        TaskStateEnum.BLOCKED,
        TaskStateEnum.PARKED,
        TaskStateEnum.CANCELLED,
        TaskStateEnum.READY,  # Allow marking back to Ready
    },
    TaskStateEnum.BLOCKED: {
        TaskStateEnum.READY,
        TaskStateEnum.PARKED,
        TaskStateEnum.CANCELLED,
    },
    TaskStateEnum.PARKED: {
        TaskStateEnum.READY,
        TaskStateEnum.CANCELLED,
    },
    TaskStateEnum.COMPLETED: set(),  # Final state - no transitions out
    TaskStateEnum.CANCELLED: set(),  # Final state - no transitions out
}


class InvalidStateTransitionError(Exception):
    """Raised when attempting an invalid state transition."""

    pass


def is_transition_allowed(from_state: TaskStateEnum, to_state: TaskStateEnum) -> bool:
    """Check if a state transition is allowed.

    Args:
        from_state: Current state of the task
        to_state: Desired new state

    Returns:
        True if transition is allowed, False otherwise
    """
    return to_state in ALLOWED_TRANSITIONS.get(from_state, set())


def validate_transition(from_state: TaskStateEnum, to_state: TaskStateEnum) -> None:
    """Validate a state transition, raising an exception if invalid.

    Args:
        from_state: Current state of the task
        to_state: Desired new state

    Raises:
        InvalidStateTransitionError: If transition is not allowed
    """
    if not is_transition_allowed(from_state, to_state):
        raise InvalidStateTransitionError(
            f"Invalid transition from {from_state.value} to {to_state.value}"
        )


def create_recurring_instance(db: Session, completed_task: Task) -> Optional[Task]:
    """Create next instance of a recurring task.

    Called automatically when a recurring task is completed.
    Creates a new task with the same attributes in Ready state.

    Args:
        db: Database session
        completed_task: The task that was just completed

    Returns:
        The newly created task instance, or None if not recurring
    """
    # Only create next instance for recurring tasks
    if completed_task.recurrence == RecurrenceEnum.NONE:
        return None

    # Calculate next due date based on recurrence pattern
    next_due_date = None
    if completed_task.due_date:
        if completed_task.recurrence == RecurrenceEnum.DAILY:
            next_due_date = completed_task.due_date + timedelta(days=1)
        elif completed_task.recurrence == RecurrenceEnum.WEEKLY:
            next_due_date = completed_task.due_date + timedelta(weeks=1)

    # Create new task instance with same attributes
    new_task = Task(
        user_id=completed_task.user_id,
        title=completed_task.title,
        description=completed_task.description,
        impact=completed_task.impact,
        urgency=completed_task.urgency,
        state=TaskStateEnum.READY,
        due_date=next_due_date,
        recurrence=completed_task.recurrence,
        parent_task_id=completed_task.id,  # Link to parent for tracking
        completion_percentage=0,
        notes=None,  # Reset notes for new instance
    )

    # Copy value associations
    new_task.values = completed_task.values

    db.add(new_task)
    db.flush()  # Flush to get ID without committing transaction

    return new_task


def transition_task_state(
    db: Session,
    task: Task,
    new_state: TaskStateEnum,
    notes: Optional[str] = None,
    completion_percentage: Optional[int] = None,
) -> Optional[Task]:
    """Transition a task to a new state with validation.

    Args:
        db: Database session
        task: The task to transition
        new_state: The desired new state
        notes: Optional notes to capture with the transition
        completion_percentage: Optional completion percentage (for partial progress)

    Returns:
        The newly created recurring task instance if applicable, None otherwise

    Raises:
        InvalidStateTransitionError: If transition is not allowed
    """
    # Validate the transition
    validate_transition(task.state, new_state)

    # Update task state
    old_state = task.state
    task.state = new_state

    # Update optional fields if provided
    if notes is not None:
        task.notes = notes
    if completion_percentage is not None:
        task.completion_percentage = completion_percentage

    # Set completed_at timestamp when transitioning to Completed
    if new_state == TaskStateEnum.COMPLETED and old_state != TaskStateEnum.COMPLETED:
        task.completed_at = datetime.now(timezone.utc)

    # Clear completed_at if transitioning away from Completed (shouldn't happen per spec)
    elif old_state == TaskStateEnum.COMPLETED and new_state != TaskStateEnum.COMPLETED:
        task.completed_at = None

    # Create next instance for recurring tasks when completed
    new_instance = None
    if new_state == TaskStateEnum.COMPLETED:
        new_instance = create_recurring_instance(db, task)

    return new_instance
