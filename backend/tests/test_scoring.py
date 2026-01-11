"""Tests for scoring strategies and service."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import (
    Base,
    DailyPriority,
    ImpactEnum,
    RejectionDampening,
    Task,
    TaskStateEnum,
    UrgencyEnum,
    User,
)
from app.services.scoring import ScoringContext
from app.services.scoring.additive_strategy import AdditiveWeightedStrategy
from app.services.scoring.registry import get_strategy_registry
from app.services.scoring.service import TaskScoringService

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables once for all tests
Base.metadata.create_all(bind=engine)


@pytest.fixture
def db():
    """Create a fresh database session for each test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        # Clean up all data after each test
        session.query(DailyPriority).delete()
        session.query(RejectionDampening).delete()
        session.query(Task).delete()
        session.query(User).delete()
        session.commit()
        session.close()


@pytest.fixture
def test_user(db):
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="$2b$12$test",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def default_config():
    """Default scoring configuration."""
    return {
        "impact_weight": 2.0,
        "urgency_weight": 1.5,
        "strategic_nudge_boost": 1.5,
        "dampening_factor": 0.5,
        "priority_multiplier": 2.0,
        "impact_values": {"A": 4, "B": 3, "C": 2, "D": 1},
        "urgency_values": {1: 4, 2: 3, 3: 2, 4: 1},
    }


@pytest.fixture
def strategy():
    """Create strategy instance."""
    return AdditiveWeightedStrategy()


