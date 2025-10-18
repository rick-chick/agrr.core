# xfailed テスト - 仕様提案書

各xfailedテストについて、実装すべき仕様の具体案を提示します。

---

## 1. test_missing_required_columns

### 現状
- HTMLテーブルから必須カラムが欠落している場合の処理が未定義
- 現在は行をスキップするが、データ品質保証が不十分

### 仕様案A: Strict モード（推奨）

**方針**: 必須データが欠落している行は無効とみなす

```python
def _parse_row(self, row: TableRow, year: int, month: int) -> Optional[WeatherData]:
    """
    Parse a single row from JMA table.
    
    必須カラム:
    - cells[0]: 日（必須）
    - cells[3]: 降水量（必須）
    - cells[6]: 平均気温（オプション）
    - cells[7]: 最高気温（オプション）
    - cells[8]: 最低気温（オプション）
    - cells[16]: 日照時間（オプション）
    
    Returns:
        WeatherData or None if row is invalid
    """
    # 最低限必要なカラム数をチェック
    MIN_REQUIRED_CELLS = 9  # cells[0-8]まで必須
    
    if len(row.cells) < MIN_REQUIRED_CELLS:
        self.logger.warning(
            f"Row has insufficient columns: {len(row.cells)} < {MIN_REQUIRED_CELLS}. "
            f"Skipping row."
        )
        return None
    
    # 日付の必須チェック
    day_str = row.cells[0].strip()
    if not day_str or not day_str.isdigit():
        self.logger.warning(f"Invalid day value: '{day_str}'. Skipping row.")
        return None
    
    # データ抽出
    day = int(day_str)
    precipitation = self._safe_float(row.cells[3])
    temp_mean = self._safe_float(row.cells[6])
    temp_max = self._safe_float(row.cells[7])
    temp_min = self._safe_float(row.cells[8])
    
    # 気温が全てNullの場合は警告
    if temp_max is None and temp_min is None and temp_mean is None:
        self.logger.warning(
            f"All temperature values are None for {year}-{month:02d}-{day:02d}. "
            f"Data quality issue."
        )
        # このケースは許容するか？
        # Option A: 許容（降水量データは有効）
        # Option B: 拒否（気温データは重要）
    
    # ... 以下続く
```

**メリット**:
- データ品質が保証される
- エラー検出が早い
- デバッグしやすい

**デメリット**:
- データ取得量が減る可能性

### 仕様案B: Lenient モード

**方針**: 可能な限りデータを取得、欠損は None で埋める

```python
def _parse_row(self, row: TableRow, year: int, month: int) -> Optional[WeatherData]:
    # 最低限、日付と1つ以上の有効データがあればOK
    if len(row.cells) < 4:  # 日付 + 何かしらのデータ
        return None
    
    # 全てのデータをOptionalとして扱う
    day = self._safe_int(row.cells[0])
    if day is None:
        return None
    
    precipitation = self._safe_float(row.cells[3] if len(row.cells) > 3 else None)
    temp_mean = self._safe_float(row.cells[6] if len(row.cells) > 6 else None)
    temp_max = self._safe_float(row.cells[7] if len(row.cells) > 7 else None)
    temp_min = self._safe_float(row.cells[8] if len(row.cells) > 8 else None)
    
    return WeatherData(...)  # 全てNoneも許容
```

**メリット**:
- データ取得量が最大化
- 部分的なデータも活用可能

**デメリット**:
- 下流での None チェックが必要
- データ品質が不安定

### 推奨: **仕様案A（Strict モード）- 気温のみ必須**
- 農業予測では気温データが最重要（GDD計算に必須）
- **降水量、日照、湿度などは欠損OK**（オプション扱い）
- 気温データを保証しつつ、データ取得量を最大化
- 柔軟性と品質のバランスを実現

---

## 2. test_duplicate_dates_in_csv

### 現状
- 同じ日付のデータが複数回出現した場合の処理が未定義
- 現在はそのまま処理（重複が混入する可能性）

