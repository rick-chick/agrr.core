# 気象庁Repository - 必須修正事項

## 📋 概要

プロのテスタによるレビューで発見された**Critical Issues**の修正ガイドです。
14個の必須テストケースを追加済みです。これらは現在`@pytest.mark.xfail`でマークされており、
修正完了後にこのマークを外してください。

## 🎯 修正対象

### テストファイル
- `tests/test_adapter/test_weather_jma_repository_critical.py` (新規追加済み)

### 実装ファイル
- `src/agrr_core/adapter/repositories/weather_jma_repository.py`
- `src/agrr_core/framework/repositories/csv_downloader.py`

---

## 🔴 Phase 1: Critical Issues（緊急）

### Issue 1: エラーの沈黙化

**場所:** `weather_jma_repository.py:262-264`

**現在のコード:**
```python
except Exception as e:
    # Skip problematic rows but continue processing
    continue
```

**問題:**
- エラーが完全に無視される
- デバッグ不可能
- データロスが発生

**修正方法:**
```python
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(
        f"Failed to parse row at index {_}: {e}. "
        f"Date: {row.get('年月日', 'N/A')}, "
        f"Data: {dict(row)}"
    )
    continue
```

**対応テスト:** なし（ロギングの動作確認）

---

### Issue 2: 日付バリデーション不足

**場所:** `weather_jma_repository.py:105-106`

**現在のコード:**
```python
start = datetime.strptime(start_date, "%Y-%m-%d")
end = datetime.strptime(end_date, "%Y-%m-%d")
```

**問題:**
- 不正な日付フォーマットでValueErrorが投げられる
- start > end のチェックがない

**修正方法:**
```python
try:
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
except ValueError as e:
    raise WeatherAPIError(
        f"Invalid date format. Expected YYYY-MM-DD, "
        f"got start_date='{start_date}', end_date='{end_date}': {e}"
    )

if start > end:
    raise WeatherAPIError(
        f"start_date ({start_date}) must be before or equal to "
        f"end_date ({end_date})"
    )
```

**対応テスト:**
- ✅ `test_invalid_date_format`
- ✅ `test_start_date_after_end_date`

**確認コマンド:**
```bash
pytest tests/test_adapter/test_weather_jma_repository_critical.py::TestWeatherJMARepositoryCritical::test_invalid_date_format -v
pytest tests/test_adapter/test_weather_jma_repository_critical.py::TestWeatherJMARepositoryCritical::test_start_date_after_end_date -v
```

---

### Issue 3: 月跨ぎのバグ（2月31日問題）

**場所:** `weather_jma_repository.py:123-127`

**現在のコード:**
```python
if current.month == 12:
    current = current.replace(year=current.year + 1, month=1)
else:
    current = current.replace(month=current.month + 1)
```

**問題:**
- 1月31日 → 2月31日（存在しない）でValueError
- 無限ループの可能性

**修正方法（Option 1: 月初に揃える）:**
```python
# 月初の1日に揃える
current = current.replace(day=1)
if current.month == 12:
    current = current.replace(year=current.year + 1, month=1)
else:
    current = current.replace(month=current.month + 1)
```

**修正方法（Option 2: relativedeltaを使用）:**
```python
from dateutil.relativedelta import relativedelta

# 月を安全に進める
current = current + relativedelta(months=1)
```

**依存関係追加（Option 2の場合）:**
```bash
# requirements.txt に追加
python-dateutil>=2.8.2
```

**対応テスト:**
- ✅ `test_date_range_spans_february_from_31st`

**確認コマンド:**
```bash
pytest tests/test_adapter/test_weather_jma_repository_critical.py::TestWeatherJMARepositoryCritical::test_date_range_spans_february_from_31st -v
```

---

## 🟡 Phase 2: High Priority Issues（1週間以内）

### Issue 4: 距離計算の不正確性

**場所:** `weather_jma_repository.py:65`

**現在のコード:**
```python
distance = ((latitude - lat) ** 2 + (longitude - lon) ** 2) ** 0.5
```

**問題:**
- ユークリッド距離（平面）を使用
- 球面での実距離と大きく乖離

**修正方法:**
```python
from math import radians, sin, cos, sqrt, atan2

def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great-circle distance using Haversine formula.
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
        
    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth radius in km
    
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    
    a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c

# _find_nearest_locationで使用
distance = self._haversine_distance(latitude, longitude, lat, lon)
```

**対応テスト:**
- ✅ `test_distance_calculation_hokkaido_okinawa`

**確認コマンド:**
```bash
pytest tests/test_adapter/test_weather_jma_repository_critical.py::TestWeatherJMARepositoryCritical::test_distance_calculation_hokkaido_okinawa -v
```

---

### Issue 5: データ品質検証の欠如

**場所:** `weather_jma_repository.py:232-260`

**問題:**
- 異常値（-100℃、1000℃など）をそのまま受け入れる
- 負の降水量も許容
- 温度逆転（max < min）のチェックなし

