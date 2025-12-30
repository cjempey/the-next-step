"""
Task endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import TaskCreate, TaskUpdate, TaskResponse

router = APIRouter()


@router.get("/", response_model=list[TaskResponse])
async def list_tasks(db: Session = Depends(get_db)):
    """List all tasks."""
    # TODO: Implement
    return []


@router.post("/", response_model=TaskResponse)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    # TODO: Implement
    pass


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a specific task."""
    # TODO: Implement
    pass


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db)):
    """Update a task."""
    # TODO: Implement
    pass


@router.delete("/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task."""
    # TODO: Implement
    pass
