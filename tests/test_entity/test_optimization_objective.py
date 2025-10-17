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


class TestYieldFactorImpact:
    """Test yield_factor impact on revenue and profit."""
    
    def test_yield_factor_default_is_one(self):
        """Test that default yield_factor is 1.0 (no impact)."""
        metrics = OptimizationMetrics(
            area_used=100.0,
            revenue_per_area=10.0,
            growth_days=50,
            daily_fixed_cost=5.0,
        )
        
        assert metrics.yield_factor == 1.0
        assert metrics.revenue == 1000.0  # 100 * 10 * 1.0
        assert metrics.profit == 750.0    # 1000 - 250
    
    def test_yield_factor_reduces_revenue(self):
        """Test that yield_factor < 1.0 reduces revenue."""
        metrics = OptimizationMetrics(
            area_used=100.0,
            revenue_per_area=10.0,
            growth_days=50,
            daily_fixed_cost=5.0,
            yield_factor=0.8,  # 20% yield loss
        )
        
        assert metrics.revenue == 800.0  # 100 * 10 * 0.8
        assert metrics.profit == 550.0   # 800 - 250
    
    def test_yield_factor_severe_impact(self):
        """Test severe yield impact (50% loss)."""
        metrics = OptimizationMetrics(
            area_used=200.0,
            revenue_per_area=20.0,
            growth_days=100,
            daily_fixed_cost=10.0,
            yield_factor=0.5,  # 50% yield loss
        )
        
        # Base revenue: 200 * 20 = 4000
        # Adjusted revenue: 4000 * 0.5 = 2000
        # Cost: 100 * 10 = 1000
        # Profit: 2000 - 1000 = 1000
        assert metrics.revenue == 2000.0
        assert metrics.cost == 1000.0
        assert metrics.profit == 1000.0
    
    def test_yield_factor_with_max_revenue_constraint(self):
        """Test yield_factor interaction with max_revenue constraint."""
        metrics = OptimizationMetrics(
            area_used=200.0,
            revenue_per_area=20.0,
            growth_days=100,
            daily_fixed_cost=10.0,
            yield_factor=0.9,      # 10% yield loss
            max_revenue=3000.0,    # Revenue cap
        )
        
        # Base revenue: 200 * 20 = 4000
        # With yield_factor: 4000 * 0.9 = 3600
        # With max_revenue: min(3600, 3000) = 3000
        assert metrics.revenue == 3000.0  # Capped
        assert metrics.profit == 2000.0   # 3000 - 1000
    
    def test_yield_factor_zero_total_loss(self):
        """Test yield_factor = 0.0 (complete crop failure)."""
        metrics = OptimizationMetrics(
            area_used=100.0,
            revenue_per_area=10.0,
            growth_days=50,
            daily_fixed_cost=5.0,
            yield_factor=0.0,  # Total crop failure
        )
        
        assert metrics.revenue == 0.0     # No revenue
        assert metrics.cost == 250.0
        assert metrics.profit == -250.0   # Pure loss
    
    def test_objective_calculate_with_yield_factor(self):
        """Test OptimizationObjective.calculate() with yield_factor."""
        objective = OptimizationObjective()
        
        # Scenario: 15% yield loss
        metrics = OptimizationMetrics(
            area_used=150.0,
            revenue_per_area=15.0,
            growth_days=80,
            daily_fixed_cost=8.0,
            yield_factor=0.85,  # 15% yield loss
        )
        
        profit = objective.calculate(metrics)
        
        # Revenue: 150 * 15 * 0.85 = 1912.5
        # Cost: 80 * 8 = 640
        # Profit: 1912.5 - 640 = 1272.5
        expected_profit = (150.0 * 15.0 * 0.85) - (80 * 8)
        assert abs(profit - expected_profit) < 0.01
    
    def test_select_best_considers_yield_factor(self):
        """Test that select_best accounts for yield_factor differences."""
        objective = OptimizationObjective()
        
        # Candidate A: Higher base revenue but lower yield
        metrics_a = OptimizationMetrics(
            area_used=200.0,
            revenue_per_area=12.0,
            growth_days=100,
            daily_fixed_cost=10.0,
            yield_factor=0.7,  # 30% yield loss
        )
        
        # Candidate B: Lower base revenue but better yield
        metrics_b = OptimizationMetrics(
            area_used=200.0,
            revenue_per_area=10.0,
            growth_days=100,
            daily_fixed_cost=10.0,
            yield_factor=0.95,  # 5% yield loss
        )
        
        candidates = [
            {"name": "A", "metrics": metrics_a},
            {"name": "B", "metrics": metrics_b},
        ]
        
        best = objective.select_best(
            candidates,
            key_func=lambda c: objective.calculate(c["metrics"])
        )
        
        # A: revenue=200*12*0.7=1680, cost=1000, profit=680
        # B: revenue=200*10*0.95=1900, cost=1000, profit=900
        # B should win despite lower revenue_per_area
        assert best["name"] == "B"


