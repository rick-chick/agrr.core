"""HTML table service interface for adapter layer."""

from abc import ABC, abstractmethod
from typing import List

from ..structures.html_table_structures import HtmlTable

class HtmlTableServiceInterface(ABC):
    """HTMLテーブル取得サービスインターフェース"""
    
    @abstractmethod
    def get(self, url: str) -> List[HtmlTable]:
        """
        URLから全テーブルを取得
        
        Args:
            url: HTMLページのURL
            
        Returns:
            List[HtmlTable]: ページ内の全テーブル
            
        Raises:
            HtmlFetchError: HTML取得またはパースに失敗した場合
        """
        pass

