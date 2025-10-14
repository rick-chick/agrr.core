"""Configuration for multi-field crop allocation optimization."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class OptimizationConfig:
    """Configuration for optimization algorithm.
    
    This configuration allows fine-tuning of the optimization algorithm
    for different scenarios (speed vs quality trade-off).
    """
    
    # ===== Candidate Generation =====
    
    area_levels: List[float] = field(
        default_factory=lambda: [1.0, 0.75, 0.5, 0.25]
    )
    """Area levels to generate candidates at (as fraction of field area).
    
    Values represent area fraction (0.0-1.0) of field.area to allocate.
    Example: [1.0, 0.75, 0.5, 0.25] generates candidates using 100%, 75%, 50%, 25% of field area.
    """
    
    top_period_candidates: int = 100
    """Number of top period candidates to use from DP results.
    
    Since candidates are now sorted by cost (ascending), this allows the algorithm
    to consider a wide range of cultivation periods including the most cost-effective ones.
    """
    
    min_profit_rate_threshold: float = -0.5
    """Minimum profit rate to accept a candidate (-0.5 = loss up to 50%)."""
    
    min_revenue_cost_ratio: float = 0.5
    """Minimum revenue/cost ratio to accept a candidate."""
    
    enable_candidate_filtering: bool = True
    """Enable quality-based candidate filtering."""
    
    max_candidates_per_field_crop: int = 10
    """Maximum number of candidates to keep per field×crop combination."""
    
    # ===== Greedy Allocation =====
    
    # (No specific parameters for now)
    
    # ===== Local Search =====
    
    max_local_search_iterations: int = 100
    """Maximum number of local search iterations."""
    
    max_no_improvement: int = 20
    """Maximum consecutive iterations without improvement before early stopping."""
    
    max_neighbors_per_iteration: int = 200
    """Maximum number of neighbors to evaluate per iteration."""
    
    enable_neighbor_sampling: bool = True
    """Enable neighbor sampling to limit computational cost."""
    
    enable_incremental_feasibility: bool = True
    """Enable incremental feasibility checking for faster validation."""
    
    enable_adaptive_early_stopping: bool = True
    """Enable adaptive early stopping based on improvement rate."""
    
    improvement_threshold_ratio: float = 0.001
    """Relative improvement threshold for early stopping (0.1%)."""
    
    # ===== Area Adjustment =====
    
    area_adjustment_multipliers: List[float] = field(
        default_factory=lambda: [0.8, 0.9, 1.1, 1.2]
    )
    """Multipliers for area adjustment operations (±10%, ±20%).
    
    Values multiply the current area_used to generate neighbor solutions.
    Example: [0.8, 0.9, 1.1, 1.2] tries -20%, -10%, +10%, +20% adjustments.
    """
    
    # ===== Operation Weights =====
    
    operation_weights: Dict[str, float] = field(default_factory=lambda: {
        'field_swap': 0.3,
        'field_move': 0.1,
        'field_replace': 0.05,
        'field_remove': 0.05,
        'crop_insert': 0.2,
        'crop_change': 0.1,
        'period_replace': 0.1,
        'area_adjust': 0.1,
    })
    """Weights for different neighborhood operations (for prioritized sampling)."""
    
    # ===== Performance Options =====
    
    enable_parallel_candidate_generation: bool = True
    """Enable parallel candidate generation for faster preprocessing."""
    
    max_period_replace_alternatives: int = 5
    """Maximum number of period alternatives to try in period replace operation."""
    
    max_insert_neighbors: int = 50
    """Maximum number of insert neighbors to generate (to prevent explosion)."""
    
    @classmethod
    def fast_profile(cls) -> 'OptimizationConfig':
        """Create a fast optimization profile (lower quality, higher speed).
        
        Expected performance:
            - Time: -60% compared to default
            - Quality: -5% compared to default
        """
        return cls(
            area_levels=[1.0, 0.5],
            top_period_candidates=30,  # Increased to ensure best candidates are included
            max_local_search_iterations=50,
            max_no_improvement=10,
            max_neighbors_per_iteration=100,
            max_candidates_per_field_crop=5,
        )
    
    @classmethod
    def quality_profile(cls) -> 'OptimizationConfig':
        """Create a quality optimization profile (higher quality, lower speed).
        
        Expected performance:
            - Time: +50% compared to default
            - Quality: +2-3% compared to default
        """
        return cls(
            area_levels=[1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.25],
            top_period_candidates=200,  # Use more candidates for higher quality
            max_local_search_iterations=200,
            max_no_improvement=30,
            max_neighbors_per_iteration=300,
            max_candidates_per_field_crop=15,
        )
    
    @classmethod
    def balanced_profile(cls) -> 'OptimizationConfig':
        """Create a balanced optimization profile (default).
        
        This is the default configuration.
        """
        return cls()

