"""Tests for BaseOptimizer.

CRITICAL: These tests ensure all optimizers use the unified objective.
"""

import pytest
from dataclasses import dataclass
from typing import Optional
from agrr_core.usecase.interactors.base_optimizer import BaseOptimizer
from agrr_core.entity.value_objects.optimization_objective import (
    OptimizationMetrics,
    OptimizationObjective,
    DEFAULT_OBJECTIVE,
)

@dataclass
class MockCandidate:
    """Mock candidate for testing."""
    growth_days: int
    daily_fixed_cost: float
    area_used: Optional[float] = None
    revenue_per_area: Optional[float] = None
    
    def get_metrics(self) -> OptimizationMetrics:
        """Implement Optimizable protocol."""
        return OptimizationMetrics(
            growth_days=self.growth_days,
            daily_fixed_cost=self.daily_fixed_cost,
            area_used=self.area_used,
            revenue_per_area=self.revenue_per_area,
        )

class MockOptimizer(BaseOptimizer[MockCandidate]):
    """Mock optimizer for testing."""
    pass

class TestBaseOptimizer:
    """Test BaseOptimizer base class."""
    
    def test_uses_default_objective_by_default(self):
        """BaseOptimizer uses DEFAULT_OBJECTIVE by default."""
        optimizer = MockOptimizer()
        
        assert optimizer.objective is DEFAULT_OBJECTIVE
    
    def test_can_use_custom_objective(self):
        """BaseOptimizer can accept custom objective."""
        custom_objective = OptimizationObjective()
        optimizer = MockOptimizer(objective=custom_objective)
        
        assert optimizer.objective is custom_objective
    
    def test_select_best_with_revenue(self):
        """select_best maximizes profit when revenue is present."""
        optimizer = MockOptimizer()
        candidates = [
            MockCandidate(growth_days=10, daily_fixed_cost=10, area_used=20, revenue_per_area=10),  # cost=100, revenue=200, profit=100
            MockCandidate(growth_days=8, daily_fixed_cost=10, area_used=22, revenue_per_area=10),   # cost=80, revenue=220, profit=140 ← best
            MockCandidate(growth_days=12, daily_fixed_cost=10, area_used=18, revenue_per_area=10),  # cost=120, revenue=180, profit=60
        ]
        
        best = optimizer.select_best(candidates)
        
        assert best.get_metrics().cost == 80
        assert best.get_metrics().revenue == 220
    
    def test_select_best_without_revenue(self):
        """select_best minimizes cost when revenue is absent."""
        optimizer = MockOptimizer()
        candidates = [
            MockCandidate(growth_days=10, daily_fixed_cost=10),  # cost=100, profit=-100
            MockCandidate(growth_days=5, daily_fixed_cost=10),   # cost=50, profit=-50 ← best (min cost)
            MockCandidate(growth_days=20, daily_fixed_cost=10),  # cost=200, profit=-200
        ]
        
        best = optimizer.select_best(candidates)
        
        assert best.get_metrics().cost == 50
    
    def test_select_best_with_empty_list_raises_error(self):
        """select_best raises error for empty list."""
        optimizer = MockOptimizer()
        
        with pytest.raises(ValueError, match="empty"):
            optimizer.select_best([])
    
    def test_calculate_value(self):
        """calculate_value returns profit."""
        optimizer = MockOptimizer()
        candidate = MockCandidate(growth_days=10, daily_fixed_cost=10, area_used=20, revenue_per_area=10)
        
        value = optimizer.calculate_value(candidate)
        
        assert value == 100  # profit = 200 - 100
    
    def test_compare_candidates(self):
        """compare_candidates compares two candidates."""
        optimizer = MockOptimizer()
        candidate1 = MockCandidate(growth_days=10, daily_fixed_cost=10, area_used=30, revenue_per_area=10)  # cost=100, revenue=300, profit=200
        candidate2 = MockCandidate(growth_days=10, daily_fixed_cost=10, area_used=25, revenue_per_area=10)  # cost=100, revenue=250, profit=150
        
        result = optimizer.compare_candidates(candidate1, candidate2)
        
        assert result == 1  # candidate1 is better
    
    def test_sort_candidates(self):
        """sort_candidates sorts by profit."""
        optimizer = MockOptimizer()
        candidates = [
            MockCandidate(growth_days=10, daily_fixed_cost=10, area_used=20, revenue_per_area=10),  # cost=100, revenue=200, profit=100
            MockCandidate(growth_days=8, daily_fixed_cost=10, area_used=22, revenue_per_area=10),   # cost=80, revenue=220, profit=140
            MockCandidate(growth_days=12, daily_fixed_cost=10, area_used=18, revenue_per_area=10),  # cost=120, revenue=180, profit=60
        ]
        
        sorted_candidates = optimizer.sort_candidates(candidates)
        
        # Best first (reverse=True by default)
        assert sorted_candidates[0].get_metrics().cost == 80   # profit=140
        assert sorted_candidates[1].get_metrics().cost == 100  # profit=100
        assert sorted_candidates[2].get_metrics().cost == 120  # profit=60
    
    def test_sort_candidates_ascending(self):
        """sort_candidates can sort in ascending order."""
        optimizer = MockOptimizer()
        candidates = [
            MockCandidate(growth_days=10, daily_fixed_cost=10, area_used=20, revenue_per_area=10),  # cost=100, revenue=200, profit=100
            MockCandidate(growth_days=8, daily_fixed_cost=10, area_used=22, revenue_per_area=10),   # cost=80, revenue=220, profit=140
            MockCandidate(growth_days=12, daily_fixed_cost=10, area_used=18, revenue_per_area=10),  # cost=120, revenue=180, profit=60
        ]
        
        sorted_candidates = optimizer.sort_candidates(candidates, reverse=False)
        
        # Worst first (reverse=False)
        assert sorted_candidates[0].get_metrics().cost == 120  # profit=60
        assert sorted_candidates[1].get_metrics().cost == 100  # profit=100
        assert sorted_candidates[2].get_metrics().cost == 80   # profit=140

class TestBaseOptimizerConsistency:
    """Test that BaseOptimizer ensures consistency."""
    
    def test_all_instances_use_same_default_objective(self):
        """All BaseOptimizer instances use the same DEFAULT_OBJECTIVE."""
        optimizer1 = MockOptimizer()
        optimizer2 = MockOptimizer()
        
        assert optimizer1.objective is optimizer2.objective
        assert optimizer1.objective is DEFAULT_OBJECTIVE
    
    def test_calculate_value_is_consistent(self):
        """calculate_value produces same result for same candidate."""
        optimizer1 = MockOptimizer()
        optimizer2 = MockOptimizer()
        candidate = MockCandidate(growth_days=10, daily_fixed_cost=10, area_used=20, revenue_per_area=10)
        
        value1 = optimizer1.calculate_value(candidate)
        value2 = optimizer2.calculate_value(candidate)
        
        assert value1 == value2 == 100
    
    def test_select_best_is_consistent(self):
        """Different optimizers select the same best candidate."""
        optimizer1 = MockOptimizer()
        optimizer2 = MockOptimizer()
        candidates = [
            MockCandidate(growth_days=10, daily_fixed_cost=10, area_used=20, revenue_per_area=10),
            MockCandidate(growth_days=8, daily_fixed_cost=10, area_used=22, revenue_per_area=10),
            MockCandidate(growth_days=12, daily_fixed_cost=10, area_used=18, revenue_per_area=10),
        ]
        
        best1 = optimizer1.select_best(candidates)
        best2 = optimizer2.select_best(candidates)
        
        assert best1 is best2
        assert best1.get_metrics().cost == 80

