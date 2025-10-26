# 候補リスト提示機能 テスト設計書

## 概要

候補リスト提示機能のテスト設計書です。要件定義書に基づいて、単体テスト、統合テスト、パフォーマンステストを設計します。

## テスト戦略

### テストファースト原則
- 実装前にテストを設計・実装
- Clean Architectureに沿った各層の単体テスト
- パッチを使用せず、依存性注入によるテスト

### テスト層別設計
1. **Entity層テスト** - エンティティの振る舞いテスト
2. **UseCase層テスト** - ビジネスロジックテスト
3. **Adapter層テスト** - CLI、ファイル入出力テスト
4. **統合テスト** - エンドツーエンドテスト
5. **パフォーマンステスト** - 性能要件テスト

## テストケース設計

### 1. Entity層テスト

#### 1.1 CandidateSuggestion エンティティテスト

**ファイル**: `tests/test_entity/test_candidate_suggestion_entity.py`

```python
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
        field = Field(field_id="field_1", name="Field 1", area=1000.0, daily_fixed_cost=1000.0)
        crop = Crop(crop_id="tomato", name="Tomato", revenue_per_area=1500.0)
        
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
```

#### 1.2 CandidateType エンティティテスト

**ファイル**: `tests/test_entity/test_candidate_type_entity.py`

```python
import pytest
from agrr_core.entity.entities.candidate_suggestion_entity import CandidateType

class TestCandidateType:
    """CandidateType エンティティのテスト"""
    
    def test_candidate_type_values(self):
        """候補タイプの値テスト"""
        assert CandidateType.INSERT == "INSERT"
        assert CandidateType.MOVE == "MOVE"
    
    def test_candidate_type_string_representation(self):
        """候補タイプの文字列表現テスト"""
        assert str(CandidateType.INSERT) == "INSERT"
        assert str(CandidateType.MOVE) == "MOVE"
```

### 2. UseCase層テスト

#### 2.1 CandidateSuggestionInteractor テスト

**ファイル**: `tests/test_usecase/test_candidate_suggestion_interactor.py`

