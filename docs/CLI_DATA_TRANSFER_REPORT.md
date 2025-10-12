# CLIコンポーネント データ移送レポート

## 概要

AGRRプロジェクトのCLIコンポーネントにおける、各層間のデータ移送を項目ごとに整理したドキュメントです。

## CLIコンポーネント一覧

### Controllers（5つ）
1. `GrowthPeriodOptimizeCliController` - 栽培期間最適化
2. `WeatherCliPredictController` - 天気予測
3. `WeatherCliFetchController` - 天気データ取得
4. `GrowthProgressCliController` - 生育進捗計算
5. `CropCliCraftController` - 作物要件生成

### Presenters（3つ）
1. `GrowthPeriodOptimizeCliPresenter` - 栽培期間最適化結果表示
2. `GrowthProgressCLIPresenter` - 生育進捗結果表示
3. `WeatherCLIPresenter` - 天気データ表示

---

## 1. GrowthPeriodOptimizeCliController（栽培期間最適化）

### データフロー

```
[CLI Args] → [Controller] → [RequestDTO] → [Interactor] → [ResponseDTO] → [Presenter] → [CLI Output]
```

### 層間データ移送

#### 1-1. CLI Args → Controller
**入力データ項目:**
- `--crop` (str): 作物名（例: "rice"）
- `--variety` (str, optional): 品種（例: "Koshihikari"）
- `--evaluation-start` (str): 評価期間開始日（YYYY-MM-DD形式）
- `--evaluation-end` (str): 評価期間終了日（YYYY-MM-DD形式）
- `--weather-file` (str): 天気データファイルパス
- `--field-config` (str): 圃場設定ファイルパス
- `--format` (str): 出力フォーマット（table/json）
- `--save-results` (bool): 結果保存フラグ
- `--crop-requirement-file` (str, optional): 作物要件ファイルパス

**処理:**
```python
# handle_optimize_command()内
evaluation_start = self._parse_date(args.evaluation_start)  # str → datetime
evaluation_end = self._parse_date(args.evaluation_end)      # str → datetime
```

#### 1-2. Controller → RequestDTO
**データ変換:**
```python
request = OptimalGrowthPeriodRequestDTO(
    crop_id=args.crop,                              # str
    variety=args.variety,                           # str | None
    evaluation_period_start=evaluation_start,       # datetime
    evaluation_period_end=evaluation_end,           # datetime
    weather_data_file=args.weather_file,           # str
    field=self.field,                              # Field Entity
    crop_requirement_file=getattr(args, 'crop_requirement_file', None),  # str | None
)
```

**重要な変換:**
- `--field-config`ファイル → `Field` Entity（Repository経由、Controller初期化時）
- 文字列の日付 → `datetime`オブジェクト

#### 1-3. Interactor → ResponseDTO
**ResponseDTO構造:**
```python
OptimalGrowthPeriodResponseDTO(
    optimal_start_date: datetime,       # 最適開始日
    completion_date: datetime,          # 完了日
    growth_days: int,                   # 栽培日数
    total_cost: float,                  # 総コスト
    daily_fixed_cost: float,           # 日次固定コスト
    field: Field,                       # Field Entity（不変）
    crop_name: str,                    # 作物名
    variety: str | None,               # 品種
    candidates: List[CandidateResult], # 全候補
)
```

**Field Entityの保持:**
- Request → Response まで同じField Entityインスタンスが参照される
- `field.daily_fixed_cost`がコスト計算に使用される
- Field Entityは`frozen=True`で不変

#### 1-4. ResponseDTO → Presenter
**Presenterでの利用項目:**
```python
# _present_table()内
response.crop_name                      # 作物名表示
response.variety                        # 品種表示
response.field.name                     # 圃場名表示
response.field.field_id                 # 圃場ID表示
response.field.area                     # 面積表示
response.field.location                 # 場所表示
response.field.daily_fixed_cost        # 日次コスト表示
response.optimal_start_date            # 最適開始日表示
response.completion_date               # 完了日表示
response.growth_days                   # 栽培日数表示
response.total_cost                    # 総コスト表示
response.candidates                    # 候補一覧表示
```

