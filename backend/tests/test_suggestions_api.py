"""Tests for suggestions API endpoints."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import get_current_active_user
from app.core.database import get_db
from app.main import app
from app.models import (
    Base,
    DailyPriority,
    ImpactEnum,
    RejectionDampening,
    Task,
    TaskStateEnum,
    UrgencyEnum,
    User,
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

# Test user storage for authentication override
_test_user_data = None


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


async def override_get_current_active_user():
    """Override authentication to return test user without requiring valid JWT."""
    if _test_user_data is None:
        raise Exception("No test user set")

    class MockUser:
        def __init__(self, id, username, email, is_active):
            self.id = id
            self.username = username
            self.email = email
            self.is_active = is_active

    return MockUser(
        id=_test_user_data["id"],
        username=_test_user_data["username"],
        email=_test_user_data["email"],
        is_active=_test_user_data["is_active"],
    )


# Create test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def override_dependencies():
    """Set up and tear down FastAPI dependency overrides for each test."""
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def db():
    """Create a fresh database session for each test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        # Clean up all data after each test
        session.query(DailyPriority).delete()
        session.query(RejectionDampening).delete()
        session.query(Task).delete()
        session.query(User).delete()
        session.commit()
        session.close()


@pytest.fixture
def test_user(db):
    """Create a test user."""
    global _test_user_data
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="$2b$12$test",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Store user data as dict to avoid session issues
    _test_user_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
    }
    return user


