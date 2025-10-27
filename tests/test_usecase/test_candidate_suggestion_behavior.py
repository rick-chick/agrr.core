"""
CLI optimize candidates機能の動作確認テスト

このテストは、圃場ごとの最適挿入位置が正しく返されることを確認します。
- 3つの圃場があって、1つの作物を選んだ時にmovesが3つ返ってくるか
- 1つの圃場があって、1つの作物を選んだ時にmovesが1つ返ってくるか
- 3つの圃場があって2つしか最適な挿入位置が見つからないとき2つのmovesが返ってくるか
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta

from agrr_core.usecase.interactors.candidate_suggestion_interactor import CandidateSuggestionInteractor
from agrr_core.usecase.dto.candidate_suggestion_request_dto import CandidateSuggestionRequestDTO
from agrr_core.entity.entities.candidate_suggestion_entity import CandidateSuggestion, CandidateType
from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.crop_profile_entity import CropProfile
from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.entity.entities.field_schedule_entity import FieldSchedule


class TestCandidateSuggestionBehavior:
    """候補リスト提示機能の動作確認テスト"""
    
    @pytest.mark.asyncio
    async def test_three_fields_one_crop_returns_three_candidates(self):
        """3つの圃場があって、1つの作物を選んだ時にmovesが3つ返ってくることを確認"""
        # Arrange
        interactor = self._create_interactor()
        
        # 3つの圃場をモック
        fields = [
            Field(field_id="field_1", name="Field 1", area=100.0, daily_fixed_cost=1000.0, location="Tokyo"),
            Field(field_id="field_2", name="Field 2", area=150.0, daily_fixed_cost=1500.0, location="Tokyo"),
            Field(field_id="field_3", name="Field 3", area=200.0, daily_fixed_cost=2000.0, location="Tokyo")
        ]
        
        # 1つの作物をモック
        crops = [
            CropProfile(
                crop=Crop(crop_id="tomato", name="tomato", variety=None, area_per_unit=0.25, revenue_per_area=1800, max_revenue=None, groups=["Solanaceae"]),
                stage_requirements=[]
            )
        ]
        
        # 空の配分結果をモック
        allocation_result = Mock()
        allocation_result.field_schedules = []
        
        # ゲートウェイをモック
        interactor._allocation_result_gateway.get = AsyncMock(return_value=allocation_result)
        interactor._field_gateway.get_all = AsyncMock(return_value=fields)
        interactor._crop_gateway.get_all = AsyncMock(return_value=crops)
        interactor._weather_gateway.get = AsyncMock(return_value=[{"time": "2024-04-01", "temperature_2m_max": 20.0, "temperature_2m_min": 10.0}])
        
        # 候補生成をモック（各圃場に1つずつ候補を返す）
        interactor._generate_candidates = AsyncMock(return_value=[
            CandidateSuggestion(field_id="field_1", candidate_type=CandidateType.INSERT, crop_id="tomato", start_date=datetime(2024, 4, 1), area=50.0, expected_profit=1000.0, move_instruction=None),
            CandidateSuggestion(field_id="field_2", candidate_type=CandidateType.INSERT, crop_id="tomato", start_date=datetime(2024, 4, 15), area=75.0, expected_profit=1200.0, move_instruction=None),
            CandidateSuggestion(field_id="field_3", candidate_type=CandidateType.INSERT, crop_id="tomato", start_date=datetime(2024, 5, 1), area=100.0, expected_profit=1500.0, move_instruction=None)
        ])
        
        request = CandidateSuggestionRequestDTO(
            target_crop_id="tomato",
            planning_period_start=datetime(2024, 4, 1),
            planning_period_end=datetime(2024, 10, 31)
        )
        
        # Act
        response = await interactor.execute(request)
        
        # Assert
        assert response.success
        assert len(response.candidates) == 3
        assert all(candidate.field_id in ["field_1", "field_2", "field_3"] for candidate in response.candidates)
        assert len(set(candidate.field_id for candidate in response.candidates)) == 3  # 各圃場に1つずつ
    
    @pytest.mark.asyncio
    async def test_one_field_one_crop_returns_one_candidate(self):
        """1つの圃場があって、1つの作物を選んだ時にmovesが1つ返ってくることを確認"""
        # Arrange
        interactor = self._create_interactor()
        
        # 1つの圃場をモック
        fields = [
            Field(field_id="field_1", name="Field 1", area=100.0, daily_fixed_cost=1000.0, location="Tokyo")
        ]
        
        # 1つの作物をモック
        crops = [
            CropProfile(
                crop=Crop(crop_id="tomato", name="tomato", variety=None, area_per_unit=0.25, revenue_per_area=1800, max_revenue=None, groups=["Solanaceae"]),
                stage_requirements=[]
            )
        ]
        
        # 空の配分結果をモック
        allocation_result = Mock()
        allocation_result.field_schedules = []
        
        # ゲートウェイをモック
        interactor._allocation_result_gateway.get = AsyncMock(return_value=allocation_result)
        interactor._field_gateway.get_all = AsyncMock(return_value=fields)
        interactor._crop_gateway.get_all = AsyncMock(return_value=crops)
        interactor._weather_gateway.get = AsyncMock(return_value=[{"time": "2024-04-01", "temperature_2m_max": 20.0, "temperature_2m_min": 10.0}])
        
        # 候補生成をモック（1つの圃場に1つの候補を返す）
        interactor._generate_candidates = AsyncMock(return_value=[
            CandidateSuggestion(field_id="field_1", candidate_type=CandidateType.INSERT, crop_id="tomato", start_date=datetime(2024, 4, 1), area=50.0, expected_profit=1000.0, move_instruction=None)
        ])
        
        request = CandidateSuggestionRequestDTO(
            target_crop_id="tomato",
            planning_period_start=datetime(2024, 4, 1),
            planning_period_end=datetime(2024, 10, 31)
        )
        
        # Act
        response = await interactor.execute(request)
        
        # Assert
        assert response.success
        assert len(response.candidates) == 1
        assert response.candidates[0].field_id == "field_1"
    
    @pytest.mark.asyncio
    async def test_three_fields_two_optimal_candidates_returns_two_candidates(self):
        """3つの圃場があって2つしか最適な挿入位置が見つからないとき2つのmovesが返ってくることを確認"""
        # Arrange
        interactor = self._create_interactor()
        
        # 3つの圃場をモック
        fields = [
            Field(field_id="field_1", name="Field 1", area=100.0, daily_fixed_cost=1000.0, location="Tokyo"),
            Field(field_id="field_2", name="Field 2", area=150.0, daily_fixed_cost=1500.0, location="Tokyo"),
            Field(field_id="field_3", name="Field 3", area=200.0, daily_fixed_cost=2000.0, location="Tokyo")
        ]
        
        # 1つの作物をモック
        crops = [
            CropProfile(
                crop=Crop(crop_id="tomato", name="tomato", variety=None, area_per_unit=0.25, revenue_per_area=1800, max_revenue=None, groups=["Solanaceae"]),
                stage_requirements=[]
            )
        ]
        
        # 空の配分結果をモック
        allocation_result = Mock()
        allocation_result.field_schedules = []
        
        # ゲートウェイをモック
        interactor._allocation_result_gateway.get = AsyncMock(return_value=allocation_result)
        interactor._field_gateway.get_all = AsyncMock(return_value=fields)
        interactor._crop_gateway.get_all = AsyncMock(return_value=crops)
        interactor._weather_gateway.get = AsyncMock(return_value=[{"time": "2024-04-01", "temperature_2m_max": 20.0, "temperature_2m_min": 10.0}])
        
        # 候補生成をモック（2つの圃場にのみ候補を返す）
        interactor._generate_candidates = AsyncMock(return_value=[
            CandidateSuggestion(field_id="field_1", candidate_type=CandidateType.INSERT, crop_id="tomato", start_date=datetime(2024, 4, 1), area=50.0, expected_profit=1000.0, move_instruction=None),
            CandidateSuggestion(field_id="field_3", candidate_type=CandidateType.INSERT, crop_id="tomato", start_date=datetime(2024, 5, 1), area=100.0, expected_profit=1500.0, move_instruction=None)
        ])
        
        request = CandidateSuggestionRequestDTO(
            target_crop_id="tomato",
            planning_period_start=datetime(2024, 4, 1),
            planning_period_end=datetime(2024, 10, 31)
        )
        
        # Act
        response = await interactor.execute(request)
        
        # Assert
        assert response.success
        assert len(response.candidates) == 2
        assert all(candidate.field_id in ["field_1", "field_3"] for candidate in response.candidates)
        assert len(set(candidate.field_id for candidate in response.candidates)) == 2  # 2つの圃場に1つずつ
    
    @pytest.mark.asyncio
    async def test_select_best_candidates_per_field_logic(self):
        """圃場ごとの最良候補選択ロジックを直接テスト"""
        # Arrange
        interactor = self._create_interactor()
        
        # 複数の候補を作成（同じ圃場に複数の候補がある場合）
        candidates = [
            CandidateSuggestion(field_id="field_1", candidate_type=CandidateType.INSERT, crop_id="tomato", start_date=datetime(2024, 4, 1), area=50.0, expected_profit=1000.0, move_instruction=None),
            CandidateSuggestion(field_id="field_1", candidate_type=CandidateType.INSERT, crop_id="tomato", start_date=datetime(2024, 4, 15), area=75.0, expected_profit=1200.0, move_instruction=None),  # より高い利益
            CandidateSuggestion(field_id="field_2", candidate_type=CandidateType.INSERT, crop_id="tomato", start_date=datetime(2024, 5, 1), area=100.0, expected_profit=1500.0, move_instruction=None),
            CandidateSuggestion(field_id="field_2", candidate_type=CandidateType.INSERT, crop_id="tomato", start_date=datetime(2024, 5, 15), area=80.0, expected_profit=800.0, move_instruction=None),  # より低い利益
            CandidateSuggestion(field_id="field_3", candidate_type=CandidateType.INSERT, crop_id="tomato", start_date=datetime(2024, 6, 1), area=90.0, expected_profit=2000.0, move_instruction=None)
        ]
        
        # Act
        best_candidates = interactor._select_best_candidates_per_field(candidates)
        
        # Assert
        assert len(best_candidates) == 3  # 3つの圃場それぞれに1つずつ
        
        # field_1の最良候補（利益1200.0）が選択されている
        field_1_candidate = next(c for c in best_candidates if c.field_id == "field_1")
        assert field_1_candidate.expected_profit == 1200.0
        
        # field_2の最良候補（利益1500.0）が選択されている
        field_2_candidate = next(c for c in best_candidates if c.field_id == "field_2")
        assert field_2_candidate.expected_profit == 1500.0
        
        # field_3の候補（利益2000.0）が選択されている
        field_3_candidate = next(c for c in best_candidates if c.field_id == "field_3")
        assert field_3_candidate.expected_profit == 2000.0
    
    def _create_interactor(self):
        """テスト用のInteractorインスタンスを作成"""
        # モックゲートウェイを作成
        allocation_result_gateway = Mock()
        field_gateway = Mock()
        crop_gateway = Mock()
        weather_gateway = Mock()
        interaction_rule_gateway = Mock()
        
        # Interactorを作成
        interactor = CandidateSuggestionInteractor(
            allocation_result_gateway=allocation_result_gateway,
            field_gateway=field_gateway,
            crop_gateway=crop_gateway,
            weather_gateway=weather_gateway,
            interaction_rule_gateway=interaction_rule_gateway
        )
        
        return interactor
