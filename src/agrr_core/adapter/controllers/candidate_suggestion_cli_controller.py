"""
候補リスト提示CLI Controller

このモジュールは候補リスト提示機能のCLI Controllerを実装します。
既存のoptimizeコマンドのサブコマンドとして統合されます。
"""
import argparse
from datetime import datetime
from typing import Optional
from agrr_core.adapter.controllers.allocation_adjust_cli_controller import AllocationAdjustCliController
from agrr_core.usecase.interactors.candidate_suggestion_interactor import CandidateSuggestionInteractor
from agrr_core.usecase.dto.candidate_suggestion_request_dto import CandidateSuggestionRequestDTO
from agrr_core.usecase.gateways.allocation_result_gateway import AllocationResultGateway
from agrr_core.usecase.gateways.field_gateway import FieldGateway
from agrr_core.usecase.gateways.crop_gateway import CropGateway
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway
from agrr_core.usecase.gateways.interaction_rule_gateway import InteractionRuleGateway
from agrr_core.adapter.presenters.candidate_suggestion_cli_presenter import CandidateSuggestionCliPresenter


class CandidateSuggestionCliController:
    """
    候補リスト提示CLI Controller
    
    既存のoptimizeコマンドのサブコマンドとして統合されます。
    """
    
    def __init__(
        self,
        allocation_result_gateway: AllocationResultGateway,
        field_gateway: FieldGateway,
        crop_gateway: CropGateway,
        weather_gateway: WeatherGateway,
        presenter: CandidateSuggestionCliPresenter,
        interaction_rule_gateway: Optional[InteractionRuleGateway] = None
    ):
        """
        初期化
        
        Args:
            allocation_result_gateway: 最適化結果ゲートウェイ
            field_gateway: 圃場ゲートウェイ
            crop_gateway: 作物ゲートウェイ
            weather_gateway: 気象ゲートウェイ
            presenter: CLI Presenter
            interaction_rule_gateway: 相互作用ルールゲートウェイ（オプション）
        """
        self._allocation_result_gateway = allocation_result_gateway
        self._field_gateway = field_gateway
        self._crop_gateway = crop_gateway
        self._weather_gateway = weather_gateway
        self._interaction_rule_gateway = interaction_rule_gateway
        self._presenter = presenter
        
        # Interactorをインスタンス化
        self._interactor = CandidateSuggestionInteractor(
            allocation_result_gateway=allocation_result_gateway,
            field_gateway=field_gateway,
            crop_gateway=crop_gateway,
            weather_gateway=weather_gateway,
            interaction_rule_gateway=interaction_rule_gateway
        )
    
    def create_argument_parser(self) -> argparse.ArgumentParser:
        """
        引数パーサーを作成
        
        Returns:
            argparse.ArgumentParser: 引数パーサー
        """
        parser = argparse.ArgumentParser(
            description="Generate candidate suggestions for crop allocation optimization",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Basic usage
  agrr optimize candidates \\
    --allocation current_allocation.json \\
    --fields-file fields.json \\
    --crops-file crops.json \\
    --target-crop tomato \\
    --planning-start 2024-04-01 --planning-end 2024-10-31 \\
    --weather-file weather.json \\
    --output candidates.txt

  # With interaction rules
  agrr optimize candidates \\
    --allocation current_allocation.json \\
    --fields-file fields.json \\
    --crops-file crops.json \\
    --target-crop tomato \\
    --interaction-rules-file interaction_rules.json \\
    --planning-start 2024-04-01 --planning-end 2024-10-31 \\
    --weather-file weather.json \\
    --output candidates.txt

  # JSON output for adjust command
  agrr optimize candidates \\
    --allocation current_allocation.json \\
    --fields-file fields.json \\
    --crops-file crops.json \\
    --target-crop tomato \\
    --planning-start 2024-04-01 --planning-end 2024-10-31 \\
    --weather-file weather.json \\
    --output candidates.json \\
    --format json
            """
        )
        
        # 必須オプション
        parser.add_argument(
            "--allocation",
            required=True,
            help="Path to current allocation result file"
        )
        parser.add_argument(
            "--fields-file",
            required=True,
            help="Path to fields configuration file"
        )
        parser.add_argument(
            "--crops-file",
            required=True,
            help="Path to crops configuration file"
        )
        parser.add_argument(
            "--target-crop",
            required=True,
            help="Target crop ID for candidate generation"
        )
        parser.add_argument(
            "--planning-start",
            required=True,
            help="Planning period start date (YYYY-MM-DD)"
        )
        parser.add_argument(
            "--planning-end",
            required=True,
            help="Planning period end date (YYYY-MM-DD)"
        )
        parser.add_argument(
            "--weather-file",
            required=True,
            help="Path to weather data file"
        )
        parser.add_argument(
            "--output", "-o",
            required=True,
            help="Output file path"
        )
        
        # オプション
        parser.add_argument(
            "--interaction-rules-file",
            help="Path to interaction rules file (optional)"
        )
        parser.add_argument(
            "--format", "-fmt",
            choices=["table", "json"],
            default="table",
            help="Output format (default: table)"
        )
        
        return parser
    
    async def handle_candidates_command(self, args: argparse.Namespace) -> None:
        """
        候補生成コマンドを処理
        
        Args:
            args: コマンドライン引数
        """
        try:
            # 日付の解析
            planning_start = self._parse_date(args.planning_start)
            planning_end = self._parse_date(args.planning_end)
            
            # リクエストDTOを作成
            request = CandidateSuggestionRequestDTO(
                target_crop_id=args.target_crop,
                planning_period_start=planning_start,
                planning_period_end=planning_end
            )
            
            # Interactorを実行
            response = await self._interactor.execute(request)
            
            # Presenterで出力
            self._presenter.output_format = args.format
            await self._presenter.present(response, args.output)
            
        except ValueError as e:
            print(f"Error: Invalid date format: \"{e}\". Use YYYY-MM-DD (e.g., \"2024-04-01\")")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    def _parse_date(self, date_str: str) -> datetime:
        """
        日付文字列を解析
        
        Args:
            date_str: 日付文字列 (YYYY-MM-DD)
            
        Returns:
            datetime: 解析された日付
            
        Raises:
            ValueError: 無効な日付形式の場合
        """
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: \"{date_str}\". Use YYYY-MM-DD (e.g., \"2024-04-01\")")
