# 必須カラムの欠損処理 - 詳細仕様

## 1. JMAのHTMLテーブル構造

気象庁（JMA）から取得するHTMLテーブルの構造：

### 正常なテーブル行（完全なデータ）
```
cells[0]  = '1'        # 日（必須）
cells[1]  = '1013.0'   # 気圧（現地）
cells[2]  = '1023.0'   # 気圧（海面）
cells[3]  = '0.0'      # 降水量合計(mm)（必須）
cells[4]  = ...        # その他
cells[5]  = ...
cells[6]  = '6.4'      # 平均気温(℃)（重要）
cells[7]  = '10.5'     # 最高気温(℃)（重要）
cells[8]  = '2.3'      # 最低気温(℃)（重要）
cells[9]  = ...
cells[10] = '3.0'      # 平均風速(m/s)
cells[11] = ...
cells[12] = '3.5'      # 最大風速(m/s)
cells[13] = ...
...
cells[16] = '5.2'      # 日照時間(h)
```

### 問題のある行（カラムが欠損）
```
# ケース1: 短すぎる行（cells[0-3]しかない）
cells[0]  = '1'        # 日
cells[1]  = '1013.0'   # 気圧
cells[2]  = '1023.0'   # 気圧
cells[3]  = '0.0'      # 降水量
# cells[4-16] が存在しない！← 気温データが取得できない
```

---

## 2. 「必須カラム」の定義

### 現在の実装（緩い）
```python
# weather_jma_repository.py line 318
if len(row.cells) < 17:
    continue  # スキップするだけ
```
- 17個未満のセルがある行はスキップ
- **問題**: どのカラムが本当に必要か不明確

### 提案する仕様（厳密）

#### レベル1: 絶対必須（これがないと行として無効）
- `cells[0]`: **日付** - これがないと何のデータか不明

#### レベル2: 農業予測に必須（気温のみ）
- `cells[6]`: **平均気温** - GDD計算に使用
- `cells[7]`: **最高気温** - ストレス評価に使用
- `cells[8]`: **最低気温** - 霜害リスク評価に使用

**重要**: 気温3つ（mean, max, min）のうち、**少なくとも1つ**があればOK
- 平均気温があれば最適
- なければ最高・最低から計算可能

#### レベル3: オプション（欠損していてもOK）
- `cells[3]`: 降水量 - あると良いが必須ではない
- `cells[16]`: 日照時間 - 光合成評価（オプション）
- `cells[10-12]`: 風速 - 病害リスク（オプション）
- その他の気象データ - 全てオプション

---

## 3. 具体的な問題シナリオ

### シナリオ1: 短すぎる行

**入力データ**:
```python
row.cells = ['1', '1013.0', '1023.0', '0.0']
# 4つしかない！cells[6-8]（気温）が存在しない
```

**現在の挙動**:
```python
if len(row.cells) < 17:
    continue  # 行をスキップ → 1月1日のデータが消える
```

**問題点**:
- データが欠落したことに気づきにくい
- なぜスキップされたか不明（ログもない）

**提案する処理**:
```python
# 必須カラムの明示的なチェック
# 気温取得に必要な最低限のカラム数
REQUIRED_FOR_TEMPERATURE = 9  # cells[0-8]まで（日付 + 気温3種）

if len(row.cells) < REQUIRED_FOR_TEMPERATURE:
    self.logger.warning(
        f"Row has insufficient columns: {len(row.cells)} < {REQUIRED_FOR_TEMPERATURE}. "
        f"Cannot extract temperature data. "
        f"Skipping row for day '{row.cells[0] if row.cells else 'N/A'}'."
    )
    return None  # この行は無効

# 日付の存在チェック（絶対必須）
if not row.cells[0] or not row.cells[0].strip().isdigit():
    self.logger.warning(f"Invalid or missing date. Skipping row.")
    return None

# 気温カラムのチェック（少なくとも1つ必要）
temp_mean = self._safe_float(row.cells[6])
temp_max = self._safe_float(row.cells[7])
temp_min = self._safe_float(row.cells[8])

if temp_mean is None and temp_max is None and temp_min is None:
    self.logger.warning(
        f"All temperature values are None for row. "
        f"Temperature is required for agricultural predictions. Skipping."
    )
    return None  # 気温が全くないので無効
```

---

## 4. 実装例の比較

### ケースA: 気温が欠損している日のデータ

**データ**:
```
2024-01-01: 降水量=0.0mm, 気温=None, None, None
2024-01-02: 降水量=2.5mm, 気温=6.4℃, 10.5℃, 2.3℃
```