```python
import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from agrr_core.usecase.interactors.candidate_suggestion_interactor import CandidateSuggestionInteractor
from agrr_core.usecase.dto.candidate_suggestion_request_dto import CandidateSuggestionRequestDTO
from agrr_core.usecase.dto.candidate_suggestion_response_dto import CandidateSuggestionResponseDTO
from agrr_core.entity.entities.candidate_suggestion_entity import CandidateSuggestion, CandidateType

class TestCandidateSuggestionInteractor:
    """CandidateSuggestionInteractor のテスト"""
    
    @pytest.fixture
    def mock_gateways(self):
        """モックゲートウェイの作成"""
        return {
            'allocation_result_gateway': AsyncMock(),
            'field_gateway': AsyncMock(),
            'crop_gateway': AsyncMock(),
            'weather_gateway': AsyncMock(),
            'interaction_rule_gateway': AsyncMock(),
        }
    
    @pytest.fixture
    def interactor(self, mock_gateways):
        """Interactorのインスタンス作成"""
        return CandidateSuggestionInteractor(**mock_gateways)
    
    @pytest.mark.asyncio
    async def test_execute_success_with_insert_candidates(self, interactor, mock_gateways):
        """新しい作物挿入候補の生成テスト"""
        # モックデータの設定
        mock_gateways['allocation_result_gateway'].get.return_value = self._create_mock_allocation_result()
        mock_gateways['field_gateway'].get_all.return_value = self._create_mock_fields()
        mock_gateways['crop_gateway'].get_all.return_value = self._create_mock_crops()
        mock_gateways['weather_gateway'].get_all.return_value = self._create_mock_weather()
        
        # リクエスト作成
        request = CandidateSuggestionRequestDTO(
            target_crop_id="tomato",
            planning_period_start=datetime(2024, 4, 1),
            planning_period_end=datetime(2024, 10, 31)
        )
        
        # 実行
        response = await interactor.execute(request)
        
        # 検証
        assert isinstance(response, CandidateSuggestionResponseDTO)
        assert response.success is True
        assert len(response.candidates) > 0
        
        # 挿入候補が含まれていることを確認
        insert_candidates = [c for c in response.candidates if c.candidate_type == CandidateType.INSERT]
        assert len(insert_candidates) > 0
    
    @pytest.mark.asyncio
    async def test_execute_success_with_move_candidates(self, interactor, mock_gateways):
        """既存作物移動候補の生成テスト"""
        # モックデータの設定
        mock_gateways['allocation_result_gateway'].get.return_value = self._create_mock_allocation_result_with_allocations()
        mock_gateways['field_gateway'].get_all.return_value = self._create_mock_fields()
        mock_gateways['crop_gateway'].get_all.return_value = self._create_mock_crops()
        mock_gateways['weather_gateway'].get_all.return_value = self._create_mock_weather()
        
        # リクエスト作成
        request = CandidateSuggestionRequestDTO(
            target_crop_id="tomato",
            planning_period_start=datetime(2024, 4, 1),
            planning_period_end=datetime(2024, 10, 31)
        )
        
        # 実行
        response = await interactor.execute(request)
        
        # 検証
        assert isinstance(response, CandidateSuggestionResponseDTO)
        assert response.success is True
        assert len(response.candidates) > 0
        
        # 移動候補が含まれていることを確認
        move_candidates = [c for c in response.candidates if c.candidate_type == CandidateType.MOVE]
        assert len(move_candidates) > 0
    
    @pytest.mark.asyncio
    async def test_execute_no_allocation_result(self, interactor, mock_gateways):
        """既存の最適化結果がない場合のテスト"""
        # モックデータの設定（結果なし）
        mock_gateways['allocation_result_gateway'].get.return_value = None
        
        # リクエスト作成
        request = CandidateSuggestionRequestDTO(
            target_crop_id="tomato",
            planning_period_start=datetime(2024, 4, 1),
            planning_period_end=datetime(2024, 10, 31)
        )
        
        # 実行
        response = await interactor.execute(request)
        
        # 検証
        assert isinstance(response, CandidateSuggestionResponseDTO)
        assert response.success is False
        assert "Failed to load current optimization result" in response.message
    
    @pytest.mark.asyncio
    async def test_execute_target_crop_not_found(self, interactor, mock_gateways):
        """対象作物が見つからない場合のテスト"""
        # モックデータの設定
        mock_gateways['allocation_result_gateway'].get.return_value = self._create_mock_allocation_result()
        mock_gateways['field_gateway'].get_all.return_value = self._create_mock_fields()
        mock_gateways['crop_gateway'].get_all.return_value = self._create_mock_crops()  # tomatoなし
        mock_gateways['weather_gateway'].get_all.return_value = self._create_mock_weather()
        
        # リクエスト作成
        request = CandidateSuggestionRequestDTO(
            target_crop_id="nonexistent_crop",
            planning_period_start=datetime(2024, 4, 1),
            planning_period_end=datetime(2024, 10, 31)
        )
        
        # 実行
        response = await interactor.execute(request)
        
        # 検証
        assert isinstance(response, CandidateSuggestionResponseDTO)
        assert response.success is False
        assert "Target crop not found" in response.message
    
    def _create_mock_allocation_result(self):
        """モック最適化結果の作成"""
        # 実装時に実際のエンティティを使用
        pass
    
    def _create_mock_allocation_result_with_allocations(self):
        """既存配分を含むモック最適化結果の作成"""
        # 実装時に実際のエンティティを使用
        pass
    
    def _create_mock_fields(self):
        """モック圃場データの作成"""
        # 実装時に実際のエンティティを使用
        pass
    
    def _create_mock_crops(self):
        """モック作物データの作成"""
        # 実装時に実際のエンティティを使用
        pass
    
    def _create_mock_weather(self):
        """モック気象データの作成"""
        # 実装時に実際のエンティティを使用
        pass
```

#### 2.2 DTOテスト

