"""Adaptive Large Neighborhood Search (ALNS) optimizer service.

ALNS is an advanced local search method that dynamically selects
destroy and repair operators based on their historical performance.

Key Features:
- Multiple destroy operators (random, worst, related, field, time-slice)
- Multiple repair operators (greedy, regret, DP)
- Adaptive weight adjustment based on success rate
- Simulated Annealing acceptance criterion

Expected Quality: 90-98% (vs current 85-95%)
Time Complexity: O(iterations × n²)
"""

import random
import math
from typing import List, Dict, Callable, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.usecase.dto.optimization_config import OptimizationConfig


@dataclass
class OperatorPerformance:
    """Track operator performance for adaptive weight adjustment."""
    
    name: str
    weight: float = 1.0
    usage_count: int = 0
    success_count: int = 0
    total_improvement: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.usage_count == 0:
            return 0.5  # Default for unused operators
        return self.success_count / self.usage_count
    
    @property
    def avg_improvement(self) -> float:
        """Calculate average improvement."""
        if self.success_count == 0:
            return 0.0
        return self.total_improvement / self.success_count


class AdaptiveWeights:
    """Manage adaptive weights for destroy and repair operators."""
    
    def __init__(self, operators: List[str], decay_rate: float = 0.99):
        self.operators = {
            name: OperatorPerformance(name=name) 
            for name in operators
        }
        self.decay_rate = decay_rate
    
    def select_operator(self) -> str:
        """Select operator using roulette wheel selection based on weights."""
        total_weight = sum(op.weight for op in self.operators.values())
        
        if total_weight == 0:
            # Fallback: uniform random
            return random.choice(list(self.operators.keys()))
        
        # Roulette wheel selection
        r = random.uniform(0, total_weight)
        cumulative = 0.0
        
        for name, op in self.operators.items():
            cumulative += op.weight
            if cumulative >= r:
                return name
        
        # Fallback (should not happen)
        return list(self.operators.keys())[-1]
    
    def update(self, operator_name: str, improvement: float, threshold: float = 0.0):
        """Update operator weight based on improvement.
        
        Args:
            operator_name: Name of operator used
            improvement: Profit improvement (can be negative)
            threshold: Minimum improvement to consider success
        """
        op = self.operators[operator_name]
        op.usage_count += 1
        
        # Determine reward based on improvement
        if improvement > threshold:
            op.success_count += 1
            op.total_improvement += improvement
            reward = 10 if improvement > threshold * 2 else 5
        else:
            reward = 1  # Small reward for trying
        
        # Update weight: decay old weight + add reward
        op.weight = op.weight * self.decay_rate + reward
    
    def reset_periodically(self, iteration: int, period: int = 100):
        """Reset weights periodically to maintain exploration."""
        if iteration % period == 0:
            for op in self.operators.values():
                # Soft reset: move 50% toward neutral weight
                op.weight = 0.5 * op.weight + 0.5


