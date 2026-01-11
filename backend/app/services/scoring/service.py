"""
High-level task scoring service.

Provides convenient methods for stochastic selection and ranked lists,
using the strategy pattern for flexible scoring algorithms.
"""

import random
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from app.services.scoring import ScoringContext, ScoringStrategy

if TYPE_CHECKING:
    from app.models import Task


class TaskScoringService:
    """High-level service for task scoring and selection."""

    def __init__(self, strategy: ScoringStrategy, config: dict):
        """Initialize scoring service.

        Args:
            strategy: Scoring strategy to use
            config: Scoring configuration dictionary
        """
        self.strategy = strategy
        self.config = config

    def select_stochastic(
        self, tasks: list["Task"], user_id: int, db: Session
    ) -> tuple["Task", str]:
        """Randomly select one task using weighted probabilities.

        Uses weighted roulette wheel selection where higher-scored tasks
        are more likely to be selected, but lower-scored tasks still have
        a chance.

        Args:
            tasks: List of Ready tasks to choose from
            user_id: User ID for context
            db: Database session

        Returns:
            tuple[Task, str]: (selected_task, reason_string)

        Raises:
            ValueError: If tasks list is empty
        """
        if not tasks:
            raise ValueError("Cannot select from empty task list")

        context = ScoringContext(user_id, db, self.config)
        scored_tasks = self.strategy.calculate_all_scores(tasks, context)

        # Handle single task case
        if len(scored_tasks) == 1:
            task, score, reason = scored_tasks[0]
            return task, reason

        # Normalize scores to probabilities
        scores = [score for _, score, _ in scored_tasks]
        total = sum(scores)

        # Handle all-zero scores: equal probability
        if total == 0:
            probabilities = [1 / len(tasks)] * len(tasks)
        else:
            probabilities = [s / total for s in scores]

        # Weighted random selection
        selected_task, score, reason = random.choices(
            scored_tasks, weights=probabilities, k=1
        )[0]

        return selected_task, reason

    def rank_tasks(
        self, tasks: list["Task"], user_id: int, db: Session
    ) -> list[tuple["Task", float, str]]:
        """Return tasks ranked by score (descending).

        Deterministic ranking for morning planning, showing which tasks
        have the highest scores.

        Args:
            tasks: List of Ready tasks to rank
            user_id: User ID for context
            db: Database session

        Returns:
            List of (task, score, reason) tuples, sorted by score descending
        """
        if not tasks:
            return []

        context = ScoringContext(user_id, db, self.config)
        scored_tasks = self.strategy.calculate_all_scores(tasks, context)

        # Sort descending by score
        scored_tasks.sort(key=lambda x: x[1], reverse=True)

        return scored_tasks