**ファイル**: `tests/test_usecase/test_candidate_suggestion_dto.py`

```python
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
    
    def test_request_dto_validation(self):
        """リクエストDTOのバリデーションテスト"""
        # 必須フィールドのテスト
        with pytest.raises(ValueError):
            CandidateSuggestionRequestDTO(
                target_crop_id="",  # 空文字
                planning_period_start=datetime(2024, 4, 1),
                planning_period_end=datetime(2024, 10, 31)
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
```

### 3. Adapter層テスト

#### 3.1 CLI Controllerテスト

**ファイル**: `tests/test_adapter/test_candidate_suggestion_cli_controller.py`

```python
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from agrr_core.adapter.controllers.candidate_suggestion_cli_controller import CandidateSuggestionCliController

class TestCandidateSuggestionCliController:
    """CandidateSuggestionCliController のテスト"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """モック依存関係の作成"""
        return {
            'allocation_result_gateway': AsyncMock(),
            'field_gateway': AsyncMock(),
            'crop_gateway': AsyncMock(),
            'weather_gateway': AsyncMock(),
            'interaction_rule_gateway': AsyncMock(),
            'presenter': MagicMock(),
        }
    
    @pytest.fixture
    def controller(self, mock_dependencies):
        """Controllerのインスタンス作成"""
        return CandidateSuggestionCliController(**mock_dependencies)
    
    def test_create_argument_parser(self, controller):
        """引数パーサーの作成テスト"""
        parser = controller.create_argument_parser()
        
        # 必須オプションの確認
        assert parser._actions[1].dest == 'allocation'  # --allocation
        assert parser._actions[2].dest == 'fields_file'  # --fields-file
        assert parser._actions[3].dest == 'crops_file'  # --crops-file
        assert parser._actions[4].dest == 'target_crop'  # --target-crop
        assert parser._actions[5].dest == 'planning_start'  # --planning-start
        assert parser._actions[6].dest == 'planning_end'  # --planning-end
        assert parser._actions[7].dest == 'weather_file'  # --weather-file
        assert parser._actions[8].dest == 'output'  # --output
    
    @pytest.mark.asyncio
    async def test_handle_candidates_command_success(self, controller, mock_dependencies):
        """候補生成コマンドの成功テスト"""
        # モックデータの設定
        mock_dependencies['allocation_result_gateway'].get.return_value = self._create_mock_allocation_result()
        mock_dependencies['field_gateway'].get_all.return_value = self._create_mock_fields()
        mock_dependencies['crop_gateway'].get_all.return_value = self._create_mock_crops()
        mock_dependencies['weather_gateway'].get_all.return_value = self._create_mock_weather()
        
        # モック引数
        args = MagicMock()
        args.allocation = "test_allocation.json"
        args.fields_file = "test_fields.json"
        args.crops_file = "test_crops.json"
        args.target_crop = "tomato"
        args.planning_start = "2024-04-01"
        args.planning_end = "2024-10-31"
        args.weather_file = "test_weather.json"
        args.output = "test_output.txt"
        args.format = "table"
        args.interaction_rules_file = None
        
        # 実行
        await controller.handle_candidates_command(args)
        
        # 検証
        mock_dependencies['presenter'].present.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_candidates_command_invalid_date(self, controller):
        """無効な日付形式のテスト"""
        # モック引数（無効な日付）
        args = MagicMock()
        args.planning_start = "invalid-date"
        args.planning_end = "2024-10-31"
        
        # 実行
        with patch('builtins.print') as mock_print:
            await controller.handle_candidates_command(args)
            mock_print.assert_called_with("Error: Invalid date format: \"invalid-date\". Use YYYY-MM-DD (e.g., \"2024-04-01\")")
    
    def _create_mock_allocation_result(self):
        """モック最適化結果の作成"""
        pass
    
    def _create_mock_fields(self):
        """モック圃場データの作成"""
        pass
    
    def _create_mock_crops(self):
        """モック作物データの作成"""
        pass
    
    def _create_mock_weather(self):
        """モック気象データの作成"""
        pass
```

