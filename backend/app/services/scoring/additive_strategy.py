"""
Additive weighted scoring strategy (MVP default).

Implements the core scoring algorithm from MVP section 7:
  Base = (impact_weight × impact_value) + (urgency_weight × urgency_value) + strategic_nudge
  With_Dampening = Base / (1 + dampening_factor if rejected)
  Final = With_Dampening × (priority_multiplier if daily priority, else 1.0)
"""

from datetime import datetime, timezone

from app.models import DailyPriority, ImpactEnum, RejectionDampening, Task
from app.services.scoring import ScoringContext, ScoringStrategy


class AdditiveWeightedStrategy(ScoringStrategy):
    """Default MVP scoring strategy: Additive weighted scoring.

    Formula:
      Base = (impact_weight × impact_value) + (urgency_weight × urgency_value) + strategic_nudge
      With_Dampening = Base / (1 + dampening_factor if rejected)
      Final = With_Dampening × (priority_multiplier if daily priority, else 1.0)

    Strategic nudge applied when Impact=A AND Urgency>=3 (can defer or long-term).
    """

    @property
    def name(self) -> str:
        """Strategy name."""
        return "additive_weighted"

    @property
    def description(self) -> str:
        """Strategy description."""
        return "Additive weighted scoring with strategic nudge (MVP default)"

    def calculate_score(self, task: Task, context: ScoringContext) -> tuple[float, str]:
        """Calculate final score for a task.

        Args:
            task: Task to score
            context: Scoring context with user_id, db, config

        Returns:
            tuple[float, str]: (final_score, transparency_reason)
        """
        config = context.config
        reason_parts = []

        # 1. Base score: impact + urgency
        impact_value = config["impact_values"][task.impact.value]
        urgency_value = config["urgency_values"][task.urgency.value]

        base_score = (
            config["impact_weight"] * impact_value
            + config["urgency_weight"] * urgency_value
        )
        reason_parts.append(f"Impact:{task.impact.value} Urgency:{task.urgency.value}")

        # 2. Strategic nudge for high-impact, low-urgency tasks
        if task.impact == ImpactEnum.A and task.urgency.value >= 3:
            base_score *= config["strategic_nudge_boost"]
            reason_parts.append("strategic nudge")

        # 3. Rejection dampening
        if self._has_active_dampening(task, context):
            base_score /= 1 + config["dampening_factor"]
            reason_parts.append("dampened (rejected)")

        # 4. Daily priority boost
        if self._is_daily_priority(task, context):
            base_score *= config["priority_multiplier"]
            reason_parts.append("daily priority")

        reason = " + ".join(reason_parts)
        return base_score, reason

    def _has_active_dampening(self, task: Task, context: ScoringContext) -> bool:
        """Check if task has active rejection dampening.

        Args:
            task: Task to check
            context: Scoring context with caching

        Returns:
            True if task has active dampening
        """
        # Check cache first
        if task.id in context.dampening_cache:
            return context.dampening_cache[task.id]

        # Query for active dampening
        # Per MVP: expires_at is a string ("next_break" or "next_review")
        # For MVP, any dampening record means it's active
        # (Break/Review actions delete these records)
        dampening = (
            context.db.query(RejectionDampening)
            .filter(
                RejectionDampening.user_id == context.user_id,
                RejectionDampening.task_id == task.id,
            )
            .first()
        )

        has_dampening = dampening is not None
        context.dampening_cache[task.id] = has_dampening
        return has_dampening

    def _is_daily_priority(self, task: Task, context: ScoringContext) -> bool:
        """Check if task is in today's priorities.

        Args:
            task: Task to check
            context: Scoring context with caching

        Returns:
            True if task is a daily priority and not expired
        """
        # Check cache first
        if task.id in context.priority_cache:
            return context.priority_cache[task.id]

        # Query for daily priority
        now = datetime.now(timezone.utc)
        priority = (
            context.db.query(DailyPriority)
            .filter(
                DailyPriority.user_id == context.user_id,
                DailyPriority.task_id == task.id,
                DailyPriority.expires_at > now,
            )
            .first()
        )

        is_priority = priority is not None
        context.priority_cache[task.id] = is_priority
        return is_priority