class TestAdditiveWeightedStrategy:
    """Tests for AdditiveWeightedStrategy."""

    def test_basic_score_calculation(self, db, test_user, strategy, default_config):
        """Test basic score calculation without modifiers."""
        # Create task with A impact, urgency 2 (soon)
        task = Task(
            user_id=test_user.id,
            title="Test Task",
            impact=ImpactEnum.A,
            urgency=UrgencyEnum.SOON,
            state=TaskStateEnum.READY,
        )
        db.add(task)
        db.commit()

        context = ScoringContext(test_user.id, db, default_config)
        score, reason = strategy.calculate_score(task, context)

        # Expected: (2.0 * 4) + (1.5 * 3) = 8.0 + 4.5 = 12.5
        assert score == 12.5
        assert "Impact:A Urgency:2" in reason
        assert "strategic nudge" not in reason
        assert "dampened" not in reason
        assert "daily priority" not in reason

    def test_strategic_nudge_a3(self, db, test_user, strategy, default_config):
        """Test strategic nudge for A3 tasks."""
        # Create A3 task (high impact, can defer)
        task = Task(
            user_id=test_user.id,
            title="Important but not urgent",
            impact=ImpactEnum.A,
            urgency=UrgencyEnum.CAN_DEFER,
            state=TaskStateEnum.READY,
        )
        db.add(task)
        db.commit()

        context = ScoringContext(test_user.id, db, default_config)
        score, reason = strategy.calculate_score(task, context)

        # Expected: ((2.0 * 4) + (1.5 * 2)) * 1.5 = (8.0 + 3.0) * 1.5 = 16.5
        assert score == 16.5
        assert "strategic nudge" in reason

    def test_strategic_nudge_a4(self, db, test_user, strategy, default_config):
        """Test strategic nudge for A4 tasks."""
        # Create A4 task (high impact, long-term)
        task = Task(
            user_id=test_user.id,
            title="Important long-term",
            impact=ImpactEnum.A,
            urgency=UrgencyEnum.LONGTERM,
            state=TaskStateEnum.READY,
        )
        db.add(task)
        db.commit()

        context = ScoringContext(test_user.id, db, default_config)
        score, reason = strategy.calculate_score(task, context)

        # Expected: ((2.0 * 4) + (1.5 * 1)) * 1.5 = (8.0 + 1.5) * 1.5 = 14.25
        assert score == 14.25
        assert "strategic nudge" in reason

    def test_no_strategic_nudge_a1(self, db, test_user, strategy, default_config):
        """Test no strategic nudge for A1 tasks (high urgency)."""
        task = Task(
            user_id=test_user.id,
            title="Urgent and important",
            impact=ImpactEnum.A,
            urgency=UrgencyEnum.IMMEDIATE,
            state=TaskStateEnum.READY,
        )
        db.add(task)
        db.commit()

        context = ScoringContext(test_user.id, db, default_config)
        score, reason = strategy.calculate_score(task, context)

        # Expected: (2.0 * 4) + (1.5 * 4) = 8.0 + 6.0 = 14.0 (no nudge)
        assert score == 14.0
        assert "strategic nudge" not in reason

    def test_no_strategic_nudge_b3(self, db, test_user, strategy, default_config):
        """Test no strategic nudge for B3 tasks (not A impact)."""
        task = Task(
            user_id=test_user.id,
            title="Medium impact, can defer",
            impact=ImpactEnum.B,
            urgency=UrgencyEnum.CAN_DEFER,
            state=TaskStateEnum.READY,
        )
        db.add(task)
        db.commit()

        context = ScoringContext(test_user.id, db, default_config)
        score, reason = strategy.calculate_score(task, context)

        # Expected: (2.0 * 3) + (1.5 * 2) = 6.0 + 3.0 = 9.0 (no nudge)
        assert score == 9.0
        assert "strategic nudge" not in reason

    def test_rejection_dampening(self, db, test_user, strategy, default_config):
        """Test rejection dampening reduces score."""
        task = Task(
            user_id=test_user.id,
            title="Rejected task",
            impact=ImpactEnum.B,
            urgency=UrgencyEnum.SOON,
            state=TaskStateEnum.READY,
        )
        db.add(task)
        db.commit()

        # Add dampening record
        dampening = RejectionDampening(
            user_id=test_user.id,
            task_id=task.id,
            expires_at="next_review",
        )
        db.add(dampening)
        db.commit()

        context = ScoringContext(test_user.id, db, default_config)
        score, reason = strategy.calculate_score(task, context)

        # Expected: ((2.0 * 3) + (1.5 * 3)) / (1 + 0.5) = 10.5 / 1.5 = 7.0
        assert score == 7.0
        assert "dampened (rejected)" in reason

    def test_daily_priority_boost(self, db, test_user, strategy, default_config):
        """Test daily priority multiplier."""
        task = Task(
            user_id=test_user.id,
            title="Priority task",
            impact=ImpactEnum.C,
            urgency=UrgencyEnum.CAN_DEFER,
            state=TaskStateEnum.READY,
        )
        db.add(task)
        db.commit()

        # Add daily priority (expires in future)
        priority = DailyPriority(
            user_id=test_user.id,
            task_id=task.id,
            priority_date=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=12),
        )
        db.add(priority)
        db.commit()

        context = ScoringContext(test_user.id, db, default_config)
        score, reason = strategy.calculate_score(task, context)

        # Expected: ((2.0 * 2) + (1.5 * 2)) * 2.0 = 7.0 * 2.0 = 14.0
        assert score == 14.0
        assert "daily priority" in reason

    def test_expired_daily_priority_no_boost(
        self, db, test_user, strategy, default_config
    ):
        """Test expired daily priority doesn't boost score."""
        task = Task(
            user_id=test_user.id,
            title="Expired priority task",
            impact=ImpactEnum.C,
            urgency=UrgencyEnum.CAN_DEFER,
            state=TaskStateEnum.READY,
        )
        db.add(task)
        db.commit()

        # Add expired daily priority
        priority = DailyPriority(
            user_id=test_user.id,
            task_id=task.id,
            priority_date=datetime.now(timezone.utc) - timedelta(days=1),
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db.add(priority)
        db.commit()

        context = ScoringContext(test_user.id, db, default_config)
        score, reason = strategy.calculate_score(task, context)

        # Expected: (2.0 * 2) + (1.5 * 2) = 7.0 (no boost)
        assert score == 7.0
        assert "daily priority" not in reason

    def test_combined_modifiers(self, db, test_user, strategy, default_config):
        """Test combination of strategic nudge, dampening, and priority."""
        task = Task(
            user_id=test_user.id,
            title="Complex task",
            impact=ImpactEnum.A,
            urgency=UrgencyEnum.CAN_DEFER,
            state=TaskStateEnum.READY,
        )
        db.add(task)
        db.commit()

        # Add both dampening and priority
        dampening = RejectionDampening(
            user_id=test_user.id,
            task_id=task.id,
            expires_at="next_break",
        )
        priority = DailyPriority(
            user_id=test_user.id,
            task_id=task.id,
            priority_date=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=12),
        )
        db.add(dampening)
        db.add(priority)
        db.commit()

        context = ScoringContext(test_user.id, db, default_config)
        score, reason = strategy.calculate_score(task, context)

        # Expected:
        # Base: (2.0 * 4) + (1.5 * 2) = 11.0
        # With nudge: 11.0 * 1.5 = 16.5
        # With dampening: 16.5 / 1.5 = 11.0
        # With priority: 11.0 * 2.0 = 22.0
        assert score == 22.0
        assert "strategic nudge" in reason
        assert "dampened (rejected)" in reason
        assert "daily priority" in reason

    def test_caching_works(self, db, test_user, strategy, default_config):
        """Test that context caches dampening and priority lookups."""
        task = Task(
            user_id=test_user.id,
            title="Cached task",
            impact=ImpactEnum.B,
            urgency=UrgencyEnum.SOON,
            state=TaskStateEnum.READY,
        )
        db.add(task)
        db.commit()

        context = ScoringContext(test_user.id, db, default_config)

        # First call populates cache
        score1, reason1 = strategy.calculate_score(task, context)

        # Verify cache is populated
        assert task.id in context.dampening_cache
        assert task.id in context.priority_cache

        # Second call should use cache (we can verify by checking cache values)
        score2, reason2 = strategy.calculate_score(task, context)

        assert score1 == score2
        assert reason1 == reason2