#### 3.2 CLI Presenterテスト

**ファイル**: `tests/test_adapter/test_candidate_suggestion_cli_presenter.py`

```python
import pytest
from unittest.mock import patch, mock_open
from agrr_core.adapter.presenters.candidate_suggestion_cli_presenter import CandidateSuggestionCliPresenter
from agrr_core.usecase.dto.candidate_suggestion_response_dto import CandidateSuggestionResponseDTO
from agrr_core.entity.entities.candidate_suggestion_entity import CandidateSuggestion, CandidateType
from datetime import datetime

class TestCandidateSuggestionCliPresenter:
    """CandidateSuggestionCliPresenter のテスト"""
    
    @pytest.fixture
    def presenter(self):
        """Presenterのインスタンス作成"""
        return CandidateSuggestionCliPresenter()
    
    @pytest.fixture
    def mock_candidates_response(self):
        """モック候補レスポンスの作成"""
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
        
        return CandidateSuggestionResponseDTO(
            candidates=candidates,
            success=True,
            message="Successfully generated candidates"
        )
    
    def test_present_table_format(self, presenter, mock_candidates_response):
        """Table形式での出力テスト"""
        presenter.output_format = "table"
        
        with patch('builtins.open', mock_open()) as mock_file:
            presenter.present(mock_candidates_response, "test_output.txt")
            
            # ファイルが開かれたことを確認
            mock_file.assert_called_once_with("test_output.txt", "w", encoding="utf-8")
            
            # 書き込み内容の確認
            written_content = ''.join(call.args[0] for call in mock_file().write.call_args_list)
            assert "候補リスト提示結果" in written_content
            assert "field_1" in written_content
            assert "field_2" in written_content
            assert "INSERT" in written_content
            assert "MOVE" in written_content
    
    def test_present_json_format(self, presenter, mock_candidates_response):
        """JSON形式での出力テスト"""
        presenter.output_format = "json"
        
        with patch('builtins.open', mock_open()) as mock_file:
            presenter.present(mock_candidates_response, "test_output.json")
            
            # ファイルが開かれたことを確認
            mock_file.assert_called_once_with("test_output.json", "w", encoding="utf-8")
            
            # JSON形式で書き込まれたことを確認
            written_content = ''.join(call.args[0] for call in mock_file().write.call_args_list)
            assert '"candidates"' in written_content
            assert '"field_id"' in written_content
            assert '"candidate_type"' in written_content
    
    def test_present_failure_response(self, presenter):
        """失敗レスポンスの出力テスト"""
        failure_response = CandidateSuggestionResponseDTO(
            candidates=[],
            success=False,
            message="Failed to generate candidates"
        )
        
        presenter.output_format = "table"
        
        with patch('builtins.open', mock_open()) as mock_file:
            presenter.present(failure_response, "test_output.txt")
            
            # エラーメッセージが含まれることを確認
            written_content = ''.join(call.args[0] for call in mock_file().write.call_args_list)
            assert "Failed to generate candidates" in written_content
```

### 4. 統合テスト

#### 4.1 エンドツーエンドテスト

**ファイル**: `tests/test_integration/test_candidate_suggestion_integration.py`