### 仕様案A: First Wins（最初の値を採用）

```python
def _parse_jma_table(self, table: HtmlTable, ...) -> List[WeatherData]:
    weather_data_dict = {}  # Dict[datetime, WeatherData]
    
    for row in table.rows:
        record_date = datetime(year, month, day)
        
        # 既に存在する日付はスキップ
        if record_date in weather_data_dict:
            self.logger.warning(
                f"Duplicate date detected: {record_date.date()}. "
                f"Using first occurrence."
            )
            continue
        
        weather_data = WeatherData(...)
        weather_data_dict[record_date] = weather_data
    
    return list(weather_data_dict.values())
```

**メリット**: シンプル、予測可能
**デメリット**: 最初のデータが間違っている可能性

### 仕様案B: Last Wins（最後の値を採用）

```python
# 最後のデータで上書き
weather_data_dict[record_date] = weather_data  # 常に上書き
```

**メリット**: 修正データを反映可能
**デメリット**: データソースに依存

### 仕様案C: Average（平均を取る）

```python
if record_date in weather_data_dict:
    # 既存データと新データを平均
    existing = weather_data_dict[record_date]
    weather_data = self._merge_weather_data(existing, weather_data)

def _merge_weather_data(self, data1: WeatherData, data2: WeatherData) -> WeatherData:
    """Merge two weather data by averaging."""
    return WeatherData(
        time=data1.time,
        temperature_2m_max=(
            (data1.temperature_2m_max + data2.temperature_2m_max) / 2
            if data1.temperature_2m_max and data2.temperature_2m_max
            else data1.temperature_2m_max or data2.temperature_2m_max
        ),
        # ... 他のフィールドも同様
    )
```

**メリット**: 統計的に妥当
**デメリット**: 複雑、計算コスト

### 仕様案D: Strict Error（エラーを投げる）

```python
if record_date in weather_data_dict:
    raise WeatherAPIError(
        f"Duplicate date detected: {record_date.date()}. "
        f"Data quality issue in source."
    )
```

**メリット**: データ品質問題を早期発見
**デメリット**: データ取得が失敗しやすい

### 推奨: **仕様案A（First Wins）+ ログ警告**
- シンプルで予測可能
- 重複を警告ログで記録
- 実用上十分

---

## 3. test_session_cleanup_on_error

### 現状
- `CsvDownloader`でエラー時にセッションがクリーンアップされない
- リソースリークの可能性

### 仕様案A: Context Manager パターン（推奨）

```python
# src/agrr_core/framework/repositories/csv_downloader.py

class CsvDownloader(CsvServiceInterface):
    """CSV downloader with proper resource management."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = None  # 遅延初期化
    
    def __enter__(self):
        """Context manager entry."""
        self.session = requests.Session()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        if self.session:
            self.session.close()
            self.session = None
        return False
    
    async def download_csv(self, url: str, encoding: str = 'utf-8') -> pd.DataFrame:
        """Download CSV with automatic cleanup."""
        # セッションがない場合は作成
        if self.session is None:
            self.session = requests.Session()
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            csv_text = response.content.decode(encoding)
            df = pd.read_csv(StringIO(csv_text))
            
            return df
            
        except requests.RequestException as e:
            # エラー時もクリーンアップ
            if self.session:
                self.session.close()
                self.session = None
            raise CsvDownloadError(f"Failed to download CSV: {e}")
    
    def __del__(self):
        """Destructor with final cleanup."""
        if self.session:
            self.session.close()
```

**使用例**:
```python
# 使用側でContext Managerを使用
with CsvDownloader(timeout=30) as downloader:
    df = await downloader.download_csv(url)
# 自動クリーンアップ
```

**メリット**:
- Pythonic な実装
- 自動リソース管理
- エラー時も確実にクリーンアップ

### 仕様案B: Finally Block