#### 現在の実装（緩い）
```python
# cells[6-8]がNoneでもWeatherDataを作成
weather_data = WeatherData(
    time=datetime(2024, 1, 1),
    temperature_2m_max=None,  # ← これでもOK
    temperature_2m_min=None,
    temperature_2m_mean=None,
    precipitation_sum=0.0,
)
# 結果: 2日分のデータを返す
```

**問題**:
- 気温がないデータが混入
- GDD計算ができない（`temperature_2m_mean`が必須）
- 下流で`None`チェックが必要

#### 提案する実装（厳密）

**仕様A: Strict - 気温必須**
```python
# 気温が全てNoneの場合は無効
if (temp_max is None and 
    temp_min is None and 
    temp_mean is None):
    self.logger.warning(
        f"All temperature values are None for {record_date.date()}. "
        f"Cannot use for agricultural predictions. Skipping."
    )
    return None  # この日のデータは無効

# 結果: 1日分のデータのみ返す（2024-01-02のみ）
```

**仕様B: Lenient - 部分データも許容**
```python
# 気温が全てNoneでも許容
weather_data = WeatherData(
    temperature_2m_max=None,  # Noneでも受け入れる
    ...
)
# ただし警告は出す
if temp_max is None and temp_min is None:
    self.logger.info(f"Temperature data missing for {record_date.date()}")

# 結果: 2日分のデータを返す（どちらも）
```

---

## 5. 具体的な影響範囲

### シナリオ: 2024年1月のデータ取得

**取得したHTMLテーブル**:
```
Day  Precip  Temp_Mean  Temp_Max  Temp_Min  Sunshine
1    0.0     6.4        10.5      2.3       5.2        ✅ 完全
2    2.5     --         --        --        3.1        ❌ 気温欠損
3    0.0     7.2        11.2      3.1       4.8        ✅ 完全
4    1.0                                               ❌ ほぼ全て欠損
...（省略）
```

### 処理結果の比較

#### 現在の実装
```python
if len(row.cells) < 17:
    continue  # 行をスキップ
```
**結果**: 
- Day 1: ✅ 取得（17カラム以上）
- Day 2: ✅ 取得（17カラム以上、気温はNone）
- Day 3: ✅ 取得
- Day 4: ❌ スキップ（カラム数不足）

**返却**: 3日分のデータ（Day 2は気温None）

#### 提案する実装（Strict）
```python
# 必須カラムチェック
if len(row.cells) <= 8:  # cells[0-8]必須
    self.logger.warning(f"Insufficient columns: {len(row.cells)}")
    return None

# 気温の必須チェック
if temp_mean is None:
    self.logger.warning(f"Temperature data missing for {record_date}")
    return None  # 気温がないデータは無効
```
**結果**:
- Day 1: ✅ 取得（完全なデータ）
- Day 2: ❌ スキップ（気温欠損）← **これが「無効」の意味**
- Day 3: ✅ 取得（完全なデータ）
- Day 4: ❌ スキップ（カラム数不足）

**返却**: 2日分のデータのみ（Day 1, 3）

---

## 6. 「無効」とする基準

### 提案する基準

```python
def _is_row_valid(self, row: TableRow) -> bool:
    """
    行が有効かどうかを判定
    
    無効とする条件:
    1. カラム数が最低限（9個）未満 → 気温データにアクセスできない
    2. 日付カラム（cells[0]）が空または不正 → 何日のデータか不明
    3. 気温カラム（cells[6,7,8]）が全てNone → GDD計算不可
    
    有効とする条件:
    - 日付があり、気温データが少なくとも1つあればOK
    - 降水量、日照、湿度などは欠損していてもOK（オプション）
    """
    # 条件1: カラム数チェック（気温データにアクセスできるか）
    MIN_REQUIRED_CELLS = 9  # cells[0-8]（日付 + 気温3種まで）
    if len(row.cells) < MIN_REQUIRED_CELLS:
        return False
    
    # 条件2: 日付チェック（絶対必須）
    day_str = row.cells[0].strip()
    if not day_str or not day_str.isdigit():
        return False
    
    # 条件3: 気温チェック（必須だが柔軟）
    temp_mean = self._safe_float(row.cells[6])
    temp_max = self._safe_float(row.cells[7])
    temp_min = self._safe_float(row.cells[8])
    
    # 気温が少なくとも1つあればOK
    # 平均気温が最優先
    if temp_mean is not None:
        return True
    
    # または最高・最低から平均を計算可能ならOK
    if temp_max is not None or temp_min is not None:
        return True
    
    # 気温が全くない場合のみ無効
    return False
```