```python
import pytest
import asyncio
import json
import tempfile
import os
from datetime import datetime
from agrr_core.adapter.controllers.candidate_suggestion_cli_controller import CandidateSuggestionCliController
from agrr_core.adapter.presenters.candidate_suggestion_cli_presenter import CandidateSuggestionCliPresenter
from agrr_core.adapter.gateways.allocation_result_file_gateway import AllocationResultFileGateway
from agrr_core.adapter.gateways.field_file_gateway import FieldFileGateway
from agrr_core.adapter.gateways.crop_profile_file_gateway import CropProfileFileGateway
from agrr_core.adapter.gateways.weather_file_gateway import WeatherFileGateway
from agrr_core.adapter.gateways.interaction_rule_file_gateway import InteractionRuleFileGateway
from agrr_core.framework.services.io.file_service import FileService

class TestCandidateSuggestionIntegration:
    """候補リスト提示機能の統合テスト"""
    
    @pytest.fixture
    def temp_dir(self):
        """一時ディレクトリの作成"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def test_data_files(self, temp_dir):
        """テストデータファイルの作成"""
        # 既存の最適化結果ファイル
        allocation_file = os.path.join(temp_dir, "allocation.json")
        with open(allocation_file, "w", encoding="utf-8") as f:
            json.dump(self._create_test_allocation_data(), f, ensure_ascii=False, indent=2)
        
        # 圃場設定ファイル
        fields_file = os.path.join(temp_dir, "fields.json")
        with open(fields_file, "w", encoding="utf-8") as f:
            json.dump(self._create_test_fields_data(), f, ensure_ascii=False, indent=2)
        
        # 作物設定ファイル
        crops_file = os.path.join(temp_dir, "crops.json")
        with open(crops_file, "w", encoding="utf-8") as f:
            json.dump(self._create_test_crops_data(), f, ensure_ascii=False, indent=2)
        
        # 気象データファイル
        weather_file = os.path.join(temp_dir, "weather.json")
        with open(weather_file, "w", encoding="utf-8") as f:
            json.dump(self._create_test_weather_data(), f, ensure_ascii=False, indent=2)
        
        return {
            'allocation_file': allocation_file,
            'fields_file': fields_file,
            'crops_file': crops_file,
            'weather_file': weather_file,
        }
    
    @pytest.fixture
    def controller_with_gateways(self, test_data_files):
        """ゲートウェイ付きControllerの作成"""
        file_service = FileService()
        
        allocation_gateway = AllocationResultFileGateway(
            file_service=file_service,
            file_path=test_data_files['allocation_file']
        )
        
        field_gateway = FieldFileGateway(
            file_service=file_service,
            file_path=test_data_files['fields_file']
        )
        
        crop_gateway = CropProfileFileGateway(
            file_service=file_service,
            file_path=test_data_files['crops_file']
        )
        
        weather_gateway = WeatherFileGateway(
            file_service=file_service,
            file_path=test_data_files['weather_file']
        )
        
        presenter = CandidateSuggestionCliPresenter()
        
        return CandidateSuggestionCliController(
            allocation_result_gateway=allocation_gateway,
            field_gateway=field_gateway,
            crop_gateway=crop_gateway,
            weather_gateway=weather_gateway,
            presenter=presenter,
            interaction_rule_gateway=None,
        )
    
    @pytest.mark.asyncio
    async def test_end_to_end_candidate_generation(self, controller_with_gateways, temp_dir):
        """エンドツーエンド候補生成テスト"""
        # 出力ファイル
        output_file = os.path.join(temp_dir, "candidates.txt")
        
        # モック引数
        args = MagicMock()
        args.allocation = "allocation.json"
        args.fields_file = "fields.json"
        args.crops_file = "crops.json"
        args.target_crop = "tomato"
        args.planning_start = "2024-04-01"
        args.planning_end = "2024-10-31"
        args.weather_file = "weather.json"
        args.output = output_file
        args.format = "table"
        args.interaction_rules_file = None
        
        # 実行
        await controller_with_gateways.handle_candidates_command(args)
        
        # 出力ファイルの確認
        assert os.path.exists(output_file)
        
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "候補リスト提示結果" in content
            assert "field_1" in content or "field_2" in content
    
    @pytest.mark.asyncio
    async def test_end_to_end_json_output(self, controller_with_gateways, temp_dir):
        """エンドツーエンドJSON出力テスト"""
        # 出力ファイル
        output_file = os.path.join(temp_dir, "candidates.json")
        
        # モック引数
        args = MagicMock()
        args.allocation = "allocation.json"
        args.fields_file = "fields.json"
        args.crops_file = "crops.json"
        args.target_crop = "tomato"
        args.planning_start = "2024-04-01"
        args.planning_end = "2024-10-31"
        args.weather_file = "weather.json"
        args.output = output_file
        args.format = "json"
        args.interaction_rules_file = None
        
        # 実行
        await controller_with_gateways.handle_candidates_command(args)
        
        # 出力ファイルの確認
        assert os.path.exists(output_file)
        
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            data = json.loads(content)
            assert "candidates" in data
            assert isinstance(data["candidates"], list)
    
    def _create_test_allocation_data(self):
        """テスト用最適化結果データの作成"""
        return {
            "optimization_result": {
                "optimization_id": "test_opt_001",
                "field_schedules": [
                    {
                        "field_id": "field_1",
                        "field_name": "Field 1",
                        "allocations": [
                            {
                                "allocation_id": "alloc_001",
                                "crop_id": "carrot",
                                "crop_name": "Carrot",
                                "area_used": 300.0,
                                "start_date": "2024-05-01",
                                "completion_date": "2024-07-15",
                                "growth_days": 75,
                                "total_cost": 75000,
                                "expected_revenue": 120000,
                                "profit": 45000
                            }
                        ]
                    }
                ],
                "total_profit": 45000.0
            }
        }
    
    def _create_test_fields_data(self):
        """テスト用圃場データの作成"""
        return {
            "fields": [
                {
                    "field_id": "field_1",
                    "field_name": "Field 1",
                    "area": 1000.0,
                    "daily_fixed_cost": 1000.0
                },
                {
                    "field_id": "field_2",
                    "field_name": "Field 2",
                    "area": 800.0,
                    "daily_fixed_cost": 800.0
                }
            ]
        }
    
    def _create_test_crops_data(self):
        """テスト用作物データの作成"""
        return {
            "crops": [
                {
                    "crop_id": "tomato",
                    "name": "Tomato",
                    "area_per_unit": 1.0,
                    "variety": "default",
                    "revenue_per_area": 1500.0,
                    "max_revenue": 1000000.0,
                    "groups": ["solanaceae"]
                },
                {
                    "crop_id": "carrot",
                    "name": "Carrot",
                    "area_per_unit": 1.0,
                    "variety": "default",
                    "revenue_per_area": 1200.0,
                    "max_revenue": 800000.0,
                    "groups": ["umbelliferae"]
                }
            ]
        }
    
    def _create_test_weather_data(self):
        """テスト用気象データの作成"""
        return {
            "latitude": 35.6762,
            "longitude": 139.6503,
            "elevation": 40.0,
            "timezone": "Asia/Tokyo",
            "data": [
                {
                    "time": "2024-04-01",
                    "temperature_2m_max": 20.0,
                    "temperature_2m_min": 10.0,
                    "temperature_2m_mean": 15.0
                },
                {
                    "time": "2024-04-02",
                    "temperature_2m_max": 22.0,
                    "temperature_2m_min": 12.0,
                    "temperature_2m_mean": 17.0
                }
            ]
        }
```

