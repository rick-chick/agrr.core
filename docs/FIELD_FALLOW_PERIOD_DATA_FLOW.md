# 圃場休閑期間（Fallow Period）機能のデータフロー整理

## 概要

圃場（Field）に休閑期間を追加する機能を実装するため、Fieldエンティティが関与する全コンポーネント間のデータ移送を整理します。

**仕様**:
- フィールド名: `fallow_period_days`
- 型: `Optional[int]`
- デフォルト値: `28` (日数)
- 説明: 作物の栽培終了後、次の作物を植えるまでに必要な休閑期間（土壌回復期間）

## Fieldエンティティの定義

### 現在の定義

```python
# src/agrr_core/entity/entities/field_entity.py
@dataclass(frozen=True)
class Field:
    """Represents a field with daily fixed cost information."""
    
    field_id: str
    name: str
    area: float
    daily_fixed_cost: float
    location: Optional[str] = None
```

### 変更後の定義（追加予定）

```python
# src/agrr_core/entity/entities/field_entity.py
@dataclass(frozen=True)
class Field:
    """Represents a field with daily fixed cost information."""
    
    field_id: str
    name: str
    area: float
    daily_fixed_cost: float
    location: Optional[str] = None
    fallow_period_days: int = 28  # 休閑期間（日数）
```

## データフロー図

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. JSONファイル (外部データソース)                                     │
├─────────────────────────────────────────────────────────────────────┤
│ field.json / fields.json                                              │
│ {                                                                      │
│   "field_id": "field_01",                                             │
│   "name": "北圃場",                                                    │
│   "area": 1000.0,                                                     │
│   "daily_fixed_cost": 5000.0,                                         │
│   "location": "北区画",                                                │
│   "fallow_period_days": 28  ← NEW (Optional, default: 28)           │
│ }                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 2. Gateway実装 (Adapter Layer)                                        │
│    FieldFileGateway / FieldInMemoryGateway                            │
├─────────────────────────────────────────────────────────────────────┤
│ 責務: JSONデータをFieldエンティティに変換                              │
│                                                                        │
│ 変更点:                                                                │
│ - _convert_dict_to_field() メソッド                                   │
│   - fallow_period_days フィールドの読み込み追加                       │
│   - デフォルト値 28 の設定                                             │
│ - validate_field_data() メソッド                                      │
│   - fallow_period_days のバリデーション追加（0以上の整数）             │
│                                                                        │
│ Input: Dict[str, Any] (JSON)                                          │
│ Output: Field(fallow_period_days=28)                                  │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 3. Field Entity (Entity Layer)                                        │
│    field_entity.py                                                    │
├─────────────────────────────────────────────────────────────────────┤
│ 責務: ビジネスエンティティの定義                                       │
│                                                                        │
│ 変更点:                                                                │
│ - fallow_period_days: int = 28 フィールドの追加                       │
│                                                                        │
│ Field(                                                                │
│   field_id="field_01",                                                │
│   name="北圃場",                                                       │
│   area=1000.0,                                                        │
│   daily_fixed_cost=5000.0,                                            │
│   location="北区画",                                                   │
│   fallow_period_days=28                                               │
│ )                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 4. DTO (UseCase Layer)                                                │
│    OptimalGrowthPeriodRequestDTO, その他のDTO                         │
├─────────────────────────────────────────────────────────────────────┤
│ 責務: データの型安全性とバリデーション                                 │
│                                                                        │
│ 変更点: なし                                                           │
│ - DTOはFieldエンティティをそのまま保持するため変更不要                 │
│                                                                        │
│ OptimalGrowthPeriodRequestDTO(                                        │
│   crop_id="rice",                                                     │
│   field=Field(fallow_period_days=28),  ← 自動的に含まれる            │
│   ...                                                                 │
│ )                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 5. Interactor / Services (UseCase Layer)                              │
│    - GrowthPeriodOptimizeInteractor                                   │
│    - MultiFieldCropAllocationGreedyInteractor                         │
│    - ALNSOptimizerService                                             │
│    - NeighborOperations (Field関連)                                   │
├─────────────────────────────────────────────────────────────────────┤
│ 責務: ビジネスロジックの実装                                           │
│                                                                        │
│ 変更点:                                                                │
│ - 休閑期間を考慮したスケジューリング                                   │
│   - 圃場での作物栽培完了後、次の作物を植えるまでに                     │
│     field.fallow_period_days 日数の間隔を確保                         │
│                                                                        │
│ 例: 作物Aの収穫完了日が2024-06-30の場合                               │
│     次の作物Bの最早開始日 = 2024-07-28 (28日後)                       │
│                                                                        │
│ 影響を受けるロジック:                                                  │
│ - 圃場の利用可能期間の計算                                             │
│ - 時間的重複チェック                                                   │
│ - スケジュール最適化アルゴリズム                                       │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 6. Entity (Entity Layer)                                              │
│    - FieldSchedule                                                    │
│    - CropAllocation                                                   │
├─────────────────────────────────────────────────────────────────────┤
│ 責務: ビジネスエンティティの集約と検証                                 │
│                                                                        │
│ 変更点:                                                                │
│ - FieldSchedule.__post_init__()                                       │
│   - 時間的重複チェック時に休閑期間を考慮                               │
│   - allocations間の間隔が fallow_period_days 以上かチェック           │
│                                                                        │
│ - CropAllocation.overlaps_with()                                      │
│   - 休閑期間を含めた重複チェック                                       │
│   - completion_date + fallow_period_days < other.start_date           │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 7. Response DTO & Presenter (Adapter Layer)                           │
│    - OptimalGrowthPeriodResponseDTO                                   │
│    - GrowthPeriodOptimizeCliPresenter                                 │
├─────────────────────────────────────────────────────────────────────┤
│ 責務: 表示用データの構造化とフォーマット                               │
│                                                                        │
│ 変更点:                                                                │
│ - Presenter                                                           │
│   - 休閑期間の情報を表示に追加（オプション）                           │
│   - "Fallow Period: 28 days"                                          │
│                                                                        │
│ 出力例:                                                                │
│   Field: 北圃場 (field_01)                                            │
│   Area: 1,000 m²                                                      │
│   Daily Fixed Cost: ¥5,000/day                                        │
│   Fallow Period: 28 days  ← NEW                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## 影響を受けるコンポーネント一覧

