"""Benchmark script to compare DP + Local Search vs DP + ALNS.

This script runs allocation optimization with different algorithms
and compares their performance in terms of:
- Solution quality (profit, revenue, cost)
- Computation time
- Number of allocations

Usage:
    python scripts/benchmark_dp_vs_alns.py
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from agrr_core.usecase.interactors.multi_field_crop_allocation_greedy_interactor import (
    MultiFieldCropAllocationGreedyInteractor,
)
from agrr_core.usecase.dto.multi_field_crop_allocation_request_dto import (
    MultiFieldCropAllocationRequestDTO,
)
from agrr_core.usecase.dto.optimization_config import OptimizationConfig
from agrr_core.adapter.gateways.field_inmemory_gateway import FieldInMemoryGateway
from agrr_core.adapter.gateways.crop_profile_inmemory_gateway import CropProfileInMemoryGateway
from agrr_core.adapter.gateways.weather_file_gateway import WeatherFileGateway
from agrr_core.adapter.gateways.interaction_rule_file_gateway import InteractionRuleFileGateway
from agrr_core.entity.entities.field_entity import Field
from agrr_core.usecase.services.crop_profile_mapper import CropProfileMapper


class BenchmarkRunner:
    """Run benchmarks comparing DP + LocalSearch vs DP + ALNS."""
    
    def __init__(self, test_data_dir: Path):
        self.test_data_dir = test_data_dir
        self.results = []
    
    async def load_data(
        self,
        fields_file: str,
        crops_file: str,
        weather_file: str,
        rules_file: str = None
    ) -> tuple:
        """Load test data from files."""
        
        # Load fields
        with open(self.test_data_dir / fields_file, 'r', encoding='utf-8') as f:
            fields_data = json.load(f)
        
        fields = []
        for field_data in fields_data['fields']:
            field = Field(
                field_id=field_data['field_id'],
                name=field_data['name'],
                area=field_data['area'],
                daily_fixed_cost=field_data['daily_fixed_cost'],
                location=field_data.get('location'),
            )
            fields.append(field)
        
        # Load crops using CropProfileMapper
        with open(self.test_data_dir / crops_file, 'r', encoding='utf-8') as f:
            crops_data = json.load(f)
        
        crops = []
        mapper = CropProfileMapper()
        for crop_data in crops_data['crops']:
            crop_profile = mapper.from_dict(crop_data)
            crops.append(crop_profile)
        
        # Load interaction rules if provided
        interaction_rules = []
        if rules_file:
            gateway = InteractionRuleFileGateway(str(self.test_data_dir / rules_file))
            interaction_rules = await gateway.get_all()
        
        return fields, crops, interaction_rules
    
    async def run_single_benchmark(
        self,
        test_name: str,
        fields: List[Field],
        crops: List,  # List of CropProfile
        weather_file: str,
        planning_start: str,
        planning_end: str,
        interaction_rules: List = None,
    ) -> Dict[str, Any]:
        """Run a single benchmark comparing both algorithms."""
        
        print(f"\n{'='*80}")
        print(f"Running benchmark: {test_name}")
        print(f"{'='*80}")
        print(f"Fields: {len(fields)}, Crops: {len(crops)}")
        print(f"Planning period: {planning_start} to {planning_end}")
        
        # Prepare gateways
        field_gateway = FieldInMemoryGateway()
        for field in fields:
            await field_gateway.save(field)
        
        crop_gateway = CropProfileInMemoryGateway()
        for crop in crops:
            await crop_gateway.save(crop)
        
        weather_gateway = WeatherFileGateway(str(self.test_data_dir / weather_file))
        
        crop_profile_gateway_internal = CropProfileInMemoryGateway()
        
        # Create request
        request = MultiFieldCropAllocationRequestDTO(
            field_ids=[f.field_id for f in fields],
            planning_period_start=datetime.fromisoformat(planning_start),
            planning_period_end=datetime.fromisoformat(planning_end),
            optimization_objective="maximize_profit",
        )
        
        results = {}
        
        # ===== Test 1: DP + Local Search (Hill Climbing) =====
        print("\n--- Running: DP + Local Search (Hill Climbing) ---")
        
        config_ls = OptimizationConfig(
            enable_parallel_candidate_generation=True,
            enable_candidate_filtering=True,
            max_local_search_iterations=100,
            enable_alns=False,  # Use Hill Climbing
        )
        
        interactor_ls = MultiFieldCropAllocationGreedyInteractor(
            field_gateway=field_gateway,
            crop_gateway=crop_gateway,
            weather_gateway=weather_gateway,
            crop_profile_gateway_internal=crop_profile_gateway_internal,
            config=config_ls,
            interaction_rules=interaction_rules or [],
        )
        
        start_time = time.time()
        try:
            response_ls = await interactor_ls.execute(
                request=request,
                enable_local_search=True,
                use_dp_allocation=True,  # Use DP
                config=config_ls,
            )
            elapsed_ls = time.time() - start_time
            
            result = response_ls.optimization_result
            results['dp_local_search'] = {
                'success': True,
                'time': elapsed_ls,
                'total_profit': result.total_profit,
                'total_revenue': result.total_revenue,
                'total_cost': result.total_cost,
                'num_allocations': sum(len(fs.allocations) for fs in result.field_schedules),
                'algorithm': result.algorithm_used,
            }
            
            print(f"✓ Completed in {elapsed_ls:.2f}s")
            print(f"  Total Profit: ¥{result.total_profit:,.0f}")
            print(f"  Allocations: {results['dp_local_search']['num_allocations']}")
            
        except Exception as e:
            elapsed_ls = time.time() - start_time
            results['dp_local_search'] = {
                'success': False,
                'time': elapsed_ls,
                'error': str(e),
            }
            print(f"✗ Failed: {e}")
        
        # ===== Test 2: DP + ALNS =====
        print("\n--- Running: DP + ALNS ---")
        
        config_alns = OptimizationConfig(
            enable_parallel_candidate_generation=True,
            enable_candidate_filtering=True,
            enable_alns=True,  # Use ALNS
            alns_iterations=200,
            alns_removal_rate=0.3,
        )
        
        interactor_alns = MultiFieldCropAllocationGreedyInteractor(
            field_gateway=field_gateway,
            crop_gateway=crop_gateway,
            weather_gateway=weather_gateway,
            crop_profile_gateway_internal=crop_profile_gateway_internal,
            config=config_alns,
            interaction_rules=interaction_rules or [],
        )
        
        start_time = time.time()
        try:
            response_alns = await interactor_alns.execute(
                request=request,
                enable_local_search=True,
                use_dp_allocation=True,  # Use DP
                config=config_alns,
            )
            elapsed_alns = time.time() - start_time
            
            result = response_alns.optimization_result
            results['dp_alns'] = {
                'success': True,
                'time': elapsed_alns,
                'total_profit': result.total_profit,
                'total_revenue': result.total_revenue,
                'total_cost': result.total_cost,
                'num_allocations': sum(len(fs.allocations) for fs in result.field_schedules),
                'algorithm': result.algorithm_used,
            }
            
            print(f"✓ Completed in {elapsed_alns:.2f}s")
            print(f"  Total Profit: ¥{result.total_profit:,.0f}")
            print(f"  Allocations: {results['dp_alns']['num_allocations']}")
            
        except Exception as e:
            elapsed_alns = time.time() - start_time
            results['dp_alns'] = {
                'success': False,
                'time': elapsed_alns,
                'error': str(e),
            }
            print(f"✗ Failed: {e}")
        
        # ===== Comparison =====
        if results['dp_local_search']['success'] and results['dp_alns']['success']:
            print("\n--- Comparison ---")
            
            ls_profit = results['dp_local_search']['total_profit']
            alns_profit = results['dp_alns']['total_profit']
            profit_diff = alns_profit - ls_profit
            profit_improvement = (profit_diff / ls_profit * 100) if ls_profit != 0 else 0
            
            ls_time = results['dp_local_search']['time']
            alns_time = results['dp_alns']['time']
            time_diff = alns_time - ls_time
            
            print(f"Profit Improvement: ¥{profit_diff:,.0f} ({profit_improvement:+.2f}%)")
            print(f"Time Difference: {time_diff:+.2f}s ({alns_time/ls_time*100:.1f}% of LS)")
            
            results['comparison'] = {
                'profit_improvement': profit_improvement,
                'profit_diff': profit_diff,
                'time_diff': time_diff,
                'time_ratio': alns_time / ls_time if ls_time > 0 else 0,
            }
        
        return {
            'test_name': test_name,
            'fields_count': len(fields),
            'crops_count': len(crops),
            **results
        }
    
    async def run_all_benchmarks(self):
        """Run all benchmark scenarios."""
        
        # Scenario 1: Medium problem (10 fields, 6 crops)
        fields, crops, rules = await self.load_data(
            'allocation_fields_large.json',
            'allocation_crops_6types.json',
            'allocation_weather_1760533282.json',
            'allocation_rules_1760533282.json',
        )
        
        result1 = await self.run_single_benchmark(
            test_name="Medium: 10 fields, 6 crops (1 year)",
            fields=fields,
            crops=crops,
            weather_file='allocation_weather_1760533282.json',
            planning_start='2025-01-01',
            planning_end='2025-12-31',
            interaction_rules=rules,
        )
        self.results.append(result1)
        
        # Scenario 2: Large problem (20 fields, 6 crops) if xlarge file exists
        try:
            fields_xl, crops, rules = await self.load_data(
                'allocation_fields_xlarge.json',
                'allocation_crops_6types.json',
                'allocation_weather_extended.json',
                'allocation_rules_1760533282.json',
            )
            
            result2 = await self.run_single_benchmark(
                test_name="Large: 20 fields, 6 crops (1 year)",
                fields=fields_xl,
                crops=crops,
                weather_file='allocation_weather_extended.json',
                planning_start='2025-01-01',
                planning_end='2025-12-31',
                interaction_rules=rules,
            )
            self.results.append(result2)
        except FileNotFoundError:
            print("\n⚠ Skipping large scenario (xlarge file not found)")
        
        # Scenario 3: Balanced crops
        try:
            fields, crops_balanced, _ = await self.load_data(
                'allocation_fields_large.json',
                'allocation_crops_balanced.json',
                'allocation_weather_1760533282.json',
            )
            
            result3 = await self.run_single_benchmark(
                test_name="Balanced: 10 fields, balanced crops",
                fields=fields,
                crops=crops_balanced,
                weather_file='allocation_weather_1760533282.json',
                planning_start='2025-01-01',
                planning_end='2025-12-31',
            )
            self.results.append(result3)
        except FileNotFoundError:
            print("\n⚠ Skipping balanced scenario (file not found)")
    
    def print_summary(self):
        """Print summary of all benchmarks."""
        
        print("\n" + "="*80)
        print("BENCHMARK SUMMARY")
        print("="*80)
        
        for i, result in enumerate(self.results, 1):
            print(f"\n{i}. {result['test_name']}")
            print(f"   Fields: {result['fields_count']}, Crops: {result['crops_count']}")
            
            if result['dp_local_search']['success'] and result['dp_alns']['success']:
                ls = result['dp_local_search']
                alns = result['dp_alns']
                comp = result['comparison']
                
                print(f"\n   DP + Local Search:")
                print(f"     Profit: ¥{ls['total_profit']:,.0f}")
                print(f"     Time:   {ls['time']:.2f}s")
                print(f"     Allocs: {ls['num_allocations']}")
                
                print(f"\n   DP + ALNS:")
                print(f"     Profit: ¥{alns['total_profit']:,.0f}")
                print(f"     Time:   {alns['time']:.2f}s")
                print(f"     Allocs: {alns['num_allocations']}")
                
                print(f"\n   Improvement:")
                print(f"     Profit: {comp['profit_improvement']:+.2f}%")
                print(f"     Time:   {comp['time_diff']:+.2f}s ({comp['time_ratio']:.2f}x)")
            else:
                print("   ⚠ One or both algorithms failed")
        
        # Overall statistics
        successful_comparisons = [
            r for r in self.results 
            if r['dp_local_search']['success'] and r['dp_alns']['success']
        ]
        
        if successful_comparisons:
            avg_improvement = sum(r['comparison']['profit_improvement'] for r in successful_comparisons) / len(successful_comparisons)
            avg_time_ratio = sum(r['comparison']['time_ratio'] for r in successful_comparisons) / len(successful_comparisons)
            
            print(f"\n{'='*80}")
            print("OVERALL STATISTICS")
            print(f"{'='*80}")
            print(f"Average Profit Improvement: {avg_improvement:+.2f}%")
            print(f"Average Time Ratio: {avg_time_ratio:.2f}x")
            print(f"Successful Comparisons: {len(successful_comparisons)}/{len(self.results)}")
    
    def save_results(self, output_file: str):
        """Save results to JSON file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n✓ Results saved to: {output_file}")


async def main():
    """Main entry point."""
    
    # Setup
    test_data_dir = Path(__file__).parent.parent / 'test_data'
    runner = BenchmarkRunner(test_data_dir)
    
    # Run benchmarks
    await runner.run_all_benchmarks()
    
    # Print summary
    runner.print_summary()
    
    # Save results
    output_file = test_data_dir / f'benchmark_results_{int(time.time())}.json'
    runner.save_results(str(output_file))


if __name__ == '__main__':
    asyncio.run(main())