#### 1-5. データ整合性の保証
- **Field Entity不変性**: `@dataclass(frozen=True)`により、全層でデータが不変
- **参照の保持**: 同じField Entityインスタンスが全層で共有
- **型安全性**: DTOにより型が保証される

---

## 2. WeatherCliPredictController（天気予測）

### データフロー

```
[CLI Args] → [Controller] → [Interactor] → [Predictions] → [Presenter] → [CLI Output]
```

### 層間データ移送

#### 2-1. CLI Args → Controller
**入力データ項目:**
- `--input` (str): 履歴天気データファイルパス
- `--output` (str): 予測結果保存先パス
- `--days` (int): 予測日数（デフォルト: 7）

**処理:**
```python
# handle_predict_command()内
predictions = await self.predict_interactor.execute(
    input_source=args.input,            # str
    output_destination=args.output,     # str
    prediction_days=args.days           # int
)
```

#### 2-2. Interactor → Predictions
**出力データ構造:**
```python
# predictions: List[PredictionResult]
[
    {
        "date": "2024-11-01",
        "predicted_value": 18.5,
        "confidence_lower": 16.2,
        "confidence_upper": 20.8,
        "metric": "temperature"
    },
    ...
]
```

#### 2-3. Predictions → Presenter
**Presenterでの表示:**
```python
self.cli_presenter.display_success_message(
    f"✓ Prediction completed successfully!\n"
    f"  Model: ARIMA time series\n"
    f"  Generated: {len(predictions)} daily predictions\n"
    f"  Period: {args.days} days into the future\n"
    f"  Output: {args.output}"
)
```

**特徴:**
- ファイルベースの入出力（JSON/CSV）
- Gateway経由でファイル読み書き
- 予測結果はファイルに保存される

---

## 3. WeatherCliFetchController（天気データ取得）

### データフロー

```
[CLI Args] → [Controller] → [RequestDTO] → [Interactor] → [ResponseDTO] → [Presenter] → [CLI Output]
```

### 層間データ移送

#### 3-1. CLI Args → Controller（weatherコマンド）
**入力データ項目:**
- `--location` (str): 緯度,経度（例: "35.6762,139.6503"）
- `--start-date` (str, optional): 開始日（YYYY-MM-DD）
- `--end-date` (str, optional): 終了日（YYYY-MM-DD）
- `--days` (int): 履歴日数（デフォルト: 7）
- `--json` (bool): JSON出力フラグ

**処理:**
```python
# handle_weather_command()内
latitude, longitude = self.parse_location(args.location)  # str → (float, float)
start_date = self.parse_date(args.start_date)            # str → str (YYYY-MM-DD)
end_date = self.parse_date(args.end_date)                # str → str (YYYY-MM-DD)
```

#### 3-2. Controller → RequestDTO
**データ変換:**
```python
request = WeatherDataRequestDTO(
    latitude=latitude,         # float
    longitude=longitude,       # float
    start_date=start_date,     # str (YYYY-MM-DD)
    end_date=end_date          # str (YYYY-MM-DD)
)
```

#### 3-3. Interactor → ResponseDTO
**ResponseDTO構造:**
```python
WeatherDataListResponseDTO(
    data=[                           # List[WeatherDataResponseDTO]
        WeatherDataResponseDTO(
            time: str,                      # 日付
            temperature_2m_max: float,      # 最高気温
            temperature_2m_min: float,      # 最低気温
            temperature_2m_mean: float,     # 平均気温
            precipitation_sum: float,       # 降水量
            sunshine_duration: float,       # 日照時間（秒）
            sunshine_hours: float,          # 日照時間（時間）
            wind_speed_10m: float,          # 風速
            weather_code: int               # 天気コード
        ),
        ...
    ],
    total_count: int,                # データ件数
    location: LocationResponseDTO(   # 位置情報
        latitude: float,
        longitude: float,
        elevation: float,
        timezone: str
    )
)
```

