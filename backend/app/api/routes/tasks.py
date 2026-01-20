"""
Task endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskStateEnum,
    TaskTransition,
    TaskTransitionResponse,
)
from app.models import Task, User, Value
from app.auth import get_current_active_user
from app.services.state_machine import (
    transition_task_state,
    InvalidStateTransitionError,
)

router = APIRouter()


@router.get("/", response_model=list[TaskResponse])
async def list_tasks(
    state: Optional[TaskStateEnum] = Query(None),
    value_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all tasks for the authenticated user with optional filters."""
    query = db.query(Task).filter(Task.user_id == current_user.id)

    # Apply state filter if provided
    if state is not None:
        query = query.filter(Task.state == state)

    # Apply value filter if provided
    if value_id is not None:
        # Verify the value exists and belongs to the current user
        value = (
            db.query(Value)
            .filter(Value.id == value_id, Value.user_id == current_user.id)
            .first()
        )
        if value is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Value not found",
            )
        query = query.join(Task.values).filter(Value.id == value_id)

    tasks = query.all()
    return [
        TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            value_ids=[v.id for v in task.values],
            impact=task.impact,
            urgency=task.urgency,
            state=task.state,
            due_date=task.due_date,
            recurrence=task.recurrence,
            completion_percentage=task.completion_percentage,
            notes=task.notes,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
        for task in tasks
    ]


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new task for the authenticated user."""
    # Create task with only explicitly provided fields
    # SQLAlchemy will apply model defaults for impact/urgency if not provided
    task_dict = {
        "user_id": current_user.id,
        "title": task_data.title,
        "description": task_data.description,
        "due_date": task_data.due_date,
        "recurrence": task_data.recurrence,
    }

    # Only set impact/urgency if provided (to allow model defaults)
    if task_data.impact is not None:
        task_dict["impact"] = task_data.impact
    if task_data.urgency is not None:
        task_dict["urgency"] = task_data.urgency

    new_task = Task(**task_dict)

    # Handle value linking if value_ids provided
    if task_data.value_ids:
        # Deduplicate IDs to avoid false negatives when validating
        unique_value_ids = list(set(task_data.value_ids))

        # Query values that exist and belong to user
        values = (
            db.query(Value)
            .filter(Value.id.in_(unique_value_ids), Value.user_id == current_user.id)
            .all()
        )

        # Verify all requested values were found
        if len(values) != len(unique_value_ids):
            raise HTTPException(status_code=400, detail="Invalid value_ids")

        # Link to task
        new_task.values = values

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return TaskResponse(
        id=new_task.id,
        title=new_task.title,
        description=new_task.description,
        value_ids=[v.id for v in new_task.values],
        impact=new_task.impact,
        urgency=new_task.urgency,
        state=new_task.state,
        due_date=new_task.due_date,
        recurrence=new_task.recurrence,
        completion_percentage=new_task.completion_percentage,
        notes=new_task.notes,
        created_at=new_task.created_at,
        updated_at=new_task.updated_at,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific task for the authenticated user."""
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.user_id == current_user.id)
        .first()
    )

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        value_ids=[v.id for v in task.values],
        impact=task.impact,
        urgency=task.urgency,
        state=task.state,
        due_date=task.due_date,
        recurrence=task.recurrence,
        completion_percentage=task.completion_percentage,
        notes=task.notes,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a task for the authenticated user."""
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.user_id == current_user.id)
        .first()
    )

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    # Update fields if provided
    if task_data.title is not None:
        task.title = task_data.title
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.impact is not None:
        task.impact = task_data.impact
    if task_data.urgency is not None:
        task.urgency = task_data.urgency
    if task_data.state is not None:
        task.state = task_data.state
    if task_data.due_date is not None:
        task.due_date = task_data.due_date
    if task_data.completion_percentage is not None:
        task.completion_percentage = task_data.completion_percentage
    if task_data.notes is not None:
        task.notes = task_data.notes

    # Update value_ids if provided
    if task_data.value_ids is not None:
        if task_data.value_ids:
            # Deduplicate IDs to avoid false negatives when validating
            unique_value_ids = list(set(task_data.value_ids))

            # Query values that exist and belong to user
            values = (
                db.query(Value)
                .filter(
                    Value.id.in_(unique_value_ids), Value.user_id == current_user.id
                )
                .all()
            )

            # Verify all requested values were found
            if len(values) != len(unique_value_ids):
                raise HTTPException(status_code=400, detail="Invalid value_ids")

            # Replace task values
            task.values = values
        else:
            # Clear all values
            task.values = []

    db.commit()
    db.refresh(task)

    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        value_ids=[v.id for v in task.values],
        impact=task.impact,
        urgency=task.urgency,
        state=task.state,
        due_date=task.due_date,
        recurrence=task.recurrence,
        completion_percentage=task.completion_percentage,
        notes=task.notes,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a task for the authenticated user."""
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.user_id == current_user.id)
        .first()
    )

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    db.delete(task)
    db.commit()


@router.post("/{task_id}/transition", response_model=TaskTransitionResponse)
async def transition_task(
    task_id: int,
    transition_data: TaskTransition,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Transition a task to a new state with validation.

    Validates that the transition is allowed per the state machine rules.
    Automatically creates next instance for recurring tasks when completed.
    """
    # Fetch the task
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.user_id == current_user.id)
        .first()
    )

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    # Perform the transition
    try:
        next_instance = transition_task_state(
            db=db,
            task=task,
            new_state=transition_data.new_state,
            notes=transition_data.notes,
            completion_percentage=transition_data.completion_percentage,
        )
        db.commit()
        db.refresh(task)
        if next_instance:
            db.refresh(next_instance)
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Build response
    task_response = TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        value_ids=[v.id for v in task.values],
        impact=task.impact,
        urgency=task.urgency,
        state=task.state,
        due_date=task.due_date,
        recurrence=task.recurrence,
        completion_percentage=task.completion_percentage,
        notes=task.notes,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
    )

    next_instance_response = None
    if next_instance:
        next_instance_response = TaskResponse(
            id=next_instance.id,
            title=next_instance.title,
            description=next_instance.description,
            value_ids=[v.id for v in next_instance.values],
            impact=next_instance.impact,
            urgency=next_instance.urgency,
            state=next_instance.state,
            due_date=next_instance.due_date,
            recurrence=next_instance.recurrence,
            completion_percentage=next_instance.completion_percentage,
            notes=next_instance.notes,
            created_at=next_instance.created_at,
            updated_at=next_instance.updated_at,
            completed_at=next_instance.completed_at,
        )

    return TaskTransitionResponse(
        task=task_response, next_instance=next_instance_response
    )
