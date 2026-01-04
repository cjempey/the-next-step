"""Tests for timezone-aware datetime serialization."""

from datetime import datetime, timezone
from app.schemas import ValueResponse


def test_aware_datetime_adds_timezone_to_naive():
    """Test that AwareDatetime adds UTC timezone to naive datetimes."""
    # Create a naive datetime
    naive_dt = datetime(2026, 1, 4, 7, 8, 0)
    assert naive_dt.tzinfo is None

    # The ensure_utc_timezone validator should add UTC timezone
    from app.schemas import ensure_utc_timezone

    aware_dt = ensure_utc_timezone(naive_dt)

    assert aware_dt is not None  # Type narrowing
    assert aware_dt.tzinfo == timezone.utc
    assert aware_dt.year == 2026
    assert aware_dt.month == 1
    assert aware_dt.day == 4


def test_aware_datetime_passes_through_utc_datetimes():
    """Test that ensure_utc_timezone is idempotent for UTC datetimes."""
    from app.schemas import ensure_utc_timezone

    # Create a UTC-aware datetime
    aware_dt = datetime(2026, 1, 4, 7, 8, 0, tzinfo=timezone.utc)

    # Validator should return it unchanged
    result = ensure_utc_timezone(aware_dt)

    assert result is not None  # Type narrowing
    assert result is aware_dt  # Same object
    assert result.tzinfo == timezone.utc


def test_aware_datetime_converts_non_utc_to_utc():
    """Test that non-UTC aware datetimes are converted to UTC."""
    from datetime import timedelta
    from app.schemas import ensure_utc_timezone

    # Create a datetime with PST timezone (UTC-8)
    pst = timezone(timedelta(hours=-8))
    pst_dt = datetime(2026, 1, 4, 7, 8, 0, tzinfo=pst)

    # Validator should convert to UTC
    result = ensure_utc_timezone(pst_dt)

    assert result is not None  # Type narrowing
    assert result.tzinfo == timezone.utc
    # 7:08 PST = 15:08 UTC
    assert result.hour == 15
    assert result.minute == 8


def test_aware_datetime_serializes_with_z_suffix():
    """Test that AwareDatetime serializes with 'Z' suffix and second precision."""
    from app.schemas import serialize_datetime_with_z

    # Test with naive datetime
    naive_dt = datetime(2026, 1, 4, 7, 8, 0)
    result = serialize_datetime_with_z(naive_dt)

    assert result is not None  # Type narrowing
    assert result.endswith("Z")
    assert result == "2026-01-04T07:08:00Z"

    # Test with aware datetime
    aware_dt = datetime(2026, 1, 4, 7, 8, 0, tzinfo=timezone.utc)
    result = serialize_datetime_with_z(aware_dt)

    assert result is not None  # Type narrowing
    assert result.endswith("Z")
    assert result == "2026-01-04T07:08:00Z"

    # Test with microseconds - should be omitted with timespec='seconds'
    dt_with_micros = datetime(2026, 1, 4, 7, 8, 0, 123456, tzinfo=timezone.utc)
    result = serialize_datetime_with_z(dt_with_micros)

    assert result is not None  # Type narrowing
    assert result == "2026-01-04T07:08:00Z"
    assert "123456" not in result  # Microseconds omitted


def test_value_response_serialization():
    """Test that ValueResponse serializes datetimes with timezone."""
    # Create a ValueResponse with naive datetime (simulating SQLite behavior)
    naive_dt = datetime(2026, 1, 4, 7, 8, 0)

    value = ValueResponse(
        id=1,
        statement="Test value",
        archived=False,
        created_at=naive_dt,
        archived_at=None,
    )

    # Serialize to JSON
    json_data = value.model_dump_json()

    # Check that the JSON contains 'Z' suffix
    assert '"created_at":"2026-01-04T07:08:00Z"' in json_data
    assert '"archived_at":null' in json_data


def test_value_response_with_archived_at():
    """Test that archived_at also serializes with timezone."""
    created_dt = datetime(2026, 1, 3, 7, 0, 0)
    archived_dt = datetime(2026, 1, 4, 7, 8, 0)

    value = ValueResponse(
        id=1,
        statement="Archived value",
        archived=True,
        created_at=created_dt,
        archived_at=archived_dt,
    )

    # Serialize to JSON
    json_data = value.model_dump_json()

    # Check that both timestamps have 'Z' suffix
    assert '"created_at":"2026-01-03T07:00:00Z"' in json_data
    assert '"archived_at":"2026-01-04T07:08:00Z"' in json_data


def test_api_response_contains_z_suffix():
    """Integration test: verify API responses contain 'Z' suffix in timestamps."""
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from fastapi import FastAPI

    from app.core.database import get_db
    from app.models import Base, User
    from app.auth import get_current_active_user
    from app.api.routes import values

    # Create a new FastAPI app instance for this test
    test_app = FastAPI()
    test_app.include_router(values.router, prefix="/api/values")

    # Create in-memory database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    class MockUser:
        def __init__(self):
            self.id = 1
            self.username = "testuser"
            self.email = "test@example.com"
            self.is_active = True

    async def override_auth():
        return MockUser()

    # Override dependencies on test app only
    test_app.dependency_overrides[get_db] = override_get_db
    test_app.dependency_overrides[get_current_active_user] = override_auth

    # Create test user in DB
    db = SessionLocal()
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="dummy",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.close()

    # Test with TestClient
    client = TestClient(test_app)

    # Create a value
    response = client.post("/api/values/", json={"statement": "Test value"})
    assert response.status_code == 201

    data = response.json()

    # Verify created_at has timezone (ends with Z or has +/- offset)
    created_at = data["created_at"]
    assert created_at.endswith("Z") or "+" in created_at or (created_at.count("-") > 2)

    # Specifically check for Z suffix (our implementation)
    assert created_at.endswith("Z"), f"Expected 'Z' suffix, got: {created_at}"

    # Archive the value
    value_id = data["id"]
    archive_response = client.patch(f"/api/values/{value_id}/archive")
    assert archive_response.status_code == 200

    archive_data = archive_response.json()
    archived_at = archive_data["archived_at"]

    # Verify archived_at also has Z suffix
    assert archived_at.endswith("Z"), f"Expected 'Z' suffix, got: {archived_at}"
