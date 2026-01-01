"""Tests for Values API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db
from app.models import Base, Value

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


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_database():
    """Clean up database tables after each test."""
    yield
    # Clear all data but keep schema
    db = TestingSessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
    finally:
        db.close()


def test_create_value():
    """Test creating a new value."""
    response = client.post(
        "/api/values/",
        json={"statement": "I am improving in my craft"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["statement"] == "I am improving in my craft"
    assert data["archived"] is False
    assert "id" in data
    assert "created_at" in data


def test_create_value_with_whitespace():
    """Test creating a value strips whitespace."""
    response = client.post(
        "/api/values/",
        json={"statement": "  My family comes first  "}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["statement"] == "My family comes first"


def test_create_value_empty_string():
    """Test creating a value with empty string fails."""
    response = client.post(
        "/api/values/",
        json={"statement": ""}
    )
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Value statement cannot be empty"


def test_create_value_only_whitespace():
    """Test creating a value with only whitespace fails."""
    response = client.post(
        "/api/values/",
        json={"statement": "   "}
    )
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Value statement cannot be empty"


def test_list_values_empty():
    """Test listing values when none exist."""
    response = client.get("/api/values/")
    
    assert response.status_code == 200
    assert response.json() == []


def test_list_values():
    """Test listing active values."""
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


def test_update_value():
    """Test updating a value statement."""
    # Create a value
    create_response = client.post(
        "/api/values/",
        json={"statement": "Original statement"}
    )
    value_id = create_response.json()["id"]
    
    # Update the value
    update_response = client.put(
        f"/api/values/{value_id}",
        json={"statement": "Updated statement"}
    )
    
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["id"] == value_id
    assert data["statement"] == "Updated statement"
    assert data["archived"] is False


def test_update_value_with_whitespace():
    """Test updating a value strips whitespace."""
    # Create a value
    create_response = client.post(
        "/api/values/",
        json={"statement": "Original"}
    )
    value_id = create_response.json()["id"]
    
    # Update with whitespace
    update_response = client.put(
        f"/api/values/{value_id}",
        json={"statement": "  Updated  "}
    )
    
    assert update_response.status_code == 200
    assert update_response.json()["statement"] == "Updated"


def test_update_value_empty_string():
    """Test updating a value with empty string fails."""
    # Create a value
    create_response = client.post(
        "/api/values/",
        json={"statement": "Original"}
    )
    value_id = create_response.json()["id"]
    
    # Try to update with empty string
    update_response = client.put(
        f"/api/values/{value_id}",
        json={"statement": ""}
    )
    
    assert update_response.status_code == 400
    assert update_response.json()["detail"] == "Value statement cannot be empty"


def test_update_value_only_whitespace():
    """Test updating a value with only whitespace fails."""
    # Create a value
    create_response = client.post(
        "/api/values/",
        json={"statement": "Original"}
    )
    value_id = create_response.json()["id"]
    
    # Try to update with whitespace only
    update_response = client.put(
        f"/api/values/{value_id}",
        json={"statement": "   "}
    )
    
    assert update_response.status_code == 400
    assert update_response.json()["detail"] == "Value statement cannot be empty"


def test_update_nonexistent_value():
    """Test updating a value that doesn't exist."""
    response = client.put(
        "/api/values/999",
        json={"statement": "New statement"}
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Value not found"


def test_archive_value():
    """Test archiving a value."""
    # Create a value
    create_response = client.post(
        "/api/values/",
        json={"statement": "To be archived"}
    )
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
    response = client.patch("/api/values/999/archive")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Value not found"


def test_archive_value_doesnt_affect_tasks():
    """Test that archiving a value doesn't affect existing task-value links."""
    # Create a value
    value_response = client.post(
        "/api/values/",
        json={"statement": "Test Value"}
    )
    value_id = value_response.json()["id"]
    
    # Create a task linked to this value (using database directly since tasks API may not be implemented)
    db = TestingSessionLocal()
    try:
        from app.models import Task, ImpactEnum, UrgencyEnum, TaskStateEnum, RecurrenceEnum
        
        task = Task(
            title="Test Task",
            impact=ImpactEnum.A,
            urgency=UrgencyEnum.IMMEDIATE,
            state=TaskStateEnum.READY,
            recurrence=RecurrenceEnum.NONE
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
        assert len(task.values) == 1
        assert task.values[0].id == value_id
        assert task.values[0].archived is True
    finally:
        db.close()


def test_archived_value_can_be_updated():
    """Test that archived values can still be updated."""
    # Create and archive a value
    create_response = client.post(
        "/api/values/",
        json={"statement": "Original"}
    )
    value_id = create_response.json()["id"]
    client.patch(f"/api/values/{value_id}/archive")
    
    # Update the archived value
    update_response = client.put(
        f"/api/values/{value_id}",
        json={"statement": "Updated archived value"}
    )
    
    assert update_response.status_code == 200
    assert update_response.json()["statement"] == "Updated archived value"
    assert update_response.json()["archived"] is True
