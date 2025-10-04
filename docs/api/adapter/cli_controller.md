# CLI Controller API Reference

`CLIWeatherController`は、コマンドライン引数の処理と天気予報取得ユースケースの呼び出しを担当するAdapter層のコンポーネントです。

## クラス概要

```python
class CLIWeatherController:
    """CLI controller for weather data operations."""
```

**パス**: `src/agrr_core/adapter/controllers/cli_weather_controller.py`

## コンストラクタ

```python
def __init__(
    self, 
    fetch_weather_interactor: FetchWeatherDataInteractor,
    cli_presenter: CLIWeatherPresenter
) -> None
```

### パラメータ

| パラメータ | 型 | 説明 |
|---|---|---|
| `fetch_weather_interactor` | `FetchWeatherDataInteractor` | 天気データ取得ユースケース |
| `cli_presenter` | `CLIWeatherPresenter` | CLI表示用プレゼンター |

## 主要メソッド

### `create_argument_parser()`

コマンドライン引数パーサーを作成します。

```python
def create_argument_parser(self) -> argparse.ArgumentParser
```

**戻り値**: `argparse.ArgumentParser` - 引数パーサー

**例**:
```python
controller = CLIWeatherController(interactor, presenter)
parser = controller.create_argument_parser()
args = parser.parse_args(['weather', '--location', '35.6762,139.6503', '--days', '7'])
```

### `parse_location()`

位置情報文字列を緯度・経度に解析します。

```python
def parse_location(self, location_str: str) -> tuple[float, float]
```

**パラメータ**:
- `location_str` (str): "緯度,経度" 形式の文字列

**戻り値**: `tuple[float, float]` - (緯度, 経度)

**例外**:
- `ValueError`: 無効な形式または座標範囲外の場合

**例**:
```python
lat, lon = controller.parse_location("35.6762,139.6503")
# lat = 35.6762, lon = 139.6503
```

### `parse_date()`

日付文字列をYYYY-MM-DD形式で検証します。

```python
def parse_date(self, date_str: str) -> str
```

**パラメータ**:
- `date_str` (str): 日付文字列（YYYY-MM-DD形式）

**戻り値**: `str` - 検証済み日付文字列

**例外**:
- `ValueError`: 無効な日付形式の場合

### `calculate_date_range()`

指定日数から開始日・終了日を計算します（昨日まで）。

```python
def calculate_date_range(self, days: int) -> tuple[str, str]
```

**パラメータ**:
- `days` (int): 日数

**戻り値**: `tuple[str, str]` - (開始日, 終了日)

**注**: Archive APIは過去のデータのみをサポートするため、終了日は昨日になります。

### `handle_weather_command()`

天気予報コマンドを処理します。

```python
async def handle_weather_command(self, args) -> None
```

**パラメータ**:
- `args`: 解析済みコマンドライン引数

**処理フロー**:
1. 位置情報の解析・検証
2. 日付範囲の決定
3. ユースケースの実行
4. 結果の表示（テーブルまたはJSON形式）

### `run()`

CLIアプリケーションを実行します。

```python
async def run(self, args: Optional[list] = None) -> None
```

**パラメータ**:
- `args` (Optional[list]): コマンドライン引数リスト

**処理フロー**:
1. 引数パーサーの作成
2. 引数の解析
3. コマンドの実行

## コマンドライン引数

### weatherコマンド

| 引数 | 短縮形 | 必須 | 説明 | 例 |
|---|---|---|---|---|
| `--location` | `-l` | ✓ | 位置情報（緯度,経度） | `35.6762,139.6503` |
| `--days` | `-d` | - | 過去何日分のデータ（デフォルト: 7） | `7` |
| `--start-date` | `-s` | - | 開始日（YYYY-MM-DD） | `2024-01-01` |
| `--end-date` | `-e` | - | 終了日（YYYY-MM-DD） | `2024-01-07` |
| `--json` | - | - | JSON形式で出力 | - |

### 引数の組み合わせ

- `--days`、`--start-date`、`--end-date`は相互に組み合わせ可能
- `--location`は必須
- 日付指定なしの場合、デフォルトで過去7日間

## エラーハンドリング

### バリデーションエラー

| エラー | 説明 | 例 |
|---|---|---|
| `Invalid location format` | 位置情報形式が無効 | `"35.6762"` |
| `Latitude must be between -90 and 90` | 緯度が範囲外 | `91.0,139.6503` |
| `Longitude must be between -180 and 180` | 経度が範囲外 | `35.6762,181.0` |
| `Invalid date format` | 日付形式が無効 | `"2024/01/01"` |

## 使用例

### 基本的な使用

```python
from agrr_core.adapter.controllers.cli_weather_controller import CLIWeatherController
from agrr_core.usecase.interactors.fetch_weather_data_interactor import FetchWeatherDataInteractor
from agrr_core.adapter.presenters.cli_weather_presenter import CLIWeatherPresenter

# 依存性の設定
interactor = FetchWeatherDataInteractor(...)
presenter = CLIWeatherPresenter()
controller = CLIWeatherController(interactor, presenter)

# CLIアプリケーションの実行
await controller.run(['weather', '--location', '35.6762,139.6503', '--days', '7'])
```

## テスト

テストは `tests/test_adapter/test_cli_weather_controller.py` にあります。
