# 各層のデータ移送まとめ

## 概要

`optimize-period`コマンドにおける、各層間のデータ移送を整理したドキュメントです。
単体テストで各層のデータ転送が正しく行われることを検証しています。

## データフロー全体図

```
[CLI] --field-config field_01.json
  ↓ (1) JSONファイル読み込み
[Repository] FieldFileRepository
  ↓ (2) Field Entity 作成
[Entity] Field(field_id, name, area, daily_fixed_cost, location)
  ↓ (3) DTOに設定
[DTO] OptimalGrowthPeriodRequestDTO(field=Field(...))
  ↓ (4) Interactorで使用
[Interactor] daily_fixed_cost = request.field.daily_fixed_cost
  ↓ (5) コスト計算
[Interactor] total_cost = growth_days × daily_fixed_cost
  ↓ (6) Response作成
[DTO] OptimalGrowthPeriodResponseDTO(field=Field(...), total_cost=...)
  ↓ (7) Presenter表示
[Presenter] "Field: {field.name}, Cost: ¥{total_cost:,}"
```

## 各層のデータ移送と単体テスト

### Layer 1: Repository → Field Entity

**責務**: JSONデータからFieldエンティティへの変換

**データ移送**:
```python
# Input (JSON)
{
  "field_id": "field_01",
  "name": "北圃場",
  "area": 1000.0,
  "daily_fixed_cost": 5000.0,
  "location": "北区画"
}

# Processing
field = Field(
    field_id="field_01",
    name="北圃場",
    area=1000.0,
    daily_fixed_cost=5000.0,
    location="北区画"
)

# Output
Field entity (frozen dataclass)
```

**テストファイル**: `tests/test_data_flow/test_layer1_repository_to_entity.py`

**検証項目**:
- ✅ JSONの各フィールドがFieldエンティティに正確にマッピングされる
- ✅ daily_fixed_costの精度が保たれる（小数点、ゼロ、大きな値）
- ✅ locationは省略可能
- ✅ 必須フィールドが欠けている場合エラー
- ✅ 負のdaily_fixed_costは拒否される
- ✅ Fieldエンティティはイミュータブル
- ✅ 単一フィールド形式が読み込まれる
- ✅ 文字列の数値がfloatに変換される

**テスト数**: 10件

---

### Layer 2: Field Entity → Request DTO

**責務**: FieldエンティティをRequest DTOに設定

**データ移送**:
```python
# Input
field = Field(
    field_id="field_01",
    daily_fixed_cost=5000.0,
    ...
)

# Processing
request_dto = OptimalGrowthPeriodRequestDTO(
    crop_id="rice",
    variety="Koshihikari",
    evaluation_period_start=datetime(2024, 4, 1),
    evaluation_period_end=datetime(2024, 9, 30),
    weather_data_file="weather.json",
    field=field  # Fieldエンティティをそのまま設定
)

# Output
request_dto.field.daily_fixed_cost == 5000.0
```

**テストファイル**: `tests/test_data_flow/test_layer2_entity_to_dto.py`

**検証項目**:
- ✅ FieldエンティティがRequestDTOに正しく設定される
- ✅ daily_fixed_costにアクセスできる
- ✅ DTO内のFieldもイミュータブル
- ✅ DTOがFieldのすべてのプロパティを保持する
- ✅ locationがNoneのFieldも設定できる
- ✅ DTOのバリデーション（日付順序）が機能する
- ✅ 同じFieldエンティティを複数のDTOで共有できる

**テスト数**: 8件

---

### Layer 3: Request DTO → Interactor (コスト計算)

**責務**: DTOからdaily_fixed_costを取得してコスト計算に使用

**データ移送**:
```python
# Input
request = OptimalGrowthPeriodRequestDTO(
    field=Field(daily_fixed_cost=5000.0, ...),
    ...
)

# Processing
daily_fixed_cost = request.field.daily_fixed_cost  # 5000.0

for start_date in candidates:
    growth_days = calculate_growth_days(...)
    total_cost = growth_days × daily_fixed_cost

# Output
optimal_candidate with minimum total_cost
```

**テストファイル**: `tests/test_data_flow/test_layer3_dto_to_interactor.py`

**検証項目**:
- ✅ Interactorがrequest.field.daily_fixed_costを取得できる
- ✅ コスト計算が正確（growth_days × daily_fixed_cost）
- ✅ 様々なコスト値で正しく計算される
- ✅ 小数点を含むコストの計算精度
- ✅ 複数候補から最小コストを選択
- ✅ 計算中もFieldエンティティは不変
- ✅ コスト0の圃場でも計算が正しく行われる
- ✅ RequestDTOのfieldに自由にアクセスできる