```python
async def download_csv(self, url: str, encoding: str = 'utf-8') -> pd.DataFrame:
    try:
        response = self.session.get(url, timeout=self.timeout)
        # ... 処理
        return df
    except Exception as e:
        raise CsvDownloadError(f"Failed: {e}")
    finally:
        # 常にクリーンアップ
        if self.session:
            self.session.close()
            self.session = None
```

**メリット**: シンプル
**デメリット**: 毎回セッションを作り直す（非効率）

### 推奨: **仕様案A（Context Manager）**
- Pythonのベストプラクティス
- リソース管理が確実
- 再利用可能

---

## 4. test_partial_month_failure

### 現状
- 複数月のデータ取得で一部が失敗した場合の挙動が未定義
- 部分成功を許容すべきか、全失敗すべきか不明

### 仕様案A: Fail Fast（全失敗）

**方針**: 1つでも失敗したら全体を失敗とする

```python
async def get_by_location_and_date_range(...) -> WeatherDataWithLocationDTO:
    all_weather_data = []
    
    for month_period in month_periods:
        try:
            month_data = await self._fetch_month_data(...)
            all_weather_data.extend(month_data)
        except HtmlFetchError as e:
            # 1つでも失敗したら全体を失敗
            raise WeatherAPIError(
                f"Failed to fetch data for {year}-{month}: {e}. "
                f"Aborting entire request for data consistency."
            )
    
    return WeatherDataWithLocationDTO(...)
```

**メリット**:
- データの整合性が保証される
- 欠損がない完全なデータセット
- シンプルな実装

**デメリット**:
- 利用可能なデータも取得できない
- ユーザー体験が悪い

### 仕様案B: Partial Success（部分成功）

**方針**: 取得できたデータだけ返す

```python
async def get_by_location_and_date_range(...) -> WeatherDataWithLocationDTO:
    all_weather_data = []
    failed_months = []
    
    for month_period in month_periods:
        try:
            month_data = await self._fetch_month_data(...)
            all_weather_data.extend(month_data)
        except HtmlFetchError as e:
            # 失敗を記録するが続行
            failed_months.append((year, month))
            self.logger.warning(
                f"Failed to fetch {year}-{month}: {e}. "
                f"Continuing with available data."
            )
    
    # 1つもデータが取得できなかった場合のみエラー
    if not all_weather_data:
        raise WeatherDataNotFoundError(
            f"No weather data available. Failed months: {failed_months}"
        )
    
    # 部分的なデータを返す（警告付き）
    if failed_months:
        self.logger.warning(
            f"Partial data returned. Missing data for: {failed_months}"
        )
    
    return WeatherDataWithLocationDTO(...)
```

**メリット**:
- ユーザーが利用可能なデータを取得できる
- 部分的な障害に強い

**デメリット**:
- データが不完全（欠損がある）
- 下流処理で欠損を考慮する必要

### 仕様案C: Retry with Fallback

**方針**: 失敗したら再試行、それでも失敗なら部分成功

```python
async def get_by_location_and_date_range(...) -> WeatherDataWithLocationDTO:
    all_weather_data = []
    
    for month_period in month_periods:
        month_data = await self._fetch_month_data_with_retry(
            year, month, prec_no, block_no, max_retries=3
        )
        
        if month_data:
            all_weather_data.extend(month_data)
        # month_dataがNoneでも続行（警告は出す）
    
    if not all_weather_data:
        raise WeatherDataNotFoundError(...)
    
    return WeatherDataWithLocationDTO(...)

async def _fetch_month_data_with_retry(
    self, year: int, month: int, prec_no: int, block_no: int,
    max_retries: int = 3
) -> Optional[List[WeatherData]]:
    """Fetch month data with retry logic."""
    for attempt in range(max_retries):
        try:
            return await self._fetch_month_data(year, month, prec_no, block_no)
        except HtmlFetchError as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                self.logger.error(f"Failed after {max_retries} attempts: {e}")
                return None  # Give up
```

