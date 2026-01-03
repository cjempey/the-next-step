"""Tests for Values API endpoints."""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db
from app.models import Base, Value, User
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


# Override the dependencies
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_active_user] = override_get_current_active_user

# Create test client
client = TestClient(app)


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


def test_create_value():
    """Test creating a new value."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    response = client.post(
        "/api/values/",
        json={"statement": "I am improving in my craft"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["statement"] == "I am improving in my craft"
    assert data["archived"] is False
    assert "id" in data
    assert "created_at" in data


def test_create_value_with_whitespace():
    """Test creating a value strips whitespace."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    response = client.post(
        "/api/values/",
        json={"statement": "  My family comes first  "},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["statement"] == "My family comes first"


def test_create_value_empty_string():
    """Test creating a value with empty string fails."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    response = client.post("/api/values/", json={"statement": ""})

    assert response.status_code == 400
    assert response.json()["detail"] == "Value statement cannot be empty"


def test_create_value_only_whitespace():
    """Test creating a value with only whitespace fails."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    response = client.post("/api/values/", json={"statement": "   "})

    assert response.status_code == 400
    assert response.json()["detail"] == "Value statement cannot be empty"


def test_create_value_exceeds_max_length():
    """Test creating a value with statement exceeding 255 characters fails."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create a statement longer than 255 characters
    long_statement = "A" * 256

    response = client.post("/api/values/", json={"statement": long_statement})

    assert response.status_code == 400
    assert response.json()["detail"] == "Value statement must not exceed 255 characters"


def test_create_value_at_max_length():
    """Test creating a value with exactly 255 characters succeeds."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create a statement with exactly 255 characters
    max_statement = "A" * 255

    response = client.post("/api/values/", json={"statement": max_statement})

    assert response.status_code == 201
    data = response.json()
    assert len(data["statement"]) == 255
    assert data["statement"] == max_statement