### Entity Layer

1. **field_entity.py** ✓ 変更必要
   - `fallow_period_days: int = 28` フィールドを追加

2. **field_schedule_entity.py** ✓ 変更必要
   - `__post_init__()`: 休閑期間を考慮した重複チェック

3. **crop_allocation_entity.py** ✓ 変更必要（検討）
   - `overlaps_with()`: 休閑期間を含めた重複判定

### UseCase Layer

4. **field_gateway.py** ✗ 変更不要
   - インターフェースのみ、実装はAdapter層

5. **growth_period_optimize_request_dto.py** ✗ 変更不要
   - Fieldエンティティを保持するだけ

6. **growth_period_optimize_interactor.py** ✓ 変更必要（将来）
   - 単一圃場の最適化では現状不要だが、連作を考慮する場合は必要

7. **multi_field_crop_allocation_greedy_interactor.py** ✓ 変更必要
   - 圃場スケジューリングロジックに休閑期間を組み込む
   - 次の作物を割り当てる際に `fallow_period_days` を考慮

8. **alns_optimizer_service.py** ✓ 変更必要
   - 近傍解生成時に休閑期間を考慮
   - フィールド間移動・スワップ時の制約チェック

9. **neighbor_operations/** ✓ 変更必要
   - `field_move_operation.py`
   - `field_swap_operation.py`
   - `field_replace_operation.py`
   - `field_remove_operation.py`
   - 操作の実行可能性チェックに休閑期間制約を追加

### Adapter Layer

10. **field_file_gateway.py** ✓ 変更必要
    - `_convert_dict_to_field()`: JSONから `fallow_period_days` を読み込み
    - `validate_field_data()`: `fallow_period_days` のバリデーション

11. **field_inmemory_gateway.py** ✗ 変更不要
    - Fieldエンティティをそのまま保存するだけ

12. **growth_period_optimize_cli_controller.py** ✗ 変更不要
    - Fieldエンティティを渡すだけ

13. **growth_period_optimize_cli_presenter.py** ✓ 変更検討
    - 休閑期間の表示を追加（オプション）

### Tests

14. **全てのテストファイル** ✓ 変更必要
    - Field生成箇所にデフォルト値が適用される
    - 既存のテストコードは動作するが、休閑期間を考慮したテストを追加

## 実装の優先順位

### Phase 1: Entity層の変更（基本）

1. `field_entity.py`: `fallow_period_days` フィールド追加
2. `field_file_gateway.py`: JSONからの読み込み実装
3. 単体テスト: `test_field_entity.py`、`test_field_file_gateway.py`

### Phase 2: スケジューリングロジックへの統合

4. `field_schedule_entity.py`: 休閑期間を考慮した重複チェック
5. `crop_allocation_entity.py`: 休閑期間を含めた重複判定（検討）
6. 単体テスト: `test_field_schedule_entity.py`、`test_crop_allocation_entity.py`

### Phase 3: 最適化アルゴリズムへの統合

7. `multi_field_crop_allocation_greedy_interactor.py`: 休閑期間を考慮したスケジューリング
8. `alns_optimizer_service.py`: 近傍解生成時の休閑期間制約
9. `neighbor_operations/`: 各操作に休閑期間制約を追加
10. 統合テスト: 最適化アルゴリズムの検証

### Phase 4: UI/UX改善

11. `growth_period_optimize_cli_presenter.py`: 休閑期間の表示
12. ドキュメント更新: `FIELD_CONFIG_FORMAT.md`

## JSON形式の例

### 単一フィールド

```json
{
  "field_id": "field_01",
  "name": "北圃場",
  "area": 1000.0,
  "daily_fixed_cost": 5000.0,
  "location": "北区画",
  "fallow_period_days": 28
}
```

### 複数フィールド

```json
{
  "fields": [
    {
      "field_id": "field_01",
      "name": "北圃場",
      "area": 1000.0,
      "daily_fixed_cost": 5000.0,
      "location": "北区画",
      "fallow_period_days": 28
    },
    {
      "field_id": "field_02",
      "name": "南圃場",
      "area": 1500.0,
      "daily_fixed_cost": 6000.0,
      "location": "南区画",
      "fallow_period_days": 21
    },
    {
      "field_id": "field_03",
      "name": "東圃場",
      "area": 800.0,
      "daily_fixed_cost": 4000.0
    }
  ]
}
```

※ `fallow_period_days` が省略された場合はデフォルト値 28 が使用される

## バリデーションルール

1. **型**: `int`（整数）
2. **範囲**: `>= 0`（0日以上）
3. **デフォルト**: `28`日
4. **省略可能**: Yes（省略時はデフォルト値を使用）

## ビジネスロジックでの使用例

### 例1: 連続栽培の最早開始日計算

```python
# 作物Aの収穫完了日
completion_date_a = datetime(2024, 6, 30)

# 休閑期間を考慮した次の作物Bの最早開始日
fallow_period = field.fallow_period_days  # 28
earliest_start_b = completion_date_a + timedelta(days=fallow_period)
# → 2024-07-28
```

### 例2: 時間的重複チェック（休閑期間を含む）

```python
def overlaps_with_fallow(alloc1: CropAllocation, alloc2: CropAllocation) -> bool:
    """休閑期間を考慮した重複チェック"""
    if alloc1.field.field_id != alloc2.field.field_id:
        return False
    
    # alloc1の終了日 + 休閑期間
    alloc1_end_with_fallow = alloc1.completion_date + timedelta(
        days=alloc1.field.fallow_period_days
    )
    
    # alloc2の終了日 + 休閑期間
    alloc2_end_with_fallow = alloc2.completion_date + timedelta(
        days=alloc2.field.fallow_period_days
    )
    
    # 重複チェック
    return not (alloc1_end_with_fallow <= alloc2.start_date or 
                alloc2_end_with_fallow <= alloc1.start_date)
```

### 例3: 圃場の利用可能期間計算

```python
def get_next_available_date(field: Field, current_allocations: List[CropAllocation]) -> datetime:
    """圃場が次に利用可能な日付を取得"""
    if not current_allocations:
        return evaluation_period_start
    
    # 最後の作物の完了日
    last_completion = max(alloc.completion_date for alloc in current_allocations)
    
    # 休閑期間を考慮
    next_available = last_completion + timedelta(days=field.fallow_period_days)
    
    return next_available
```

## テスト戦略

### 単体テスト（Entity Layer）

- `test_field_entity.py`
  - デフォルト値28が設定されること
  - カスタム値が正しく設定されること
  - 負の値が拒否されること

### 単体テスト（Adapter Layer）

- `test_field_file_gateway.py`
  - JSONから `fallow_period_days` が読み込まれること
  - 省略時にデフォルト値28が使用されること
  - 不正な値（負の値、非整数）が拒否されること

### 統合テスト（UseCase Layer）

- `test_multi_field_crop_allocation_greedy_interactor.py`
  - 休閑期間を考慮したスケジューリングが行われること
  - 連続栽培時に最低28日の間隔が確保されること
  - 異なる圃場では休閑期間が独立していること

- `test_alns_optimizer_service.py`
  - 近傍解生成時に休閑期間制約が守られること
  - フィールド間移動時に休閑期間が再計算されること

### 統合テスト（End-to-End）

- 実際のJSONファイルから読み込み、最適化を実行
- 生成されたスケジュールが休閑期間制約を満たすことを検証

## 関連ドキュメント

- [ARCHITECTURE.md](ARCHITECTURE.md) - クリーンアーキテクチャの全体設計
- [FIELD_CONFIG_FORMAT.md](FIELD_CONFIG_FORMAT.md) - フィールド設定ファイル形式
- [FIELD_DATA_FLOW_SIMPLIFIED.md](FIELD_DATA_FLOW_SIMPLIFIED.md) - フィールドデータフロー