### 5. パフォーマンステスト

#### 5.1 性能要件テスト

**ファイル**: `tests/test_performance/test_candidate_suggestion_performance.py`

```python
import pytest
import asyncio
import time
import tempfile
import os
from datetime import datetime
from agrr_core.usecase.interactors.candidate_suggestion_interactor import CandidateSuggestionInteractor
from agrr_core.usecase.dto.candidate_suggestion_request_dto import CandidateSuggestionRequestDTO

class TestCandidateSuggestionPerformance:
    """候補リスト提示機能のパフォーマンステスト"""
    
    @pytest.mark.asyncio
    async def test_performance_with_large_dataset(self):
        """大量データでの性能テスト"""
        # 大量の圃場・作物データを作成
        large_fields = self._create_large_fields_dataset(100)  # 100圃場
        large_crops = self._create_large_crops_dataset(50)     # 50作物
        
        # モックゲートウェイの設定
        mock_gateways = self._create_mock_gateways_with_large_data(large_fields, large_crops)
        
        # Interactorの作成
        interactor = CandidateSuggestionInteractor(**mock_gateways)
        
        # リクエスト作成
        request = CandidateSuggestionRequestDTO(
            target_crop_id="tomato",
            planning_period_start=datetime(2024, 4, 1),
            planning_period_end=datetime(2024, 10, 31)
        )
        
        # 実行時間測定
        start_time = time.time()
        response = await interactor.execute(request)
        execution_time = time.time() - start_time
        
        # 性能要件の確認
        assert execution_time < 60.0  # 1分以内
        assert response.success is True
        assert len(response.candidates) > 0
    
    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """メモリ使用量テスト"""
        import psutil
        import os
        
        # プロセス取得
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 大量データでの実行
        large_fields = self._create_large_fields_dataset(50)
        large_crops = self._create_large_crops_dataset(25)
        mock_gateways = self._create_mock_gateways_with_large_data(large_fields, large_crops)
        
        interactor = CandidateSuggestionInteractor(**mock_gateways)
        
        request = CandidateSuggestionRequestDTO(
            target_crop_id="tomato",
            planning_period_start=datetime(2024, 4, 1),
            planning_period_end=datetime(2024, 10, 31)
        )
        
        response = await interactor.execute(request)
        
        # メモリ使用量の確認
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        assert memory_increase < 500  # 500MB以内の増加
        assert response.success is True
    
    def _create_large_fields_dataset(self, count):
        """大量圃場データセットの作成"""
        fields = []
        for i in range(count):
            fields.append({
                "field_id": f"field_{i}",
                "field_name": f"Field {i}",
                "area": 1000.0 + i * 100,
                "daily_fixed_cost": 1000.0 + i * 50
            })
        return fields
    
    def _create_large_crops_dataset(self, count):
        """大量作物データセットの作成"""
        crops = []
        crop_names = ["tomato", "carrot", "lettuce", "cabbage", "onion"]
        for i in range(count):
            crop_name = crop_names[i % len(crop_names)]
            crops.append({
                "crop_id": f"{crop_name}_{i}",
                "name": f"{crop_name.title()} {i}",
                "area_per_unit": 1.0,
                "variety": "default",
                "revenue_per_area": 1000.0 + i * 100,
                "max_revenue": 1000000.0,
                "groups": ["test_group"]
            })
        return crops
    
    def _create_mock_gateways_with_large_data(self, fields, crops):
        """大量データ付きモックゲートウェイの作成"""
        # 実装時に詳細を記述
        pass
```