**修正方法:**
```python
def _validate_weather_data(self, data: WeatherData, date_str: str = "") -> bool:
    """
    Validate weather data ranges.
    
    Args:
        data: WeatherData to validate
        date_str: Date string for logging
        
    Returns:
        True if valid, False if invalid
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Temperature range check (Japan realistic range)
    if data.temperature_2m_max is not None:
        if not -50 <= data.temperature_2m_max <= 50:
            logger.warning(
                f"[{date_str}] Suspicious max temp: {data.temperature_2m_max}°C"
            )
            return False
    
    if data.temperature_2m_min is not None:
        if not -50 <= data.temperature_2m_min <= 50:
            logger.warning(
                f"[{date_str}] Suspicious min temp: {data.temperature_2m_min}°C"
            )
            return False
    
    # Temperature inversion check
    if (data.temperature_2m_max is not None and 
        data.temperature_2m_min is not None):
        if data.temperature_2m_max < data.temperature_2m_min:
            logger.warning(
                f"[{date_str}] Temperature inversion: "
                f"max={data.temperature_2m_max}°C < min={data.temperature_2m_min}°C"
            )
            return False
    
    # Precipitation check
    if data.precipitation_sum is not None:
        if data.precipitation_sum < 0:
            logger.warning(
                f"[{date_str}] Negative precipitation: {data.precipitation_sum}mm"
            )
            return False
        if data.precipitation_sum > 1000:  # Extreme but possible
            logger.warning(
                f"[{date_str}] Extreme precipitation: {data.precipitation_sum}mm"
            )
    
    # Sunshine duration check
    if data.sunshine_duration is not None:
        if data.sunshine_duration < 0:
            logger.warning(
                f"[{date_str}] Negative sunshine: {data.sunshine_duration}s"
            )
            return False
        if data.sunshine_duration > 24 * 3600:
            logger.warning(
                f"[{date_str}] Sunshine over 24h: {data.sunshine_duration}s"
            )
            return False
    
    return True

# パース処理で使用（line 260付近）
date_str = row.get('年月日', 'unknown')
if self._validate_weather_data(weather_data, date_str):
    weather_data_list.append(weather_data)
else:
    skipped_count += 1  # カウンターを追加

# 最後にログ出力
if skipped_count > 0:
    logger.info(f"Skipped {skipped_count} invalid weather records")
```

**対応テスト:**
- ✅ `test_negative_precipitation`
- ✅ `test_temperature_inversion`
- ✅ `test_all_null_temperature_values`

**確認コマンド:**
```bash
pytest tests/test_adapter/test_weather_jma_repository_critical.py::TestWeatherJMARepositoryCritical::test_negative_precipitation -v
pytest tests/test_adapter/test_weather_jma_repository_critical.py::TestWeatherJMARepositoryCritical::test_temperature_inversion -v
pytest tests/test_adapter/test_weather_jma_repository_critical.py::TestWeatherJMARepositoryCritical::test_all_null_temperature_values -v
```

---

### Issue 6: リソースリーク（csv_downloader）

**場所:** `csv_downloader.py:23, 43-54`

**問題:**
- 非同期なのに同期的な`requests.Session`を使用
- `close()`が呼ばれない場合にリソースリーク

**修正方法（aiohttpへ移行）:**

**1. 依存関係追加:**
```bash
# requirements.txt に追加
aiohttp>=3.8.0
```

**2. CsvDownloader書き換え:**
```python
"""CSV downloader implementation for framework layer."""

import aiohttp
import pandas as pd
from io import StringIO
from typing import Optional

from agrr_core.entity.exceptions.csv_download_error import CsvDownloadError
from agrr_core.adapter.interfaces.csv_service_interface import CsvServiceInterface


class CsvDownloader(CsvServiceInterface):
    """CSV downloader for fetching CSV data from URLs."""
    
    def __init__(self, timeout: int = 30):
        """
        Initialize CSV downloader.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session
    
    async def download_csv(
        self,
        url: str,
        encoding: str = 'utf-8'
    ) -> pd.DataFrame:
        """
        Download and parse CSV data.
        
        Args:
            url: URL to download CSV from
            encoding: Character encoding of the CSV file
            
        Returns:
            DataFrame containing the parsed CSV data
            
        Raises:
            CsvDownloadError: If download or parsing fails
        """
        session = await self._get_session()
        
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                content = await response.read()
                
                # Decode with specified encoding
                try:
                    csv_text = content.decode(encoding)
                except UnicodeDecodeError as e:
                    raise CsvDownloadError(
                        f"Failed to decode CSV with encoding {encoding}: {e}"
                    )
                
                # Parse CSV
                try:
                    df = pd.read_csv(StringIO(csv_text))
                    return df
                except pd.errors.ParserError as e:
                    raise CsvDownloadError(f"Failed to parse CSV: {e}")
                    
        except aiohttp.ClientError as e:
            raise CsvDownloadError(f"Failed to download CSV from {url}: {e}")
        except Exception as e:
            raise CsvDownloadError(f"Unexpected error while downloading CSV: {e}")
    
    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
```