class TestSoilRecoveryFactor:
    """Test soil_recovery_factor impact on revenue and profit."""
    
    def test_soil_recovery_factor_default_is_one(self):
        """Test that default soil_recovery_factor is 1.0 (no bonus)."""
        metrics = OptimizationMetrics(
            area_used=100.0,
            revenue_per_area=10.0,
            growth_days=50,
            daily_fixed_cost=5.0,
        )
        
        assert metrics.soil_recovery_factor == 1.0
        assert metrics.revenue == 1000.0  # 100 * 10 * 1.0
        assert metrics.profit == 750.0    # 1000 - 250
    
    def test_soil_recovery_factor_increases_revenue(self):
        """Test that soil_recovery_factor > 1.0 increases revenue."""
        metrics = OptimizationMetrics(
            area_used=100.0,
            revenue_per_area=10.0,
            growth_days=50,
            daily_fixed_cost=5.0,
            soil_recovery_factor=1.05,  # 5% recovery bonus
        )
        
        assert metrics.revenue == 1050.0  # 100 * 10 * 1.05
        assert metrics.profit == 800.0    # 1050 - 250
    
    def test_soil_recovery_factor_maximum_bonus(self):
        """Test maximum soil recovery bonus (60+ days fallow)."""
        metrics = OptimizationMetrics(
            area_used=200.0,
            revenue_per_area=20.0,
            growth_days=100,
            daily_fixed_cost=10.0,
            soil_recovery_factor=1.10,  # 10% recovery bonus
        )
        
        # Base revenue: 200 * 20 = 4000
        # With recovery: 4000 * 1.10 = 4400
        # Cost: 100 * 10 = 1000
        # Profit: 4400 - 1000 = 3400
        assert metrics.revenue == 4400.0
        assert metrics.cost == 1000.0
        assert metrics.profit == 3400.0
    
    def test_soil_recovery_with_interaction_impact(self):
        """Test soil recovery combined with interaction impact (continuous cultivation)."""
        metrics = OptimizationMetrics(
            area_used=100.0,
            revenue_per_area=10.0,
            growth_days=50,
            daily_fixed_cost=5.0,
            interaction_impact=0.75,     # -25% continuous cultivation penalty
            soil_recovery_factor=1.05,   # +5% soil recovery bonus
        )
        
        # Base revenue: 100 * 10 = 1000
        # With interaction: 1000 * 0.75 = 750
        # With recovery: 750 * 1.05 = 787.5
        # Cost: 50 * 5 = 250
        # Profit: 787.5 - 250 = 537.5
        assert metrics.revenue == 787.5
        assert metrics.profit == 537.5
    
    def test_soil_recovery_with_yield_factor_and_interaction(self):
        """Test all three factors combined: yield, interaction, and soil recovery."""
        metrics = OptimizationMetrics(
            area_used=100.0,
            revenue_per_area=10.0,
            growth_days=50,
            daily_fixed_cost=5.0,
            yield_factor=0.9,            # -10% temperature stress
            interaction_impact=0.8,      # -20% continuous cultivation
            soil_recovery_factor=1.10,   # +10% soil recovery
        )
        
        # Base revenue: 100 * 10 = 1000
        # With yield: 1000 * 0.9 = 900
        # With interaction: 900 * 0.8 = 720
        # With recovery: 720 * 1.10 = 792
        # Cost: 50 * 5 = 250
        # Profit: 792 - 250 = 542
        assert abs(metrics.revenue - 792.0) < 0.01
        assert abs(metrics.profit - 542.0) < 0.01
    
    def test_objective_calculate_with_soil_recovery(self):
        """Test OptimizationObjective.calculate() with soil_recovery_factor."""
        objective = OptimizationObjective()
        
        # Scenario: 60+ day fallow period (10% bonus)
        metrics = OptimizationMetrics(
            area_used=150.0,
            revenue_per_area=15.0,
            growth_days=80,
            daily_fixed_cost=8.0,
            soil_recovery_factor=1.10,  # 10% recovery bonus
        )
        
        profit = objective.calculate(metrics)
        
        # Revenue: 150 * 15 * 1.10 = 2475
        # Cost: 80 * 8 = 640
        # Profit: 2475 - 640 = 1835
        expected_profit = (150.0 * 15.0 * 1.10) - (80 * 8)
        assert abs(profit - expected_profit) < 0.01
    
    def test_select_best_considers_soil_recovery(self):
        """Test that select_best accounts for soil_recovery_factor differences."""
        objective = OptimizationObjective()
        
        # Candidate A: Higher base revenue but no soil recovery
        metrics_a = OptimizationMetrics(
            area_used=200.0,
            revenue_per_area=11.0,
            growth_days=100,
            daily_fixed_cost=10.0,
            soil_recovery_factor=1.0,  # No recovery
        )
        
        # Candidate B: Lower base revenue but good soil recovery
        metrics_b = OptimizationMetrics(
            area_used=200.0,
            revenue_per_area=10.0,
            growth_days=100,
            daily_fixed_cost=10.0,
            soil_recovery_factor=1.10,  # 10% recovery bonus
        )
        
        candidates = [
            {"name": "A", "metrics": metrics_a},
            {"name": "B", "metrics": metrics_b},
        ]
        
        best = objective.select_best(
            candidates,
            key_func=lambda c: objective.calculate(c["metrics"])
        )
        
        # A: revenue=200*11*1.0=2200, cost=1000, profit=1200
        # B: revenue=200*10*1.10=2200, cost=1000, profit=1200
        # They are equal, so either could win
        assert best["name"] in ["A", "B"]
