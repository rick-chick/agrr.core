# 候補リスト提示機能 API リファレンス

## 概要

候補リスト提示機能のAPIリファレンスです。Clean Architectureに従って実装された各層のAPIを説明します。

## Entity層

### CandidateSuggestion

候補提案エンティティです。

```python
from agrr_core.entity.entities.candidate_suggestion_entity import CandidateSuggestion, CandidateType
from datetime import datetime

# 新規挿入候補の作成
candidate = CandidateSuggestion(
    field_id="field_1",
    candidate_type=CandidateType.INSERT,
    crop_id="tomato",
    start_date=datetime(2024, 6, 1),
    area=500.0,
    expected_profit=150000.0,
    move_instruction=None
)

# 移動候補の作成
candidate = CandidateSuggestion(
    field_id="field_2",
    candidate_type=CandidateType.MOVE,
    allocation_id="alloc_001",
    start_date=datetime(2024, 7, 1),
    area=300.0,
    expected_profit=120000.0,
    move_instruction=None
)
```

**属性**:
- `field_id: str` - 圃場ID
- `candidate_type: CandidateType` - 候補タイプ（INSERT/MOVE）
- `crop_id: Optional[str]` - 作物ID（INSERT候補の場合）
- `allocation_id: Optional[str]` - 配分ID（MOVE候補の場合）
- `start_date: datetime` - 開始日
- `area: float` - 面積（m²）
- `expected_profit: float` - 期待利益
- `move_instruction: Optional[MoveInstruction]` - 移動指示

### CandidateType

候補タイプの列挙型です。

```python
from agrr_core.entity.entities.candidate_suggestion_entity import CandidateType

# 候補タイプの使用
if candidate.candidate_type == CandidateType.INSERT:
    print("新規挿入候補")
elif candidate.candidate_type == CandidateType.MOVE:
    print("移動候補")
```

**値**:
- `INSERT` - 新規挿入候補
- `MOVE` - 移動候補

## UseCase層

### CandidateSuggestionInteractor

候補リスト提示のビジネスロジックを実装するInteractorです。

```python
from agrr_core.usecase.interactors.candidate_suggestion_interactor import CandidateSuggestionInteractor
from agrr_core.usecase.dto.candidate_suggestion_request_dto import CandidateSuggestionRequestDTO
from datetime import datetime

# Interactorの初期化
interactor = CandidateSuggestionInteractor(
    allocation_result_gateway=allocation_gateway,
    field_gateway=field_gateway,
    crop_gateway=crop_gateway,
    weather_gateway=weather_gateway,
    interaction_rule_gateway=interaction_rule_gateway
)

# リクエストの作成
request = CandidateSuggestionRequestDTO(
    target_crop_id="tomato",
    planning_period_start=datetime(2024, 4, 1),
    planning_period_end=datetime(2024, 10, 31)
)

# 実行
response = await interactor.execute(request)
```

**メソッド**:
- `execute(request: CandidateSuggestionRequestDTO) -> CandidateSuggestionResponseDTO` - 候補生成の実行

### CandidateSuggestionRequestDTO

候補生成リクエストのDTOです。

```python
from agrr_core.usecase.dto.candidate_suggestion_request_dto import CandidateSuggestionRequestDTO
from datetime import datetime

request = CandidateSuggestionRequestDTO(
    target_crop_id="tomato",
    planning_period_start=datetime(2024, 4, 1),
    planning_period_end=datetime(2024, 10, 31)
)
```

**属性**:
- `target_crop_id: str` - 対象作物ID
- `planning_period_start: datetime` - 計画期間開始日
- `planning_period_end: datetime` - 計画期間終了日

### CandidateSuggestionResponseDTO

候補生成レスポンスのDTOです。

```python
from agrr_core.usecase.dto.candidate_suggestion_response_dto import CandidateSuggestionResponseDTO
from agrr_core.entity.entities.candidate_suggestion_entity import CandidateSuggestion

response = CandidateSuggestionResponseDTO(
    candidates=[candidate1, candidate2],
    success=True,
    message="Successfully generated candidates"
)
```