#### 3-4. CLI Args → Controller（forecastコマンド）
**入力データ項目:**
- `--location` (str): 緯度,経度
- `--json` (bool): JSON出力フラグ

**RequestDTO:**
```python
request = WeatherForecastRequestDTO(
    latitude=latitude,         # float
    longitude=longitude        # float
)
```

#### 3-5. ResponseDTO → Presenter
**Presenterでの利用項目（テーブル形式）:**
```python
# display_weather_data()内
weather_data_list.location.latitude         # 緯度
weather_data_list.location.longitude        # 経度
weather_data_list.location.elevation        # 標高
weather_data_list.location.timezone         # タイムゾーン

for item in weather_data_list.data:
    item.time                              # 日付
    item.temperature_2m_max                # 最高気温
    item.temperature_2m_min                # 最低気温
    item.temperature_2m_mean               # 平均気温
    item.precipitation_sum                 # 降水量
    item.sunshine_hours                    # 日照時間
    item.wind_speed_10m                    # 風速
    item.weather_code                      # 天気コード
```

**Presenterでの利用項目（JSON形式）:**
```python
# display_weather_data_json()内
format_weather_data_list_dto(weather_data_list)  # → Dict形式に変換
```

---

## 4. GrowthProgressCliController（生育進捗計算）

### データフロー

```
[CLI Args] → [Controller] → [RequestDTO] → [Interactor] → [ResponseDTO] → [Presenter] → [CLI Output]
```

### 層間データ移送

#### 4-1. CLI Args → Controller
**入力データ項目:**
- `--crop` (str): 作物名（例: "rice"）
- `--variety` (str, optional): 品種（例: "Koshihikari"）
- `--start-date` (str): 栽培開始日（YYYY-MM-DD形式）
- `--weather-file` (str): 天気データファイルパス
- `--format` (str): 出力フォーマット（table/json）

**処理:**
```python
# handle_progress_command()内
start_date = datetime.strptime(args.start_date, "%Y-%m-%d")  # str → datetime
```

#### 4-2. Controller → RequestDTO
**データ変換:**
```python
request = GrowthProgressCalculateRequestDTO(
    crop_id=args.crop,                    # str
    variety=args.variety,                 # str | None
    start_date=start_date,                # datetime
    weather_data_file=args.weather_file   # str
)
```

#### 4-3. Interactor → ResponseDTO
**ResponseDTO構造:**
```python
GrowthProgressCalculateResponseDTO(
    crop_name: str,                       # 作物名
    variety: str | None,                  # 品種
    start_date: datetime,                 # 開始日
    progress_records: List[ProgressRecord],  # 進捗記録リスト
)

# ProgressRecord構造
ProgressRecord(
    date: datetime,                       # 日付
    stage_name: str,                      # ステージ名
    cumulative_gdd: float,                # 累積GDD
    growth_percentage: float,             # 成長率（%）
    is_complete: bool,                    # 完了フラグ
    total_required_gdd: float             # 必要GDD総量
)
```

#### 4-4. ResponseDTO → Presenter
**Presenterでの利用項目（テーブル形式）:**
```python
# _present_table()内
response.crop_name                        # 作物名
response.variety                          # 品種
response.start_date                       # 開始日
len(response.progress_records)            # レコード数

for record in response.progress_records:
    record.date                           # 日付
    record.stage_name                     # ステージ名
    record.cumulative_gdd                 # 累積GDD
    record.growth_percentage              # 成長率
    record.is_complete                    # 完了フラグ
    record.total_required_gdd             # 必要GDD総量
```

**Presenterでの利用項目（JSON形式）:**
```python
# _present_json()内
response.to_dict()  # ResponseDTOを辞書形式に変換
```

---

## 5. CropCliCraftController（作物要件生成）

### データフロー

```
[CLI Args] → [Controller] → [RequestDTO] → [Interactor] → [JSON Result] → [CLI Output]
```

### 層間データ移送

#### 5-1. CLI Args → Controller
**入力データ項目:**
- `--query` (str): 作物クエリ（例: "トマト", "アイコトマト", "稲"）
- `--json` (bool): JSON出力フラグ