**具体例**:
```python
# ✅ 有効な行
cells = ['1', '1013.0', '1023.0', '0.0', ..., '6.4', '10.5', '2.3', ...]
# → 日付あり、気温あり → データ取得

# ❌ 無効な行（気温欠損）
cells = ['2', '1013.0', '1023.0', '2.5', ..., None, None, None, ...]
# → 日付あり、気温なし → スキップ（無効）

# ❌ 無効な行（カラム不足）
cells = ['3', '1013.0', '1023.0', '0.0']
# → カラム数不足（4 < 9） → スキップ（無効）
```

---

## 7. 実装時の考慮点

### なぜ「無効」とするのか？

#### 理由1: 農業予測の要件
```python
# 成長度日（GDD）計算には気温が必須
def calculate_gdd(temp_mean: float, base_temp: float) -> float:
    return max(0, temp_mean - base_temp)

# temp_meanがNoneの場合
calculate_gdd(None, 10.0)  # ← エラー！
```
- 気温データがないとGDD計算不可
- 作物の成長予測ができない
- **データとして意味がない**

#### 理由2: データ品質保証
```python
# 下流の処理で常にNoneチェックが必要
for weather_data in data_list:
    if weather_data.temperature_2m_mean is not None:  # ← 面倒
        gdd = calculate_gdd(...)
    else:
        # どうする？スキップ？エラー？
        pass
```
- 不完全なデータが混入すると下流処理が複雑化
- **ソースで品質を保証する**べき

#### 理由3: エラー検出
```python
# データソースの問題を早期発見
result = await repository.get_by_location_and_date_range(...)

if len(result.weather_data_list) < expected_days:
    # 欠損があることがすぐわかる
    logger.warning(f"Expected {expected_days} days, got {len(result.weather_data_list)}")
```

---

## 8. 実装の提案

### Strict モード（推奨）

```python
def _parse_row(
    self,
    row: TableRow,
    year: int,
    month: int
) -> Optional[WeatherData]:
    """
    Parse a single row from JMA HTML table.
    
    Returns:
        WeatherData if row is valid
        None if row is invalid (will be skipped)
    """
    # ==========================================
    # Step 1: カラム数の事前チェック
    # ==========================================
    MIN_REQUIRED_CELLS = 9  # cells[0-8]まで必須
    
    if len(row.cells) < MIN_REQUIRED_CELLS:
        self.logger.warning(
            f"Invalid row: only {len(row.cells)} columns "
            f"(minimum {MIN_REQUIRED_CELLS} required). "
            f"First cell: '{row.cells[0] if row.cells else 'EMPTY'}'"
        )
        return None  # ← この行は「無効」
    
    # ==========================================
    # Step 2: 日付の必須チェック
    # ==========================================
    day_str = row.cells[0].strip()
    if not day_str or not day_str.isdigit():
        self.logger.warning(f"Invalid day value: '{day_str}'")
        return None  # ← 日付がないので「無効」
    
    day = int(day_str)
    record_date = datetime(year, month, day)
    
    # ==========================================
    # Step 3: データ抽出
    # ==========================================
    # 気温データ（必須）
    temp_mean = self._safe_float(row.cells[6])
    temp_max = self._safe_float(row.cells[7])
    temp_min = self._safe_float(row.cells[8])
    
    # その他のデータ（オプション - Noneでも可）
    precipitation = self._safe_float(row.cells[3]) if len(row.cells) > 3 else None
    # ↑ 降水量が欠損していてもOK
    
    # ==========================================
    # Step 4: 気温の必須チェック（唯一の必須項目）
    # ==========================================
    # 農業予測には気温が必須（少なくとも1つ）
    if temp_mean is None and temp_max is None and temp_min is None:
        self.logger.warning(
            f"[{record_date.date()}] All temperature values are None. "
            f"Cannot use for agricultural predictions (GDD calculation requires temperature)."
        )
        return None  # ← 気温が全くないので「無効」
    
    # 平均気温がなければ最高・最低から計算
    if temp_mean is None and temp_max is not None and temp_min is not None:
        temp_mean = (temp_max + temp_min) / 2
        self.logger.info(f"[{record_date.date()}] Calculated mean temp from max/min")
    
    # ==========================================
    # Step 5: オプショナルデータ（全て欠損OK）
    # ==========================================
    sunshine_hours = self._safe_float(row.cells[16] if len(row.cells) > 16 else None)
    sunshine_duration = sunshine_hours * 3600 if sunshine_hours is not None else None
    # ← sunshine_durationがNoneでもOK（オプション）
    
    wind_speed_max = self._safe_float(row.cells[12] if len(row.cells) > 12 else None)
    wind_speed_avg = self._safe_float(row.cells[10] if len(row.cells) > 10 else None)
    # ← 風速がNoneでもOK（オプション）
    
    # 降水量もNoneでOK（オプション）
    
    # ==========================================
    # Step 6: WeatherDataエンティティ作成
    # ==========================================
    weather_data = WeatherData(
        time=record_date,
        temperature_2m_max=temp_max,      # 必須（少なくとも1つ）
        temperature_2m_min=temp_min,      # 必須（少なくとも1つ）
        temperature_2m_mean=temp_mean,    # 必須（少なくとも1つ）
        precipitation_sum=precipitation,  # オプション（Noneでも可）
        sunshine_duration=sunshine_duration,  # オプション（Noneでも可）
        wind_speed_10m=wind_speed,       # オプション（Noneでも可）
    )
    
    # ==========================================
    # Step 7: データ品質検証
    # ==========================================
    if not self._validate_weather_data(weather_data, str(record_date.date())):
        return None  # ← バリデーション失敗で「無効」
    
    return weather_data  # ← この行は「有効」
```