**属性**:
- `candidates: List[CandidateSuggestion]` - 生成された候補リスト
- `success: bool` - 成功フラグ
- `message: str` - メッセージ

## Adapter層

### CandidateSuggestionCliController

CLIコントローラーです。

```python
from agrr_core.adapter.controllers.candidate_suggestion_cli_controller import CandidateSuggestionCliController
import argparse

# Controllerの初期化
controller = CandidateSuggestionCliController(
    allocation_result_gateway=allocation_gateway,
    field_gateway=field_gateway,
    crop_gateway=crop_gateway,
    weather_gateway=weather_gateway,
    presenter=presenter,
    interaction_rule_gateway=interaction_rule_gateway
)

# 引数パーサーの作成
parser = controller.create_argument_parser()

# コマンドの実行
args = parser.parse_args(['--allocation', 'allocation.json', ...])
await controller.handle_candidates_command(args)
```

**メソッド**:
- `create_argument_parser() -> argparse.ArgumentParser` - 引数パーサーの作成
- `handle_candidates_command(args: argparse.Namespace) -> None` - 候補生成コマンドの処理

### CandidateSuggestionCliPresenter

CLIプレゼンターです。

```python
from agrr_core.adapter.presenters.candidate_suggestion_cli_presenter import CandidateSuggestionCliPresenter
from agrr_core.usecase.dto.candidate_suggestion_response_dto import CandidateSuggestionResponseDTO

# Presenterの初期化
presenter = CandidateSuggestionCliPresenter()

# 出力形式の設定
presenter.output_format = "table"  # または "json"

# 結果の表示
response = CandidateSuggestionResponseDTO(...)
presenter.present(response, "output.txt")
```

**メソッド**:
- `present(response: CandidateSuggestionResponseDTO, output_path: str) -> None` - 結果の表示

## Gateway層

### AllocationResultGateway

最適化結果のゲートウェイインターフェースです。

```python
from agrr_core.usecase.gateways.allocation_result_gateway import AllocationResultGateway

class MyAllocationResultGateway(AllocationResultGateway):
    async def get(self, optimization_id: str) -> Optional[Any]:
        # 最適化結果の取得実装
        pass
```

**メソッド**:
- `get(optimization_id: str) -> Optional[Any]` - 最適化結果の取得

### FieldGateway

圃場データのゲートウェイインターフェースです。

```python
from agrr_core.usecase.gateways.field_gateway import FieldGateway
from agrr_core.entity.entities.field_entity import Field

class MyFieldGateway(FieldGateway):
    async def get_all(self) -> List[Field]:
        # 圃場データの取得実装
        pass
```

**メソッド**:
- `get_all() -> List[Field]` - 全圃場データの取得

### CropGateway

作物データのゲートウェイインターフェースです。

```python
from agrr_core.usecase.gateways.crop_gateway import CropGateway
from agrr_core.entity.entities.crop_entity import Crop

class MyCropGateway(CropGateway):
    async def get_all(self) -> List[Crop]:
        # 作物データの取得実装
        pass
```

**メソッド**:
- `get_all() -> List[Crop]` - 全作物データの取得

### WeatherGateway

気象データのゲートウェイインターフェースです。

```python
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway

class MyWeatherGateway(WeatherGateway):
    async def get_all(self) -> List[Any]:
        # 気象データの取得実装
        pass
```

**メソッド**:
- `get_all() -> List[Any]` - 全気象データの取得

### InteractionRuleGateway

相互作用ルールのゲートウェイインターフェースです。

```python
from agrr_core.usecase.gateways.interaction_rule_gateway import InteractionRuleGateway
from agrr_core.entity.entities.interaction_rule_entity import InteractionRule

class MyInteractionRuleGateway(InteractionRuleGateway):
    async def get_all(self) -> List[InteractionRule]:
        # 相互作用ルールの取得実装
        pass
```