def test_list_values_empty():
    """Test listing values when none exist."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    response = client.get("/api/values/")

    assert response.status_code == 200
    assert response.json() == []


def test_list_values():
    """Test listing active values."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create some values
    client.post("/api/values/", json={"statement": "Value 1"})
    client.post("/api/values/", json={"statement": "Value 2"})
    client.post("/api/values/", json={"statement": "Value 3"})

    response = client.get("/api/values/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["statement"] == "Value 1"
    assert data[1]["statement"] == "Value 2"
    assert data[2]["statement"] == "Value 3"


def test_list_values_excludes_archived():
    """Test that archived values are not returned."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create values
    response1 = client.post("/api/values/", json={"statement": "Active Value"})
    value1_id = response1.json()["id"]

    response2 = client.post("/api/values/", json={"statement": "Archived Value"})
    value2_id = response2.json()["id"]

    # Archive the second value
    client.patch(f"/api/values/{value2_id}/archive")

    # List values
    response = client.get("/api/values/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["statement"] == "Active Value"
    assert data[0]["id"] == value1_id


def test_list_values_with_include_archived():
    """Test that archived values are included when include_archived=true."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create values
    response1 = client.post("/api/values/", json={"statement": "Active Value"})
    value1_id = response1.json()["id"]

    response2 = client.post("/api/values/", json={"statement": "Archived Value"})
    value2_id = response2.json()["id"]

    # Archive the second value
    client.patch(f"/api/values/{value2_id}/archive")

    # List values with include_archived=true
    response = client.get("/api/values/?include_archived=true")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Sort by id to ensure consistent ordering for assertions
    data_sorted = sorted(data, key=lambda x: x["id"])
    assert data_sorted[0]["id"] == value1_id
    assert data_sorted[0]["statement"] == "Active Value"
    assert data_sorted[0]["archived"] is False

    assert data_sorted[1]["id"] == value2_id
    assert data_sorted[1]["statement"] == "Archived Value"
    assert data_sorted[1]["archived"] is True


def test_list_values_include_archived_false_explicit():
    """Test that explicitly setting include_archived=false excludes archived values."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create values
    response1 = client.post("/api/values/", json={"statement": "Active Value"})
    value1_id = response1.json()["id"]

    response2 = client.post("/api/values/", json={"statement": "Archived Value"})
    value2_id = response2.json()["id"]

    # Archive the second value
    client.patch(f"/api/values/{value2_id}/archive")

    # List values with explicit include_archived=false
    response = client.get("/api/values/?include_archived=false")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["statement"] == "Active Value"
    assert data[0]["id"] == value1_id


def test_list_values_multi_user_isolation_with_archived():
    """Test that users only see their own archived values."""
    db = TestingSessionLocal()

    # Create first user and their values
    create_test_user(db, username="user1", email="user1@example.com")
    db.close()

    client.post("/api/values/", json={"statement": "User1 Active"})

    response2 = client.post("/api/values/", json={"statement": "User1 Archived"})
    user1_value2_id = response2.json()["id"]
    client.patch(f"/api/values/{user1_value2_id}/archive")

    # Create second user and their values
    db = TestingSessionLocal()
    create_test_user(db, username="user2", email="user2@example.com")
    db.close()

    response3 = client.post("/api/values/", json={"statement": "User2 Active"})
    user2_value1_id = response3.json()["id"]

    response4 = client.post("/api/values/", json={"statement": "User2 Archived"})
    user2_value2_id = response4.json()["id"]
    client.patch(f"/api/values/{user2_value2_id}/archive")

    # User2 should only see their own values (both active and archived)
    response = client.get("/api/values/?include_archived=true")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Verify all values belong to user2
    for value in data:
        assert value["id"] in [user2_value1_id, user2_value2_id]
        assert value["statement"].startswith("User2")


def test_update_value():
    """Test updating a value statement."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create a value
    create_response = client.post(
        "/api/values/", json={"statement": "Original statement"}
    )
    value_id = create_response.json()["id"]

    # Update the value
    update_response = client.put(
        f"/api/values/{value_id}",
        json={"statement": "Updated statement"},
    )

    assert update_response.status_code == 200
    data = update_response.json()
    assert data["id"] == value_id
    assert data["statement"] == "Updated statement"
    assert data["archived"] is False


def test_update_value_with_whitespace():
    """Test updating a value strips whitespace."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create a value
    create_response = client.post("/api/values/", json={"statement": "Original"})
    value_id = create_response.json()["id"]

    # Update with whitespace
    update_response = client.put(
        f"/api/values/{value_id}",
        json={"statement": "  Updated  "},
    )

    assert update_response.status_code == 200
    assert update_response.json()["statement"] == "Updated"


def test_update_value_empty_string():
    """Test updating a value with empty string fails."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create a value
    create_response = client.post("/api/values/", json={"statement": "Original"})
    value_id = create_response.json()["id"]

    # Try to update with empty string
    update_response = client.put(f"/api/values/{value_id}", json={"statement": ""})

    assert update_response.status_code == 400
    assert update_response.json()["detail"] == "Value statement cannot be empty"


def test_update_value_only_whitespace():
    """Test updating a value with only whitespace fails."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create a value
    create_response = client.post("/api/values/", json={"statement": "Original"})
    value_id = create_response.json()["id"]

    # Try to update with whitespace only
    update_response = client.put(f"/api/values/{value_id}", json={"statement": "   "})

    assert update_response.status_code == 400
    assert update_response.json()["detail"] == "Value statement cannot be empty"


def test_update_value_exceeds_max_length():
    """Test updating a value with statement exceeding 255 characters fails."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create a value
    create_response = client.post("/api/values/", json={"statement": "Original"})
    value_id = create_response.json()["id"]

    # Try to update with a statement longer than 255 characters
    long_statement = "B" * 256
    update_response = client.put(
        f"/api/values/{value_id}",
        json={"statement": long_statement},
    )

    assert update_response.status_code == 400
    assert (
        update_response.json()["detail"]
        == "Value statement must not exceed 255 characters"
    )


def test_update_value_at_max_length():
    """Test updating a value with exactly 255 characters succeeds."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create a value
    create_response = client.post("/api/values/", json={"statement": "Original"})
    value_id = create_response.json()["id"]

    # Update with exactly 255 characters
    max_statement = "B" * 255
    update_response = client.put(
        f"/api/values/{value_id}",
        json={"statement": max_statement},
    )

    assert update_response.status_code == 200
    data = update_response.json()
    assert len(data["statement"]) == 255
    assert data["statement"] == max_statement


def test_update_nonexistent_value():
    """Test updating a value that doesn't exist."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    response = client.put("/api/values/999", json={"statement": "New statement"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Value not found"


def test_archive_value():
    """Test archiving a value."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create a value
    create_response = client.post("/api/values/", json={"statement": "To be archived"})
    value_id = create_response.json()["id"]

    # Archive the value
    archive_response = client.patch(f"/api/values/{value_id}/archive")

    assert archive_response.status_code == 200
    data = archive_response.json()
    assert data["id"] == value_id
    assert data["statement"] == "To be archived"
    assert data["archived"] is True


def test_archive_nonexistent_value():
    """Test archiving a value that doesn't exist."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    response = client.patch("/api/values/999/archive")

    assert response.status_code == 404
    assert response.json()["detail"] == "Value not found"


def test_archive_value_doesnt_affect_tasks():
    """Test that archiving a value doesn't affect existing task-value links."""
    db = TestingSessionLocal()
    user = create_test_user(db)
    user_id = user.id  # Store user_id before using db for other operations

    # Create a value
    value_response = client.post("/api/values/", json={"statement": "Test Value"})
    value_id = value_response.json()["id"]

    # Create a task linked to this value (using database directly since tasks API may not be implemented)
    try:
        from app.models import (
            Task,
            ImpactEnum,
            UrgencyEnum,
            TaskStateEnum,
            RecurrenceEnum,
        )

        task = Task(
            user_id=user_id,
            title="Test Task",
            impact=ImpactEnum.A,
            urgency=UrgencyEnum.IMMEDIATE,
            state=TaskStateEnum.READY,
            recurrence=RecurrenceEnum.NONE,
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        # Link task to value
        value = db.query(Value).filter(Value.id == value_id).first()
        task.values.append(value)
        db.commit()

        task_id = task.id
    finally:
        db.close()

    # Archive the value
    client.patch(f"/api/values/{value_id}/archive")

    # Verify task still has the link
    db = TestingSessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        assert task is not None
        assert len(task.values) == 1
        assert task.values[0].id == value_id
        assert task.values[0].archived is True
    finally:
        db.close()


def test_archived_value_can_be_updated():
    """Test that archived values can still be updated."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create and archive a value
    create_response = client.post("/api/values/", json={"statement": "Original"})
    value_id = create_response.json()["id"]
    client.patch(f"/api/values/{value_id}/archive")

    # Update the archived value
    update_response = client.put(
        f"/api/values/{value_id}",
        json={"statement": "Updated archived value"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["statement"] == "Updated archived value"
    assert update_response.json()["archived"] is True


# Tests for archived_at timestamp functionality (Issue #16)


def test_archive_value_sets_archived_at_timestamp():
    """Test that archiving a value sets the archived_at timestamp."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create a value
    create_response = client.post("/api/values/", json={"statement": "To be archived"})
    value_id = create_response.json()["id"]

    # Archive the value
    archive_response = client.patch(f"/api/values/{value_id}/archive")

    assert archive_response.status_code == 200
    data = archive_response.json()
    assert data["archived"] is True
    assert data["archived_at"] is not None
    assert isinstance(data["archived_at"], str)  # ISO 8601 timestamp


def test_archive_value_idempotent_preserves_timestamp():
    """Test that archiving an already-archived value is idempotent and preserves the original timestamp."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create a value
    create_response = client.post("/api/values/", json={"statement": "To be archived"})
    value_id = create_response.json()["id"]

    # Archive the value first time
    first_archive = client.patch(f"/api/values/{value_id}/archive")
    assert first_archive.status_code == 200
    first_timestamp = first_archive.json()["archived_at"]
    assert first_timestamp is not None

    # Archive the value again (should be idempotent)
    second_archive = client.patch(f"/api/values/{value_id}/archive")
    assert second_archive.status_code == 200
    second_timestamp = second_archive.json()["archived_at"]

    # Timestamp should be unchanged
    assert second_timestamp == first_timestamp


def test_new_value_has_null_archived_at():
    """Test that creating a new value leaves archived_at as NULL."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    response = client.post("/api/values/", json={"statement": "Active value"})

    assert response.status_code == 201
    data = response.json()
    assert data["archived"] is False
    assert data["archived_at"] is None


def test_api_response_includes_archived_and_archived_at():
    """Test that API responses include both archived (computed) and archived_at fields."""
    db = TestingSessionLocal()
    create_test_user(db)
    db.close()

    # Create and archive a value
    create_response = client.post("/api/values/", json={"statement": "Test value"})
    value_id = create_response.json()["id"]
    client.patch(f"/api/values/{value_id}/archive")

    # Test GET endpoint
    response = client.get("/api/values/?include_archived=true")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "archived" in data[0]
    assert "archived_at" in data[0]
    assert data[0]["archived"] is True
    assert data[0]["archived_at"] is not None


def test_hybrid_property_filtering_active_values():
    """Test that filtering by ~Value.archived returns only active values."""
    db = TestingSessionLocal()
    user = create_test_user(db)

    # Create active and archived values directly in DB
    active_value = Value(user_id=user.id, statement="Active value")
    db.add(active_value)
    db.commit()
    db.refresh(active_value)

    archived_value = Value(user_id=user.id, statement="Archived value")
    db.add(archived_value)
    db.commit()
    db.refresh(archived_value)

    # Archive one value
    from datetime import datetime
    archived_value.archived_at = datetime.utcnow()
    db.commit()
    db.close()

    # Query through API
    response = client.get("/api/values/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["statement"] == "Active value"
    assert data[0]["archived"] is False


def test_hybrid_property_filtering_archived_values():
    """Test that filtering by Value.archived returns only archived values."""
    db = TestingSessionLocal()
    user = create_test_user(db)

    # Create active and archived values
    active_value = Value(user_id=user.id, statement="Active value")
    db.add(active_value)
    db.commit()

    archived_value = Value(user_id=user.id, statement="Archived value")
    db.add(archived_value)
    db.commit()
    db.refresh(archived_value)

    # Archive one value
    from datetime import datetime
    archived_value.archived_at = datetime.utcnow()
    db.commit()
    db.close()

    # Query through API with include_archived
    response = client.get("/api/values/?include_archived=true")
    assert response.status_code == 200
    data = response.json()

    # Should have both values
    assert len(data) == 2

    # Find the archived one
    archived_values = [v for v in data if v["archived"]]
    assert len(archived_values) == 1
    assert archived_values[0]["statement"] == "Archived value"


def test_hybrid_property_returns_correct_boolean():
    """Test that the hybrid property value.archived returns the correct boolean based on archived_at."""
    db = TestingSessionLocal()
    user = create_test_user(db)

    # Create an active value
    active_value = Value(user_id=user.id, statement="Active")
    db.add(active_value)
    db.commit()
    db.refresh(active_value)

    # Test active value
    assert active_value.archived is False
    assert active_value.archived_at is None

    # Archive the value
    from datetime import datetime
    active_value.archived_at = datetime.utcnow()
    db.commit()
    db.refresh(active_value)

    # Test archived value
    assert active_value.archived is True
    assert active_value.archived_at is not None

    db.close()