---

## 9. 実際の影響

### 例: 2024年1月の31日間のデータ取得

**取得したHTMLテーブル**:
```
31行のデータ
├─ 26行: 完全なデータ（気温、降水量、日照など全て有り）
├─ 2行: カラム数不足（4カラムのみ、気温にアクセス不可）← 無効
├─ 1行: 気温データ欠損（降水量・日照はあるが気温なし）← 無効
└─ 2行: 降水量欠損（気温はあるが降水量なし）← 有効！
```

#### 現在の実装（緩い）
```python
if len(row.cells) < 17:
    continue  # カラム数だけチェック
```
**結果**: 26日分のデータ（降水量欠損の2行も含む、気温欠損は混入の可能性）

#### 提案する実装（気温のみ必須）
```python
# カラム数チェック: 2行スキップ（気温にアクセス不可）
# 気温必須チェック: 1行スキップ（気温が全てNone）
# 降水量チェック: しない（欠損OK）
# 計: 3行スキップ
```
**結果**: 28日分のデータ
- 26日: 完全なデータ
- 2日: 気温あり、降水量なし ← **これもOK**

**メリット**:
- GDD計算が確実に動作（気温は保証）
- 降水量欠損でもデータを活用可能
- 柔軟性と品質のバランス

**ユーザーへの通知**:
```
Warning: Skipped 3 days due to missing temperature data:
  - 2024-01-05: Insufficient columns (4 < 9) - cannot access temperature
  - 2024-01-12: Insufficient columns (4 < 9) - cannot access temperature
  - 2024-01-20: All temperature values are None

Info: 2 days have missing precipitation data (using None):
  - 2024-01-15: precipitation=None (temperature=8.5℃)
  - 2024-01-22: precipitation=None (temperature=7.2℃)

Returning 28 days of valid data (requested 31 days).
All returned data has temperature values for GDD calculation.
```

---

## 10. まとめ

### 「必須カラムが欠損している行は無効」の意味

**簡潔に言うと**:
> 農業予測に必要な最低限のデータ（**日付と気温**）が揃っていない行は、
> データとして不完全なので取得せず、スキップする（無効とする）。
> 
> **降水量、日照、湿度などは欠損していてもOK**（オプション扱い）。

### メリット
1. ✅ **GDD計算が保証** - 気温データは必ず存在
2. ✅ **柔軟性** - 降水量や日照が欠損していてもデータを活用
3. ✅ **データ取得量** - 気温さえあれば取得（最大限活用）
4. ✅ **明確な基準** - 何が必須で何がオプションか明確

### デメリット
1. ⚠️ 降水量や日照がNoneの可能性 - 下流で部分的にNoneチェック必要
2. ⚠️ 完全なデータセットではない - 一部の分析には使えない可能性

### 推奨
**気温のみ必須モード** - GDD計算を保証しつつデータを最大限活用

### 設定例
```python
class WeatherJMARepository:
    """
    必須データ:
    - 日付: 絶対必須
    - 気温: 必須（mean, max, min のいずれか1つ以上）
    
    オプションデータ（Noneでも可）:
    - 降水量
    - 日照時間
    - 風速
    - 湿度
    - その他全ての気象データ
    """
    def __init__(
        self,
        html_fetcher: HtmlTableFetchInterface,
        require_temperature: bool = True,      # 気温を必須とするか
        require_precipitation: bool = False,   # 降水量を必須とするか（デフォルト: オプション）
        require_sunshine: bool = False,        # 日照を必須とするか（デフォルト: オプション）
    ):
        self.require_temperature = require_temperature
        self.require_precipitation = require_precipitation
        self.require_sunshine = require_sunshine
```