**メソッド**:
- `get_all() -> List[InteractionRule]` - 全相互作用ルールの取得

## 実装例

### 基本的な使用例

```python
import asyncio
from datetime import datetime
from agrr_core.usecase.interactors.candidate_suggestion_interactor import CandidateSuggestionInteractor
from agrr_core.usecase.dto.candidate_suggestion_request_dto import CandidateSuggestionRequestDTO
from agrr_core.adapter.gateways.allocation_result_file_gateway import AllocationResultFileGateway
from agrr_core.adapter.gateways.field_file_gateway import FieldFileGateway
from agrr_core.adapter.gateways.crop_profile_file_gateway import CropProfileFileGateway
from agrr_core.adapter.gateways.weather_file_gateway import WeatherFileGateway
from agrr_core.framework.services.io.file_service import FileService

async def main():
    # ファイルサービスの初期化
    file_service = FileService()
    
    # ゲートウェイの初期化
    allocation_gateway = AllocationResultFileGateway(
        file_repository=file_service,
        file_path="allocation.json"
    )
    
    field_gateway = FieldFileGateway(
        file_repository=file_service,
        file_path="fields.json"
    )
    
    crop_gateway = CropProfileFileGateway(
        file_repository=file_service,
        file_path="crops.json"
    )
    
    weather_gateway = WeatherFileGateway(
        file_repository=file_service,
        file_path="weather.json"
    )
    
    # Interactorの初期化
    interactor = CandidateSuggestionInteractor(
        allocation_result_gateway=allocation_gateway,
        field_gateway=field_gateway,
        crop_gateway=crop_gateway,
        weather_gateway=weather_gateway,
        interaction_rule_gateway=None
    )
    
    # リクエストの作成
    request = CandidateSuggestionRequestDTO(
        target_crop_id="tomato",
        planning_period_start=datetime(2024, 4, 1),
        planning_period_end=datetime(2024, 10, 31)
    )
    
    # 実行
    response = await interactor.execute(request)
    
    # 結果の確認
    if response.success:
        print(f"Successfully generated {len(response.candidates)} candidates")
        for candidate in response.candidates:
            print(f"Field: {candidate.field_id}, Type: {candidate.candidate_type}, Profit: {candidate.expected_profit}")
    else:
        print(f"Error: {response.message}")

if __name__ == "__main__":
    asyncio.run(main())
```

### CLIコントローラーの使用例

```python
import asyncio
from agrr_core.adapter.controllers.candidate_suggestion_cli_controller import CandidateSuggestionCliController
from agrr_core.adapter.presenters.candidate_suggestion_cli_presenter import CandidateSuggestionCliPresenter
from agrr_core.adapter.gateways.allocation_result_file_gateway import AllocationResultFileGateway
from agrr_core.adapter.gateways.field_file_gateway import FieldFileGateway
from agrr_core.adapter.gateways.crop_profile_file_gateway import CropProfileFileGateway
from agrr_core.adapter.gateways.weather_file_gateway import WeatherFileGateway
from agrr_core.framework.services.io.file_service import FileService

async def main():
    # ファイルサービスの初期化
    file_service = FileService()
    
    # ゲートウェイの初期化
    allocation_gateway = AllocationResultFileGateway(
        file_repository=file_service,
        file_path="allocation.json"
    )
    
    field_gateway = FieldFileGateway(
        file_repository=file_service,
        file_path="fields.json"
    )
    
    crop_gateway = CropProfileFileGateway(
        file_repository=file_service,
        file_path="crops.json"
    )
    
    weather_gateway = WeatherFileGateway(
        file_repository=file_service,
        file_path="weather.json"
    )
    
    # Presenterの初期化
    presenter = CandidateSuggestionCliPresenter()
    
    # Controllerの初期化
    controller = CandidateSuggestionCliController(
        allocation_result_gateway=allocation_gateway,
        field_gateway=field_gateway,
        crop_gateway=crop_gateway,
        weather_gateway=weather_gateway,
        presenter=presenter,
        interaction_rule_gateway=None
    )
    
    # 引数パーサーの作成
    parser = controller.create_argument_parser()
    
    # 引数の解析
    args = parser.parse_args([
        '--allocation', 'allocation.json',
        '--fields-file', 'fields.json',
        '--crops-file', 'crops.json',
        '--target-crop', 'tomato',
        '--planning-start', '2024-04-01',
        '--planning-end', '2024-10-31',
        '--weather-file', 'weather.json',
        '--output', 'candidates.txt'
    ])
    
    # コマンドの実行
    await controller.handle_candidates_command(args)

if __name__ == "__main__":
    asyncio.run(main())
```