**処理:**
```python
# handle_craft_command()内
request = CropRequirementCraftRequestDTO(crop_query=args.query)
```

#### 5-2. Controller → RequestDTO
**データ変換:**
```python
CropRequirementCraftRequestDTO(
    crop_query=args.query  # str（日本語可）
)
```

#### 5-3. Interactor → JSON Result
**出力データ構造:**
```python
{
    "success": True,
    "data": {
        "crop_name": str,                # 作物名（英語）
        "variety": str,                  # 品種
        "base_temperature": float,       # 基準温度
        "gdd_requirement": float,        # 必要GDD総量
        "stages": [                      # ステージリスト
            {
                "name": str,                    # ステージ名
                "gdd_requirement": float,       # ステージ必要GDD
                "optimal_temp_min": float,      # 最適温度（最小）
                "optimal_temp_max": float,      # 最適温度（最大）
                "description": str              # 説明（日本語）
            },
            ...
        ]
    }
}
```

#### 5-4. JSON Result → CLI Output
**出力:**
```python
print(json.dumps(result, ensure_ascii=False))  # JSON文字列として出力
```

**特徴:**
- Presenter層を経由せず直接JSON出力
- LLM経由で生成されるため、成功/失敗の両パターンを処理
- 日本語クエリ → 英語データへの変換をLLMが担当

---

## 6. GrowthPeriodOptimizeCliPresenter（栽培期間最適化結果表示）

### データフロー

```
[ResponseDTO] → [Presenter] → [Formatted Output] → [CLI]
```

### 層間データ移送

#### 6-1. ResponseDTO → Presenter
**受け取るDTO:**
```python
OptimalGrowthPeriodResponseDTO(
    optimal_start_date: datetime,
    completion_date: datetime,
    growth_days: int,
    total_cost: float,
    daily_fixed_cost: float,
    field: Field,
    crop_name: str,
    variety: str | None,
    candidates: List[CandidateResult],
)
```

#### 6-2. Presenter → Formatted Output
**テーブル形式:**
```
=== Optimal Growth Period Analysis ===
Crop: Rice (Koshihikari)

Field Information:
  Field: 北圃場 (field_01)
  Area: 1,000.0 m²
  Location: 北区画
  Daily Fixed Cost: ¥5,000/day

Optimal Solution:
  Start Date: 2024-04-15
  Completion Date: 2024-09-18
  Growth Days: 156 days
  Total Cost: ¥780,000

All Candidates:
Start Date      Completion      Days   Total Cost      Status
--------------------------------------------------------------
2024-04-15      2024-09-18        156   ¥780,000       ← OPTIMAL
2024-04-20      2024-09-22        155   ¥775,000       
```

**JSON形式:**
```python
response.to_dict()  # ResponseDTOの全データを辞書形式に変換
```

**データ変換処理:**
- `datetime` → 文字列（YYYY-MM-DD形式）
- `float` → カンマ区切り数値表示（¥1,000,000）
- `Field` Entity → 複数の項目に展開

---

## 7. GrowthProgressCLIPresenter（生育進捗結果表示）

### データフロー

```
[ResponseDTO] → [Presenter] → [Formatted Output] → [CLI]
```

### 層間データ移送

#### 7-1. ResponseDTO → Presenter
**受け取るDTO:**
```python
GrowthProgressCalculateResponseDTO(
    crop_name: str,
    variety: str | None,
    start_date: datetime,
    progress_records: List[ProgressRecord],
)
```

#### 7-2. Presenter → Formatted Output
**テーブル形式:**
```
=== Growth Progress for rice ===
Variety: Koshihikari
Start Date: 2024-05-01
Total Records: 137

Date         Stage                GDD        Progress   Complete
-----------------------------------------------------------------
2024-05-01   germination         10.3         0.4%         No
2024-05-02   germination         22.8         1.0%         No
...
2024-09-15   ripening          2400.0       100.0%        Yes

Final Progress: 100.0%
Total GDD Accumulated: 2400.0 / 2400.0
```

**JSON形式:**
```python
response.to_dict()  # ResponseDTOの全データを辞書形式に変換
```

