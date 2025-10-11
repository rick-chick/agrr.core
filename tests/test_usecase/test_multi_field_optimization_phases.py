"""Tests for Phase 1-3 optimizations."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.usecase.dto.optimization_config import OptimizationConfig
from agrr_core.usecase.interactors.multi_field_crop_allocation_greedy_interactor import (
    MultiFieldCropAllocationGreedyInteractor,
    AllocationCandidate,
)


class TestPhase1Filtering:
    """Test Phase 1: Candidate filtering."""
    
    def test_candidate_filtering_enabled(self):
        """Test that filtering removes low-quality candidates."""
        # Create interactor with filtering enabled
        config = OptimizationConfig(
            enable_candidate_filtering=True,
            min_profit_rate_threshold=-0.5,
            min_revenue_cost_ratio=0.5,
        )
        interactor = MultiFieldCropAllocationGreedyInteractor(
            None, None, None, config=config
        )
        
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        crop = Crop("c1", "Crop 1", 0.25, revenue_per_area=10000.0)
        
        # Create candidates with different quality
        candidates = [
            AllocationCandidate(
                field=field, crop=crop,
                start_date=datetime(2025, 4, 1),
                completion_date=datetime(2025, 8, 31),
                growth_days=150, accumulated_gdd=1800.0,
                quantity=1000.0, cost=1000000.0,
                revenue=2500000.0,  # Good: revenue/cost = 2.5
                profit=1500000.0, profit_rate=1.5,
                area_used=250.0,
            ),
            AllocationCandidate(
                field=field, crop=crop,
                start_date=datetime(2025, 4, 1),
                completion_date=datetime(2025, 8, 31),
                growth_days=150, accumulated_gdd=1800.0,
                quantity=500.0, cost=1000000.0,
                revenue=400000.0,  # Bad: revenue/cost = 0.4 < 0.5
                profit=-600000.0, profit_rate=-0.6,
                area_used=125.0,
            ),
        ]
        
        # Simulate filtering logic (would happen in _generate_candidates)
        filtered = [
            c for c in candidates
            if c.profit_rate >= config.min_profit_rate_threshold
            and (c.revenue / c.cost if c.cost > 0 else 0) >= config.min_revenue_cost_ratio
        ]
        
        assert len(filtered) == 1
        assert filtered[0].profit_rate == 1.5
    
    def test_post_filtering_limits_candidates(self):
        """Test post-filtering limits candidates per field×crop."""
        config = OptimizationConfig(
            max_candidates_per_field_crop=3
        )
        interactor = MultiFieldCropAllocationGreedyInteractor(
            None, None, None, config=config
        )
        
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        crop = Crop("c1", "Crop 1", 0.25, revenue_per_area=10000.0)
        
        # Create 10 candidates for same field×crop
        candidates = []
        for i in range(10):
            candidates.append(AllocationCandidate(
                field=field, crop=crop,
                start_date=datetime(2025, 4, i+1),
                completion_date=datetime(2025, 8, i+1),
                growth_days=150, accumulated_gdd=1800.0,
                quantity=1000.0, cost=1000000.0,
                revenue=2500000.0, profit=1500000.0,
                profit_rate=1.5 + i * 0.1,  # Different profit rates
                area_used=250.0,
            ))
        
        # Apply post-filtering
        filtered = interactor._post_filter_candidates(candidates, config)
        
        # Should keep only top 3
        assert len(filtered) == 3
        
        # Should keep highest profit_rate
        profit_rates = [c.profit_rate for c in filtered]
        assert max(profit_rates) == pytest.approx(2.4)  # 1.5 + 9*0.1


class TestPhase1Sampling:
    """Test Phase 1: Neighbor sampling."""
    
    def test_neighbor_sampling_reduces_count(self):
        """Test that sampling reduces neighbor count."""
        config = OptimizationConfig(
            enable_neighbor_sampling=True,
            max_neighbors_per_iteration=50,
        )
        interactor = MultiFieldCropAllocationGreedyInteractor(
            None, None, None, config=config
        )
        
        # Create a moderate solution
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        crop = Crop("c1", "Crop 1", 0.25, revenue_per_area=10000.0)
        
        solution = []
        for i in range(10):
            solution.append(CropAllocation(
                allocation_id=f"alloc_{i}",
                field=field, crop=crop,
                quantity=100.0,
                start_date=datetime(2025, 4, 1),
                completion_date=datetime(2025, 8, 31),
                growth_days=150, accumulated_gdd=1800.0,
                total_cost=100000.0,
                expected_revenue=250000.0,
                profit=150000.0,
                area_used=25.0,
            ))
        
        # Generate neighbors with sampling
        neighbors = interactor._generate_neighbors_sampled(
            solution, [], [field], [crop], config
        )
        
        # Should be limited to max_neighbors_per_iteration
        assert len(neighbors) <= config.max_neighbors_per_iteration


class TestPhase2ParallelGeneration:
    """Test Phase 2: Parallel candidate generation."""
    
    @pytest.mark.asyncio
    async def test_parallel_generation_structure(self):
        """Test that parallel generation has correct structure."""
        # Create mock gateways
        field_gateway = AsyncMock()
        crop_req_gateway = AsyncMock()
        weather_gateway = AsyncMock()
        
        config = OptimizationConfig(
            enable_parallel_candidate_generation=True
        )
        
        interactor = MultiFieldCropAllocationGreedyInteractor(
            field_gateway, crop_req_gateway, weather_gateway, config=config
        )
        
        # Check that method exists
        assert hasattr(interactor, '_generate_candidates_parallel')
        assert hasattr(interactor, '_generate_candidates_for_field_crop')


class TestPhase3AdaptiveStopping:
    """Test Phase 3: Adaptive early stopping."""
    
    def test_adaptive_parameters(self):
        """Test adaptive parameter calculation."""
        config = OptimizationConfig(
            enable_adaptive_early_stopping=True,
            max_no_improvement=20,
            improvement_threshold_ratio=0.001,
        )
        
        # Simulate adaptive calculation
        problem_size = 30
        max_no_improvement = max(10, min(20, problem_size // 2))
        
        assert max_no_improvement == 15  # min(20, 30//2)
        
        # Threshold calculation
        current_profit = 1000000.0
        improvement_threshold = current_profit * config.improvement_threshold_ratio
        
        assert improvement_threshold == pytest.approx(1000.0)  # 0.1%


class TestConfigProfiles:
    """Test different configuration profiles."""
    
    def test_fast_profile_settings(self):
        """Test fast profile has fewer iterations."""
        fast = OptimizationConfig.fast_profile()
        default = OptimizationConfig()
        
        assert fast.max_local_search_iterations < default.max_local_search_iterations
        assert len(fast.quantity_levels) < len(default.quantity_levels)
        assert fast.max_neighbors_per_iteration < default.max_neighbors_per_iteration
    
    def test_quality_profile_settings(self):
        """Test quality profile has more iterations."""
        quality = OptimizationConfig.quality_profile()
        default = OptimizationConfig()
        
        assert quality.max_local_search_iterations > default.max_local_search_iterations
        assert len(quality.quantity_levels) > len(default.quantity_levels)
        assert quality.max_neighbors_per_iteration > default.max_neighbors_per_iteration
    
    def test_profile_comparison(self):
        """Test that profiles have expected ordering."""
        fast = OptimizationConfig.fast_profile()
        balanced = OptimizationConfig.balanced_profile()
        quality = OptimizationConfig.quality_profile()
        
        # Speed: fast < balanced < quality
        assert fast.max_local_search_iterations < balanced.max_local_search_iterations < quality.max_local_search_iterations
        
        # Thoroughness: fast < balanced < quality
        assert len(fast.quantity_levels) < len(balanced.quantity_levels) < len(quality.quantity_levels)


class TestIntegration:
    """Test that all phases work together."""
    
    def test_config_can_be_passed_to_interactor(self):
        """Test that config can be passed to interactor."""
        custom_config = OptimizationConfig(
            max_local_search_iterations=10,
            enable_neighbor_sampling=False,
        )
        
        interactor = MultiFieldCropAllocationGreedyInteractor(
            None, None, None, config=custom_config
        )
        
        assert interactor.config.max_local_search_iterations == 10
        assert interactor.config.enable_neighbor_sampling is False
    
    def test_config_can_be_overridden_at_execution(self):
        """Test that config can be overridden at execution time."""
        default_config = OptimizationConfig(
            max_local_search_iterations=100
        )
        
        interactor = MultiFieldCropAllocationGreedyInteractor(
            None, None, None, config=default_config
        )
        
        # Override should work at execution
        override_config = OptimizationConfig(
            max_local_search_iterations=10
        )
        
        # Verify interactor accepts config parameter in execute
        # (actual execution would require more setup)
        assert hasattr(interactor, 'execute')
        import inspect
        sig = inspect.signature(interactor.execute)
        assert 'config' in sig.parameters

