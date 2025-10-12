"""Tests for OptimizationConfig."""

import pytest
from agrr_core.usecase.dto.optimization_config import OptimizationConfig


class TestOptimizationConfig:
    """Test OptimizationConfig."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = OptimizationConfig()
        
        assert config.area_levels == [1.0, 0.75, 0.5, 0.25]
        assert config.top_period_candidates == 3
        assert config.max_local_search_iterations == 100
        assert config.max_no_improvement == 20
        assert config.max_neighbors_per_iteration == 200
        assert config.enable_neighbor_sampling is True
        assert config.enable_candidate_filtering is True
        assert config.enable_parallel_candidate_generation is True
    
    def test_fast_profile(self):
        """Test fast optimization profile."""
        config = OptimizationConfig.fast_profile()
        
        assert config.area_levels == [1.0, 0.5]
        assert config.top_period_candidates == 2
        assert config.max_local_search_iterations == 50
        assert config.max_no_improvement == 10
        assert config.max_neighbors_per_iteration == 100
    
    def test_quality_profile(self):
        """Test quality optimization profile."""
        config = OptimizationConfig.quality_profile()
        
        assert len(config.area_levels) == 9
        assert config.top_period_candidates == 5
        assert config.max_local_search_iterations == 200
        assert config.max_no_improvement == 30
        assert config.max_neighbors_per_iteration == 300
    
    def test_balanced_profile(self):
        """Test balanced profile (should be same as default)."""
        config_default = OptimizationConfig()
        config_balanced = OptimizationConfig.balanced_profile()
        
        assert config_default.area_levels == config_balanced.area_levels
        assert config_default.max_local_search_iterations == config_balanced.max_local_search_iterations
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = OptimizationConfig(
            area_levels=[1.0, 0.3],
            max_local_search_iterations=10,
            enable_neighbor_sampling=False,
        )
        
        assert config.area_levels == [1.0, 0.3]
        assert config.max_local_search_iterations == 10
        assert config.enable_neighbor_sampling is False
        assert config.max_no_improvement == 20  # Default value
    
    def test_operation_weights(self):
        """Test operation weights configuration."""
        config = OptimizationConfig()
        
        assert 'field_swap' in config.operation_weights
        assert 'crop_insert' in config.operation_weights
        assert sum(config.operation_weights.values()) == pytest.approx(1.0)