**データ変換処理:**
- `datetime` → 文字列（YYYY-MM-DD形式）
- `float` → 小数点1桁表示
- `bool` → "Yes"/"No"表示

---

## 8. WeatherCLIPresenter（天気データ表示）

### データフロー

```
[ResponseDTO] → [Presenter] → [Formatted Output] → [CLI]
```

### 層間データ移送

#### 8-1. ResponseDTO → Presenter
**受け取るDTO:**
```python
WeatherDataListResponseDTO(
    data: List[WeatherDataResponseDTO],
    total_count: int,
    location: LocationResponseDTO
)
```

#### 8-2. Presenter → Formatted Output
**テーブル形式:**
```
================================================================================
WEATHER FORECAST
================================================================================

Location: 35.6762°N, 139.6503°E | Elevation: 40m | Timezone: Asia/Tokyo

Date         Max Temp   Min Temp   Avg Temp   Precip   Sunshine   Wind Speed   Weather
----------------------------------------------------------------------------------------
2024-10-01   25.5°C     15.2°C     20.3°C     0.0mm    8.0h       10.5km/h     0
2024-10-02   26.0°C     16.0°C     21.0°C     2.5mm    7.5h       12.0km/h     3

================================================================================
Total records: 7
================================================================================
```

**JSON形式:**
```json
{
  "success": true,
  "data": {
    "data": [
      {
        "time": "2024-10-01",
        "temperature_2m_max": 25.5,
        "temperature_2m_min": 15.2,
        "temperature_2m_mean": 20.3,
        "precipitation_sum": 0.0,
        "sunshine_duration": 28800.0,
        "sunshine_hours": 8.0,
        "wind_speed_10m": 10.5,
        "weather_code": 0
      }
    ],
    "total_count": 7,
    "location": {
      "latitude": 35.6762,
      "longitude": 139.6503,
      "elevation": 40.0,
      "timezone": "Asia/Tokyo"
    }
  }
}
```

**データ変換処理:**
- `float` → 単位付き表示（°C, mm, h, km/h）
- `None` → "N/A"表示
- `datetime` → YYYY-MM-DD形式
- エラー時はUnicode絵文字のフォールバック対応

---

## データ移送パターンの分類

### パターン1: Entity保持型（GrowthPeriodOptimize）
**特徴:**
- Field EntityがRequest → Response → Presenterまで同じインスタンスとして保持される
- Entity不変性（frozen=True）により整合性が保証される
- 参照渡しで効率的

**データフロー:**
```
Field JSON → Field Entity → RequestDTO.field → ResponseDTO.field → Presenter
（同一インスタンス）
```

### パターン2: ファイルベース型（WeatherPredict）
**特徴:**
- 入出力ともにファイルパス指定
- Gateway層でファイル読み書きを処理
- 大量データの処理に適している

**データフロー:**
```
Input File Path → Gateway → Processing → Gateway → Output File Path
```

### パターン3: API連携型（WeatherFetch）
**特徴:**
- 外部API（Open-Meteo）からデータ取得
- Location情報を含む複雑なDTO構造
- テーブル/JSON両形式の出力対応

**データフロー:**
```
Location (lat,lon) → API Gateway → WeatherData Entity → DTO → Presenter
```

### パターン4: LLM生成型（CropCraft）
**特徴:**
- LLM（Claude）による動的データ生成
- 日本語クエリ → 英語データへの変換
- 成功/失敗の両パターンを処理

**データフロー:**
```
Japanese Query → LLM Gateway → Structured JSON → Direct Output
```

### パターン5: 計算型（GrowthProgress）
**特徴:**
- 天気データと作物要件から日次進捗を計算
- 時系列データの処理（List[ProgressRecord]）
- 累積値の計算

**データフロー:**
```
Start Date + Weather File → Calculation → List[ProgressRecord] → Presenter
```

---

## データ整合性の保証メカニズム

### 1. 型安全性
**DTO（Data Transfer Object）の使用:**
- 各層の境界でDTOを使用し、型を明示
- dataclass + type hintsにより静的型チェック可能
- 誤ったデータ型の混入を防止

