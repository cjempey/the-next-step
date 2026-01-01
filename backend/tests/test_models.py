"""Tests for database models."""

from app.models import (
    Task,
    Value,
    ReviewCard,
    ImpactEnum,
    UrgencyEnum,
    TaskStateEnum,
    RecurrenceEnum,
    ReviewCardTypeEnum,
    task_value_association,
)


def test_task_model_attributes():
    """Test that Task model has all required attributes."""
    task = Task()

    # Verify all required columns exist
    assert hasattr(task, "id")
    assert hasattr(task, "title")
    assert hasattr(task, "description")
    assert hasattr(task, "state")
    assert hasattr(task, "impact")
    assert hasattr(task, "urgency")
    assert hasattr(task, "due_date")
    assert hasattr(task, "recurrence")
    assert hasattr(task, "completion_percentage")
    assert hasattr(task, "notes")
    assert hasattr(task, "created_at")
    assert hasattr(task, "updated_at")
    assert hasattr(task, "completed_at")
    assert hasattr(task, "parent_task_id")

    # Verify relationships
    assert hasattr(task, "values")
    assert hasattr(task, "parent_task")


def test_value_model_attributes():
    """Test that Value model has all required attributes."""
    value = Value()

    # Verify all required columns exist
    assert hasattr(value, "id")
    assert hasattr(value, "statement")
    assert hasattr(value, "archived")
    assert hasattr(value, "created_at")
    assert hasattr(value, "updated_at")

    # Verify relationships
    assert hasattr(value, "tasks")


def test_review_card_model_attributes():
    """Test that ReviewCard model has all required attributes."""
    review_card = ReviewCard()

    # Verify all required columns exist
    assert hasattr(review_card, "id")
    assert hasattr(review_card, "type")
    assert hasattr(review_card, "task_id")
    assert hasattr(review_card, "content")
    assert hasattr(review_card, "responses")
    assert hasattr(review_card, "generated_at")


def test_impact_enum():
    """Test that ImpactEnum has all required values."""
    assert hasattr(ImpactEnum, "A")
    assert hasattr(ImpactEnum, "B")
    assert hasattr(ImpactEnum, "C")
    assert hasattr(ImpactEnum, "D")
    assert ImpactEnum.A.value == "A"
    assert ImpactEnum.B.value == "B"


def test_urgency_enum():
    """Test that UrgencyEnum has all required values."""
    assert hasattr(UrgencyEnum, "IMMEDIATE")
    assert hasattr(UrgencyEnum, "SOON")
    assert hasattr(UrgencyEnum, "CAN_DEFER")
    assert hasattr(UrgencyEnum, "LONGTERM")
    assert UrgencyEnum.IMMEDIATE.value == 1
    assert UrgencyEnum.SOON.value == 2
    assert UrgencyEnum.CAN_DEFER.value == 3
    assert UrgencyEnum.LONGTERM.value == 4


def test_task_state_enum():
    """Test that TaskStateEnum has all required values."""
    assert hasattr(TaskStateEnum, "READY")
    assert hasattr(TaskStateEnum, "IN_PROGRESS")
    assert hasattr(TaskStateEnum, "BLOCKED")
    assert hasattr(TaskStateEnum, "PARKED")
    assert hasattr(TaskStateEnum, "COMPLETED")
    assert hasattr(TaskStateEnum, "CANCELLED")
    assert TaskStateEnum.READY.value == "Ready"
    assert TaskStateEnum.IN_PROGRESS.value == "In Progress"


def test_recurrence_enum():
    """Test that RecurrenceEnum has all required values."""
    assert hasattr(RecurrenceEnum, "NONE")
    assert hasattr(RecurrenceEnum, "DAILY")
    assert hasattr(RecurrenceEnum, "WEEKLY")
    assert RecurrenceEnum.NONE.value == "none"
    assert RecurrenceEnum.DAILY.value == "daily"
    assert RecurrenceEnum.WEEKLY.value == "weekly"


def test_review_card_type_enum():
    """Test that ReviewCardTypeEnum has all required values."""
    assert hasattr(ReviewCardTypeEnum, "COMPLETION")
    assert hasattr(ReviewCardTypeEnum, "REJECTION")
    assert hasattr(ReviewCardTypeEnum, "IN_PROGRESS")
    assert hasattr(ReviewCardTypeEnum, "BLOCKED")
    assert hasattr(ReviewCardTypeEnum, "RECURRING")
    assert ReviewCardTypeEnum.COMPLETION.value == "completion"
    assert ReviewCardTypeEnum.REJECTION.value == "rejection"


def test_task_value_association_table():
    """Test that task_value_association table is defined."""
    assert task_value_association is not None
    assert task_value_association.name == "task_value_association"

    # Check columns
    column_names = [col.name for col in task_value_association.columns]
    assert "task_id" in column_names
    assert "value_id" in column_names
