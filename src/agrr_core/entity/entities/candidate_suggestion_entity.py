"""
候補リスト提示機能のエンティティ

このモジュールは候補リスト提示機能で使用されるエンティティを定義します。
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

class CandidateType(Enum):
    """候補タイプの列挙型"""
    INSERT = "INSERT"  # 新しい作物挿入候補
    MOVE = "MOVE"      # 既存作物移動候補

@dataclass
class CandidateSuggestion:
    """
    候補リスト提示のエンティティ
    
    圃場ごとに利益最高の挿入可能な候補を表現します。
    """
    field_id: str
    candidate_type: CandidateType
    start_date: datetime
    area: float
    expected_profit: float
    move_instruction: Optional[object] = None  # MoveInstruction エンティティへの参照
    
    # INSERT候補の場合に使用
    crop_id: Optional[str] = None
    
    # MOVE候補の場合に使用
    allocation_id: Optional[str] = None
    
    def __post_init__(self):
        """バリデーション"""
        if self.candidate_type == CandidateType.INSERT and not self.crop_id:
            raise ValueError("INSERT候補にはcrop_idが必要です")
        if self.candidate_type == CandidateType.MOVE and not self.allocation_id:
            raise ValueError("MOVE候補にはallocation_idが必要です")
    
    def __lt__(self, other):
        """利益による比較（ソート用）"""
        return self.expected_profit < other.expected_profit
    
    def __gt__(self, other):
        """利益による比較（ソート用）"""
        return self.expected_profit > other.expected_profit
    
    def __eq__(self, other):
        """等価性の比較"""
        if not isinstance(other, CandidateSuggestion):
            return False
        return (
            self.field_id == other.field_id and
            self.candidate_type == other.candidate_type and
            self.start_date == other.start_date and
            self.area == other.area and
            self.expected_profit == other.expected_profit
        )
    
    def __hash__(self):
        """ハッシュ値の計算"""
        return hash((
            self.field_id,
            self.candidate_type,
            self.start_date,
            self.area,
            self.expected_profit
        ))
    
    def to_dict(self) -> dict:
        """辞書形式への変換"""
        return {
            "field_id": self.field_id,
            "candidate_type": self.candidate_type.value,
            "start_date": self.start_date.isoformat(),
            "area": self.area,
            "expected_profit": self.expected_profit,
            "crop_id": self.crop_id,
            "allocation_id": self.allocation_id,
            "move_instruction": self.move_instruction.to_dict() if self.move_instruction else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CandidateSuggestion':
        """辞書形式からの変換"""
        return cls(
            field_id=data["field_id"],
            candidate_type=CandidateType(data["candidate_type"]),
            start_date=datetime.fromisoformat(data["start_date"]),
            area=data["area"],
            expected_profit=data["expected_profit"],
            crop_id=data.get("crop_id"),
            allocation_id=data.get("allocation_id"),
            move_instruction=data.get("move_instruction")
        )