### 2. 不変性（Immutability）
**Field Entityの例:**
```python
@dataclass(frozen=True)
class Field:
    field_id: str
    name: str
    area: float
    daily_fixed_cost: float
    location: Optional[str] = None
```
- `frozen=True`により変更不可
- 全層で同じデータが保証される

### 3. バリデーション
**各層でのバリデーション:**
- **Controller層**: 日付フォーマット、座標範囲チェック
- **DTO層**: 必須フィールドチェック、型チェック
- **Entity層**: ビジネスルールチェック（負の値の拒否など）

### 4. エラーハンドリング
**一貫したエラー処理:**
```python
try:
    response = await self.execute(request)
    self.presenter.present(response)
except ValueError as e:
    self.cli_presenter.display_error(str(e), "VALIDATION_ERROR")
except Exception as e:
    self.cli_presenter.display_error(f"Unexpected error: {e}", "INTERNAL_ERROR")
```

---

## CLIコンポーネントの設計原則

### 1. Controller層の責務
- ✅ CLI引数のパース
- ✅ データ変換（文字列 → datetime等）
- ✅ Interactorのインスタンス化と実行
- ✅ Presenterへの結果受け渡し
- ❌ ビジネスロジックは含まない
- ❌ UseCase層のインターフェースをインジェクトしない（Adapter層のみ）

### 2. Presenter層の責務
- ✅ ResponseDTOのフォーマット
- ✅ テーブル/JSON形式の切り替え
- ✅ 単位付き数値表示（¥, °C, mm等）
- ❌ ビジネスロジックは含まない
- ❌ データの加工は最小限（表示用のみ）

### 3. DTOの設計原則
- ✅ イミュータブル（frozen dataclass）
- ✅ 型ヒント必須
- ✅ to_dict()メソッドでJSON変換可能
- ✅ ビジネスロジックは含まない
- ❌ 複雑な計算ロジックは持たない

### 4. データ変換の原則
- ✅ 層の境界で明示的に変換
- ✅ 変換ロジックは単純に保つ
- ✅ エラーハンドリングを忘れない
- ❌ 暗黙的な変換は避ける

---

## 改善提案

### 1. 共通化の機会
**日付パース処理:**
- 複数のControllerで同じ`_parse_date()`メソッドが実装されている
- 共通のUtilityクラスへの移動を検討

**エラーハンドリング:**
- 各Controllerで類似のtry-except構造
- デコレータまたはベースクラスでの共通化を検討

### 2. テスト戦略
**各層の単体テスト:**
- Controller: 引数パースと変換のテスト
- Presenter: フォーマット出力のテスト
- DTO: バリデーションのテスト

**統合テスト:**
- CLI引数 → 出力までのEnd-to-Endテスト
- モックを使わない実データでのテスト

### 3. ドキュメント化
**各CLIコマンドのドキュメント:**
- ✅ ヘルプテキストが充実している
- ✅ Examples付き
- ✅ フォーマット説明あり
- 改善点: ユーザーマニュアルの作成

---

## まとめ

### データ移送の特徴
1. **明確な層分離**: Controller → DTO → Interactor → DTO → Presenter
2. **型安全性**: dataclass + type hints
3. **不変性**: Field Entityなど重要データはfrozen
4. **多様なパターン**: Entity保持、ファイルベース、API連携、LLM生成、計算型

### 設計の強み
- Clean Architectureに準拠
- 各層の責務が明確
- テストが容易
- 拡張性が高い

### 今後の改善点
- 共通処理の抽出
- テストカバレッジの向上
- エラーメッセージの多言語対応

---

## 関連ドキュメント
- [LAYER_DATA_TRANSFER_SUMMARY.md](LAYER_DATA_TRANSFER_SUMMARY.md) - optimize-period詳細
- [ARCHITECTURE.md](../ARCHITECTURE.md) - 全体アーキテクチャ
- [FIELD_CONFIG_FORMAT.md](FIELD_CONFIG_FORMAT.md) - 圃場設定フォーマット