## テスト実行環境

### テストデータ
- `test_data/` ディレクトリにテスト用データファイルを配置
- 既存のテストデータを再利用（fields.json, crops.json, weather.json等）

### テスト実行コマンド
```bash
# 全テスト実行
pytest tests/test_candidate_suggestion/

# 単体テストのみ
pytest tests/test_entity/test_candidate_suggestion_entity.py
pytest tests/test_usecase/test_candidate_suggestion_interactor.py

# 統合テストのみ
pytest tests/test_integration/test_candidate_suggestion_integration.py

# パフォーマンステストのみ
pytest tests/test_performance/test_candidate_suggestion_performance.py

# カバレッジ付き実行
pytest --cov=agrr_core.usecase.interactors.candidate_suggestion_interactor tests/test_candidate_suggestion/
```

## テスト品質基準

### カバレッジ要件
- **Entity層**: 100%カバレッジ
- **UseCase層**: 95%以上カバレッジ
- **Adapter層**: 90%以上カバレッジ

### テスト実行時間
- **単体テスト**: 各テスト5秒以内
- **統合テスト**: 各テスト30秒以内
- **パフォーマンステスト**: 各テスト60秒以内

### テストデータ管理
- テストデータは`test_data/`ディレクトリに配置
- 既存のテストデータを可能な限り再利用
- 新しいテストデータは最小限に抑制

## 継続的インテグレーション

### GitHub Actions設定
```yaml
name: Candidate Suggestion Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.8
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Run tests
        run: pytest tests/test_candidate_suggestion/ --cov=agrr_core
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

## まとめ

このテスト設計書に基づいて、候補リスト提示機能の包括的なテストを実装します。テストファーストの原則に従い、実装前にテストを設計・実装することで、高品質な機能を提供できます。
