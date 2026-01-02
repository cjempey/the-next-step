"""
Task endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import TaskCreate, TaskUpdate, TaskResponse
from app.models import Task, User
from app.auth import get_current_active_user

router = APIRouter()


@router.get("/", response_model=list[TaskResponse])
async def list_tasks(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """List all tasks for the authenticated user."""
    tasks = db.query(Task).filter(Task.user_id == current_user.id).all()
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
    new_task = Task(
        user_id=current_user.id,
        title=task_data.title,
        description=task_data.description,
        impact=task_data.impact,
        urgency=task_data.urgency,
        due_date=task_data.due_date,
        recurrence=task_data.recurrence,
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return TaskResponse(
        id=new_task.id,
        title=new_task.title,
        description=new_task.description,
        value_ids=[],
        impact=new_task.impact,
        urgency=new_task.urgency,
        state=new_task.state,
        due_date=new_task.due_date,
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
