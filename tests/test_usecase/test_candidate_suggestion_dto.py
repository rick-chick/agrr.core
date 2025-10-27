"""
候補リスト提示機能のDTOテスト

このモジュールは候補リスト提示機能のDTOのテストを実装します。
"""
import pytest
from datetime import datetime
from agrr_core.usecase.dto.candidate_suggestion_request_dto import CandidateSuggestionRequestDTO
from agrr_core.usecase.dto.candidate_suggestion_response_dto import CandidateSuggestionResponseDTO
from agrr_core.entity.entities.candidate_suggestion_entity import CandidateSuggestion, CandidateType


class TestCandidateSuggestionRequestDTO:
    """CandidateSuggestionRequestDTO のテスト"""
    
    def test_create_request_dto(self):
        """リクエストDTOの作成テスト"""
        request = CandidateSuggestionRequestDTO(
            target_crop_id="tomato",
            planning_period_start=datetime(2024, 4, 1),
            planning_period_end=datetime(2024, 10, 31)
        )
        
        assert request.target_crop_id == "tomato"
        assert request.planning_period_start == datetime(2024, 4, 1)
        assert request.planning_period_end == datetime(2024, 10, 31)
    
    def test_request_dto_validation_empty_crop_id(self):
        """空のcrop_idでのバリデーションテスト"""
        with pytest.raises(ValueError, match="target_crop_idは必須です"):
            CandidateSuggestionRequestDTO(
                target_crop_id="",  # 空文字
                planning_period_start=datetime(2024, 4, 1),
                planning_period_end=datetime(2024, 10, 31)
            )
    
    def test_request_dto_validation_invalid_date_range(self):
        """無効な日付範囲でのバリデーションテスト"""
        with pytest.raises(ValueError, match="planning_period_startはplanning_period_endより前である必要があります"):
            CandidateSuggestionRequestDTO(
                target_crop_id="tomato",
                planning_period_start=datetime(2024, 10, 31),  # 終了日より後
                planning_period_end=datetime(2024, 4, 1)
            )


class TestCandidateSuggestionResponseDTO:
    """CandidateSuggestionResponseDTO のテスト"""
    
    def test_create_success_response_dto(self):
        """成功レスポンスDTOの作成テスト"""
        candidates = [
            CandidateSuggestion(
                field_id="field_1",
                candidate_type=CandidateType.INSERT,
                crop_id="tomato",
                start_date=datetime(2024, 6, 1),
                area=500.0,
                expected_profit=150000.0,
                move_instruction=None
            )
        ]
        
        response = CandidateSuggestionResponseDTO(
            candidates=candidates,
            success=True,
            message="Successfully generated candidates"
        )
        
        assert response.success is True
        assert len(response.candidates) == 1
        assert response.message == "Successfully generated candidates"
    
    def test_create_failure_response_dto(self):
        """失敗レスポンスDTOの作成テスト"""
        response = CandidateSuggestionResponseDTO(
            candidates=[],
            success=False,
            message="Failed to generate candidates"
        )
        
        assert response.success is False
        assert len(response.candidates) == 0
        assert response.message == "Failed to generate candidates"
    
    def test_get_candidates_by_field(self):
        """指定された圃場の候補を取得するテスト"""
        candidates = [
            CandidateSuggestion(
                field_id="field_1",
                candidate_type=CandidateType.INSERT,
                crop_id="tomato",
                start_date=datetime(2024, 6, 1),
                area=500.0,
                expected_profit=150000.0,
                move_instruction=None
            ),
            CandidateSuggestion(
                field_id="field_2",
                candidate_type=CandidateType.MOVE,
                allocation_id="alloc_001",
                start_date=datetime(2024, 7, 1),
                area=300.0,
                expected_profit=120000.0,
                move_instruction=None
            )
        ]
        
        response = CandidateSuggestionResponseDTO(
            candidates=candidates,
            success=True,
            message="Success"
        )
        
        field_1_candidates = response.get_candidates_by_field("field_1")
        assert len(field_1_candidates) == 1
        assert field_1_candidates[0].field_id == "field_1"
        
        field_2_candidates = response.get_candidates_by_field("field_2")
        assert len(field_2_candidates) == 1
        assert field_2_candidates[0].field_id == "field_2"
    
    def test_get_best_candidate_per_field(self):
        """圃場ごとの最良候補を取得するテスト"""
        candidates = [
            CandidateSuggestion(
                field_id="field_1",
                candidate_type=CandidateType.INSERT,
                crop_id="tomato",
                start_date=datetime(2024, 6, 1),
                area=500.0,
                expected_profit=150000.0,
                move_instruction=None
            ),
            CandidateSuggestion(
                field_id="field_1",
                candidate_type=CandidateType.MOVE,
                allocation_id="alloc_001",
                start_date=datetime(2024, 7, 1),
                area=300.0,
                expected_profit=200000.0,  # より高い利益
                move_instruction=None
            ),
            CandidateSuggestion(
                field_id="field_2",
                candidate_type=CandidateType.INSERT,
                crop_id="carrot",
                start_date=datetime(2024, 8, 1),
                area=400.0,
                expected_profit=100000.0,
                move_instruction=None
            )
        ]
        
        response = CandidateSuggestionResponseDTO(
            candidates=candidates,
            success=True,
            message="Success"
        )
        
        best_candidates = response.get_best_candidate_per_field()
        assert len(best_candidates) == 2
        
        # field_1の最良候補は利益200000.0のもの
        field_1_best = next(c for c in best_candidates if c.field_id == "field_1")
        assert field_1_best.expected_profit == 200000.0
        
        # field_2の最良候補は利益100000.0のもの
        field_2_best = next(c for c in best_candidates if c.field_id == "field_2")
        assert field_2_best.expected_profit == 100000.0
    
    def test_to_dict_conversion(self):
        """辞書形式への変換テスト"""
        candidates = [
            CandidateSuggestion(
                field_id="field_1",
                candidate_type=CandidateType.INSERT,
                crop_id="tomato",
                start_date=datetime(2024, 6, 1),
                area=500.0,
                expected_profit=150000.0,
                move_instruction=None
            )
        ]
        
        response = CandidateSuggestionResponseDTO(
            candidates=candidates,
            success=True,
            message="Success"
        )
        
        result = response.to_dict()
        
        assert result["success"] is True
        assert result["message"] == "Success"
        assert len(result["candidates"]) == 1
        assert result["candidates"][0]["field_id"] == "field_1"
