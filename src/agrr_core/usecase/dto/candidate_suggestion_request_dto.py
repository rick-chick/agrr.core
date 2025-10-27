"""
候補リスト提示機能のDTO

このモジュールは候補リスト提示機能で使用されるDTOを定義します。
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from agrr_core.entity.entities.candidate_suggestion_entity import CandidateSuggestion


@dataclass
class CandidateSuggestionRequestDTO:
    """
    候補リスト提示リクエストDTO
    
    候補リスト提示機能への入力パラメータを表現します。
    """
    target_crop_id: str
    planning_period_start: datetime
    planning_period_end: datetime
    
    def __post_init__(self):
        """バリデーション"""
        if not self.target_crop_id:
            raise ValueError("target_crop_idは必須です")
        if self.planning_period_start >= self.planning_period_end:
            raise ValueError("planning_period_startはplanning_period_endより前である必要があります")


@dataclass
class CandidateSuggestionResponseDTO:
    """
    候補リスト提示レスポンスDTO
    
    候補リスト提示機能の出力結果を表現します。
    """
    candidates: List[CandidateSuggestion]
    success: bool
    message: str
    
    def __post_init__(self):
        """バリデーション"""
        if not isinstance(self.candidates, list):
            raise ValueError("candidatesはリストである必要があります")
        if not isinstance(self.success, bool):
            raise ValueError("successはブール値である必要があります")
        if not isinstance(self.message, str):
            raise ValueError("messageは文字列である必要があります")
    
    def get_candidates_by_field(self, field_id: str) -> List[CandidateSuggestion]:
        """指定された圃場の候補を取得"""
        return [c for c in self.candidates if c.field_id == field_id]
    
    def get_best_candidate_per_field(self) -> List[CandidateSuggestion]:
        """圃場ごとの最良候補を取得"""
        field_candidates = {}
        for candidate in self.candidates:
            if candidate.field_id not in field_candidates:
                field_candidates[candidate.field_id] = candidate
            elif candidate.expected_profit > field_candidates[candidate.field_id].expected_profit:
                field_candidates[candidate.field_id] = candidate
        
        return list(field_candidates.values())
    
    def to_dict(self) -> dict:
        """辞書形式への変換"""
        return {
            "candidates": [c.to_dict() for c in self.candidates],
            "success": self.success,
            "message": self.message
        }
