"""Tests for Pydantic schemas."""

from datetime import datetime
from app.schemas import (
    TaskCreate,
    TaskUpdate,
    ValueCreate,
    ValueResponse,
    ReviewCardResponse,
    ImpactEnum,
    UrgencyEnum,
    TaskStateEnum,
    RecurrenceEnum,
    ReviewCardTypeEnum,
)


def test_task_create_schema():
    """Test TaskCreate schema."""
    task_data = {
        "title": "Test Task",
        "description": "Test description",
        "value_ids": [1, 2],
        "impact": ImpactEnum.A,
        "urgency": UrgencyEnum.IMMEDIATE,
        "due_date": datetime.utcnow(),
        "recurrence": RecurrenceEnum.NONE,
    }
    task = TaskCreate(**task_data)

    assert task.title == "Test Task"
    assert task.description == "Test description"
    assert task.value_ids == [1, 2]
    assert task.impact == ImpactEnum.A
    assert task.urgency == UrgencyEnum.IMMEDIATE
    assert task.recurrence == RecurrenceEnum.NONE


def test_task_create_minimal():
    """Test TaskCreate with minimal required fields."""
    task = TaskCreate(title="Minimal Task")

    assert task.title == "Minimal Task"
    assert task.description is None
    assert task.value_ids == []
    assert task.impact is None
    assert task.urgency is None
    assert task.recurrence == RecurrenceEnum.NONE


def test_task_update_schema():
    """Test TaskUpdate schema."""
    update_data = {
        "title": "Updated Task",
        "state": TaskStateEnum.IN_PROGRESS,
        "completion_percentage": 50,
    }
    update = TaskUpdate(**update_data)

    assert update.title == "Updated Task"
    assert update.state == TaskStateEnum.IN_PROGRESS
    assert update.completion_percentage == 50


def test_value_create_schema():
    """Test ValueCreate schema."""
    value = ValueCreate(statement="Test Value")

    assert value.statement == "Test Value"


def test_value_response_schema():
    """Test ValueResponse schema."""
    value_data = {
        "id": 1,
        "statement": "Test Value",
        "archived": False,
        "created_at": datetime.utcnow(),
    }
    value = ValueResponse(**value_data)

    assert value.id == 1
    assert value.statement == "Test Value"
    assert value.archived is False


def test_review_card_response_schema():
    """Test ReviewCardResponse schema."""
    card_data = {
        "id": 1,
        "type": ReviewCardTypeEnum.COMPLETION,
        "task_id": 123,
        "content": "Test content",
        "responses": [{"option": "Yes", "action": "confirm"}],
        "generated_at": datetime.utcnow(),
    }
    card = ReviewCardResponse(**card_data)

    assert card.id == 1
    assert card.type == ReviewCardTypeEnum.COMPLETION
    assert card.task_id == 123
    assert card.content == "Test content"
    assert len(card.responses) == 1
    assert card.responses[0]["option"] == "Yes"


def test_review_card_response_nullable_task_id():
    """Test ReviewCardResponse with nullable task_id."""
    card_data = {
        "id": 1,
        "type": ReviewCardTypeEnum.COMPLETION,
        "task_id": None,
        "content": "Test content",
        "responses": [],
        "generated_at": datetime.utcnow(),
    }
    card = ReviewCardResponse(**card_data)

    assert card.task_id is None


def test_all_enum_values():
    """Test that all enum types are accessible in schemas."""
    # ImpactEnum
    assert ImpactEnum.A
    assert ImpactEnum.B
    assert ImpactEnum.C
    assert ImpactEnum.D

    # UrgencyEnum
    assert UrgencyEnum.IMMEDIATE
    assert UrgencyEnum.SOON
    assert UrgencyEnum.CAN_DEFER
    assert UrgencyEnum.LONGTERM

    # TaskStateEnum
    assert TaskStateEnum.READY
    assert TaskStateEnum.IN_PROGRESS
    assert TaskStateEnum.BLOCKED
    assert TaskStateEnum.PARKED
    assert TaskStateEnum.COMPLETED
    assert TaskStateEnum.CANCELLED

    # RecurrenceEnum
    assert RecurrenceEnum.NONE
    assert RecurrenceEnum.DAILY
    assert RecurrenceEnum.WEEKLY

    # ReviewCardTypeEnum
    assert ReviewCardTypeEnum.COMPLETION
    assert ReviewCardTypeEnum.REJECTION
    assert ReviewCardTypeEnum.IN_PROGRESS
    assert ReviewCardTypeEnum.BLOCKED
    assert ReviewCardTypeEnum.RECURRING