class TestGetNextSuggestion:
    """Tests for /api/suggestions/next endpoint."""

    def test_get_next_suggestion_single_task(self, db, test_user):
        """Test getting suggestion with single task."""
        task = Task(
            user_id=test_user.id,
            title="Only task",
            impact=ImpactEnum.B,
            urgency=UrgencyEnum.SOON,
            state=TaskStateEnum.READY,
        )
        db.add(task)
        db.commit()

        response = client.post(
            "/api/suggestions/next", json={"include_in_progress": False}
        )

        assert response.status_code == 200
        data = response.json()
        assert "task" in data
        assert "reason" in data
        assert data["task"]["title"] == "Only task"
        assert "Impact:B Urgency:2" in data["reason"]

    def test_get_next_suggestion_no_tasks(self, db, test_user):
        """Test getting suggestion with no tasks returns 404."""
        response = client.post(
            "/api/suggestions/next", json={"include_in_progress": False}
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "No tasks available"

    def test_get_next_suggestion_only_ready_tasks(self, db, test_user):
        """Test that only Ready tasks are suggested by default."""
        ready_task = Task(
            user_id=test_user.id,
            title="Ready task",
            impact=ImpactEnum.B,
            urgency=UrgencyEnum.SOON,
            state=TaskStateEnum.READY,
        )
        blocked_task = Task(
            user_id=test_user.id,
            title="Blocked task",
            impact=ImpactEnum.A,
            urgency=UrgencyEnum.IMMEDIATE,
            state=TaskStateEnum.BLOCKED,
        )
        db.add_all([ready_task, blocked_task])
        db.commit()

        response = client.post(
            "/api/suggestions/next", json={"include_in_progress": False}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["task"]["title"] == "Ready task"

    def test_get_next_suggestion_include_in_progress(self, db, test_user):
        """Test including in-progress tasks."""
        ready_task = Task(
            user_id=test_user.id,
            title="Ready task",
            impact=ImpactEnum.B,
            urgency=UrgencyEnum.SOON,
            state=TaskStateEnum.READY,
        )
        in_progress_task = Task(
            user_id=test_user.id,
            title="In progress task",
            impact=ImpactEnum.A,
            urgency=UrgencyEnum.IMMEDIATE,
            state=TaskStateEnum.IN_PROGRESS,
        )
        db.add_all([ready_task, in_progress_task])
        db.commit()

        response = client.post(
            "/api/suggestions/next", json={"include_in_progress": True}
        )

        assert response.status_code == 200
        data = response.json()
        # In progress task has higher score, should be more likely
        assert data["task"]["title"] in ["Ready task", "In progress task"]

    def test_get_next_suggestion_respects_dampening(self, db, test_user):
        """Test that dampening affects suggestions."""
        high_score_task = Task(
            user_id=test_user.id,
            title="High score",
            impact=ImpactEnum.A,
            urgency=UrgencyEnum.IMMEDIATE,
            state=TaskStateEnum.READY,
        )
        db.add(high_score_task)
        db.commit()

        # Add dampening
        dampening = RejectionDampening(
            user_id=test_user.id,
            task_id=high_score_task.id,
            expires_at="next_review",
        )
        db.add(dampening)
        db.commit()

        response = client.post(
            "/api/suggestions/next", json={"include_in_progress": False}
        )

        assert response.status_code == 200
        data = response.json()
        assert "dampened (rejected)" in data["reason"]

    def test_get_next_suggestion_respects_daily_priority(self, db, test_user):
        """Test that daily priority boosts suggestions."""
        task = Task(
            user_id=test_user.id,
            title="Priority task",
            impact=ImpactEnum.C,
            urgency=UrgencyEnum.CAN_DEFER,
            state=TaskStateEnum.READY,
        )
        db.add(task)
        db.commit()

        # Add daily priority
        priority = DailyPriority(
            user_id=test_user.id,
            task_id=task.id,
            priority_date=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=12),
        )
        db.add(priority)
        db.commit()

        response = client.post(
            "/api/suggestions/next", json={"include_in_progress": False}
        )

        assert response.status_code == 200
        data = response.json()
        assert "daily priority" in data["reason"]


class TestListScoringStrategies:
    """Tests for /api/suggestions/strategies endpoint."""

    def test_list_strategies(self, db, test_user):
        """Test listing available strategies."""
        response = client.get("/api/suggestions/strategies")

        assert response.status_code == 200
        data = response.json()
        assert "strategies" in data
        assert len(data["strategies"]) >= 1
        assert any(s["name"] == "additive_weighted" for s in data["strategies"])


class TestGetRankedTasks:
    """Tests for /api/suggestions/planning/ranked-tasks endpoint."""

    def test_ranked_tasks_empty(self, db, test_user):
        """Test ranked tasks with no tasks."""
        response = client.get("/api/suggestions/planning/ranked-tasks")

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert len(data["tasks"]) == 0

    def test_ranked_tasks_sorted_by_score(self, db, test_user):
        """Test tasks are ranked in descending score order."""
        # Create tasks with different scores
        task_a1 = Task(
            user_id=test_user.id,
            title="A1",
            impact=ImpactEnum.A,
            urgency=UrgencyEnum.IMMEDIATE,
            state=TaskStateEnum.READY,
        )
        task_b2 = Task(
            user_id=test_user.id,
            title="B2",
            impact=ImpactEnum.B,
            urgency=UrgencyEnum.SOON,
            state=TaskStateEnum.READY,
        )
        task_d4 = Task(
            user_id=test_user.id,
            title="D4",
            impact=ImpactEnum.D,
            urgency=UrgencyEnum.LONGTERM,
            state=TaskStateEnum.READY,
        )
        db.add_all([task_d4, task_a1, task_b2])
        db.commit()

        response = client.get("/api/suggestions/planning/ranked-tasks")

        assert response.status_code == 200
        data = response.json()
        tasks = data["tasks"]
        assert len(tasks) == 3

        # Should be in descending order: A1, B2, D4
        assert tasks[0]["task"]["title"] == "A1"
        assert tasks[1]["task"]["title"] == "B2"
        assert tasks[2]["task"]["title"] == "D4"

        # Verify scores are descending
        assert tasks[0]["score"] > tasks[1]["score"] > tasks[2]["score"]

    def test_ranked_tasks_includes_reasons(self, db, test_user):
        """Test ranked tasks include reason strings."""
        task = Task(
            user_id=test_user.id,
            title="Task with reason",
            impact=ImpactEnum.A,
            urgency=UrgencyEnum.CAN_DEFER,
            state=TaskStateEnum.READY,
        )
        db.add(task)
        db.commit()

        response = client.get("/api/suggestions/planning/ranked-tasks")

        assert response.status_code == 200
        data = response.json()
        tasks = data["tasks"]
        assert len(tasks) == 1
        assert "reason" in tasks[0]
        assert "Impact:A Urgency:3" in tasks[0]["reason"]
        assert "strategic nudge" in tasks[0]["reason"]

    def test_ranked_tasks_only_ready(self, db, test_user):
        """Test ranked tasks only includes Ready tasks."""
        ready_task = Task(
            user_id=test_user.id,
            title="Ready",
            impact=ImpactEnum.B,
            urgency=UrgencyEnum.SOON,
            state=TaskStateEnum.READY,
        )
        blocked_task = Task(
            user_id=test_user.id,
            title="Blocked",
            impact=ImpactEnum.A,
            urgency=UrgencyEnum.IMMEDIATE,
            state=TaskStateEnum.BLOCKED,
        )
        db.add_all([ready_task, blocked_task])
        db.commit()

        response = client.get("/api/suggestions/planning/ranked-tasks")

        assert response.status_code == 200
        data = response.json()
        tasks = data["tasks"]
        assert len(tasks) == 1
        assert tasks[0]["task"]["title"] == "Ready"


class TestRejectSuggestion:
    """Tests for /api/suggestions/reject endpoint."""

    def test_reject_suggestion_creates_dampening(self, db, test_user):
        """Test that rejecting a task creates a dampening record."""
        task = Task(
            user_id=test_user.id,
            title="Task to reject",
            impact=ImpactEnum.B,
            urgency=UrgencyEnum.SOON,
            state=TaskStateEnum.READY,
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        response = client.post(f"/api/suggestions/reject?task_id={task.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Task rejected"
        assert data["task_id"] == task.id

        # Verify dampening record was created
        dampening = db.query(RejectionDampening).filter(
            RejectionDampening.user_id == test_user.id,
            RejectionDampening.task_id == task.id,
        ).first()
        assert dampening is not None
        assert dampening.expires_at == "next_break"

    def test_reject_suggestion_idempotent(self, db, test_user):
        """Test that rejecting same task multiple times is idempotent."""
        task = Task(
            user_id=test_user.id,
            title="Task to reject twice",
            impact=ImpactEnum.B,
            urgency=UrgencyEnum.SOON,
            state=TaskStateEnum.READY,
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        # First rejection
        response1 = client.post(f"/api/suggestions/reject?task_id={task.id}")
        assert response1.status_code == 200

        # Second rejection (should not create duplicate)
        response2 = client.post(f"/api/suggestions/reject?task_id={task.id}")
        assert response2.status_code == 200

        # Verify only one dampening record exists
        count = db.query(RejectionDampening).filter(
            RejectionDampening.user_id == test_user.id,
            RejectionDampening.task_id == task.id,
        ).count()
        assert count == 1

    def test_reject_suggestion_nonexistent_task(self, db, test_user):
        """Test rejecting a non-existent task returns 404."""
        response = client.post("/api/suggestions/reject?task_id=99999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"

    def test_reject_suggestion_other_users_task(self, db, test_user):
        """Test rejecting another user's task returns 404."""
        # Create another user
        other_user = User(
            username="otheruser",
            email="other@example.com",
            password_hash="$2b$12$test",
            is_active=True,
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        # Create task for other user
        task = Task(
            user_id=other_user.id,
            title="Other user's task",
            impact=ImpactEnum.B,
            urgency=UrgencyEnum.SOON,
            state=TaskStateEnum.READY,
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        # Try to reject as test_user
        response = client.post(f"/api/suggestions/reject?task_id={task.id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"


class TestTakeBreak:
    """Tests for /api/suggestions/break endpoint."""

    def test_take_break_clears_all_dampening(self, db, test_user):
        """Test that taking a break clears all rejection dampening."""
        # Create multiple tasks with dampening
        task1 = Task(
            user_id=test_user.id,
            title="Task 1",
            impact=ImpactEnum.B,
            urgency=UrgencyEnum.SOON,
            state=TaskStateEnum.READY,
        )
        task2 = Task(
            user_id=test_user.id,
            title="Task 2",
            impact=ImpactEnum.A,
            urgency=UrgencyEnum.IMMEDIATE,
            state=TaskStateEnum.READY,
        )
        db.add_all([task1, task2])
        db.commit()
        db.refresh(task1)
        db.refresh(task2)

        # Create dampening records
        dampening1 = RejectionDampening(
            user_id=test_user.id,
            task_id=task1.id,
            rejected_at=datetime.now(timezone.utc),
            expires_at="next_break",
        )
        dampening2 = RejectionDampening(
            user_id=test_user.id,
            task_id=task2.id,
            rejected_at=datetime.now(timezone.utc),
            expires_at="next_break",
        )
        db.add_all([dampening1, dampening2])
        db.commit()

        # Take break
        response = client.post("/api/suggestions/break")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Break taken, rejection dampening cleared"
        assert data["cleared_count"] == 2

        # Verify all dampening records are deleted
        count = db.query(RejectionDampening).filter(
            RejectionDampening.user_id == test_user.id
        ).count()
        assert count == 0

    def test_take_break_no_dampening(self, db, test_user):
        """Test taking a break with no existing dampening."""
        response = client.post("/api/suggestions/break")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Break taken, rejection dampening cleared"
        assert data["cleared_count"] == 0

    def test_take_break_only_clears_own_dampening(self, db, test_user):
        """Test that break only clears current user's dampening."""
        # Create another user
        other_user = User(
            username="otheruser",
            email="other@example.com",
            password_hash="$2b$12$test",
            is_active=True,
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        # Create tasks for both users
        test_task = Task(
            user_id=test_user.id,
            title="Test user's task",
            impact=ImpactEnum.B,
            urgency=UrgencyEnum.SOON,
            state=TaskStateEnum.READY,
        )
        other_task = Task(
            user_id=other_user.id,
            title="Other user's task",
            impact=ImpactEnum.B,
            urgency=UrgencyEnum.SOON,
            state=TaskStateEnum.READY,
        )
        db.add_all([test_task, other_task])
        db.commit()
        db.refresh(test_task)
        db.refresh(other_task)

        # Create dampening for both users
        test_dampening = RejectionDampening(
            user_id=test_user.id,
            task_id=test_task.id,
            rejected_at=datetime.now(timezone.utc),
            expires_at="next_break",
        )
        other_dampening = RejectionDampening(
            user_id=other_user.id,
            task_id=other_task.id,
            rejected_at=datetime.now(timezone.utc),
            expires_at="next_break",
        )
        db.add_all([test_dampening, other_dampening])
        db.commit()

        # Test user takes break
        response = client.post("/api/suggestions/break")

        assert response.status_code == 200
        data = response.json()
        assert data["cleared_count"] == 1

        # Verify only test user's dampening is cleared
        test_count = db.query(RejectionDampening).filter(
            RejectionDampening.user_id == test_user.id
        ).count()
        other_count = db.query(RejectionDampening).filter(
            RejectionDampening.user_id == other_user.id
        ).count()
        assert test_count == 0
        assert other_count == 1