**メリット**:
- 一時的なネットワーク障害に強い
- データ取得率が向上

**デメリット**:
- 複雑
- 実行時間が長くなる可能性

### 推奨: **仕様案B（Partial Success）**
- 実用性重視
- ユーザーが一部のデータでも取得できる
- ログで欠損を明示
- 将来的に仕様案Cを追加検討

---

## 5. test_duplicate_dates_in_csv（詳細仕様）

### 実装案

```python
def _parse_jma_table(
    self,
    table: HtmlTable,
    start_date: str,
    end_date: str,
    year: int,
    month: int
) -> List[WeatherData]:
    """Parse JMA HTML table with duplicate detection."""
    weather_data_dict: Dict[datetime, WeatherData] = {}
    duplicate_count = 0
    
    for row in table.rows:
        try:
            # ... データ解析 ...
            
            record_date = datetime(year, month, day)
            
            # 重複チェック
            if record_date in weather_data_dict:
                duplicate_count += 1
                self.logger.warning(
                    f"Duplicate date detected: {record_date.date()}. "
                    f"Keeping first occurrence, discarding duplicate."
                )
                continue  # First Wins
            
            # Filter by date range
            if record_date < start_dt or record_date > end_dt:
                continue
            
            weather_data = WeatherData(...)
            
            # Validate before storing
            date_str = f"{year}-{month:02d}-{day:02d}"
            if self._validate_weather_data(weather_data, date_str):
                weather_data_dict[record_date] = weather_data
            
        except Exception as e:
            self.logger.warning(f"Failed to parse row: {e}")
            continue
    
    # 重複があった場合は警告
    if duplicate_count > 0:
        self.logger.warning(
            f"Detected {duplicate_count} duplicate dates in data. "
            f"Data quality issue."
        )
    
    # 日付順にソート
    return sorted(weather_data_dict.values(), key=lambda x: x.time)
```

**重複検出の追加メトリクス**:
```python
class WeatherDataQualityMetrics:
    """Data quality metrics for monitoring."""
    duplicate_dates: int = 0
    missing_columns: int = 0
    invalid_values: int = 0
    total_rows: int = 0
    
    @property
    def quality_score(self) -> float:
        """Calculate data quality score (0-1)."""
        if self.total_rows == 0:
            return 1.0
        issues = self.duplicate_dates + self.missing_columns + self.invalid_values
        return max(0.0, 1.0 - (issues / self.total_rows))
```

---

## 6. test_session_cleanup_on_error（詳細実装）

### 完全な実装案

```python
# src/agrr_core/framework/repositories/csv_downloader.py

import requests
import pandas as pd
from io import StringIO
from typing import Optional
from contextlib import asynccontextmanager
import asyncio

from agrr_core.entity.exceptions.csv_download_error import CsvDownloadError
from agrr_core.adapter.interfaces.csv_service_interface import CsvServiceInterface


class CsvDownloader(CsvServiceInterface):
    """CSV downloader with proper resource management."""
    
    def __init__(self, timeout: int = 30):
        """Initialize CSV downloader."""
        self.timeout = timeout
        self._session: Optional[requests.Session] = None
        self._is_closed = False
    
    def _ensure_session(self):
        """Ensure session exists."""
        if self._session is None or self._is_closed:
            self._session = requests.Session()
            self._is_closed = False
    
    async def download_csv(
        self,
        url: str,
        encoding: str = 'utf-8'
    ) -> pd.DataFrame:
        """Download and parse CSV data with automatic cleanup on error."""
        self._ensure_session()
        
        try:
            # Run blocking I/O in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._session.get(url, timeout=self.timeout)
            )
            response.raise_for_status()
            
            # Parse CSV
            csv_text = response.content.decode(encoding)
            df = pd.read_csv(StringIO(csv_text))
            
            return df
            
        except requests.RequestException as e:
            # Clean up on error
            self.close()
            raise CsvDownloadError(f"Failed to download CSV from {url}: {e}")
        except Exception as e:
            # Clean up on any error
            self.close()
            raise CsvDownloadError(f"Failed to process CSV: {e}")
    
    def close(self):
        """Close session and cleanup resources."""
        if self._session and not self._is_closed:
            self._session.close()
            self._is_closed = True
            self._session = None
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.close()
    
    def __enter__(self):
        """Context manager entry."""
        self._ensure_session()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.close()
        return False
```

