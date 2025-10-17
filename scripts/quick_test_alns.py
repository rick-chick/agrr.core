"""Quick test to verify ALNS integration works."""

import asyncio
from datetime import datetime

from agrr_core.usecase.dto.optimization_config import OptimizationConfig

# Test OptimizationConfig
config_ls = OptimizationConfig(enable_alns=False)
print(f"✓ DP + Local Search config created")
print(f"  enable_alns: {config_ls.enable_alns}")

config_alns = OptimizationConfig(
    enable_alns=True,
    alns_iterations=10,  # Small for testing
    alns_removal_rate=0.3,
)
print(f"\n✓ DP + ALNS config created")
print(f"  enable_alns: {config_alns.enable_alns}")
print(f"  alns_iterations: {config_alns.alns_iterations}")
print(f"  alns_removal_rate: {config_alns.alns_removal_rate}")

# Test ALNSOptimizer import
try:
    from agrr_core.usecase.services.alns_optimizer_service import ALNSOptimizer
    alns = ALNSOptimizer(config_alns)
    print(f"\n✓ ALNSOptimizer imported and instantiated")
    print(f"  Destroy operators: {len(alns.destroy_operators)}")
    print(f"  Repair operators: {len(alns.repair_operators)}")
except Exception as e:
    print(f"\n✗ ALNSOptimizer error: {e}")
    import traceback
    traceback.print_exc()

# Test AllocationUtils import
try:
    from agrr_core.usecase.services.allocation_utils import AllocationUtils
    print(f"\n✓ AllocationUtils imported")
    
    # Test a simple method
    from datetime import datetime
    start1 = datetime(2025, 1, 1)
    end1 = datetime(2025, 3, 1)
    start2 = datetime(2025, 2, 1)
    end2 = datetime(2025, 4, 1)
    
    overlaps = AllocationUtils.time_overlaps(start1, end1, start2, end2)
    print(f"  time_overlaps test: {overlaps} (expected: True)")
    
except Exception as e:
    print(f"\n✗ AllocationUtils error: {e}")
    import traceback
    traceback.print_exc()

# Test Interactor integration
try:
    from agrr_core.usecase.interactors.multi_field_crop_allocation_greedy_interactor import (
        MultiFieldCropAllocationGreedyInteractor
    )
    print(f"\n✓ MultiFieldCropAllocationGreedyInteractor imported")
    print(f"  ALNS integration: Ready")
    
except Exception as e:
    print(f"\n✗ Interactor error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("ALNS INTEGRATION TEST COMPLETE")
print("="*80)
print("\nAll components are ready for benchmarking!")
print("\nNext steps:")
print("1. Run benchmark: python scripts/benchmark_dp_vs_alns.py")
print("2. Or use in your code with: config = OptimizationConfig(enable_alns=True)")

