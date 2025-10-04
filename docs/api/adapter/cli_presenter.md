# CLI Presenter API Reference

`CLIWeatherPresenter`は、コンソール出力に最適化された天気データの表示を担当するAdapter層のコンポーネントです。

## クラス概要

```python
class CLIWeatherPresenter(WeatherPresenterOutputPort):
    """CLI presenter for weather data display in terminal."""
```

**パス**: `src/agrr_core/adapter/presenters/cli_weather_presenter.py`

## コンストラクタ

```python
def __init__(self, output_stream=sys.stdout) -> None
```

### パラメータ

| パラメータ | 型 | デフォルト | 説明 |
|---|---|---|---|
| `output_stream` | `IO[str]` | `sys.stdout` | 出力ストリーム |

## 主要メソッド

### データフォーマットメソッド

#### `format_weather_data_dto()`

天気データDTOを表示用フォーマットに変換します。

```python
def format_weather_data_dto(self, dto: WeatherDataResponseDTO) -> Dict[str, Any]
```

**パラメータ**:
- `dto` (WeatherDataResponseDTO): 天気データDTO

**戻り値**: `Dict[str, Any]` - フォーマット済みデータ

#### `format_weather_data_list_dto()`

天気データリストDTOを表示用フォーマットに変換します。

```python
def format_weather_data_list_dto(self, dto: WeatherDataListResponseDTO) -> Dict[str, Any]
```

**パラメータ**:
- `dto` (WeatherDataListResponseDTO): 天気データリストDTO

**戻り値**: `Dict[str, Any]` - フォーマット済みデータリスト

#### `format_error()`

エラーレスポンスをフォーマットします。

```python
def format_error(self, error_message: str, error_code: str = "WEATHER_ERROR") -> Dict[str, Any]
```

**パラメータ**:
- `error_message` (str): エラーメッセージ
- `error_code` (str): エラーコード（デフォルト: "WEATHER_ERROR"）

**戻り値**: `Dict[str, Any]` - フォーマット済みエラーレスポンス

#### `format_success()`

成功レスポンスをフォーマットします。

```python
def format_success(self, data: Dict[str, Any]) -> Dict[str, Any]
```

**パラメータ**:
- `data` (Dict[str, Any]): レスポンスデータ

**戻り値**: `Dict[str, Any]` - フォーマット済み成功レスポンス

### 表示メソッド

#### `display_weather_data()`

天気データを表形式でコンソールに表示します。

```python
def display_weather_data(self, weather_data_list: WeatherDataListResponseDTO) -> None
```

**パラメータ**:
- `weather_data_list` (WeatherDataListResponseDTO): 天気データリスト

**表示例**:
```
================================================================================
WEATHER FORECAST
================================================================================

Location: 35.6762°N, 139.6503°E | Elevation: 37m | Timezone: Asia/Tokyo

Date        Max Temp   Min Temp   Avg Temp   Precip   Sunshine  
----------------------------------------------------------------
2024-01-15  15.5°C     8.2°C      11.8°C     5.0mm    8.0h      
2024-01-16  18.3°C     10.1°C     14.2°C     0.0mm    9.0h      

================================================================================
Total records: 2
================================================================================
```

#### `display_weather_data_json()`

天気データをJSON形式で出力します。

```python
def display_weather_data_json(self, weather_data_list: WeatherDataListResponseDTO) -> None
```

**パラメータ**:
- `weather_data_list` (WeatherDataListResponseDTO): 天気データリスト

**出力例**:
```json
{
  "success": true,
  "data": {
    "data": [
      {
        "time": "2024-01-15",
        "temperature_2m_max": 15.5,
        "temperature_2m_min": 8.2,
        "temperature_2m_mean": 11.8,
        "precipitation_sum": 5.0,
        "sunshine_duration": 28800.0,
        "sunshine_hours": 8.0
      }
    ],
    "total_count": 1,
    "location": {
      "latitude": 35.6762,
      "longitude": 139.6503,
      "elevation": 37.0,
      "timezone": "Asia/Tokyo"
    }
  }
}
```

#### `display_error()`

エラーメッセージをコンソールに表示します。

```python
def display_error(self, error_message: str, error_code: str = "WEATHER_ERROR") -> None
```

**パラメータ**:
- `error_message` (str): エラーメッセージ
- `error_code` (str): エラーコード（デフォルト: "WEATHER_ERROR"）

**表示例**:
```
[ERROR] VALIDATION_ERROR: Latitude must be between -90 and 90, got 91.0
```

#### `display_success_message()`

成功メッセージをコンソールに表示します。

```python
def display_success_message(self, message: str) -> None
```

**パラメータ**:
- `message` (str): 成功メッセージ

**表示例**:
```
[SUCCESS] Fetching weather data for location (35.6762, 139.6503)...
```

### ユーティリティメソッド

#### `_format_date()`

日付文字列を表示用にフォーマットします。

```python
def _format_date(self, date_str: str) -> str
```

#### `_format_temperature()`

温度を表示用にフォーマットします。

```python
def _format_temperature(self, temp: float) -> str
```

#### `_format_precipitation()`

降水量を表示用にフォーマットします。

```python
def _format_precipitation(self, precip: float) -> str
```

#### `_format_sunshine()`

日照時間を表示用にフォーマットします。

```python
def _format_sunshine(self, sunshine: float) -> str
```

## Unicode対応

Windows環境でのUnicode文字（絵文字）表示に対応しています。

```python
def display_error(self, error_message: str, error_code: str = "WEATHER_ERROR") -> None:
    try:
        self.output_stream.write(f"\n❌ Error [{error_code}]: {error_message}\n\n")
    except UnicodeEncodeError:
        # Fallback for systems that don't support Unicode emojis
        self.output_stream.write(f"\n[ERROR] {error_code}: {error_message}\n\n")
```

## 使用例

### 基本的な使用

```python
from agrr_core.adapter.presenters.cli_weather_presenter import CLIWeatherPresenter
from agrr_core.usecase.dto.weather_data_list_response_dto import WeatherDataListResponseDTO
from agrr_core.usecase.dto.weather_data_response_dto import WeatherDataResponseDTO

# Presenterの作成
presenter = CLIWeatherPresenter()

# 天気データの表示
weather_list = WeatherDataListResponseDTO(data=[weather_data], total_count=1)
presenter.display_weather_data(weather_list)
```

### JSON形式での出力

```python
# JSON形式で出力
presenter.display_weather_data_json(weather_list)
```

### カスタム出力ストリーム

```python
from io import StringIO

# カスタム出力ストリームの使用
output_stream = StringIO()
presenter = CLIWeatherPresenter(output_stream=output_stream)

# メッセージの表示
presenter.display_success_message("Test message")

# 出力の取得
output = output_stream.getvalue()
print(output)  # "[SUCCESS] Test message"
```

## テスト

テストは `tests/test_adapter/test_cli_weather_presenter.py` にあります。
