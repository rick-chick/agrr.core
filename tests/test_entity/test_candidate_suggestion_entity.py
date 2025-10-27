"""
候補リスト提示機能のEntity層テスト

このモジュールは候補リスト提示機能のEntity層のテストを実装します。
"""
import pytest
from datetime import datetime
from agrr_core.entity.entities.candidate_suggestion_entity import (
    CandidateSuggestion, 
    CandidateType
)
from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop


class TestCandidateSuggestion:
    """CandidateSuggestion エンティティのテスト"""
    
    def test_create_insert_candidate(self):
        """新しい作物挿入候補の作成テスト"""
        candidate = CandidateSuggestion(
            field_id="field_1",
            candidate_type=CandidateType.INSERT,
            crop_id="tomato",
            start_date=datetime(2024, 6, 1),
            area=500.0,
            expected_profit=150000.0,
            move_instruction=None
        )
        
        assert candidate.field_id == "field_1"
        assert candidate.candidate_type == CandidateType.INSERT
        assert candidate.crop_id == "tomato"
        assert candidate.expected_profit == 150000.0
    
    def test_create_move_candidate(self):
        """既存作物移動候補の作成テスト"""
        candidate = CandidateSuggestion(
            field_id="field_2",
            candidate_type=CandidateType.MOVE,
            allocation_id="alloc_001",
            start_date=datetime(2024, 7, 1),
            area=300.0,
            expected_profit=120000.0,
            move_instruction=None
        )
        
        assert candidate.field_id == "field_2"
        assert candidate.candidate_type == CandidateType.MOVE
        assert candidate.allocation_id == "alloc_001"
        assert candidate.expected_profit == 120000.0
    
    def test_candidate_comparison(self):
        """候補の比較テスト（利益順）"""
        candidate1 = CandidateSuggestion(
            field_id="field_1",
            candidate_type=CandidateType.INSERT,
            crop_id="tomato",
            start_date=datetime(2024, 6, 1),
            area=500.0,
            expected_profit=150000.0,
            move_instruction=None
        )
        
        candidate2 = CandidateSuggestion(
            field_id="field_2",
            candidate_type=CandidateType.MOVE,
            allocation_id="alloc_001",
            start_date=datetime(2024, 7, 1),
            area=300.0,
            expected_profit=120000.0,
            move_instruction=None
        )
        
        assert candidate1.expected_profit > candidate2.expected_profit
        assert candidate1 > candidate2  # 利益で比較
    
    def test_validation_insert_candidate_missing_crop_id(self):
        """INSERT候補でcrop_idが不足している場合のバリデーションテスト"""
        with pytest.raises(ValueError, match="INSERT候補にはcrop_idが必要です"):
            CandidateSuggestion(
                field_id="field_1",
                candidate_type=CandidateType.INSERT,
                start_date=datetime(2024, 6, 1),
                area=500.0,
                expected_profit=150000.0,
                move_instruction=None
            )
    
    def test_validation_move_candidate_missing_allocation_id(self):
        """MOVE候補でallocation_idが不足している場合のバリデーションテスト"""
        with pytest.raises(ValueError, match="MOVE候補にはallocation_idが必要です"):
            CandidateSuggestion(
                field_id="field_2",
                candidate_type=CandidateType.MOVE,
                start_date=datetime(2024, 7, 1),
                area=300.0,
                expected_profit=120000.0,
                move_instruction=None
            )
    
    def test_to_dict_conversion(self):
        """辞書形式への変換テスト"""
        candidate = CandidateSuggestion(
            field_id="field_1",
            candidate_type=CandidateType.INSERT,
            crop_id="tomato",
            start_date=datetime(2024, 6, 1),
            area=500.0,
            expected_profit=150000.0,
            move_instruction=None
        )
        
        result = candidate.to_dict()
        
        assert result["field_id"] == "field_1"
        assert result["candidate_type"] == "INSERT"
        assert result["crop_id"] == "tomato"
        assert result["area"] == 500.0
        assert result["expected_profit"] == 150000.0
        assert result["start_date"] == "2024-06-01T00:00:00"


class TestCandidateType:
    """CandidateType エンティティのテスト"""
    
    def test_candidate_type_values(self):
        """候補タイプの値テスト"""
        assert CandidateType.INSERT.value == "INSERT"
        assert CandidateType.MOVE.value == "MOVE"
    
    def test_candidate_type_string_representation(self):
        """候補タイプの文字列表現テスト"""
        assert str(CandidateType.INSERT.value) == "INSERT"
        assert str(CandidateType.MOVE.value) == "MOVE"
