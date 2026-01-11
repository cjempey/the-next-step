"""
Scoring service for task suggestion weighting.

This module implements a strategy pattern for scoring algorithms,
allowing easy experimentation with different formulas and future
per-user customization.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from app.models import Task


class ScoringContext:
    """Context passed to scoring strategies."""

    def __init__(self, user_id: int, db: Session, config: dict):
        """Initialize scoring context.

        Args:
            user_id: User ID for filtering dampening and priorities
            db: Database session for queries
            config: Scoring configuration dictionary
        """
        self.user_id = user_id
        self.db = db
        self.config = config
        self.dampening_cache: dict[int, bool] = {}  # task_id -> has_dampening
        self.priority_cache: dict[int, bool] = {}  # task_id -> is_priority


class ScoringStrategy(ABC):
    """Abstract base for scoring strategies."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable strategy name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of this strategy's approach."""
        pass

    @abstractmethod
    def calculate_score(
        self, task: "Task", context: ScoringContext
    ) -> tuple[float, str]:
        """Calculate final score for a task.

        Args:
            task: Task to score
            context: Scoring context with user_id, db, config

        Returns:
            tuple[float, str]: (final_score, transparency_reason)
        """
        pass

    def calculate_all_scores(
        self, tasks: list["Task"], context: ScoringContext
    ) -> list[tuple["Task", float, str]]:
        """Calculate scores for all tasks.

        Args:
            tasks: List of tasks to score
            context: Scoring context

        Returns:
            List of (task, score, reason) tuples
        """
        return [(task, *self.calculate_score(task, context)) for task in tasks]


__all__ = ["ScoringContext", "ScoringStrategy"]