**テスト数**: 8件

---

### Layer 4: Response DTO

**責務**: 計算結果とFieldエンティティの保持

**データ移送**:
```python
# Input
field = Field(daily_fixed_cost=5000.0, ...)
total_cost = 780000.0  # 156日 × 5000円

# Processing
response = OptimalGrowthPeriodResponseDTO(
    optimal_start_date=datetime(2024, 4, 15),
    completion_date=datetime(2024, 9, 18),
    growth_days=156,
    total_cost=780000.0,
    daily_fixed_cost=5000.0,
    field=field,  # Fieldエンティティを含む
    candidates=[...]
)

# Output
response.field.name == "北圃場"
response.total_cost == 780000.0
```

**テストファイル**: `tests/test_data_flow/test_layer4_response_dto.py`

**検証項目**:
- ✅ ResponseDTOがFieldエンティティを保持する
- ✅ コスト情報が一貫している
- ✅ Fieldのすべての情報が保持される
- ✅ ResponseDTO内のFieldもイミュータブル
- ✅ 候補リストとの整合性
- ✅ コスト計算の検証
- ✅ コスト0の圃場のResponseDTO
- ✅ 表示用のフィールドメタデータが取得できる

**テスト数**: 8件

---

## テストサマリー

### データフロー層間テスト
- **Layer 1 (Repository → Entity)**: 10件 ✅
- **Layer 2 (Entity → DTO)**: 8件 ✅
- **Layer 3 (DTO → Interactor)**: 8件 ✅
- **Layer 4 (Response DTO)**: 8件 ✅

**合計**: 34件 全て成功

### その他の関連テスト
- **FieldFileRepository**: 11件 ✅
- **FieldEntity**: 8件 ✅
- **GrowthPeriodOptimizeInteractor**: 5件 ✅
- **GrowthPeriodOptimizeCliController**: 4件 ✅
- **GrowthPeriodOptimizeCliPresenter**: 5件 ✅
- **Multi-field optimization tests**: 40件以上 ✅

**総合計**: 116件 全て成功

---

## 重要なポイント

### 1. イミュータビリティ

Fieldエンティティは`frozen=True`のdataclassなので、どの層でも変更できません。

```python
field = Field(daily_fixed_cost=5000.0, ...)
field.daily_fixed_cost = 9999.0  # ❌ FrozenInstanceError
```

これにより、データの整合性が保証されます。

### 2. 参照の保持

Fieldエンティティは参照で渡されるため、全ての層で同じインスタンスを参照します。

```python
# CLI で作成
field = Field(...)

# Controller に渡す
request = OptimalGrowthPeriodRequestDTO(field=field)

# Interactor で使用
daily_cost = request.field.daily_fixed_cost

# Response に含める
response = OptimalGrowthPeriodResponseDTO(field=request.field)

# Presenter で表示
print(f"Field: {response.field.name}")

# 全て同じ field インスタンス
assert request.field is response.field  # True
```

### 3. 型安全性

各層でFieldエンティティの型が保証されているため、タイプミスやデータ不整合を防げます。

```python
# ❌ コンパイル時にエラー
request.field.daily_fixd_cost  # typo

# ✅ 正しい
request.field.daily_fixed_cost  # float型
```

### 4. テストの独立性

各層のテストは他の層に依存せず、モックを使って独立してテストできます。

---

## コマンド例

```bash
# フィールド設定ファイルを指定するだけ
agrr optimize-period optimize \
  --crop rice \
  --variety Koshihikari \
  --evaluation-start 2024-04-01 \
  --evaluation-end 2024-09-30 \
  --weather-file weather.json \
  --field-config examples/field_01.json
```

フィールド設定ファイル（`field_01.json`）:
```json
{
  "field_id": "field_01",
  "name": "北圃場",
  "area": 1000.0,
  "daily_fixed_cost": 5000.0,
  "location": "北区画"
}
```

出力例:
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
```

---

## 関連ドキュメント

- [FIELD_DATA_FLOW_SIMPLIFIED.md](FIELD_DATA_FLOW_SIMPLIFIED.md) - 詳細なデータフロー図
- [FIELD_CONFIG_FORMAT.md](FIELD_CONFIG_FORMAT.md) - JSONフォーマット仕様
- [ARCHITECTURE.md](ARCHITECTURE.md) - 全体アーキテクチャ

