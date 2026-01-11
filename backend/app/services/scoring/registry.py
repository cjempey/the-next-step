"""
Strategy registry for managing available scoring strategies.

Provides a centralized registry for registering and retrieving
scoring strategies, enabling runtime strategy selection.
"""

from app.services.scoring import ScoringStrategy
from app.services.scoring.additive_strategy import AdditiveWeightedStrategy


class ScoringStrategyRegistry:
    """Registry for available scoring strategies."""

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._strategies: dict[str, ScoringStrategy] = {}
        self._default_strategy_name: str = "additive_weighted"

    def register(self, strategy: ScoringStrategy) -> None:
        """Register a scoring strategy.

        Args:
            strategy: Strategy instance to register
        """
        self._strategies[strategy.name] = strategy

    def get(self, name: str) -> ScoringStrategy:
        """Get strategy by name.

        Args:
            name: Strategy name

        Returns:
            Strategy instance

        Raises:
            ValueError: If strategy not found
        """
        if name not in self._strategies:
            raise ValueError(f"Unknown scoring strategy: {name}")
        return self._strategies[name]

    def get_default(self) -> ScoringStrategy:
        """Get default strategy.

        Returns:
            Default strategy instance
        """
        return self._strategies[self._default_strategy_name]

    def list_strategies(self) -> list[dict[str, str]]:
        """List all available strategies.

        Returns:
            List of strategy metadata dicts with 'name' and 'description' keys
        """
        return [
            {"name": s.name, "description": s.description}
            for s in self._strategies.values()
        ]


# Global registry instance
_registry = ScoringStrategyRegistry()


def get_strategy_registry() -> ScoringStrategyRegistry:
    """Get the global strategy registry.

    Returns:
        Global registry instance
    """
    return _registry


# Register default strategy
_registry.register(AdditiveWeightedStrategy())
