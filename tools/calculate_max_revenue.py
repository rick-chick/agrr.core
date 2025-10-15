#!/usr/bin/env python3
"""Calculate max_revenue for crop allocation optimization.

This tool calculates the max_revenue value for each crop to achieve
balanced area allocation across multiple crops.

max_revenue acts as a total revenue cap for each crop across all fields
and cultivation periods, preventing a single highly profitable crop from
dominating the entire allocation.

Formula:
    max_revenue = (total_area / num_crops) × revenue_per_area × expected_cultivations

Where:
    - total_area: Sum of all field areas
    - num_crops: Number of crop types
    - revenue_per_area: Revenue per square meter for the crop
    - expected_cultivations: Expected number of times the crop can be planted
                            in the planning period (typically 1-2 for most crops)
"""

import json
import sys
from datetime import datetime
from typing import Dict, List


def calculate_max_revenues(
    fields_file: str,
    crops_file: str,
    planning_days: int = 214,  # Default: 7 months (Apr-Oct)
    expected_cultivations: Dict[str, float] = None
) -> Dict[str, float]:
    """Calculate max_revenue for each crop.
    
    Args:
        fields_file: Path to fields JSON file
        crops_file: Path to crops JSON file
        planning_days: Number of days in planning period (default: 214 = 7 months)
        expected_cultivations: Dict mapping crop names to expected cultivation count
                              If None, estimates based on growth period
    
    Returns:
        Dict mapping crop names to recommended max_revenue values
    """
    # Load fields
    with open(fields_file, 'r', encoding='utf-8') as f:
        fields_data = json.load(f)
    
    fields = fields_data.get('fields', [])
    total_area = sum(f['area'] for f in fields)
    
    # Load crops
    with open(crops_file, 'r', encoding='utf-8') as f:
        crops_data = json.load(f)
    
    crops = crops_data.get('crops', [])
    num_crops = len(crops)
    
    if num_crops == 0:
        raise ValueError("No crops found in crops file")
    
    # Target area per crop (equal distribution)
    target_area_per_crop = total_area / num_crops
    
    print(f"=== Input ===")
    print(f"Total area: {total_area}m²")
    print(f"Number of crops: {num_crops}")
    print(f"Target area per crop: {target_area_per_crop:.1f}m²")
    print(f"Planning period: {planning_days} days\n")
    
    # Calculate max_revenue for each crop
    max_revenues = {}
    
    print(f"=== Recommended max_revenue ===\n")
    
    for crop_data in crops:
        crop = crop_data['crop']
        crop_name = crop['name']
        revenue_per_area = crop.get('revenue_per_area', 0)
        
        # Estimate cultivation count if not provided
        if expected_cultivations and crop_name in expected_cultivations:
            cultivation_count = expected_cultivations[crop_name]
        else:
            # Estimate based on growth period (sum of required_gdd / typical daily gdd)
            # Rough estimate: assume 15-20°C mean temp → ~10-15 GDD/day
            total_gdd = sum(s['thermal']['required_gdd'] for s in crop_data['stage_requirements'])
            estimated_days = total_gdd / 12  # Assume 12 GDD/day on average
            cultivation_count = max(1, planning_days / estimated_days)
        
        # Calculate max_revenue
        # Use target_area_per_crop (not total_area) to encourage diversity
        max_revenue = target_area_per_crop * revenue_per_area * cultivation_count
        
        max_revenues[crop_name] = max_revenue
        
        print(f"{crop_name}:")
        print(f"  revenue_per_area: {revenue_per_area:,}円/m²")
        print(f"  estimated cultivations: {cultivation_count:.1f}回")
        print(f"  max_revenue: {max_revenue:,.0f}円")
        print(f"  (= {target_area_per_crop:.1f}m² × {revenue_per_area}円/m² × {cultivation_count:.1f}回)\n")
    
    return max_revenues


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Calculate max_revenue for crop allocation optimization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Calculate max_revenue for allocation optimization
  python tools/calculate_max_revenue.py \\
    --fields-file test_data/allocation_fields_1760447748.json \\
    --crops-file test_data/allocation_crops_1760447748.json \\
    --planning-days 214
  
  # With custom cultivation counts
  python tools/calculate_max_revenue.py \\
    --fields-file fields.json \\
    --crops-file crops.json \\
    --planning-days 214 \\
    --cultivations "ほうれん草:2,ニンジン:2"

Output Format:
  The tool prints recommended max_revenue values for each crop.
  Update your crops JSON file with these values to achieve balanced allocation.
"""
    )
    
    parser.add_argument(
        '--fields-file',
        required=True,
        help='Path to fields JSON file'
    )
    
    parser.add_argument(
        '--crops-file',
        required=True,
        help='Path to crops JSON file'
    )
    
    parser.add_argument(
        '--planning-days',
        type=int,
        default=214,
        help='Number of days in planning period (default: 214 = 7 months)'
    )
    
    parser.add_argument(
        '--cultivations',
        type=str,
        help='Custom cultivation counts per crop (format: "crop1:count1,crop2:count2")'
    )
    
    parser.add_argument(
        '--output-json',
        action='store_true',
        help='Output as JSON format (for scripting)'
    )
    
    args = parser.parse_args()
    
    # Parse custom cultivation counts
    custom_cultivations = None
    if args.cultivations:
        custom_cultivations = {}
        for pair in args.cultivations.split(','):
            crop_name, count = pair.split(':')
            custom_cultivations[crop_name.strip()] = float(count.strip())
    
    # Calculate max_revenues
    max_revenues = calculate_max_revenues(
        fields_file=args.fields_file,
        crops_file=args.crops_file,
        planning_days=args.planning_days,
        expected_cultivations=custom_cultivations
    )
    
    # Output
    if args.output_json:
        print(json.dumps(max_revenues, ensure_ascii=False, indent=2))
    else:
        print("\n=== Summary ===")
        print("Update your crops JSON file with these max_revenue values:")
        print("```json")
        for crop_name, max_rev in max_revenues.items():
            print(f'  "{crop_name}": {max_rev:.0f},')
        print("```")


if __name__ == '__main__':
    main()