class TestTaskScoringService:
    """Tests for TaskScoringService."""

    def test_stochastic_selection_single_task(
        self, db, test_user, strategy, default_config
    ):
        """Test stochastic selection with single task returns that task."""
        task = Task(
            user_id=test_user.id,
            title="Only task",
            impact=ImpactEnum.B,
            urgency=UrgencyEnum.SOON,
            state=TaskStateEnum.READY,
        )
        db.add(task)
        db.commit()

        service = TaskScoringService(strategy, default_config)
        selected, reason = service.select_stochastic([task], test_user.id, db)

        assert selected.id == task.id
        assert "Impact:B Urgency:2" in reason

    def test_stochastic_selection_empty_list_raises(
        self, db, test_user, strategy, default_config
    ):
        """Test stochastic selection with empty list raises error."""
        service = TaskScoringService(strategy, default_config)

        with pytest.raises(ValueError, match="Cannot select from empty task list"):
            service.select_stochastic([], test_user.id, db)

    def test_stochastic_selection_multiple_tasks(
        self, db, test_user, strategy, default_config
    ):
        """Test stochastic selection with multiple tasks."""
        tasks = []
        for i in range(5):
            task = Task(
                user_id=test_user.id,
                title=f"Task {i}",
                impact=ImpactEnum.B,
                urgency=UrgencyEnum.SOON,
                state=TaskStateEnum.READY,
            )
            db.add(task)
            tasks.append(task)
        db.commit()

        service = TaskScoringService(strategy, default_config)
        selected, reason = service.select_stochastic(tasks, test_user.id, db)

        # Should return one of the tasks
        assert selected in tasks
        assert reason is not None

    def test_stochastic_respects_weights(self, db, test_user, strategy, default_config):
        """Test that higher-scored tasks are selected more often."""
        # Create one high-score task and one low-score task
        high_task = Task(
            user_id=test_user.id,
            title="High score",
            impact=ImpactEnum.A,
            urgency=UrgencyEnum.IMMEDIATE,
            state=TaskStateEnum.READY,
        )
        low_task = Task(
            user_id=test_user.id,
            title="Low score",
            impact=ImpactEnum.D,
            urgency=UrgencyEnum.LONGTERM,
            state=TaskStateEnum.READY,
        )
        db.add(high_task)
        db.add(low_task)
        db.commit()

        service = TaskScoringService(strategy, default_config)

        # Run selection many times and count results
        high_count = 0
        low_count = 0
        iterations = 100

        for _ in range(iterations):
            selected, _ = service.select_stochastic(
                [high_task, low_task], test_user.id, db
            )
            if selected.id == high_task.id:
                high_count += 1
            else:
                low_count += 1

        # High score task should be selected significantly more often
        # With A1 (14.0) vs D4 (3.5), ratio is ~4:1
        assert high_count > low_count
        assert high_count > iterations * 0.6  # At least 60% of the time

    def test_rank_tasks_empty_list(self, db, test_user, strategy, default_config):
        """Test ranking empty list returns empty."""
        service = TaskScoringService(strategy, default_config)
        ranked = service.rank_tasks([], test_user.id, db)

        assert ranked == []

    def test_rank_tasks_sorted_descending(
        self, db, test_user, strategy, default_config
    ):
        """Test tasks are ranked in descending score order."""
        # Create tasks with different scores
        task_a1 = Task(
            user_id=test_user.id,
            title="A1",
            impact=ImpactEnum.A,
            urgency=UrgencyEnum.IMMEDIATE,
            state=TaskStateEnum.READY,
        )
        task_b2 = Task(
            user_id=test_user.id,
            title="B2",
            impact=ImpactEnum.B,
            urgency=UrgencyEnum.SOON,
            state=TaskStateEnum.READY,
        )
        task_d4 = Task(
            user_id=test_user.id,
            title="D4",
            impact=ImpactEnum.D,
            urgency=UrgencyEnum.LONGTERM,
            state=TaskStateEnum.READY,
        )
        db.add_all([task_a1, task_b2, task_d4])
        db.commit()

        service = TaskScoringService(strategy, default_config)
        ranked = service.rank_tasks([task_d4, task_a1, task_b2], test_user.id, db)

        # Should be in descending order: A1, B2, D4
        assert len(ranked) == 3
        assert ranked[0][0].title == "A1"
        assert ranked[1][0].title == "B2"
        assert ranked[2][0].title == "D4"

        # Verify scores are also descending
        assert ranked[0][1] > ranked[1][1] > ranked[2][1]

    def test_rank_tasks_includes_reasons(self, db, test_user, strategy, default_config):
        """Test ranked tasks include transparency reasons."""
        task = Task(
            user_id=test_user.id,
            title="Task with reason",
            impact=ImpactEnum.A,
            urgency=UrgencyEnum.CAN_DEFER,
            state=TaskStateEnum.READY,
        )
        db.add(task)
        db.commit()

        service = TaskScoringService(strategy, default_config)
        ranked = service.rank_tasks([task], test_user.id, db)

        assert len(ranked) == 1
        task_result, score, reason = ranked[0]
        assert "Impact:A Urgency:3" in reason
        assert "strategic nudge" in reason


