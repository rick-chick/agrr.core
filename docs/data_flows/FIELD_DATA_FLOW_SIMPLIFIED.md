# フィールド設定データフロー（簡素化版）

## 設計方針

**optimize-period は単一圃場の最適化を行う**ため、フィールド設定ファイルを直接指定するだけでよい。

## 変更点

### ❌ 削除するもの
- `--field` オプション（フィールドIDを指定する必要なし）
- `--daily-cost` オプション（フィールド設定から自動取得）

### ✅ 残すもの
- `--field-config` オプション（フィールド設定ファイルパス）

## データフロー図

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. CLI入力 (Framework Layer)                                         │
│    cli.py                                                             │
├─────────────────────────────────────────────────────────────────────┤
│ Input: コマンドライン引数                                              │
│   agrr optimize-period optimize \                                     │
│     --crop rice \                                                     │
│     --evaluation-start 2024-04-01 \                                   │
│     --evaluation-end 2024-09-30 \                                     │
│     --weather-file weather.json \                                     │
│     --field-config field_01.json  ← これだけ！                        │
│                                                                        │
│ Processing:                                                            │
│   - field-config パスを抽出: "field_01.json"                          │
│   - FieldFileRepository 初期化                                        │
│   - field.json からFieldエンティティを読み込み                        │
│                                                                        │
│ Output:                                                                │
│   field: Field(                                                        │
│     field_id="field_01",                                              │
│     name="北圃場",                                                     │
│     area=1000.0,                                                      │
│     daily_fixed_cost=5000.0,                                          │
│     location="北区画"                                                  │
│   )                                                                   │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 2. Controller (Adapter Layer)                                         │
│    GrowthPeriodOptimizeCliController                                  │
├─────────────────────────────────────────────────────────────────────┤
│ Input:                                                                 │
│   args.field_config = "field_01.json"                                │
│   field = Field(...) ← CLIから渡される                                │
│                                                                        │
│ Processing:                                                            │
│   - バリデーション（field_config必須）                                 │
│   - DTOに変換                                                          │
│                                                                        │
│ Output: OptimalGrowthPeriodRequestDTO                                 │
│   crop_id: "rice"                                                     │
│   variety: "Koshihikari"                                              │
│   evaluation_period_start: datetime(2024, 4, 1)                       │
│   evaluation_period_end: datetime(2024, 9, 30)                        │
│   weather_data_file: "weather.json"                                   │
│   field: Field(field_id="field_01", ..., daily_fixed_cost=5000.0)    │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 3. Interactor (UseCase Layer)                                         │
│    GrowthPeriodOptimizeInteractor                                     │
├─────────────────────────────────────────────────────────────────────┤
│ Input: OptimalGrowthPeriodRequestDTO                                  │
│   request.field = Field(                                              │
│     field_id="field_01",                                              │
│     daily_fixed_cost=5000.0,                                          │
│     ...                                                                │
│   )                                                                   │
│                                                                        │
│ Processing:                                                            │
│   1. daily_fixed_cost = request.field.daily_fixed_cost  # 5000.0     │
│   2. 各候補日の評価:                                                   │
│      for start_date in candidates:                                    │
│          growth_days = calculate_growth_days(...)                     │
│          total_cost = growth_days × daily_fixed_cost                  │
│   3. 最小コストの候補を選択                                             │
│                                                                        │
│ Output: OptimalGrowthPeriodResponseDTO                                │
│   optimal_start_date: datetime(2024, 4, 15)                           │
│   completion_date: datetime(2024, 9, 18)                              │
│   growth_days: 156                                                    │
│   total_cost: 780000.0  # 156日 × 5000円                              │
│   daily_fixed_cost: 5000.0                                            │
│   field: Field(...)                                                   │
│   candidates: [...]                                                   │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 4. Presenter (Adapter Layer)                                          │
│    GrowthPeriodOptimizeCliPresenter                                   │
├─────────────────────────────────────────────────────────────────────┤
│ Input: OptimalGrowthPeriodResponseDTO                                 │
│                                                                        │
│ Output: 標準出力                                                       │
│   Field: 北圃場 (field_01)                                            │
│   Daily Fixed Cost: ¥5,000/day                                        │
│                                                                        │
│   Start Date  | Completion  | Days | GDD    | Cost      | Status     │
│   2024-04-15  | 2024-09-18  | 156  | 2400.0 | ¥780,000  | ★          │
└─────────────────────────────────────────────────────────────────────┘
```

## 各層のデータ構造とテスト観点

### Layer 1: Framework Layer (CLI)

**責務**: コマンドライン引数をパースし、Fieldエンティティを読み込む

```python
# Input
args = ["optimize", "--field-config", "field_01.json", ...]