class ALNSOptimizer:
    """Adaptive Large Neighborhood Search optimizer.
    
    Implements ALNS with multiple destroy/repair operators and
    adaptive weight adjustment.
    """
    
    def __init__(self, config: OptimizationConfig):
        self.config = config
        
        # Initialize destroy operators
        self.destroy_operators: Dict[str, Callable] = {
            'random_removal': self._random_removal,
            'worst_removal': self._worst_removal,
            'related_removal': self._related_removal,
            'field_removal': self._field_removal,
            'time_slice_removal': self._time_slice_removal,
        }
        
        # Initialize repair operators
        self.repair_operators: Dict[str, Callable] = {
            'greedy_insert': self._greedy_insert,
            'regret_insert': self._regret_insert,
            'candidate_insert': self._candidate_insert,  # NEW: Insert from unused candidates
        }
        
        # Adaptive weights
        self.destroy_weights = AdaptiveWeights(list(self.destroy_operators.keys()))
        self.repair_weights = AdaptiveWeights(list(self.repair_operators.keys()))
    
    def optimize(
        self,
        initial_solution: List[CropAllocation],
        candidates: List['AllocationCandidate'],
        fields: List[Field],
        crops: List[Crop],
        max_iterations: Optional[int] = None,
    ) -> List[CropAllocation]:
        """Execute ALNS optimization.
        
        Args:
            initial_solution: Initial solution (from greedy)
            candidates: All allocation candidates
            fields: List of fields
            crops: List of crops
            max_iterations: Maximum iterations (overrides config)
            
        Returns:
            Improved solution
        """
        iterations = max_iterations or self.config.max_local_search_iterations
        
        # Initialize
        current = initial_solution
        best = current
        current_profit = self._calculate_profit(current)
        best_profit = current_profit
        
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"ALNS starting: initial_profit={current_profit:,.0f}, allocations={len(initial_solution)}")
        
        # Simulated Annealing parameters
        temp = 10000.0
        cooling_rate = 0.99
        min_temp = 1.0
        
        for iteration in range(iterations):
            # Select destroy operator
            destroy_name = self.destroy_weights.select_operator()
            destroy_op = self.destroy_operators[destroy_name]
            
            # Select repair operator
            repair_name = self.repair_weights.select_operator()
            repair_op = self.repair_operators[repair_name]
            
            # Destroy: remove part of solution
            try:
                partial, removed = destroy_op(current)
                if iteration < 5:  # Debug first few iterations
                    logger.debug(f"Iter {iteration}: Destroy '{destroy_name}' removed {len(removed)}/{len(current)} allocations")
            except Exception as e:
                # If destroy fails, skip this iteration
                logger.warning(f"Destroy operator '{destroy_name}' failed: {e}")
                continue
            
            # Repair: rebuild solution
            try:
                new_solution = repair_op(partial, removed, candidates, fields)
                if iteration < 5:  # Debug first few iterations
                    reinserted = len(new_solution) - len(partial)
                    logger.debug(f"Iter {iteration}: Repair '{repair_name}' reinserted {reinserted}/{len(removed)} allocations")
            except Exception as e:
                # If repair fails, skip this iteration
                logger.warning(f"Repair operator '{repair_name}' failed: {e}")
                continue
            
            # Evaluate
            new_profit = self._calculate_profit(new_solution)
            delta = new_profit - current_profit
            
            # Acceptance criterion (Simulated Annealing)
            if delta > 0 or (temp > min_temp and random.random() < math.exp(delta / temp)):
                # Accept new solution
                current = new_solution
                current_profit = new_profit
                
                # Update best
                if new_profit > best_profit:
                    best = new_solution
                    best_profit = new_profit
                
                # Update weights with success
                self.destroy_weights.update(destroy_name, delta, threshold=0)
                self.repair_weights.update(repair_name, delta, threshold=0)
            else:
                # Reject but still update weights
                self.destroy_weights.update(destroy_name, delta, threshold=0)
                self.repair_weights.update(repair_name, delta, threshold=0)
            
            # Cool down temperature
            temp *= cooling_rate
            
            # Periodic weight reset
            self.destroy_weights.reset_periodically(iteration)
            self.repair_weights.reset_periodically(iteration)
        
        # Final logging
        logger.info(f"ALNS finished: best_profit={best_profit:,.0f}, allocations={len(best)}")
        logger.info(f"Improvement: {best_profit - self._calculate_profit(initial_solution):,.0f}")
        
        return best
    
    # ===== Destroy Operators =====
    
    def _random_removal(
        self, 
        solution: List[CropAllocation]
    ) -> Tuple[List[CropAllocation], List[CropAllocation]]:
        """Randomly remove allocations."""
        removal_rate = 0.3  # Remove 30%
        n_remove = max(1, int(len(solution) * removal_rate))
        
        removed = random.sample(solution, n_remove)
        remaining = [a for a in solution if a not in removed]
        
        return remaining, removed
    
    def _worst_removal(
        self, 
        solution: List[CropAllocation]
    ) -> Tuple[List[CropAllocation], List[CropAllocation]]:
        """Remove allocations with lowest profit rate."""
        removal_rate = 0.3
        n_remove = max(1, int(len(solution) * removal_rate))
        
        sorted_by_profit_rate = sorted(solution, key=lambda a: a.profit_rate)
        removed = sorted_by_profit_rate[:n_remove]
        remaining = sorted_by_profit_rate[n_remove:]
        
        return remaining, removed
    
    def _related_removal(
        self, 
        solution: List[CropAllocation]
    ) -> Tuple[List[CropAllocation], List[CropAllocation]]:
        """Remove related allocations (same field or nearby time)."""
        if not solution:
            return [], []
        
        removal_rate = 0.3
        n_remove = max(1, int(len(solution) * removal_rate))
        
        # Pick a seed allocation
        seed = random.choice(solution)
        
        # Calculate relatedness
        related = []
        for alloc in solution:
            relatedness = self._calculate_relatedness(seed, alloc)
            related.append((alloc, relatedness))
        
        # Sort by relatedness (descending)
        related.sort(key=lambda x: x[1], reverse=True)
        
        # Remove most related
        removed = [a for a, _ in related[:n_remove]]
        remaining = [a for a, _ in related[n_remove:]]
        
        return remaining, removed
    
    def _field_removal(
        self, 
        solution: List[CropAllocation]
    ) -> Tuple[List[CropAllocation], List[CropAllocation]]:
        """Remove all allocations from a random field."""
        if not solution:
            return [], []
        
        # Get fields in solution
        fields_in_solution = list(set(a.field.field_id for a in solution))
        
        if not fields_in_solution:
            return solution, []
        
        # Pick random field
        target_field = random.choice(fields_in_solution)
        
        # Remove all from that field
        removed = [a for a in solution if a.field.field_id == target_field]
        remaining = [a for a in solution if a.field.field_id != target_field]
        
        return remaining, removed
    
    def _time_slice_removal(
        self, 
        solution: List[CropAllocation]
    ) -> Tuple[List[CropAllocation], List[CropAllocation]]:
        """Remove allocations in a specific time period."""
        if not solution:
            return [], []
        
        # Find median date
        all_dates = [a.start_date for a in solution]
        all_dates.sort()
        median_date = all_dates[len(all_dates) // 2]
        
        # Remove allocations near median (±3 months)
        time_window = timedelta(days=90)
        
        removed = [
            a for a in solution 
            if abs((a.start_date - median_date).days) < time_window.days
        ]
        remaining = [a for a in solution if a not in removed]
        
        # Ensure we remove at least something
        if not removed and solution:
            removed = [random.choice(solution)]
            remaining = [a for a in solution if a not in removed]
        
        return remaining, removed
    
    # ===== Repair Operators =====
    
    def _greedy_insert(
        self,
        partial: List[CropAllocation],
        removed: List[CropAllocation],
        candidates: List['AllocationCandidate'],
        fields: List[Field],
    ) -> List[CropAllocation]:
        """Greedily re-insert removed allocations."""
        current = partial.copy()
        
        # Sort removed by profit rate (descending)
        sorted_removed = sorted(removed, key=lambda a: a.profit_rate, reverse=True)
        
        for alloc in sorted_removed:
            # Check if feasible
            if self._is_feasible_to_add(current, alloc):
                current.append(alloc)
        
        return current
    
    def _regret_insert(
        self,
        partial: List[CropAllocation],
        removed: List[CropAllocation],
        candidates: List['AllocationCandidate'],
        fields: List[Field],
    ) -> List[CropAllocation]:
        """Insert using regret criterion.
        
        Regret = opportunity cost of not inserting now
               = (profit if inserted now) - (profit of best alternative)
        """
        current = partial.copy()
        remaining = removed.copy()
        
        while remaining:
            # Calculate regret for each allocation
            regrets = []
            
            for alloc in remaining:
                if not self._is_feasible_to_add(current, alloc):
                    continue
                
                # Profit if we insert this
                profit_with = self._calculate_profit(current + [alloc])
                
                # Best alternative
                alternatives = [
                    a for a in remaining 
                    if a != alloc and self._is_feasible_to_add(current, a)
                ]
                
                if alternatives:
                    best_alt = max(alternatives, key=lambda a: a.profit or 0)
                    profit_with_alt = self._calculate_profit(current + [best_alt])
                else:
                    profit_with_alt = self._calculate_profit(current)
                
                # Regret = opportunity cost
                regret = profit_with - profit_with_alt
                regrets.append((alloc, regret))
            
            if not regrets:
                break
            
            # Insert allocation with highest regret
            best_alloc, _ = max(regrets, key=lambda x: x[1])
            current.append(best_alloc)
            remaining.remove(best_alloc)
        
        return current
    
    def _candidate_insert(
        self,
        partial: List[CropAllocation],
        removed: List[CropAllocation],
        candidates: List['AllocationCandidate'],
        fields: List[Field],
    ) -> List[CropAllocation]:
        """Insert from unused candidates (similar to CropInsertOperation).
        
        This is the key missing piece: ALNS needs to be able to add
        allocations from the candidate pool, not just reinsert removed ones.
        """
        from agrr_core.usecase.services.allocation_utils import AllocationUtils
        
        current = partial.copy()
        
        # First, reinsert removed allocations (greedy)
        sorted_removed = sorted(removed, key=lambda a: a.profit_rate, reverse=True)
        for alloc in sorted_removed:
            if self._is_feasible_to_add(current, alloc):
                current.append(alloc)
        
        # Then, try to insert from unused candidates
        # Get IDs of allocations already in solution
        used_candidate_ids = {
            (a.field.field_id, a.crop.crop_id, a.start_date.isoformat())
            for a in current
        }
        
        # Sort candidates by profit (descending)
        sorted_candidates = sorted(
            candidates,
            key=lambda c: c.profit,
            reverse=True
        )
        
        # Try to insert unused candidates
        max_inserts = 50  # Limit to prevent explosion
        inserted_count = 0
        
        for candidate in sorted_candidates:
            if inserted_count >= max_inserts:
                break
            
            candidate_id = (
                candidate.field.field_id,
                candidate.crop.crop_id,
                candidate.start_date.isoformat()
            )
            
            if candidate_id in used_candidate_ids:
                continue  # Already used
            
            # Convert candidate to allocation
            new_alloc = AllocationUtils.candidate_to_allocation(candidate)
            
            # Try to add
            if self._is_feasible_to_add(current, new_alloc):
                current.append(new_alloc)
                used_candidate_ids.add(candidate_id)
                inserted_count += 1
        
        return current
    
    # ===== Helper Methods =====
    
    def _calculate_relatedness(
        self, 
        alloc1: CropAllocation, 
        alloc2: CropAllocation
    ) -> float:
        """Calculate relatedness score between two allocations.
        
        Considers:
        - Same field (weight: 0.5)
        - Temporal proximity (weight: 0.3)
        - Same crop (weight: 0.2)
        """
        score = 0.0
        
        # Same field
        if alloc1.field.field_id == alloc2.field.field_id:
            score += 0.5
        
        # Temporal proximity (closer in time = higher score)
        time_diff = abs((alloc1.start_date - alloc2.start_date).days)
        temporal_score = max(0, 1 - time_diff / 365)  # Normalize by 1 year
        score += 0.3 * temporal_score
        
        # Same crop
        if alloc1.crop.crop_id == alloc2.crop.crop_id:
            score += 0.2
        
        return score
    
    def _is_feasible_to_add(
        self, 
        current: List[CropAllocation], 
        new_alloc: CropAllocation
    ) -> bool:
        """Check if adding new_alloc to current solution is feasible."""
        # Check for time overlaps in the same field (including fallow period)
        for existing in current:
            if existing.field.field_id == new_alloc.field.field_id:
                if existing.overlaps_with_fallow(new_alloc):
                    return False  # Overlap found (considering fallow period)
        
        # TODO: Check max_revenue constraint if needed
        
        return True
    
    def _calculate_profit(self, solution: List[CropAllocation]) -> float:
        """Calculate total profit of solution."""
        return sum(a.profit for a in solution if a.profit is not None)