class TestScoringStrategyRegistry:
    """Tests for ScoringStrategyRegistry."""

    def test_registry_has_default_strategy(self):
        """Test registry has default strategy registered."""
        registry = get_strategy_registry()
        default = registry.get_default()

        assert default is not None
        assert default.name == "additive_weighted"

    def test_registry_can_get_by_name(self):
        """Test registry can retrieve strategy by name."""
        registry = get_strategy_registry()
        strategy = registry.get("additive_weighted")

        assert strategy is not None
        assert strategy.name == "additive_weighted"

    def test_registry_raises_on_unknown_strategy(self):
        """Test registry raises error for unknown strategy."""
        registry = get_strategy_registry()

        with pytest.raises(ValueError, match="Unknown scoring strategy"):
            registry.get("nonexistent_strategy")

    def test_registry_lists_strategies(self):
        """Test registry can list all strategies."""
        registry = get_strategy_registry()
        strategies = registry.list_strategies()

        assert len(strategies) >= 1
        assert any(s["name"] == "additive_weighted" for s in strategies)
        assert all("name" in s and "description" in s for s in strategies)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_all_zero_scores(self, db, test_user, strategy, default_config):
        """Test handling of all tasks having zero score."""
        # This shouldn't happen in practice, but test it anyway
        # We can't easily create zero-score tasks with the current formula,
        # so we'll test with very low scores instead
        tasks = []
        for i in range(3):
            task = Task(
                user_id=test_user.id,
                title=f"Low score {i}",
                impact=ImpactEnum.D,
                urgency=UrgencyEnum.LONGTERM,
                state=TaskStateEnum.READY,
            )
            db.add(task)
            tasks.append(task)
        db.commit()

        service = TaskScoringService(strategy, default_config)
        selected, reason = service.select_stochastic(tasks, test_user.id, db)

        # Should still select one task
        assert selected in tasks

    def test_different_user_isolation(self, db, strategy, default_config):
        """Test that users' dampening/priority don't interfere."""
        # Create two users
        user1 = User(
            username="user1",
            email="user1@example.com",
            password_hash="$2b$12$test",
            is_active=True,
        )
        user2 = User(
            username="user2",
            email="user2@example.com",
            password_hash="$2b$12$test",
            is_active=True,
        )
        db.add_all([user1, user2])
        db.commit()

        # Create task for user1 with dampening
        task1 = Task(
            user_id=user1.id,
            title="User 1 task",
            impact=ImpactEnum.B,
            urgency=UrgencyEnum.SOON,
            state=TaskStateEnum.READY,
        )
        db.add(task1)
        db.commit()

        dampening = RejectionDampening(
            user_id=user1.id, task_id=task1.id, expires_at="next_review"
        )
        db.add(dampening)
        db.commit()

        # Create task for user2 (no dampening)
        task2 = Task(
            user_id=user2.id,
            title="User 2 task",
            impact=ImpactEnum.B,
            urgency=UrgencyEnum.SOON,
            state=TaskStateEnum.READY,
        )
        db.add(task2)
        db.commit()

        # Score both tasks
        context1 = ScoringContext(user1.id, db, default_config)
        score1, reason1 = strategy.calculate_score(task1, context1)

        context2 = ScoringContext(user2.id, db, default_config)
        score2, reason2 = strategy.calculate_score(task2, context2)

        # User 1's task should be dampened, user 2's should not
        assert score1 < score2
        assert "dampened" in reason1
        assert "dampened" not in reason2