# Processing
field_file_repository = FieldFileRepository(file_repository)
fields = await field_file_repository.read_fields_from_file("field_01.json")
field = fields[0]  # 単一フィールド

# Output
field: Field
```

**テスト観点**:
- ✓ field-config が指定されていない場合、エラーメッセージ
- ✓ field-config ファイルが存在しない場合、エラーメッセージ
- ✓ field-config ファイルから正しくFieldエンティティを読み込む
- ✓ Fieldエンティティがコントローラーに渡される

---

### Layer 2: Repository Layer (Adapter)

**責務**: JSONファイルからFieldエンティティへの変換

```python
# Input
file_path: str = "field_01.json"

# Processing
content = await file_repository.read(file_path)
data = json.loads(content)
field = Field(
    field_id=data["field_id"],
    name=data["name"],
    area=data["area"],
    daily_fixed_cost=data["daily_fixed_cost"],
    location=data.get("location")
)

# Output
field: Field
```

**テスト観点**:
- ✓ 正しいJSON構造からFieldエンティティを生成
- ✓ daily_fixed_cost が正確に抽出される
- ✓ 必須フィールドが欠けている場合、適切なエラー
- ✓ 数値型が正しく変換される
- ✓ location が省略可能

---

### Layer 3: Controller Layer (Adapter)

**責務**: CLI引数とFieldエンティティからRequestDTOを構築

```python
# Input
args.field_config = "field_01.json"
field = Field(field_id="field_01", ..., daily_fixed_cost=5000.0)
args.crop = "rice"
args.evaluation_start = "2024-04-01"
args.evaluation_end = "2024-09-30"
args.weather_file = "weather.json"

# Processing
request = OptimalGrowthPeriodRequestDTO(
    crop_id=args.crop,
    variety=args.variety,
    evaluation_period_start=parse_date(args.evaluation_start),
    evaluation_period_end=parse_date(args.evaluation_end),
    weather_data_file=args.weather_file,
    field=field  # Fieldエンティティをそのまま渡す
)

# Output
request: OptimalGrowthPeriodRequestDTO
```

**テスト観点**:
- ✓ Fieldエンティティが正しくDTOに設定される
- ✓ field.daily_fixed_cost がDTOに含まれる
- ✓ field_config が未指定の場合、エラーメッセージ
- ✓ 日付文字列が正しくdatetimeに変換される
- ✓ DTOのバリデーションが機能する

---

### Layer 4: DTO (UseCase)

**責務**: データの型安全性とバリデーション

```python
@dataclass
class OptimalGrowthPeriodRequestDTO:
    crop_id: str
    variety: Optional[str]
    evaluation_period_start: datetime
    evaluation_period_end: datetime
    weather_data_file: str
    field: Field  # Fieldエンティティを保持
    crop_requirement_file: Optional[str] = None
    
    def __post_init__(self):
        # バリデーション
        if self.evaluation_period_start > self.evaluation_period_end:
            raise ValueError("Start must be before end")
        if self.field.daily_fixed_cost < 0:
            raise ValueError("Cost must be non-negative")
```

**テスト観点**:
- ✓ Fieldエンティティが正しく保持される
- ✓ field.daily_fixed_cost にアクセスできる
- ✓ 日付の順序バリデーション
- ✓ コストの非負バリデーション
- ✓ 不正な値が拒否される

---

### Layer 5: Interactor (UseCase)

**責務**: ビジネスロジック（最適化計算）

```python
# Input
request: OptimalGrowthPeriodRequestDTO

# Processing
daily_fixed_cost = request.field.daily_fixed_cost  # 5000.0

for start_date in candidate_dates:
    growth_days = calculate_growth_days(start_date, ...)
    total_cost = growth_days * daily_fixed_cost
    # 最小コストを探す

