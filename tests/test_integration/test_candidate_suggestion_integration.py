"""
候補リスト提示機能の統合テスト

このモジュールは候補リスト提示機能の統合テストを実装します。
"""
import pytest
import asyncio
import json
import tempfile
import os
from datetime import datetime
from unittest.mock import MagicMock
from agrr_core.adapter.controllers.candidate_suggestion_cli_controller import CandidateSuggestionCliController
from agrr_core.adapter.presenters.candidate_suggestion_cli_presenter import CandidateSuggestionCliPresenter
from agrr_core.adapter.gateways.allocation_result_file_gateway import AllocationResultFileGateway
from agrr_core.adapter.gateways.field_file_gateway import FieldFileGateway
from agrr_core.adapter.gateways.crop_profile_file_gateway import CropProfileFileGateway
from agrr_core.adapter.gateways.weather_file_gateway import WeatherFileGateway
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
            file_repository=file_service,
            file_path=test_data_files['allocation_file']
        )
        
        field_gateway = FieldFileGateway(
            file_repository=file_service,
            file_path=test_data_files['fields_file']
        )
        
        crop_gateway = CropProfileFileGateway(
            file_repository=file_service,
            file_path=test_data_files['crops_file']
        )
        
        weather_gateway = WeatherFileGateway(
            file_repository=file_service,
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
