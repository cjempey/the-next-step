"""Tests for timezone-aware datetime serialization."""

from datetime import datetime, timezone
from app.schemas import ValueResponse, AwareDatetime


def test_aware_datetime_adds_timezone_to_naive():
    """Test that AwareDatetime adds UTC timezone to naive datetimes."""
    # Create a naive datetime
    naive_dt = datetime(2026, 1, 4, 7, 8, 0)
    assert naive_dt.tzinfo is None
    
    # The ensure_utc_timezone validator should add UTC timezone
    from app.schemas import ensure_utc_timezone
    aware_dt = ensure_utc_timezone(naive_dt)
    
    assert aware_dt.tzinfo == timezone.utc
    assert aware_dt.year == 2026
    assert aware_dt.month == 1
    assert aware_dt.day == 4


def test_aware_datetime_serializes_with_z_suffix():
    """Test that AwareDatetime serializes with 'Z' suffix."""
    from app.schemas import serialize_datetime_with_z
    
    # Test with naive datetime
    naive_dt = datetime(2026, 1, 4, 7, 8, 0)
    result = serialize_datetime_with_z(naive_dt)
    
    assert result.endswith('Z')
    assert result == '2026-01-04T07:08:00Z'
    
    # Test with aware datetime
    aware_dt = datetime(2026, 1, 4, 7, 8, 0, tzinfo=timezone.utc)
    result = serialize_datetime_with_z(aware_dt)
    
    assert result.endswith('Z')
    assert result == '2026-01-04T07:08:00Z'


def test_value_response_serialization():
    """Test that ValueResponse serializes datetimes with timezone."""
    # Create a ValueResponse with naive datetime (simulating SQLite behavior)
    naive_dt = datetime(2026, 1, 4, 7, 8, 0)
    
    value = ValueResponse(
        id=1,
        statement="Test value",
        archived=False,
        created_at=naive_dt,
        archived_at=None
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
        archived_at=archived_dt
    )
    
    # Serialize to JSON
    json_data = value.model_dump_json()
    
    # Check that both timestamps have 'Z' suffix
    assert '"created_at":"2026-01-03T07:00:00Z"' in json_data
    assert '"archived_at":"2026-01-04T07:08:00Z"' in json_data