# Output
response: OptimalGrowthPeriodResponseDTO(
    optimal_start_date=...,
    total_cost=growth_days * daily_fixed_cost,
    daily_fixed_cost=daily_fixed_cost,
    field=request.field,
    ...
)
```

**テスト観点**:
- ✓ request.field.daily_fixed_cost が正しく取得される
- ✓ コスト計算が正確（growth_days × daily_fixed_cost）
- ✓ 様々なコスト値（0.0, 小数, 大きな値）で正しく計算
- ✓ Fieldエンティティがレスポンスに含まれる
- ✓ 最小コストの候補が正しく選択される

---

### Layer 6: Response DTO (UseCase)

**責務**: 計算結果の構造化

```python
@dataclass
class OptimalGrowthPeriodResponseDTO:
    crop_name: str
    variety: Optional[str]
    optimal_start_date: datetime
    completion_date: datetime
    growth_days: int
    total_cost: float
    daily_fixed_cost: float
    field: Field  # Fieldエンティティを含む
    candidates: List[CandidateResultDTO]
```

**テスト観点**:
- ✓ Fieldエンティティが保持される
- ✓ daily_fixed_cost が正しく設定される
- ✓ total_cost が正確に計算されている
- ✓ すべての必須フィールドが設定される

---

### Layer 7: Presenter (Adapter)

**責務**: 表示用フォーマット

```python
# Input
response: OptimalGrowthPeriodResponseDTO

# Processing (Table format)
output = f"""
Field: {response.field.name} ({response.field.field_id})
Area: {response.field.area} m²
Daily Fixed Cost: ¥{response.daily_fixed_cost:,.0f}/day

Optimal Result:
  Start Date: {response.optimal_start_date.date()}
  Completion: {response.completion_date.date()}
  Days: {response.growth_days}
  Total Cost: ¥{response.total_cost:,.0f}
"""

# Output
print(output)
```

**テスト観点**:
- ✓ Fieldエンティティの情報が表示される
- ✓ daily_fixed_cost がフォーマットされる
- ✓ total_cost がフォーマットされる
- ✓ JSON形式でも正しく出力される
- ✓ フィールド名が正しく表示される

---

## データの流れの検証ポイント

### 1. JSONファイル → Field Entity
```
field_01.json
  {"daily_fixed_cost": 5000.0}
        ↓
  Field(daily_fixed_cost=5000.0)
```
**検証**: Repository層のテスト

### 2. Field Entity → Request DTO
```
Field(daily_fixed_cost=5000.0)
        ↓
OptimalGrowthPeriodRequestDTO(field=Field(...))
```
**検証**: Controller層のテスト

### 3. Request DTO → コスト計算
```
request.field.daily_fixed_cost = 5000.0
        ↓
total_cost = 156 × 5000.0 = 780000.0
```
**検証**: Interactor層のテスト

### 4. Response DTO → 表示
```
response.field.name = "北圃場"
response.daily_fixed_cost = 5000.0
response.total_cost = 780000.0
        ↓
"Field: 北圃場"
"Daily Fixed Cost: ¥5,000/day"
"Total Cost: ¥780,000"
```
**検証**: Presenter層のテスト

---

## エラーハンドリングの流れ

### ケース1: field-config が指定されていない
```
CLI → Controller
  if not args.field_config:
    print("Error: --field-config is required")
    return
```

### ケース2: ファイルが存在しない
```
Repository
  if not file_exists(file_path):
    raise FileError(f"File not found: {file_path}")
```

### ケース3: daily_fixed_cost が負の値
```
DTO
  def __post_init__(self):
    if self.field.daily_fixed_cost < 0:
      raise ValueError("Cost must be non-negative")
```

---

## 統合テストのシナリオ

```python
# 入力
args = [
    "optimize",
    "--crop", "rice",
    "--variety", "Koshihikari",
    "--evaluation-start", "2024-04-01",
    "--evaluation-end", "2024-09-30",
    "--weather-file", "weather.json",
    "--field-config", "field_01.json"
]

# field_01.json の内容
{
  "field_id": "field_01",
  "name": "北圃場",
  "area": 1000.0,
  "daily_fixed_cost": 5000.0,
  "location": "北区画"
}

# 期待される結果
- Fieldエンティティが正しく読み込まれる
- daily_fixed_cost = 5000.0 がInteractorに渡される
- コスト計算が正しく行われる
- Presenterでフィールド情報が表示される
```