**対応テスト:**
- ✅ `test_session_cleanup_on_error`

**確認コマンド:**
```bash
pytest tests/test_adapter/test_weather_jma_repository_critical.py::TestWeatherJMARepositoryCritical::test_session_cleanup_on_error -v
```

---

## 🟢 Phase 3: その他の改善（オプション）

### Issue 7: 重複日付の処理

**対応テスト:**
- ✅ `test_duplicate_dates_in_csv`

**推奨修正:**
```python
# 重複チェック用のセット
seen_dates = set()

for _, row in df.iterrows():
    # ... date parsing ...
    
    if record_date in seen_dates:
        logger.warning(f"Duplicate date found: {record_date}, skipping")
        continue
    
    seen_dates.add(record_date)
    # ... rest of processing ...
```

---

### Issue 8: 欠損列の処理

**対応テスト:**
- ✅ `test_missing_required_columns`

**推奨修正:**
```python
# 必須列のチェック
required_columns = ['年月日']
missing_columns = [col for col in required_columns if col not in df.columns]

if missing_columns:
    raise WeatherAPIError(
        f"CSV missing required columns: {missing_columns}. "
        f"Available columns: {list(df.columns)}"
    )
```

---

## 📝 テスト実行方法

### 全必須テストを実行
```bash
pytest tests/test_adapter/test_weather_jma_repository_critical.py -v
```

### 失敗するテストのみ表示（xfail除外）
```bash
pytest tests/test_adapter/test_weather_jma_repository_critical.py -v --runxfail
```

### 特定のテストのみ実行
```bash
pytest tests/test_adapter/test_weather_jma_repository_critical.py::TestWeatherJMARepositoryCritical::test_invalid_date_format -v
```

### カバレッジ付きで実行
```bash
pytest tests/test_adapter/test_weather_jma_repository_critical.py --cov=src/agrr_core/adapter/repositories/weather_jma_repository --cov-report=html
```

---

## ✅ 修正完了チェックリスト

### Phase 1 (Critical - 必須)
- [ ] Issue 1: エラーロギング追加
- [ ] Issue 2: 日付バリデーション追加
- [ ] Issue 3: 月跨ぎバグ修正
- [ ] `test_invalid_date_format`の`@pytest.mark.xfail`を削除して合格確認
- [ ] `test_start_date_after_end_date`の`@pytest.mark.xfail`を削除して合格確認
- [ ] `test_date_range_spans_february_from_31st`の`@pytest.mark.xfail`を削除して合格確認

### Phase 2 (High Priority - 推奨)
- [ ] Issue 4: Haversine距離計算実装
- [ ] Issue 5: データ品質検証追加
- [ ] Issue 6: aiohttp移行（csv_downloader）
- [ ] `test_distance_calculation_hokkaido_okinawa`の`@pytest.mark.xfail`を削除
- [ ] `test_negative_precipitation`の`@pytest.mark.xfail`を削除
- [ ] `test_temperature_inversion`の`@pytest.mark.xfail`を削除
- [ ] `test_session_cleanup_on_error`の`@pytest.mark.xfail`を削除

### Phase 3 (オプション)
- [ ] Issue 7: 重複日付処理
- [ ] Issue 8: 欠損列チェック
- [ ] その他のxfailテストを確認

---

## 📊 現在の状況

### テストサマリー
```
Total Tests: 14 critical + 2 edge cases = 16 tests
Status: 
  - ✅ 6 tests passing
  - ⚠️  10 tests marked as xfail (expected to fail until fixes)
```

### カバレッジ
```
weather_jma_repository.py: 78% → 目標: 95%+
csv_downloader.py: 39% → 目標: 85%+
```

---

## 🚀 優先順位

1. **今すぐ修正（Phase 1）**: Issues 1, 2, 3
   - これらがないと本番投入不可
   - 推定作業時間: 2-3時間

2. **1週間以内（Phase 2）**: Issues 4, 5, 6
   - データ品質とパフォーマンスに影響
   - 推定作業時間: 1日

3. **余裕があれば（Phase 3）**: Issues 7, 8
   - エッジケースの強化
   - 推定作業時間: 2-3時間

---

## 📞 質問・相談先

- テストの意図が不明: テストコードのdocstringを参照
- 実装方針の相談: このドキュメントの「修正方法」セクション参照
- バグ報告: 新しいテストケースを追加してxfailマーク

---

## 🎓 参考資料

- [Haversine formula](https://en.wikipedia.org/wiki/Haversine_formula)
- [aiohttp documentation](https://docs.aiohttp.org/)
- [python-dateutil](https://dateutil.readthedocs.io/)
- [Pandas date parsing](https://pandas.pydata.org/docs/reference/api/pandas.to_datetime.html)

---

**最終更新:** 2025-01-12
**レビュアー:** Professional QA Tester
**修正担当:** [プログラマ名を記入]

