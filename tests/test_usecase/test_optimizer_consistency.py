"""Tests to ensure all optimizers use consistent objective function.

CRITICAL: These tests verify that all optimization interactors use
the unified objective function via BaseOptimizer inheritance.

If any test fails, it means:
1. An optimizer doesn't inherit from BaseOptimizer, OR
2. An optimizer bypasses the unified objective function

Both cases are SERIOUS ISSUES that must be fixed immediately.
"""

import pytest
from agrr_core.usecase.interactors.growth_period_optimize_interactor import (
    GrowthPeriodOptimizeInteractor,
)
from agrr_core.usecase.interactors.multi_field_crop_allocation_greedy_interactor import (
    MultiFieldCropAllocationGreedyInteractor,
)
from agrr_core.usecase.interactors.optimization_intermediate_result_schedule_interactor import (
    OptimizationIntermediateResultScheduleInteractor,
)
from agrr_core.usecase.interactors.base_optimizer import BaseOptimizer
from agrr_core.entity.value_objects.optimization_objective import (
    OptimizationMetrics,
    DEFAULT_OBJECTIVE,
)


class TestAllOptimizersInheritBaseOptimizer:
    """Verify all optimizers inherit from BaseOptimizer.
    
    ⚠️ CRITICAL: All optimization interactors MUST inherit from BaseOptimizer.
    This ensures they use the unified objective function.
    """
    
    def test_growth_period_optimize_inherits_base(self):
        """GrowthPeriodOptimizeInteractor MUST inherit BaseOptimizer."""
        assert issubclass(GrowthPeriodOptimizeInteractor, BaseOptimizer), (
            "GrowthPeriodOptimizeInteractor must inherit from BaseOptimizer "
            "to ensure unified objective function"
        )
    
    def test_multi_field_allocation_inherits_base(self):
        """MultiFieldCropAllocationGreedyInteractor MUST inherit BaseOptimizer."""
        assert issubclass(MultiFieldCropAllocationGreedyInteractor, BaseOptimizer), (
            "MultiFieldCropAllocationGreedyInteractor must inherit from BaseOptimizer "
            "to ensure unified objective function"
        )
    
    def test_schedule_interactor_inherits_base(self):
        """OptimizationIntermediateResultScheduleInteractor MUST inherit BaseOptimizer."""
        assert issubclass(OptimizationIntermediateResultScheduleInteractor, BaseOptimizer), (
            "OptimizationIntermediateResultScheduleInteractor must inherit from BaseOptimizer "
            "to ensure unified objective function"
        )


class TestAllOptimizersUseSameDefaultObjective:
    """Verify all optimizers use the same DEFAULT_OBJECTIVE.
    
    This ensures consistency across all optimization operations.
    """
    
    def test_growth_period_uses_default_objective(
        self,
        mock_growth_progress_crop_requirement_gateway,
        mock_growth_progress_weather_gateway,
    ):
        """GrowthPeriodOptimizeInteractor uses DEFAULT_OBJECTIVE."""
        interactor = GrowthPeriodOptimizeInteractor(
            crop_requirement_gateway=mock_growth_progress_crop_requirement_gateway,
            weather_gateway=mock_growth_progress_weather_gateway,
        )
        
        assert interactor.objective is DEFAULT_OBJECTIVE
    
    def test_schedule_interactor_uses_default_objective(self):
        """OptimizationIntermediateResultScheduleInteractor uses DEFAULT_OBJECTIVE."""
        interactor = OptimizationIntermediateResultScheduleInteractor()
        
        assert interactor.objective is DEFAULT_OBJECTIVE


class TestUnifiedObjectiveFunctionSignature:
    """Test that all optimizers calculate the same objective value.
    
    ⚠️ CRITICAL: If this test fails, optimizers are using different objectives.
    """
    
    def test_all_optimizers_calculate_same_profit(
        self,
        mock_growth_progress_crop_requirement_gateway,
        mock_growth_progress_weather_gateway,
    ):
        """All optimizers MUST calculate the same objective value from same metrics."""
        # Create optimizers
        period_optimizer = GrowthPeriodOptimizeInteractor(
            crop_requirement_gateway=mock_growth_progress_crop_requirement_gateway,
            weather_gateway=mock_growth_progress_weather_gateway,
        )
        schedule_optimizer = OptimizationIntermediateResultScheduleInteractor()
        
        # Create same metrics
        metrics = OptimizationMetrics(cost=1000, revenue=2000)
        
        # Calculate objective using each optimizer
        value1 = period_optimizer.objective.calculate(metrics)
        value2 = schedule_optimizer.objective.calculate(metrics)
        
        # MUST be the same
        assert value1 == value2 == 1000, (
            f"Optimizers calculate different values! "
            f"period={value1}, schedule={value2}. "
            f"Expected 1000 for both."
        )
    
    def test_all_optimizers_handle_cost_only_same_way(
        self,
        mock_growth_progress_crop_requirement_gateway,
        mock_growth_progress_weather_gateway,
    ):
        """All optimizers MUST handle cost-only case the same way."""
        # Create optimizers
        period_optimizer = GrowthPeriodOptimizeInteractor(
            crop_requirement_gateway=mock_growth_progress_crop_requirement_gateway,
            weather_gateway=mock_growth_progress_weather_gateway,
        )
        schedule_optimizer = OptimizationIntermediateResultScheduleInteractor()
        
        # Create cost-only metrics
        metrics = OptimizationMetrics(cost=1000)
        
        # Calculate objective using each optimizer
        value1 = period_optimizer.objective.calculate(metrics)
        value2 = schedule_optimizer.objective.calculate(metrics)
        
        # MUST be the same (-1000 for cost minimization)
        assert value1 == value2 == -1000, (
            f"Optimizers handle cost-only differently! "
            f"period={value1}, schedule={value2}. "
            f"Expected -1000 for both (cost minimization)."
        )


class TestObjectiveFunctionChangeDetection:
    """Detect when objective function changes.
    
    ⚠️ CRITICAL: This test will fail if you change the objective function.
    When it fails:
    1. Verify the change is intentional
    2. Update this test with new expected values
    3. Verify all optimizers still work correctly
    4. Update documentation
    """
    
    def test_current_objective_is_maximize_profit(self):
        """Current objective: maximize profit = revenue - cost.
        
        If this fails, objective has changed.
        """
        # Test with revenue
        metrics_with_revenue = OptimizationMetrics(cost=1000, revenue=2000)
        assert DEFAULT_OBJECTIVE.calculate(metrics_with_revenue) == 1000
        
        # Test without revenue (cost minimization)
        metrics_cost_only = OptimizationMetrics(cost=1000)
        assert DEFAULT_OBJECTIVE.calculate(metrics_cost_only) == -1000
    
    def test_objective_function_formula_documentation(self):
        """Document the exact formula used.
        
        Current formula:
        - With revenue: profit = revenue - cost
        - Without revenue: profit = -cost (cost minimization equivalent)
        
        Future formula (example):
        - profit = revenue - cost - tax + subsidy
        """
        # This test documents the current formula
        # Update this when the formula changes
        
        cost = 1000
        revenue = 2500
        expected_profit = revenue - cost  # Current formula
        
        metrics = OptimizationMetrics(cost=cost, revenue=revenue)
        actual_profit = DEFAULT_OBJECTIVE.calculate(metrics)
        
        assert actual_profit == expected_profit == 1500, (
            "Objective function formula has changed! "
            "Update this test and verify all optimizers."
        )

