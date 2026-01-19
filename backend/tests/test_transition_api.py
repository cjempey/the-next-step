"""Tests for task state transition API endpoint."""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone

from app.main import app
from app.core.database import get_db
from app.models import (
    Base,
    User,
    Task,
    ImpactEnum,
    UrgencyEnum,
    TaskStateEnum,
    RecurrenceEnum,
)
from app.auth import get_current_active_user

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
        raise HTTPException(status_code=401, detail="No test user set")

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


def create_test_user(db, username="testuser", email="test@example.com"):
    """Create a test user and return the user object."""
    global _test_user_data
    prehashed = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYKJkPx0tAi"
    user = User(username=username, email=email, password_hash=prehashed, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    _test_user_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
    }
    return user


@pytest.fixture(autouse=True)
def cleanup_database():
    """Clean up database tables after each test."""
    global _test_user_data
    yield
    db = TestingSessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
    finally:
        db.close()
    _test_user_data = None


def create_test_task(db, user_id, state=TaskStateEnum.READY, recurrence=RecurrenceEnum.NONE):
    """Helper to create a test task."""
    task = Task(
        user_id=user_id,
        title="Test Task",
        description="Test description",
        impact=ImpactEnum.B,
        urgency=UrgencyEnum.CAN_DEFER,
        state=state,
        recurrence=recurrence,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


class TestTransitionEndpoint:
    """Test the POST /tasks/{id}/transition endpoint."""

    def test_transition_ready_to_in_progress(self):
        """Test valid transition from Ready to In Progress."""
        db = TestingSessionLocal()
        user = create_test_user(db)
        task = create_test_task(db, user.id, TaskStateEnum.READY)
        db.close()

        response = client.post(
            f"/api/tasks/{task.id}/transition",
            json={"new_state": "In Progress"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["task"]["id"] == task.id
        assert data["task"]["state"] == "In Progress"
        assert data["task"]["completed_at"] is None
        assert data["next_instance"] is None

    def test_transition_in_progress_to_completed(self):
        """Test transition to Completed sets completed_at."""
        db = TestingSessionLocal()
        user = create_test_user(db)
        task = create_test_task(db, user.id, TaskStateEnum.IN_PROGRESS)
        db.close()

        response = client.post(
            f"/api/tasks/{task.id}/transition",
            json={"new_state": "Completed"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["task"]["state"] == "Completed"
        assert data["task"]["completed_at"] is not None
        # Verify it's a valid ISO timestamp
        datetime.fromisoformat(data["task"]["completed_at"].replace("Z", "+00:00"))

    def test_transition_with_notes(self):
        """Test transition captures notes."""
        db = TestingSessionLocal()
        user = create_test_user(db)
        task = create_test_task(db, user.id, TaskStateEnum.READY)
        db.close()

        response = client.post(
            f"/api/tasks/{task.id}/transition",
            json={
                "new_state": "In Progress",
                "notes": "Started working on this",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["task"]["notes"] == "Started working on this"

    def test_transition_with_completion_percentage(self):
        """Test transition captures completion percentage."""
        db = TestingSessionLocal()
        user = create_test_user(db)
        task = create_test_task(db, user.id, TaskStateEnum.IN_PROGRESS)
        db.close()

        response = client.post(
            f"/api/tasks/{task.id}/transition",
            json={
                "new_state": "Blocked",
                "completion_percentage": 75,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["task"]["completion_percentage"] == 75

    def test_transition_invalid_returns_400(self):
        """Test invalid transition returns 400 error."""
        db = TestingSessionLocal()
        user = create_test_user(db)
        task = create_test_task(db, user.id, TaskStateEnum.COMPLETED)
        db.close()

        response = client.post(
            f"/api/tasks/{task.id}/transition",
            json={"new_state": "Ready"},
        )

        assert response.status_code == 400
        assert "Invalid transition" in response.json()["detail"]

    def test_transition_nonexistent_task_returns_404(self):
        """Test transitioning nonexistent task returns 404."""
        db = TestingSessionLocal()
        create_test_user(db)
        db.close()

        response = client.post(
            "/api/tasks/99999/transition",
            json={"new_state": "In Progress"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_transition_recurring_task_creates_next_instance(self):
        """Test completing recurring task creates next instance."""
        db = TestingSessionLocal()
        user = create_test_user(db)
        task = create_test_task(db, user.id, TaskStateEnum.IN_PROGRESS, RecurrenceEnum.DAILY)
        task.due_date = datetime(2026, 1, 20, 12, 0, 0, tzinfo=timezone.utc)
        db.commit()
        task_id = task.id
        db.close()

        response = client.post(
            f"/api/tasks/{task_id}/transition",
            json={"new_state": "Completed"},
        )

        assert response.status_code == 200
        data = response.json()
        
        # Original task should be completed
        assert data["task"]["state"] == "Completed"
        assert data["task"]["completed_at"] is not None
        
        # Next instance should be created
        assert data["next_instance"] is not None
        assert data["next_instance"]["id"] != task_id
        assert data["next_instance"]["state"] == "Ready"
        assert data["next_instance"]["title"] == "Test Task"
        # Due date should be one day later
        next_due = datetime.fromisoformat(
            data["next_instance"]["due_date"].replace("Z", "+00:00")
        )
        assert next_due == datetime(2026, 1, 21, 12, 0, 0, tzinfo=timezone.utc)

    def test_transition_non_recurring_task_no_next_instance(self):
        """Test completing non-recurring task doesn't create instance."""
        db = TestingSessionLocal()
        user = create_test_user(db)
        task = create_test_task(db, user.id, TaskStateEnum.IN_PROGRESS, RecurrenceEnum.NONE)
        db.close()

        response = client.post(
            f"/api/tasks/{task.id}/transition",
            json={"new_state": "Completed"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["task"]["state"] == "Completed"
        assert data["next_instance"] is None


class TestTransitionScenarios:
    """Test realistic transition scenarios."""

    def test_complete_workflow_ready_to_completed(self):
        """Test complete workflow: Ready -> In Progress -> Completed."""
        db = TestingSessionLocal()
        user = create_test_user(db)
        task = create_test_task(db, user.id, TaskStateEnum.READY)
        db.close()

        # Start the task
        response1 = client.post(
            f"/api/tasks/{task.id}/transition",
            json={"new_state": "In Progress"},
        )
        assert response1.status_code == 200
        assert response1.json()["task"]["state"] == "In Progress"

        # Complete the task
        response2 = client.post(
            f"/api/tasks/{task.id}/transition",
            json={"new_state": "Completed"},
        )
        assert response2.status_code == 200
        assert response2.json()["task"]["state"] == "Completed"

    def test_block_and_unblock_workflow(self):
        """Test blocking and unblocking: In Progress -> Blocked -> Ready."""
        db = TestingSessionLocal()
        user = create_test_user(db)
        task = create_test_task(db, user.id, TaskStateEnum.IN_PROGRESS)
        db.close()

        # Block the task
        response1 = client.post(
            f"/api/tasks/{task.id}/transition",
            json={
                "new_state": "Blocked",
                "notes": "Waiting for external dependency",
            },
        )
        assert response1.status_code == 200
        assert response1.json()["task"]["state"] == "Blocked"

        # Unblock the task
        response2 = client.post(
            f"/api/tasks/{task.id}/transition",
            json={"new_state": "Ready"},
        )
        assert response2.status_code == 200
        assert response2.json()["task"]["state"] == "Ready"

    def test_park_and_resume_workflow(self):
        """Test parking and resuming: Ready -> Parked -> Ready."""
        db = TestingSessionLocal()
        user = create_test_user(db)
        task = create_test_task(db, user.id, TaskStateEnum.READY)
        db.close()

        # Park the task
        response1 = client.post(
            f"/api/tasks/{task.id}/transition",
            json={
                "new_state": "Parked",
                "notes": "Deferring for now",
            },
        )
        assert response1.status_code == 200
        assert response1.json()["task"]["state"] == "Parked"

        # Resume the task
        response2 = client.post(
            f"/api/tasks/{task.id}/transition",
            json={"new_state": "Ready"},
        )
        assert response2.status_code == 200
        assert response2.json()["task"]["state"] == "Ready"

    def test_cancel_from_various_states(self):
        """Test cancellation from different states."""
        db = TestingSessionLocal()
        user = create_test_user(db)
        
        # Cancel from Ready
        task1 = create_test_task(db, user.id, TaskStateEnum.READY)
        task1_id = task1.id
        # Cancel from In Progress
        task2 = create_test_task(db, user.id, TaskStateEnum.IN_PROGRESS)
        task2_id = task2.id
        # Cancel from Blocked
        task3 = create_test_task(db, user.id, TaskStateEnum.BLOCKED)
        task3_id = task3.id
        db.close()

        # All should successfully cancel
        for task_id in [task1_id, task2_id, task3_id]:
            response = client.post(
                f"/api/tasks/{task_id}/transition",
                json={"new_state": "Cancelled"},
            )
            assert response.status_code == 200
            assert response.json()["task"]["state"] == "Cancelled"
