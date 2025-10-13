"""E2E tests for verifying all 47 prefecture JMA location codes.

These tests verify that the location codes in LOCATION_MAPPING are correct
by attempting to fetch actual data from JMA.

Run with: pytest tests/test_e2e/test_jma_47_prefectures.py -v -m e2e
"""

import pytest
from datetime import datetime

from agrr_core.framework.repositories.html_table_fetcher import HtmlTableFetcher
from agrr_core.adapter.repositories.weather_jma_repository import (
    WeatherJMARepository,
    LOCATION_MAPPING
)


class TestJMA47Prefectures:
    """E2E tests for all 47 prefectures."""
    
    @pytest.fixture
    def html_table_fetcher(self):
        """Create HTML table fetcher instance."""
        return HtmlTableFetcher(timeout=30)
    
    @pytest.fixture
    def repository(self, html_table_fetcher):
        """Create JMA repository instance."""
        return WeatherJMARepository(html_table_fetcher)
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.parametrize("coords,expected", [
        # 動作確認済みの地点
        ((35.6895, 139.6917), (44, 47662, "東京")),
        ((43.0642, 141.3469), (14, 47412, "札幌")),
        ((34.6937, 135.5023), (62, 47772, "大阪")),
        ((35.4439, 139.6380), (46, 47670, "横浜")),  # 神奈川（修正済み）
    ])
    async def test_location_code_accuracy(
        self,
        repository,
        html_table_fetcher,
        coords,
        expected
    ):
        """Test that location codes are correct by fetching actual data."""
        lat, lon = coords
        expected_prec, expected_block, expected_name = expected
        
        # Find nearest location
        prec_no, block_no, name = repository._find_nearest_location(lat, lon)
        
        assert prec_no == expected_prec, f"prec_no mismatch for {expected_name}"
        assert block_no == expected_block, f"block_no mismatch for {expected_name}"
        assert name == expected_name
        
        # Verify we can actually fetch data with this code
        url = repository._build_url(
            prec_no=prec_no,
            block_no=block_no,
            year=2024,
            month=1
        )
        
        print(f"\n=== Testing {name} ===")
        print(f"URL: {url}")
        
        try:
            tables = await html_table_fetcher.get(url)
            assert len(tables) > 0, f"No tables found for {name}"
            
            # Find data table
            data_table = None
            for table in tables:
                if table.table_id == 'tablefix1':
                    data_table = table
                    break
            
            assert data_table is not None, f"tablefix1 not found for {name}"
            assert len(data_table.rows) > 0, f"No data rows for {name}"
            
            print(f"✅ {name}: Successfully fetched {len(data_table.rows)} rows")
            
        except Exception as e:
            pytest.fail(f"Failed to fetch data for {name} (prec_no={prec_no}, block_no={block_no}): {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.slow
    async def test_all_47_prefectures_fetchable(self, repository, html_table_fetcher):
        """Test that all 47 prefectures can fetch data from JMA.
        
        This test is marked as 'slow' because it makes 47 HTTP requests.
        Run with: pytest -m "e2e and slow"
        """
        results = []
        
        for coords, (prec_no, block_no, name) in LOCATION_MAPPING.items():
            url = repository._build_url(
                prec_no=prec_no,
                block_no=block_no,
                year=2024,
                month=1
            )
            
            try:
                tables = await html_table_fetcher.get(url)
                
                # Find data table
                data_table = None
                for table in tables:
                    if table.table_id == 'tablefix1':
                        data_table = table
                        break
                
                if data_table and len(data_table.rows) > 0:
                    results.append({
                        'name': name,
                        'prec_no': prec_no,
                        'block_no': block_no,
                        'status': 'OK',
                        'rows': len(data_table.rows)
                    })
                else:
                    results.append({
                        'name': name,
                        'prec_no': prec_no,
                        'block_no': block_no,
                        'status': 'NO_DATA',
                        'rows': 0
                    })
            except Exception as e:
                results.append({
                    'name': name,
                    'prec_no': prec_no,
                    'block_no': block_no,
                    'status': 'ERROR',
                    'error': str(e)
                })
        
        # Print summary
        print("\n=== 47 Prefectures Verification Results ===")
        ok_count = sum(1 for r in results if r['status'] == 'OK')
        error_count = sum(1 for r in results if r['status'] == 'ERROR')
        no_data_count = sum(1 for r in results if r['status'] == 'NO_DATA')
        
        print(f"✅ OK: {ok_count}/47")
        print(f"❌ ERROR: {error_count}/47")
        print(f"⚠️  NO_DATA: {no_data_count}/47")
        
        # Print errors
        if error_count > 0 or no_data_count > 0:
            print("\n=== Problem Locations ===")
            for r in results:
                if r['status'] != 'OK':
                    print(f"{r['name']}: prec_no={r['prec_no']}, block_no={r['block_no']}")
                    print(f"  Status: {r['status']}")
                    if 'error' in r:
                        print(f"  Error: {r['error']}")
        
        # Fail if any location has errors
        assert error_count == 0, f"{error_count} locations failed to fetch data"
        assert no_data_count == 0, f"{no_data_count} locations returned no data"

