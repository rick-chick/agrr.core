"""HTML table data structures for adapter layer."""

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class TableRow:
    """テーブルの1行"""
    cells: List[str]  # セルの値リスト（文字列）

@dataclass
class HtmlTable:
    """HTMLテーブル構造"""
    headers: List[List[str]]  # MultiIndexヘッダー [[row1_cells], [row2_cells], ...]
    rows: List[TableRow]  # データ行
    table_id: Optional[str] = None  # テーブルのID属性（id="tablefix1"など）
    table_class: Optional[List[str]] = None  # テーブルのclass属性

