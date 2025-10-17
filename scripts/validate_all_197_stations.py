#!/usr/bin/env python3
"""
Validate all 197 NOAA stations can fetch data for 2023.

Tests each station to ensure:
1. Station data is available
2. Data can be successfully fetched
3. Temperature data is present
"""

import asyncio
import sys
from collections import defaultdict

from agrr_core.adapter.gateways.weather_noaa_ftp_gateway import (
    WeatherNOAAFTPGateway,
    LOCATION_MAPPING
)


async def test_single_station(gateway, lat, lon, station_info):
    """Test a single station."""
    usaf, wban, name, st_lat, st_lon = station_info
    state = name.split(', ')[-1]
    
    try:
        # Test with 1 week of data from 2023
        result = await gateway.get_by_location_and_date_range(
            latitude=lat,
            longitude=lon,
            start_date="2023-01-01",
            end_date="2023-01-07"
        )
        
        # Check if we got data
        if result and result.weather_data_list:
            days = len(result.weather_data_list)
            
            # Check temperature data
            temps = [d.temperature_2m_mean for d in result.weather_data_list 
                    if d.temperature_2m_mean is not None]
            
            if temps:
                avg_temp = sum(temps) / len(temps)
                return {
                    'status': 'success',
                    'state': state,
                    'usaf': usaf,
                    'wban': wban,
                    'name': name,
                    'days': days,
                    'avg_temp': avg_temp,
                    'lat': st_lat,
                    'lon': st_lon
                }
            else:
                return {
                    'status': 'no_temp',
                    'state': state,
                    'usaf': usaf,
                    'wban': wban,
                    'name': name,
                    'days': days
                }
        else:
            return {
                'status': 'no_data',
                'state': state,
                'usaf': usaf,
                'wban': wban,
                'name': name
            }
            
    except Exception as e:
        return {
            'status': 'error',
            'state': state,
            'usaf': usaf,
            'wban': wban,
            'name': name,
            'error': str(e)
        }


async def main():
    """Test all 197 stations."""
    gateway = WeatherNOAAFTPGateway()
    
    print("="*80)
    print("Validating All 197 NOAA Stations")
    print("="*80)
    print(f"Total stations to test: {len(LOCATION_MAPPING)}")
    print(f"Test period: 2023-01-01 to 2023-01-07 (1 week)")
    print("="*80)
    print()
    
    results = []
    by_state = defaultdict(list)
    
    # Test each station
    for i, (coords, station_info) in enumerate(LOCATION_MAPPING.items(), 1):
        lat, lon = coords
        usaf, wban, name, st_lat, st_lon = station_info
        state = name.split(', ')[-1]
        
        print(f"[{i:3d}/197] Testing {state:2s} - {name[:40]:40s}...", end=' ', flush=True)
        
        result = await test_single_station(gateway, lat, lon, station_info)
        results.append(result)
        by_state[state].append(result)
        
        # Display result
        if result['status'] == 'success':
            print(f"✅ {result['days']} days, {result['avg_temp']:.1f}°C")
        elif result['status'] == 'no_temp':
            print(f"⚠️  {result['days']} days, no temp data")
        elif result['status'] == 'no_data':
            print(f"❌ No data")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown')[:30]}")
        
        # Small delay to avoid overwhelming the FTP server
        if i % 10 == 0:
            await asyncio.sleep(1)
    
    # Summary
    print()
    print("="*80)
    print("Summary")
    print("="*80)
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    no_temp_count = sum(1 for r in results if r['status'] == 'no_temp')
    no_data_count = sum(1 for r in results if r['status'] == 'no_data')
    error_count = sum(1 for r in results if r['status'] == 'error')
    
    print(f"Total tested: {len(results)}")
    print(f"✅ Success: {success_count} ({success_count/len(results)*100:.1f}%)")
    print(f"⚠️  No temperature: {no_temp_count} ({no_temp_count/len(results)*100:.1f}%)")
    print(f"❌ No data: {no_data_count} ({no_data_count/len(results)*100:.1f}%)")
    print(f"❌ Error: {error_count} ({error_count/len(results)*100:.1f}%)")
    
    print()
    print("="*80)
    print("By State")
    print("="*80)
    
    for state in sorted(by_state.keys()):
        state_results = by_state[state]
        state_success = sum(1 for r in state_results if r['status'] == 'success')
        total = len(state_results)
        print(f"{state:2s}: {state_success:2d}/{total:2d} success ({state_success/total*100:5.1f}%)")
    
    # Failed stations details
    failed = [r for r in results if r['status'] in ['no_data', 'error']]
    if failed:
        print()
        print("="*80)
        print("Failed Stations (Details)")
        print("="*80)
        for r in failed:
            print(f"{r['state']:2s} - {r['usaf']}-{r['wban']:5s} {r['name'][:40]:40s} - {r['status']}")
            if 'error' in r:
                print(f"     Error: {r['error'][:60]}")
    
    # Save results
    import json
    with open('validation_results_197.json', 'w') as f:
        json.dump({
            'total': len(results),
            'success': success_count,
            'no_temp': no_temp_count,
            'no_data': no_data_count,
            'error': error_count,
            'results': results,
            'by_state': {state: [r for r in state_results] for state, state_results in by_state.items()}
        }, f, indent=2)
    
    print()
    print("="*80)
    print(f"✅ Results saved to validation_results_197.json")
    print("="*80)
    
    # Return exit code
    if success_count >= len(results) * 0.9:  # 90%以上成功
        print("\n✅ Validation PASSED (90%+ success)")
        return 0
    else:
        print(f"\n⚠️  Validation WARNING (only {success_count/len(results)*100:.1f}% success)")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