## エラーハンドリング

### 一般的なエラー

```python
from agrr_core.usecase.dto.candidate_suggestion_response_dto import CandidateSuggestionResponseDTO

# エラーレスポンスの処理
response = await interactor.execute(request)

if not response.success:
    if "Target crop not found" in response.message:
        print("指定した作物が見つかりません")
    elif "Failed to load current optimization result" in response.message:
        print("最適化結果の読み込みに失敗しました")
    elif "No fields found" in response.message:
        print("圃場データが見つかりません")
    else:
        print(f"エラー: {response.message}")
```

### 例外処理

```python
import asyncio
from agrr_core.usecase.interactors.candidate_suggestion_interactor import CandidateSuggestionInteractor

async def safe_execute(interactor, request):
    try:
        response = await interactor.execute(request)
        return response
    except Exception as e:
        return CandidateSuggestionResponseDTO(
            candidates=[],
            success=False,
            message=f"Unexpected error: {str(e)}"
        )
```

## テスト

### 単体テストの例

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from agrr_core.usecase.interactors.candidate_suggestion_interactor import CandidateSuggestionInteractor
from agrr_core.usecase.dto.candidate_suggestion_request_dto import CandidateSuggestionRequestDTO
from datetime import datetime

class TestCandidateSuggestionInteractor:
    @pytest.fixture
    def mock_gateways(self):
        return {
            'allocation_result_gateway': AsyncMock(),
            'field_gateway': AsyncMock(),
            'crop_gateway': AsyncMock(),
            'weather_gateway': AsyncMock(),
            'interaction_rule_gateway': AsyncMock(),
        }
    
    @pytest.fixture
    def interactor(self, mock_gateways):
        return CandidateSuggestionInteractor(**mock_gateways)
    
    @pytest.mark.asyncio
    async def test_execute_success(self, interactor, mock_gateways):
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
        assert response.success is True
        assert len(response.candidates) > 0
```

## パフォーマンス

### 並列処理

```python
import asyncio
from agrr_core.usecase.interactors.candidate_suggestion_interactor import CandidateSuggestionInteractor

async def parallel_candidate_generation(interactor, requests):
    """複数のリクエストを並列処理"""
    tasks = [interactor.execute(request) for request in requests]
    responses = await asyncio.gather(*tasks)
    return responses
```

### キャッシュの活用

```python
from agrr_core.usecase.interactors.candidate_suggestion_interactor import CandidateSuggestionInteractor

# Interactorは内部でGDD計算のキャッシュを管理
interactor = CandidateSuggestionInteractor(...)

# 同じ圃場・作物・期間の組み合わせはキャッシュから取得
response1 = await interactor.execute(request1)
response2 = await interactor.execute(request2)  # キャッシュから取得
```

## 関連ドキュメント

- [要件定義書](CANDIDATE_SUGGESTION_FEATURE.md)
- [テスト設計書](CANDIDATE_SUGGESTION_TEST_DESIGN.md)
- [ユーザーガイド](CANDIDATE_SUGGESTION_USER_GUIDE.md)
- [Clean Architecture設計原則](ARCHITECTURE.md)
