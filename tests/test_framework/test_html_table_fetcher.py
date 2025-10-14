"""Tests for HtmlTableFetcher."""

import pytest

from agrr_core.framework.repositories.html_table_fetcher import HtmlTableFetcher
from agrr_core.framework.interfaces.html_table_structures import HtmlTable


class TestHtmlTableFetcher:
    """Test HtmlTableFetcher."""
    
    @pytest.fixture
    def fetcher(self):
        """Create fetcher instance."""
        return HtmlTableFetcher()
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_fetch_jma_table_real(self, fetcher):
        """実際の気象庁データ取得テスト（E2E）"""
        url = 'https://www.data.jma.go.jp/obd/stats/etrn/view/daily_s1.php?prec_no=62&block_no=47772&year=2024&month=1&day=&view='
        
        tables = await fetcher.get(url)
        
        # 複数のテーブルが取得できる
        assert len(tables) >= 1
        assert all(isinstance(t, HtmlTable) for t in tables)
        
        # id="tablefix1"のテーブルを見つける
        data_table = None
        for table in tables:
            if table.table_id == 'tablefix1':
                data_table = table
                break
        
        assert data_table is not None, "tablefix1 not found"
        
        # データ行が存在する（31日分）
        assert len(data_table.rows) == 31, f"Expected 31 rows, got {len(data_table.rows)}"
        
        # ヘッダーが存在する
        assert len(data_table.headers) > 0
        
        # 最初の行のデータを確認
        first_row = data_table.rows[0]
        assert len(first_row.cells) >= 21, f"Expected 21+ cells, got {len(first_row.cells)}"
        
        # 日付セル（最初のセル）
        assert first_row.cells[0] == '1', f"Expected '1' for first day, got '{first_row.cells[0]}'"
        
        # 数値セルの確認（平均気温など）
        # cells[6]あたりに気温データがあるはず
        print(f"\n=== First row data ===")
        print(f"Day: {first_row.cells[0]}")
        print(f"Cells 1-10: {first_row.cells[1:11]}")
        print(f"Total cells: {len(first_row.cells)}")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_fetch_multiple_tables(self, fetcher):
        """複数テーブルの取得確認"""
        url = 'https://www.data.jma.go.jp/obd/stats/etrn/view/daily_s1.php?prec_no=62&block_no=47772&year=2024&month=1&day=&view='
        
        tables = await fetcher.get(url)
        
        # 7つのテーブルが取得できるはず
        assert len(tables) >= 5
        
        # 各テーブルの構造確認
        for i, table in enumerate(tables):
            print(f"\nTable {i}:")
            print(f"  ID: {table.table_id}")
            print(f"  Headers: {len(table.headers)} rows")
            print(f"  Data rows: {len(table.rows)}")