**使用例**:
```python
# 同期的な使用
with CsvDownloader(timeout=30) as downloader:
    df = await downloader.download_csv(url)

# 非同期的な使用
async with CsvDownloader(timeout=30) as downloader:
    df = await downloader.download_csv(url)
```

**テストの更新**:
```python
@pytest.mark.asyncio
async def test_session_cleanup_on_error():
    """Test that CSV downloader cleans up resources on error."""
    downloader = CsvDownloader(timeout=1)
    
    try:
        await downloader.download_csv("http://invalid-url.test")
    except CsvDownloadError:
        pass  # Expected
    
    # Session should be cleaned up
    assert downloader._is_closed is True
    assert downloader._session is None
```

---

## 7. XPASS対応（実装済みテスト）

### test_all_null_temperature_values

**対応**: xfailマークを削除

```python
# tests/test_adapter/test_weather_jma_repository_critical.py

# Before:
@pytest.mark.xfail(reason="Data quality validation not implemented yet")
@pytest.mark.asyncio
async def test_all_null_temperature_values(...):

# After:
@pytest.mark.asyncio  # xfail削除
async def test_all_null_temperature_values(...):
    """Test handling of HTML table with all null temperature values."""
    # このテストは成功する（実装済み）
```

### test_distance_calculation_hokkaido_okinawa

**対応案1**: xfailマークを削除（ユークリッド距離で十分）
```python
# xfail削除 - ユークリッド距離で実用上問題なし
def test_distance_calculation_hokkaido_okinawa(...):
```

**対応案2**: Haversine距離を実装
```python
import math

def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Haversine distance in degrees (approximation)."""
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c  # Distance in km
```

**推奨**: 対応案1（xfail削除）- 日本国内ではユークリッド距離で十分

### test_year_boundary_crossing

**対応**: xfailマークを削除（実装済み）

```python
# xfail削除 - relativedeltaで正しく処理されている
@pytest.mark.asyncio
async def test_year_boundary_crossing(...):
    """Test date range crossing year boundary."""
```

---

## 実装優先順位

### Phase 1（即時対応）: XPASS解消
1. ✅ `test_all_null_temperature_values` - xfail削除
2. ✅ `test_year_boundary_crossing` - xfail削除
3. ✅ `test_distance_calculation_hokkaido_okinawa` - xfail削除またはreason更新

### Phase 2（短期: 1-2週間）: 高優先度
1. 🔴 `test_missing_required_columns` - Strict モード実装
2. 🟡 `test_duplicate_dates_in_csv` - First Wins + 警告実装

### Phase 3（中期: 1-2ヶ月）: 中優先度
1. 🟡 `test_session_cleanup_on_error` - Context Manager実装

### Phase 4（長期: 仕様確定後）: 低優先度
1. 🟢 `test_partial_month_failure` - 仕様決定後に実装

---

## まとめ

### xfail使用の正当性
- ✅ 4つのXFAILは全て正当（未実装機能を文書化）
- ⚠️ 3つのXPASSは技術的負債（実装済みなのにマークが残っている）

### 推奨仕様
1. **Missing Columns**: Strict モード（データ品質優先）
2. **Duplicate Dates**: First Wins + 警告（シンプルで予測可能）
3. **Session Cleanup**: Context Manager（Pythonic）
4. **Partial Failure**: Partial Success（ユーザー体験優先）

### 次のアクション
1. XPASSのxfailマークを削除（即時）
2. 優先度の高いXFAILから実装開始

