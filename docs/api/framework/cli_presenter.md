# CLI Presenter API Reference

`CLIWeatherPresenter`は、コンソール出力に最適化された天気データの表示を担当するFramework層のコンポーネントです。

## クラス概要

```python
class CLIWeatherPresenter(WeatherPresenterOutputPort):
    """CLI presenter for weather data display in terminal."""
```

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

**例**:
```python
dto = WeatherDataResponseDTO(
    time="2024-01-15T00:00:00Z",
    temperature_2m_max=15.5,
    temperature_2m_min=8.2,
    temperature_2m_mean=11.8,
    precipitation_sum=5.0,
    sunshine_duration=28800.0,
    sunshine_hours=8.0
)

formatted = presenter.format_weather_data_dto(dto)
# {'time': '2024-01-15T00:00:00Z', 'temperature_2m_max': 15.5, ...}
```

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

Date        Max Temp   Min Temp   Avg Temp   Precip   Sunshine  
----------------------------------------------------------------
2024-01-15  15.5°C     8.2°C      11.8°C     5.0mm    8.0h      
2024-01-16  18.3°C     10.1°C     14.2°C     0.0mm    9.0h      

================================================================================
Total records: 2
================================================================================
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

**パラメータ**:
- `date_str` (str): 日付文字列

**戻り値**: `str` - フォーマット済み日付

**例**:
```python
formatted = presenter._format_date("2024-01-15T00:00:00Z")
# "2024-01-15"
```

#### `_format_temperature()`

温度を表示用にフォーマットします。

```python
def _format_temperature(self, temp: float) -> str
```

**パラメータ**:
- `temp` (float): 温度値

**戻り値**: `str` - フォーマット済み温度

**例**:
```python
formatted = presenter._format_temperature(15.5)
# "15.5°C"

formatted = presenter._format_temperature(None)
# "N/A"
```

#### `_format_precipitation()`

降水量を表示用にフォーマットします。

```python
def _format_precipitation(self, precip: float) -> str
```

**パラメータ**:
- `precip` (float): 降水量

**戻り値**: `str` - フォーマット済み降水量

**例**:
```python
formatted = presenter._format_precipitation(5.0)
# "5.0mm"

formatted = presenter._format_precipitation(None)
# "N/A"
```

#### `_format_sunshine()`

日照時間を表示用にフォーマットします。

```python
def _format_sunshine(self, sunshine: float) -> str
```

**パラメータ**:
- `sunshine` (float): 日照時間

**戻り値**: `str` - フォーマット済み日照時間

**例**:
```python
formatted = presenter._format_sunshine(8.5)
# "8.5h"

formatted = presenter._format_sunshine(None)
# "N/A"
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
from agrr_core.framework.presenters import CLIWeatherPresenter
from agrr_core.usecase.dto import WeatherDataListResponseDTO, WeatherDataResponseDTO

# Presenterの作成
presenter = CLIWeatherPresenter()

# 天気データの表示
weather_data = WeatherDataResponseDTO(
    time="2024-01-15T00:00:00Z",
    temperature_2m_max=15.5,
    temperature_2m_min=8.2,
    temperature_2m_mean=11.8,
    precipitation_sum=5.0,
    sunshine_duration=28800.0,
    sunshine_hours=8.0
)

weather_list = WeatherDataListResponseDTO(data=[weather_data], total_count=1)
presenter.display_weather_data(weather_list)
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

### エラー表示

```python
# エラーメッセージの表示
presenter.display_error("API connection failed", "API_ERROR")
# 出力: [ERROR] API_ERROR: API connection failed

# 成功メッセージの表示
presenter.display_success_message("Data fetched successfully")
# 出力: [SUCCESS] Data fetched successfully
```

## テスト

```python
import pytest
from io import StringIO
from agrr_core.framework.presenters import CLIWeatherPresenter

def test_display_weather_data():
    # テスト用の出力ストリーム
    output_stream = StringIO()
    presenter = CLIWeatherPresenter(output_stream=output_stream)
    
    # テストデータの作成
    weather_data = WeatherDataResponseDTO(
        time="2024-01-15T00:00:00Z",
        temperature_2m_max=15.5,
        temperature_2m_min=8.2,
        temperature_2m_mean=11.8,
        precipitation_sum=5.0,
        sunshine_duration=28800.0,
        sunshine_hours=8.0
    )
    
    weather_list = WeatherDataListResponseDTO(data=[weather_data], total_count=1)
    
    # 表示の実行
    presenter.display_weather_data(weather_list)
    
    # 出力の検証
    output = output_stream.getvalue()
    assert "WEATHER FORECAST" in output
    assert "2024-01-15" in output
    assert "15.5°C" in output
    assert "8.2°C" in output
    assert "11.8°C" in output
    assert "5.0mm" in output
    assert "8.0h" in output
```
