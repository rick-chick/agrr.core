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
    
    def test_metrics_with_cost_only(self):
        """Calculate metrics with growth period parameters (cost only)."""
        metrics = OptimizationMetrics(growth_days=100, daily_fixed_cost=10.0)
        
        assert metrics.cost == 1000
        assert metrics.revenue is None
        assert metrics.profit == -1000  # Negative cost for maximization
    
    def test_metrics_with_cost_and_revenue(self):
        """Calculate metrics with crop allocation parameters (cost and revenue)."""
        metrics = OptimizationMetrics(
            area_used=200.0,  # 100 × 2
            revenue_per_area=10.0,
            growth_days=100,
            daily_fixed_cost=10.0
        )
        
        assert metrics.cost == 1000  # 100 * 10
        assert metrics.revenue == 2000  # 200 * 10
        assert metrics.profit == 1000  # 2000 - 1000
    
    def test_profit_property_with_revenue(self):
        """Profit property calculates revenue - cost."""
        metrics = OptimizationMetrics(
            area_used=200.0,  # 100 × 2
            revenue_per_area=7.5,
            growth_days=50,
            daily_fixed_cost=10.0
        )
        assert metrics.cost == 500  # 50 * 10
        assert metrics.revenue == 1500  # 200 * 7.5
        assert metrics.profit == 1000  # 1500 - 500
    
    def test_profit_property_without_revenue(self):
        """Profit property returns -cost when revenue is None."""
        metrics = OptimizationMetrics(growth_days=100, daily_fixed_cost=10.0)
        assert metrics.profit == -1000
    
    def test_max_revenue_constraint(self):
        """Max revenue constraint is enforced."""
        metrics = OptimizationMetrics(
            area_used=200.0,  # 100 × 2
            revenue_per_area=10.0,
            growth_days=100,
            daily_fixed_cost=10.0,
            max_revenue=1500.0  # Cap revenue at 1500
        )
        assert metrics.cost == 1000
        assert metrics.revenue == 1500  # Capped at max_revenue
        assert metrics.profit == 500  # 1500 - 1000


class TestOptimizationObjective:
    """Test OptimizationObjective."""
    
    def test_calculate_with_revenue(self):
        """Calculate profit with revenue."""
        objective = OptimizationObjective()
        metrics = OptimizationMetrics(
            area_used=200.0,  # 100 × 2
            revenue_per_area=10.0,
            growth_days=100,
            daily_fixed_cost=10.0
        )
        
        profit = objective.calculate(metrics)
        
        assert profit == 1000  # 2000 - 1000
    
    def test_calculate_without_revenue(self):
        """Calculate profit without revenue (cost minimization equivalent)."""
        objective = OptimizationObjective()
        metrics = OptimizationMetrics(growth_days=100, daily_fixed_cost=10.0)
        
        profit = objective.calculate(metrics)
        
        assert profit == -1000  # Negative cost
    
    def test_select_best_with_revenue(self):
        """Select best candidate maximizes profit."""
        objective = OptimizationObjective()
        candidates = [
            OptimizationMetrics(area_used=20, revenue_per_area=10, growth_days=10, daily_fixed_cost=10),  # profit=100
            OptimizationMetrics(area_used=22, revenue_per_area=10, growth_days=8, daily_fixed_cost=10),   # profit=140 ← best
            OptimizationMetrics(area_used=18, revenue_per_area=10, growth_days=12, daily_fixed_cost=10),  # profit=60
        ]
        
        best = objective.select_best(candidates, key_func=objective.calculate)
        
        assert best.profit == 140
    
    def test_select_best_without_revenue(self):
        """Select best candidate minimizes cost (when revenue is None)."""
        objective = OptimizationObjective()
        candidates = [
            OptimizationMetrics(growth_days=10, daily_fixed_cost=10),  # cost=100, profit=-100
            OptimizationMetrics(growth_days=5, daily_fixed_cost=10),   # cost=50, profit=-50 ← best
            OptimizationMetrics(growth_days=20, daily_fixed_cost=10),  # cost=200, profit=-200
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
        metrics1 = OptimizationMetrics(
            area_used=200, revenue_per_area=10,  # 100 × 2 = 200
            growth_days=100, daily_fixed_cost=10
        )
        assert objective.calculate(metrics1) == 1000, (
            "Objective function changed! Expected profit = 1000"
        )
        
        # Case 2: Without revenue (cost minimization)
        metrics2 = OptimizationMetrics(growth_days=100, daily_fixed_cost=10)
        assert objective.calculate(metrics2) == -1000, (
            "Objective function changed! Expected profit = -1000"
        )
    
    def test_singleton_consistency(self):
        """DEFAULT_OBJECTIVE behaves the same as new instance."""
        obj1 = DEFAULT_OBJECTIVE
        obj2 = OptimizationObjective()
        
        metrics = OptimizationMetrics(
            area_used=20, revenue_per_area=10,  # 10 × 2 = 20
            growth_days=10, daily_fixed_cost=10
        )
        
        assert obj1.calculate(metrics) == obj2.calculate(metrics)
    
    def test_objective_is_deterministic(self):
        """Objective calculation MUST be deterministic."""
        objective = OptimizationObjective()
        metrics = OptimizationMetrics(
            area_used=20, revenue_per_area=10,  # 10 × 2 = 20
            growth_days=10, daily_fixed_cost=10
        )
        
        # Call multiple times
        results = [objective.calculate(metrics) for _ in range(10)]
        
        # All results must be identical
        assert len(set(results)) == 1
    
    @pytest.mark.parametrize("growth_days,daily_fixed_cost,area_used,revenue_per_area,expected_profit", [
        (10, 10, 20, 10, 100),      # cost=100, revenue=200, profit=100
        (50, 10, 200, 10, 1500),    # cost=500, revenue=2000, profit=1500
        (0, 10, 200, 10, 2000),     # cost=0, revenue=2000, profit=2000
        (100, 10, 100, 10, 0),      # cost=1000, revenue=1000, profit=0
    ])
    def test_profit_calculation_examples(self, growth_days, daily_fixed_cost, area_used, revenue_per_area, expected_profit):
        """Test profit calculation with various inputs."""
        metrics = OptimizationMetrics(
            growth_days=growth_days,
            daily_fixed_cost=daily_fixed_cost,
            area_used=area_used,
            revenue_per_area=revenue_per_area
        )
        objective = OptimizationObjective()
        
        profit = objective.calculate(metrics)
        
        assert profit == expected_profit
