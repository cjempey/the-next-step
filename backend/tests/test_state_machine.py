"""Tests for task state machine and transitions."""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import (
    Base,
    Task,
    User,
    TaskStateEnum,
    RecurrenceEnum,
    ImpactEnum,
    UrgencyEnum,
)
from app.services.state_machine import (
    is_transition_allowed,
    validate_transition,
    transition_task_state,
    create_recurring_instance,
    InvalidStateTransitionError,
    ALLOWED_TRANSITIONS,
)

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables once for all tests
Base.metadata.create_all(bind=engine)


@pytest.fixture
def db_session():
    """Create a fresh database session for each test."""
    # Create a new connection for each test
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    # Rollback transaction and close connection
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    # Use a UUID to ensure unique users per test
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    user = User(
        username=f"testuser_{unique_id}",
        email=f"test_{unique_id}@example.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYKJkPx0tAi",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_task(db_session, test_user):
    """Create a test task in Ready state."""
    task = Task(
        user_id=test_user.id,
        title="Test Task",
        description="Test description",
        impact=ImpactEnum.B,
        urgency=UrgencyEnum.CAN_DEFER,
        state=TaskStateEnum.READY,
        recurrence=RecurrenceEnum.NONE,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


class TestAllowedTransitions:
    """Test the allowed transitions mapping."""

    def test_allowed_transitions_complete(self):
        """Verify all states have defined transitions."""
        for state in TaskStateEnum:
            assert state in ALLOWED_TRANSITIONS

    def test_ready_allowed_transitions(self):
        """Test allowed transitions from Ready state."""
        assert TaskStateEnum.IN_PROGRESS in ALLOWED_TRANSITIONS[TaskStateEnum.READY]
        assert TaskStateEnum.BLOCKED in ALLOWED_TRANSITIONS[TaskStateEnum.READY]
        assert TaskStateEnum.PARKED in ALLOWED_TRANSITIONS[TaskStateEnum.READY]
        assert TaskStateEnum.CANCELLED in ALLOWED_TRANSITIONS[TaskStateEnum.READY]
        assert TaskStateEnum.COMPLETED not in ALLOWED_TRANSITIONS[TaskStateEnum.READY]

    def test_in_progress_allowed_transitions(self):
        """Test allowed transitions from In Progress state."""
        assert TaskStateEnum.COMPLETED in ALLOWED_TRANSITIONS[TaskStateEnum.IN_PROGRESS]
        assert TaskStateEnum.BLOCKED in ALLOWED_TRANSITIONS[TaskStateEnum.IN_PROGRESS]
        assert TaskStateEnum.PARKED in ALLOWED_TRANSITIONS[TaskStateEnum.IN_PROGRESS]
        assert TaskStateEnum.CANCELLED in ALLOWED_TRANSITIONS[TaskStateEnum.IN_PROGRESS]
        assert TaskStateEnum.READY in ALLOWED_TRANSITIONS[TaskStateEnum.IN_PROGRESS]

    def test_blocked_allowed_transitions(self):
        """Test allowed transitions from Blocked state."""
        assert TaskStateEnum.READY in ALLOWED_TRANSITIONS[TaskStateEnum.BLOCKED]
        assert TaskStateEnum.PARKED in ALLOWED_TRANSITIONS[TaskStateEnum.BLOCKED]
        assert TaskStateEnum.CANCELLED in ALLOWED_TRANSITIONS[TaskStateEnum.BLOCKED]
        assert (
            TaskStateEnum.IN_PROGRESS not in ALLOWED_TRANSITIONS[TaskStateEnum.BLOCKED]
        )
        assert TaskStateEnum.COMPLETED not in ALLOWED_TRANSITIONS[TaskStateEnum.BLOCKED]

    def test_parked_allowed_transitions(self):
        """Test allowed transitions from Parked state."""
        assert TaskStateEnum.READY in ALLOWED_TRANSITIONS[TaskStateEnum.PARKED]
        assert TaskStateEnum.CANCELLED in ALLOWED_TRANSITIONS[TaskStateEnum.PARKED]
        assert (
            TaskStateEnum.IN_PROGRESS not in ALLOWED_TRANSITIONS[TaskStateEnum.PARKED]
        )
        assert TaskStateEnum.BLOCKED not in ALLOWED_TRANSITIONS[TaskStateEnum.PARKED]
        assert TaskStateEnum.COMPLETED not in ALLOWED_TRANSITIONS[TaskStateEnum.PARKED]

    def test_completed_no_transitions(self):
        """Test that Completed is a final state."""
        assert len(ALLOWED_TRANSITIONS[TaskStateEnum.COMPLETED]) == 0

    def test_cancelled_no_transitions(self):
        """Test that Cancelled is a final state."""
        assert len(ALLOWED_TRANSITIONS[TaskStateEnum.CANCELLED]) == 0


class TestTransitionValidation:
    """Test transition validation logic."""

    def test_is_transition_allowed_valid(self):
        """Test valid transitions are allowed."""
        assert (
            is_transition_allowed(TaskStateEnum.READY, TaskStateEnum.IN_PROGRESS)
            is True
        )
        assert (
            is_transition_allowed(TaskStateEnum.IN_PROGRESS, TaskStateEnum.COMPLETED)
            is True
        )
        assert is_transition_allowed(TaskStateEnum.BLOCKED, TaskStateEnum.READY) is True

    def test_is_transition_allowed_invalid(self):
        """Test invalid transitions are rejected."""
        assert (
            is_transition_allowed(TaskStateEnum.COMPLETED, TaskStateEnum.READY) is False
        )
        assert (
            is_transition_allowed(TaskStateEnum.CANCELLED, TaskStateEnum.READY) is False
        )
        assert (
            is_transition_allowed(TaskStateEnum.READY, TaskStateEnum.COMPLETED) is False
        )

    def test_validate_transition_valid(self):
        """Test validate_transition doesn't raise for valid transitions."""
        validate_transition(TaskStateEnum.READY, TaskStateEnum.IN_PROGRESS)
        validate_transition(TaskStateEnum.IN_PROGRESS, TaskStateEnum.COMPLETED)
        # Should not raise

    def test_validate_transition_invalid(self):
        """Test validate_transition raises for invalid transitions."""
        with pytest.raises(InvalidStateTransitionError):
            validate_transition(TaskStateEnum.COMPLETED, TaskStateEnum.READY)

        with pytest.raises(InvalidStateTransitionError):
            validate_transition(TaskStateEnum.CANCELLED, TaskStateEnum.IN_PROGRESS)


class TestStateTransitions:
    """Test actual task state transitions."""

    def test_transition_ready_to_in_progress(self, db_session, test_task):
        """Test transitioning from Ready to In Progress."""
        assert test_task.state == TaskStateEnum.READY

        transition_task_state(db_session, test_task, TaskStateEnum.IN_PROGRESS)

        assert test_task.state == TaskStateEnum.IN_PROGRESS
        assert test_task.completed_at is None

    def test_transition_in_progress_to_completed(self, db_session, test_task):
        """Test transitioning from In Progress to Completed sets completed_at."""
        test_task.state = TaskStateEnum.IN_PROGRESS
        db_session.commit()

        before_transition = datetime.now(timezone.utc)
        transition_task_state(db_session, test_task, TaskStateEnum.COMPLETED)
        after_transition = datetime.now(timezone.utc)

        assert test_task.state == TaskStateEnum.COMPLETED
        assert test_task.completed_at is not None
        assert before_transition <= test_task.completed_at <= after_transition

    def test_transition_with_notes(self, db_session, test_task):
        """Test transition captures notes."""
        notes_text = "Made good progress today"
        transition_task_state(
            db_session, test_task, TaskStateEnum.IN_PROGRESS, notes=notes_text
        )

        assert test_task.notes == notes_text

    def test_transition_with_completion_percentage(self, db_session, test_task):
        """Test transition captures completion percentage."""
        transition_task_state(
            db_session, test_task, TaskStateEnum.IN_PROGRESS, completion_percentage=50
        )

        assert test_task.completion_percentage == 50

    def test_transition_blocked_to_ready(self, db_session, test_task):
        """Test unblocking a task."""
        test_task.state = TaskStateEnum.BLOCKED
        db_session.commit()

        transition_task_state(db_session, test_task, TaskStateEnum.READY)

        assert test_task.state == TaskStateEnum.READY

    def test_transition_parked_to_ready(self, db_session, test_task):
        """Test resuming a parked task."""
        test_task.state = TaskStateEnum.PARKED
        db_session.commit()

        transition_task_state(db_session, test_task, TaskStateEnum.READY)

        assert test_task.state == TaskStateEnum.READY

    def test_transition_in_progress_to_blocked(self, db_session, test_task):
        """Test blocking an in-progress task."""
        test_task.state = TaskStateEnum.IN_PROGRESS
        db_session.commit()

        transition_task_state(db_session, test_task, TaskStateEnum.BLOCKED)

        assert test_task.state == TaskStateEnum.BLOCKED

    def test_transition_invalid_raises_error(self, db_session, test_task):
        """Test invalid transition raises error."""
        test_task.state = TaskStateEnum.COMPLETED
        db_session.commit()

        with pytest.raises(InvalidStateTransitionError):
            transition_task_state(db_session, test_task, TaskStateEnum.READY)


class TestRecurringTasks:
    """Test recurring task auto-creation."""

    def test_create_recurring_instance_non_recurring(self, db_session, test_task):
        """Test that non-recurring tasks don't create instances."""
        test_task.recurrence = RecurrenceEnum.NONE

        next_instance = create_recurring_instance(db_session, test_task)

        assert next_instance is None

    def test_create_recurring_instance_daily(self, db_session, test_task):
        """Test daily recurring task creates next instance."""
        test_task.recurrence = RecurrenceEnum.DAILY
        test_task.due_date = datetime(2026, 1, 20, 12, 0, 0, tzinfo=timezone.utc)

        next_instance = create_recurring_instance(db_session, test_task)

        assert next_instance is not None
        assert next_instance.title == test_task.title
        assert next_instance.description == test_task.description
        assert next_instance.state == TaskStateEnum.READY
        assert next_instance.recurrence == RecurrenceEnum.DAILY
        assert next_instance.parent_task_id == test_task.id
        assert next_instance.due_date == datetime(
            2026, 1, 21, 12, 0, 0, tzinfo=timezone.utc
        )
        assert next_instance.completion_percentage == 0
        assert next_instance.notes is None

    def test_create_recurring_instance_weekly(self, db_session, test_task):
        """Test weekly recurring task creates next instance."""
        test_task.recurrence = RecurrenceEnum.WEEKLY
        test_task.due_date = datetime(2026, 1, 20, 12, 0, 0, tzinfo=timezone.utc)

        next_instance = create_recurring_instance(db_session, test_task)

        assert next_instance is not None
        assert next_instance.due_date == datetime(
            2026, 1, 27, 12, 0, 0, tzinfo=timezone.utc
        )

    def test_create_recurring_instance_no_due_date(self, db_session, test_task):
        """Test recurring task without due date still creates instance."""
        test_task.recurrence = RecurrenceEnum.DAILY
        test_task.due_date = None

        next_instance = create_recurring_instance(db_session, test_task)

        assert next_instance is not None
        assert next_instance.due_date is None
        assert next_instance.state == TaskStateEnum.READY

    def test_transition_to_completed_creates_recurring(self, db_session, test_task):
        """Test completing recurring task auto-creates next instance."""
        test_task.state = TaskStateEnum.IN_PROGRESS
        test_task.recurrence = RecurrenceEnum.DAILY
        test_task.due_date = datetime(2026, 1, 20, 12, 0, 0, tzinfo=timezone.utc)
        db_session.commit()

        next_instance = transition_task_state(
            db_session, test_task, TaskStateEnum.COMPLETED
        )

        assert next_instance is not None
        assert test_task.state == TaskStateEnum.COMPLETED
        assert next_instance.state == TaskStateEnum.READY
        assert next_instance.parent_task_id == test_task.id

    def test_transition_to_completed_non_recurring(self, db_session, test_task):
        """Test completing non-recurring task doesn't create instance."""
        test_task.state = TaskStateEnum.IN_PROGRESS
        test_task.recurrence = RecurrenceEnum.NONE
        db_session.commit()

        next_instance = transition_task_state(
            db_session, test_task, TaskStateEnum.COMPLETED
        )

        assert next_instance is None
        assert test_task.state == TaskStateEnum.COMPLETED


class TestAllValidTransitions:
    """Comprehensive test of all valid state transitions from spec."""

    @pytest.mark.parametrize(
        "from_state,to_state",
        [
            # From Ready
            (TaskStateEnum.READY, TaskStateEnum.IN_PROGRESS),
            (TaskStateEnum.READY, TaskStateEnum.BLOCKED),
            (TaskStateEnum.READY, TaskStateEnum.PARKED),
            (TaskStateEnum.READY, TaskStateEnum.CANCELLED),
            # From In Progress
            (TaskStateEnum.IN_PROGRESS, TaskStateEnum.COMPLETED),
            (TaskStateEnum.IN_PROGRESS, TaskStateEnum.BLOCKED),
            (TaskStateEnum.IN_PROGRESS, TaskStateEnum.PARKED),
            (TaskStateEnum.IN_PROGRESS, TaskStateEnum.CANCELLED),
            (TaskStateEnum.IN_PROGRESS, TaskStateEnum.READY),
            # From Blocked
            (TaskStateEnum.BLOCKED, TaskStateEnum.READY),
            (TaskStateEnum.BLOCKED, TaskStateEnum.PARKED),
            (TaskStateEnum.BLOCKED, TaskStateEnum.CANCELLED),
            # From Parked
            (TaskStateEnum.PARKED, TaskStateEnum.READY),
            (TaskStateEnum.PARKED, TaskStateEnum.CANCELLED),
        ],
    )
    def test_valid_transition(self, db_session, test_user, from_state, to_state):
        """Test all valid transitions from the spec."""
        task = Task(
            user_id=test_user.id,
            title="Test Task",
            impact=ImpactEnum.B,
            urgency=UrgencyEnum.CAN_DEFER,
            state=from_state,
        )
        db_session.add(task)
        db_session.commit()

        transition_task_state(db_session, task, to_state)

        assert task.state == to_state


class TestAllInvalidTransitions:
    """Comprehensive test of invalid state transitions."""

    @pytest.mark.parametrize(
        "from_state,to_state",
        [
            # From Ready (can't go directly to Completed)
            (TaskStateEnum.READY, TaskStateEnum.COMPLETED),
            # From In Progress (all transitions are valid)
            # From Blocked (can't go to In Progress or Completed)
            (TaskStateEnum.BLOCKED, TaskStateEnum.IN_PROGRESS),
            (TaskStateEnum.BLOCKED, TaskStateEnum.COMPLETED),
            # From Parked (can't go to In Progress, Blocked, or Completed)
            (TaskStateEnum.PARKED, TaskStateEnum.IN_PROGRESS),
            (TaskStateEnum.PARKED, TaskStateEnum.BLOCKED),
            (TaskStateEnum.PARKED, TaskStateEnum.COMPLETED),
            # From Completed (final state - no transitions)
            (TaskStateEnum.COMPLETED, TaskStateEnum.READY),
            (TaskStateEnum.COMPLETED, TaskStateEnum.IN_PROGRESS),
            (TaskStateEnum.COMPLETED, TaskStateEnum.BLOCKED),
            (TaskStateEnum.COMPLETED, TaskStateEnum.PARKED),
            (TaskStateEnum.COMPLETED, TaskStateEnum.CANCELLED),
            # From Cancelled (final state - no transitions)
            (TaskStateEnum.CANCELLED, TaskStateEnum.READY),
            (TaskStateEnum.CANCELLED, TaskStateEnum.IN_PROGRESS),
            (TaskStateEnum.CANCELLED, TaskStateEnum.BLOCKED),
            (TaskStateEnum.CANCELLED, TaskStateEnum.PARKED),
            (TaskStateEnum.CANCELLED, TaskStateEnum.COMPLETED),
        ],
    )
    def test_invalid_transition(self, db_session, test_user, from_state, to_state):
        """Test all invalid transitions raise errors."""
        task = Task(
            user_id=test_user.id,
            title="Test Task",
            impact=ImpactEnum.B,
            urgency=UrgencyEnum.CAN_DEFER,
            state=from_state,
        )
        db_session.add(task)
        db_session.commit()

        with pytest.raises(InvalidStateTransitionError):
            transition_task_state(db_session, task, to_state)

        # State should not have changed
        assert task.state == from_state
