"""Tests for Tasks API endpoints."""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db
from app.models import (
    Base,
    User,
    ImpactEnum,
    UrgencyEnum,
    TaskStateEnum,
    RecurrenceEnum,
)
from app.auth import get_current_active_user

# Create in-memory SQLite database for testing
# Use StaticPool to ensure the same in-memory database is used across connections
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
    # Return a simple mock user object to avoid session issues
    if _test_user_data is None:
        raise HTTPException(status_code=401, detail="No test user set")

    # Create a simple class that acts like a User but isn't bound to a session
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
    """Set up and tear down FastAPI dependency overrides for each test.

    This avoids cross-module interference when multiple test files override
    dependencies on the shared FastAPI `app` instance.
    """
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user
    yield
    app.dependency_overrides.clear()


def create_test_user(db, username="testuser", email="test@example.com"):
    """Create a test user and return the user object."""
    global _test_user_data
    # Use a pre-hashed password to avoid bcrypt issues in tests
    # This is the hash for password "test123"
    prehashed = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYKJkPx0tAi"
    user = User(username=username, email=email, password_hash=prehashed, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    # Store user data as a dict to avoid session issues
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
    # Clear all data but keep schema
    db = TestingSessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
    finally:
        db.close()
    _test_user_data = None


# CREATE Tests


def test_create_task_minimal():
    """Test creating a task with only title - verify defaults applied."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    response = client.post(
        "/api/tasks/",
        json={"title": "Minimal task"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Minimal task"
    assert data["description"] is None
    assert data["value_ids"] == []
    # Verify defaults from model
    assert data["impact"] == ImpactEnum.B.value
    assert data["urgency"] == UrgencyEnum.CAN_DEFER.value
    assert data["state"] == TaskStateEnum.READY.value
    assert data["recurrence"] == RecurrenceEnum.NONE.value
    assert data["completion_percentage"] == 0
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_task_with_all_fields():
    """Test creating a task with all fields - verify all fields saved correctly."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    response = client.post(
        "/api/tasks/",
        json={
            "title": "Complete task",
            "description": "A detailed description",
            "impact": ImpactEnum.A.value,
            "urgency": UrgencyEnum.IMMEDIATE.value,
            "due_date": "2026-12-31T23:59:59Z",
            "recurrence": RecurrenceEnum.DAILY.value,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Complete task"
    assert data["description"] == "A detailed description"
    assert data["impact"] == ImpactEnum.A.value
    assert data["urgency"] == UrgencyEnum.IMMEDIATE.value
    assert data["due_date"] == "2026-12-31T23:59:59Z"
    assert data["recurrence"] == RecurrenceEnum.DAILY.value


def test_create_task_with_values():
    """Test creating a task with values - verify value linking works."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create some values first
    value1_response = client.post("/api/values/", json={"statement": "Value 1"})
    value1_id = value1_response.json()["id"]

    value2_response = client.post("/api/values/", json={"statement": "Value 2"})
    value2_id = value2_response.json()["id"]

    # Create task with values
    response = client.post(
        "/api/tasks/",
        json={
            "title": "Task with values",
            "value_ids": [value1_id, value2_id],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Task with values"
    assert set(data["value_ids"]) == {value1_id, value2_id}


def test_create_task_with_invalid_value_id():
    """Test creating a task with invalid value_id - verify 400 error."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    response = client.post(
        "/api/tasks/",
        json={
            "title": "Task with invalid value",
            "value_ids": [999],  # Non-existent value_id
        },
    )

    assert response.status_code == 400
    assert "Invalid value_ids" in response.json()["detail"]


def test_create_task_with_other_users_value():
    """Test creating a task with another user's value - verify 400 error."""
    db = TestingSessionLocal()

    # Create first user and their value
    create_test_user(db, username="user1", email="user1@example.com")
    db.close()

    value_response = client.post("/api/values/", json={"statement": "User1's Value"})
    value_id = value_response.json()["id"]

    # Switch to second user
    db = TestingSessionLocal()
    create_test_user(db, username="user2", email="user2@example.com")
    db.close()

    # Try to create task with first user's value
    response = client.post(
        "/api/tasks/",
        json={
            "title": "Task with other user's value",
            "value_ids": [value_id],
        },
    )

    assert response.status_code == 400
    assert "Invalid value_ids" in response.json()["detail"]


def test_create_task_with_duplicate_value_ids():
    """Test creating a task with duplicate value_ids - verify duplicates are handled."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create a value
    value_response = client.post("/api/values/", json={"statement": "Test Value"})
    value_id = value_response.json()["id"]

    # Create task with duplicate value_ids
    response = client.post(
        "/api/tasks/",
        json={
            "title": "Task with duplicate values",
            "value_ids": [value_id, value_id, value_id],
        },
    )

    assert response.status_code == 201
    data = response.json()
    # Should only have the value once
    assert len(data["value_ids"]) == 1
    assert data["value_ids"][0] == value_id


# LIST Tests


def test_list_tasks_empty():
    """Test listing tasks when none exist - verify empty list."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    response = client.get("/api/tasks/")

    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_multiple():
    """Test listing multiple tasks - verify all user's tasks returned."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create multiple tasks
    client.post("/api/tasks/", json={"title": "Task 1"})
    client.post("/api/tasks/", json={"title": "Task 2"})
    client.post("/api/tasks/", json={"title": "Task 3"})

    response = client.get("/api/tasks/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    titles = {task["title"] for task in data}
    assert titles == {"Task 1", "Task 2", "Task 3"}


def test_list_tasks_filter_by_state():
    """Test listing tasks filtered by state - verify state filtering."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create tasks with different states
    client.post("/api/tasks/", json={"title": "Ready task"})

    task2_response = client.post("/api/tasks/", json={"title": "In progress task"})
    task2_id = task2_response.json()["id"]

    # Update task2 to In Progress state
    client.put(
        f"/api/tasks/{task2_id}",
        json={"state": TaskStateEnum.IN_PROGRESS.value},
    )

    # Filter by Ready state
    response = client.get(f"/api/tasks/?state={TaskStateEnum.READY.value}")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Ready task"
    assert data[0]["state"] == TaskStateEnum.READY.value


def test_list_tasks_filter_by_value():
    """Test listing tasks filtered by value_id - verify value filtering."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create values
    value1_response = client.post("/api/values/", json={"statement": "Value 1"})
    value1_id = value1_response.json()["id"]

    value2_response = client.post("/api/values/", json={"statement": "Value 2"})
    value2_id = value2_response.json()["id"]

    # Create tasks with different values
    client.post("/api/tasks/", json={"title": "Task 1", "value_ids": [value1_id]})
    client.post("/api/tasks/", json={"title": "Task 2", "value_ids": [value2_id]})
    client.post(
        "/api/tasks/", json={"title": "Task 3", "value_ids": [value1_id, value2_id]}
    )

    # Filter by value1_id
    response = client.get(f"/api/tasks/?value_id={value1_id}")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    titles = {task["title"] for task in data}
    assert titles == {"Task 1", "Task 3"}


def test_list_tasks_filter_combined():
    """Test listing tasks with combined filters - verify state + value filters work together."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create value
    value_response = client.post("/api/values/", json={"statement": "Test Value"})
    value_id = value_response.json()["id"]

    # Create tasks with various combinations
    client.post("/api/tasks/", json={"title": "Ready + Value", "value_ids": [value_id]})

    task2_response = client.post(
        "/api/tasks/", json={"title": "InProgress + Value", "value_ids": [value_id]}
    )
    task2_id = task2_response.json()["id"]
    client.put(
        f"/api/tasks/{task2_id}",
        json={"state": TaskStateEnum.IN_PROGRESS.value},
    )

    client.post("/api/tasks/", json={"title": "Ready + NoValue"})

    # Filter by Ready state AND value_id
    response = client.get(
        f"/api/tasks/?state={TaskStateEnum.READY.value}&value_id={value_id}"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Ready + Value"


def test_list_tasks_only_own():
    """Test that users only see their own tasks - verify user isolation."""
    db = TestingSessionLocal()

    # Create first user and their tasks
    create_test_user(db, username="user1", email="user1@example.com")
    db.close()

    client.post("/api/tasks/", json={"title": "User1 Task 1"})
    client.post("/api/tasks/", json={"title": "User1 Task 2"})

    # Create second user and their tasks
    db = TestingSessionLocal()
    create_test_user(db, username="user2", email="user2@example.com")
    db.close()

    client.post("/api/tasks/", json={"title": "User2 Task"})

    # User2 should only see their own task
    response = client.get("/api/tasks/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "User2 Task"


def test_list_tasks_filter_by_other_users_value():
    """Test filtering by another user's value_id - verify 404 error."""
    db = TestingSessionLocal()

    # Create first user and their value
    create_test_user(db, username="user1", email="user1@example.com")
    db.close()

    value_response = client.post("/api/values/", json={"statement": "User1's Value"})
    value_id = value_response.json()["id"]

    # Switch to second user
    db = TestingSessionLocal()
    create_test_user(db, username="user2", email="user2@example.com")
    db.close()

    # Try to filter by user1's value
    response = client.get(f"/api/tasks/?value_id={value_id}")

    assert response.status_code == 404
    assert "Value not found" in response.json()["detail"]


# GET single task tests


def test_get_task_success():
    """Test getting a specific task - verify single task retrieval."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create a task
    create_response = client.post("/api/tasks/", json={"title": "Test Task"})
    task_id = create_response.json()["id"]

    # Get the task
    response = client.get(f"/api/tasks/{task_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == "Test Task"


def test_get_task_not_found():
    """Test getting non-existent task - verify 404 error."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    response = client.get("/api/tasks/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_get_task_other_user():
    """Test getting another user's task - verify 404 error."""
    db = TestingSessionLocal()

    # Create first user and their task
    create_test_user(db, username="user1", email="user1@example.com")
    db.close()

    create_response = client.post("/api/tasks/", json={"title": "User1 Task"})
    task_id = create_response.json()["id"]

    # Switch to second user
    db = TestingSessionLocal()
    create_test_user(db, username="user2", email="user2@example.com")
    db.close()

    # Try to get first user's task
    response = client.get(f"/api/tasks/{task_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


# UPDATE Tests


def test_update_task_title():
    """Test updating task title - verify partial update works."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create a task
    create_response = client.post("/api/tasks/", json={"title": "Original Title"})
    task_id = create_response.json()["id"]

    # Update just the title
    response = client.put(
        f"/api/tasks/{task_id}",
        json={"title": "Updated Title"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == "Updated Title"


def test_update_task_all_fields():
    """Test updating all task fields - verify updating all fields."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create a task
    create_response = client.post("/api/tasks/", json={"title": "Original"})
    task_id = create_response.json()["id"]

    # Update all fields
    response = client.put(
        f"/api/tasks/{task_id}",
        json={
            "title": "Updated Title",
            "description": "Updated description",
            "impact": ImpactEnum.A.value,
            "urgency": UrgencyEnum.IMMEDIATE.value,
            "state": TaskStateEnum.IN_PROGRESS.value,
            "completion_percentage": 50,
            "notes": "Some notes",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated description"
    assert data["impact"] == ImpactEnum.A.value
    assert data["urgency"] == UrgencyEnum.IMMEDIATE.value
    assert data["state"] == TaskStateEnum.IN_PROGRESS.value
    assert data["completion_percentage"] == 50
    assert data["notes"] == "Some notes"


def test_update_task_values():
    """Test updating task value_ids - verify updating value_ids."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create values
    value1_response = client.post("/api/values/", json={"statement": "Value 1"})
    value1_id = value1_response.json()["id"]

    value2_response = client.post("/api/values/", json={"statement": "Value 2"})
    value2_id = value2_response.json()["id"]

    value3_response = client.post("/api/values/", json={"statement": "Value 3"})
    value3_id = value3_response.json()["id"]

    # Create task with value1
    create_response = client.post(
        "/api/tasks/", json={"title": "Task", "value_ids": [value1_id]}
    )
    task_id = create_response.json()["id"]

    # Update to value2 and value3
    response = client.put(
        f"/api/tasks/{task_id}",
        json={"value_ids": [value2_id, value3_id]},
    )

    assert response.status_code == 200
    data = response.json()
    assert set(data["value_ids"]) == {value2_id, value3_id}


def test_update_task_clear_values():
    """Test clearing task values - verify setting value_ids to []."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create value
    value_response = client.post("/api/values/", json={"statement": "Value 1"})
    value_id = value_response.json()["id"]

    # Create task with value
    create_response = client.post(
        "/api/tasks/", json={"title": "Task", "value_ids": [value_id]}
    )
    task_id = create_response.json()["id"]

    # Clear values
    response = client.put(
        f"/api/tasks/{task_id}",
        json={"value_ids": []},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["value_ids"] == []


def test_update_task_with_invalid_value_id():
    """Test updating a task with invalid value_id - verify 400 error."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create a task
    create_response = client.post("/api/tasks/", json={"title": "Test Task"})
    task_id = create_response.json()["id"]

    # Try to update with invalid value_id
    response = client.put(
        f"/api/tasks/{task_id}",
        json={"value_ids": [999]},
    )

    assert response.status_code == 400
    assert "Invalid value_ids" in response.json()["detail"]


def test_update_task_with_other_users_value():
    """Test updating a task with another user's value - verify 400 error."""
    db = TestingSessionLocal()

    # Create first user and their value
    create_test_user(db, username="user1", email="user1@example.com")
    db.close()

    value_response = client.post("/api/values/", json={"statement": "User1's Value"})
    value_id = value_response.json()["id"]

    # Switch to second user
    db = TestingSessionLocal()
    create_test_user(db, username="user2", email="user2@example.com")
    db.close()

    # Create a task as user2
    create_response = client.post("/api/tasks/", json={"title": "User2 Task"})
    task_id = create_response.json()["id"]

    # Try to update with user1's value
    response = client.put(
        f"/api/tasks/{task_id}",
        json={"value_ids": [value_id]},
    )

    assert response.status_code == 400
    assert "Invalid value_ids" in response.json()["detail"]


def test_update_task_with_duplicate_value_ids():
    """Test updating a task with duplicate value_ids - verify duplicates are handled."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create a value
    value_response = client.post("/api/values/", json={"statement": "Test Value"})
    value_id = value_response.json()["id"]

    # Create a task
    create_response = client.post("/api/tasks/", json={"title": "Test Task"})
    task_id = create_response.json()["id"]

    # Update with duplicate value_ids
    response = client.put(
        f"/api/tasks/{task_id}",
        json={"value_ids": [value_id, value_id, value_id]},
    )

    assert response.status_code == 200
    data = response.json()
    # Should only have the value once
    assert len(data["value_ids"]) == 1
    assert data["value_ids"][0] == value_id


def test_update_task_not_found():
    """Test updating non-existent task - verify 404 error."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    response = client.put(
        "/api/tasks/999",
        json={"title": "Updated"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


# DELETE Tests


def test_delete_task_success():
    """Test deleting a task - verify 204 response."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create a task
    create_response = client.post("/api/tasks/", json={"title": "To Delete"})
    task_id = create_response.json()["id"]

    # Delete the task
    response = client.delete(f"/api/tasks/{task_id}")

    assert response.status_code == 204

    # Verify task is gone
    get_response = client.get(f"/api/tasks/{task_id}")
    assert get_response.status_code == 404


def test_delete_task_not_found():
    """Test deleting non-existent task - verify 404 error."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    response = client.delete("/api/tasks/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_delete_task_other_user():
    """Test deleting another user's task - verify 404 error."""
    db = TestingSessionLocal()

    # Create first user and their task
    create_test_user(db, username="user1", email="user1@example.com")
    db.close()

    create_response = client.post("/api/tasks/", json={"title": "User1 Task"})
    task_id = create_response.json()["id"]

    # Switch to second user
    db = TestingSessionLocal()
    create_test_user(db, username="user2", email="user2@example.com")
    db.close()

    # Try to delete first user's task
    response = client.delete(f"/api/tasks/{task_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"
