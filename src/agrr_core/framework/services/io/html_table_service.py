"""HTML table service implementation for framework layer."""

import requests
from bs4 import BeautifulSoup
from typing import List

from agrr_core.entity.exceptions.html_fetch_error import HtmlFetchError
from agrr_core.adapter.interfaces.io.html_table_service_interface import HtmlTableServiceInterface
from agrr_core.adapter.interfaces.structures.html_table_structures import HtmlTable, TableRow

class HtmlTableService(HtmlTableServiceInterface):
    """HTMLテーブル取得サービス"""
    
    def __init__(self, timeout: int = 30):
        """
        Initialize HTML table service.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
    
    def get(self, url: str) -> List[HtmlTable]:
        """
        URLから全テーブルを取得してパース
        
        Args:
            url: HTMLページのURL
            
        Returns:
            List[HtmlTable]: ページ内の全テーブル
            
        Raises:
            HtmlFetchError: HTML取得またはパースに失敗した場合
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # BeautifulSoupでパース
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 全テーブルを見つける
            table_elements = soup.find_all('table')
            
            if not table_elements:
                raise HtmlFetchError(f"No tables found in HTML from {url}")
            
            # 各テーブルをパース
            result = []
            for table_elem in table_elements:
                html_table = self._parse_table(table_elem)
                result.append(html_table)
            
            return result
            
        except requests.RequestException as e:
            raise HtmlFetchError(f"Failed to fetch HTML from {url}: {e}")
        except Exception as e:
            raise HtmlFetchError(f"Failed to parse HTML: {e}")
    
    def _parse_table(self, table_elem) -> HtmlTable:
        """
        テーブル要素をHtmlTable構造に変換
        
        Args:
            table_elem: BeautifulSoupのtable要素
            
        Returns:
            HtmlTable: 構造化されたテーブルデータ
        """
        # テーブル属性取得
        table_id = table_elem.get('id')
        table_class = table_elem.get('class')
        
        # 全行を取得
        all_rows = table_elem.find_all('tr')
        
        if not all_rows:
            return HtmlTable(
                headers=[],
                rows=[],
                table_id=table_id,
                table_class=table_class
            )
        
        # ヘッダー行とデータ行を分離
        # 気象庁の場合、最初の4行がヘッダー（MultiIndex構造）
        # <th> タグがある行をヘッダーとみなす
        header_rows = []
        data_row_start = 0
        
        for i, tr in enumerate(all_rows):
            th_cells = tr.find_all('th')
            if th_cells:
                # <th>がある行はヘッダー
                header_cells = [cell.get_text(strip=True) for cell in tr.find_all(['td', 'th'])]
                header_rows.append(header_cells)
                data_row_start = i + 1
            else:
                # <th>がない行が出たらヘッダー終了
                break
        
        # データ行をパース
        rows = []
        for tr in all_rows[data_row_start:]:
            cells = tr.find_all(['td', 'th'])
            if cells:
                cell_values = [cell.get_text(strip=True) for cell in cells]
                rows.append(TableRow(cells=cell_values))
        
        return HtmlTable(
            headers=header_rows,
            rows=rows,
            table_id=table_id,
            table_class=table_class
        )
    
    def close(self) -> None:
        """Close HTTP session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

