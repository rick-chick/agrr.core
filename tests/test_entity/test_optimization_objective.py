"""Tests for optimization objective calculation.

CRITICAL: These tests ensure that the objective function is consistent
across all optimizers. If you modify the objective function, you MUST
update these tests.
"""

import pytest
from agrr_core.entity.value_objects.optimization_objective import (
    OptimizationObjective,
    OptimizationMetrics,
    DEFAULT_OBJECTIVE,
)


class TestOptimizationMetrics:
    """Test OptimizationMetrics value object."""
    
    def test_from_cost_only(self):
        """Create metrics with cost only."""
        metrics = OptimizationMetrics.from_cost_only(cost=1000)
        
        assert metrics.cost == 1000
        assert metrics.revenue is None
        assert metrics.profit == -1000  # Negative cost for maximization
    
    def test_from_cost_and_revenue(self):
        """Create metrics with cost and revenue (profit auto-calculated)."""
        metrics = OptimizationMetrics.from_cost_and_revenue(cost=1000, revenue=2000)
        
        assert metrics.cost == 1000
        assert metrics.revenue == 2000
        assert metrics.profit == 1000  # 2000 - 1000
    
    def test_profit_property_with_revenue(self):
        """Profit property calculates revenue - cost."""
        metrics = OptimizationMetrics(cost=500, revenue=1500)
        assert metrics.profit == 1000
    
    def test_profit_property_without_revenue(self):
        """Profit property returns -cost when revenue is None."""
        metrics = OptimizationMetrics(cost=1000)
        assert metrics.profit == -1000
    
    def test_negative_cost_raises_error(self):
        """Negative cost is not allowed."""
        with pytest.raises(ValueError, match="cost must be non-negative"):
            OptimizationMetrics(cost=-100)
    
    def test_negative_revenue_raises_error(self):
        """Negative revenue is not allowed."""
        with pytest.raises(ValueError, match="revenue must be non-negative"):
            OptimizationMetrics(cost=100, revenue=-200)


class TestOptimizationObjective:
    """Test OptimizationObjective."""
    
    def test_calculate_with_revenue(self):
        """Calculate profit with revenue."""
        objective = OptimizationObjective()
        metrics = OptimizationMetrics(cost=1000, revenue=2000)
        
        profit = objective.calculate(metrics)
        
        assert profit == 1000
    
    def test_calculate_without_revenue(self):
        """Calculate profit without revenue (cost minimization equivalent)."""
        objective = OptimizationObjective()
        metrics = OptimizationMetrics(cost=1000)
        
        profit = objective.calculate(metrics)
        
        assert profit == -1000  # Negative cost
    
    def test_select_best_with_revenue(self):
        """Select best candidate maximizes profit."""
        objective = OptimizationObjective()
        candidates = [
            OptimizationMetrics(cost=100, revenue=200),  # profit=100
            OptimizationMetrics(cost=80, revenue=220),   # profit=140 ← best
            OptimizationMetrics(cost=120, revenue=180),  # profit=60
        ]
        
        best = objective.select_best(candidates, key_func=objective.calculate)
        
        assert best.profit == 140
    
    def test_select_best_without_revenue(self):
        """Select best candidate minimizes cost (when revenue is None)."""
        objective = OptimizationObjective()
        candidates = [
            OptimizationMetrics(cost=100),  # profit=-100
            OptimizationMetrics(cost=50),   # profit=-50 ← best (minimum cost = max profit)
            OptimizationMetrics(cost=200),  # profit=-200
        ]
        
        best = objective.select_best(candidates, key_func=objective.calculate)
        
        assert best.cost == 50  # Minimum cost = maximum profit
    
    def test_select_best_with_empty_list_raises_error(self):
        """select_best raises error for empty list."""
        objective = OptimizationObjective()
        
        with pytest.raises(ValueError, match="empty"):
            objective.select_best([], key_func=lambda x: 0)
    
    def test_compare(self):
        """Compare two objective values."""
        objective = OptimizationObjective()
        
        assert objective.compare(100, 50) == 1    # 100 > 50
        assert objective.compare(50, 100) == -1   # 50 < 100
        assert objective.compare(100, 100) == 0   # 100 == 100
    
    def test_default_objective_singleton(self):
        """DEFAULT_OBJECTIVE is available."""
        assert DEFAULT_OBJECTIVE is not None
        assert isinstance(DEFAULT_OBJECTIVE, OptimizationObjective)


class TestObjectiveFunctionSignature:
    """Tests to detect objective function changes.
    
    ⚠️ CRITICAL: If these tests fail, objective has changed.
    You MUST update ALL optimizers.
    """
    
    def test_current_objective_function(self):
        """Document current objective: profit = revenue - cost.
        
        If this fails, update ALL optimizers.
        """
        objective = OptimizationObjective()
        
        # Case 1: With revenue
        metrics1 = OptimizationMetrics(cost=1000, revenue=2000)
        assert objective.calculate(metrics1) == 1000, (
            "Objective function changed! Expected profit = 1000"
        )
        
        # Case 2: Without revenue (cost minimization)
        metrics2 = OptimizationMetrics(cost=1000)
        assert objective.calculate(metrics2) == -1000, (
            "Objective function changed! Expected profit = -1000"
        )
    
    def test_singleton_consistency(self):
        """DEFAULT_OBJECTIVE behaves the same as new instance."""
        obj1 = DEFAULT_OBJECTIVE
        obj2 = OptimizationObjective()
        
        metrics = OptimizationMetrics(cost=100, revenue=200)
        
        assert obj1.calculate(metrics) == obj2.calculate(metrics)
    
    def test_objective_is_deterministic(self):
        """Objective calculation MUST be deterministic."""
        objective = OptimizationObjective()
        metrics = OptimizationMetrics(cost=100, revenue=200)
        
        # Call multiple times
        results = [objective.calculate(metrics) for _ in range(10)]
        
        # All results must be identical
        assert len(set(results)) == 1
    
    @pytest.mark.parametrize("cost,revenue,expected_profit", [
        (100, 200, 100),
        (500, 1000, 500),
        (0, 1000, 1000),
        (1000, 1000, 0),
    ])
    def test_profit_calculation_examples(self, cost, revenue, expected_profit):
        """Test profit calculation with various inputs."""
        metrics = OptimizationMetrics(cost=cost, revenue=revenue)
        objective = OptimizationObjective()
        
        profit = objective.calculate(metrics)
        
        assert profit == expected_profit

