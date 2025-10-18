# 連作障害の実装サマリー

## 概要

連作障害（continuous cultivation damage）を考慮した最適化機能を実装しました。

InteractionRuleエンティティを使用して、前作と後作のグループ間の相互作用を定義し、収益に影響を与えることができます。

## 実装内容

### 1. エンティティ層

#### 1.1 Crop エンティティの拡張
```python
@dataclass(frozen=True)
class Crop:
    crop_id: str
    name: str
    area_per_unit: float
    variety: Optional[str] = None
    revenue_per_area: Optional[float] = None
    max_revenue: Optional[float] = None
    groups: Optional[List[str]] = None  # ← 新規追加
```

**グループの例**:
- `["Solanaceae"]` - ナス科
- `["Fabaceae", "legumes", "nitrogen_fixing"]` - マメ科、マメ類、窒素固定

#### 1.2 InteractionRule エンティティ
```python
@dataclass(frozen=True)
class InteractionRule:
    rule_id: str
    rule_type: str              # "continuous_cultivation"など
    source_group: str           # 前作グループ
    target_group: str           # 後作グループ
    impact_ratio: float         # 収益影響係数
    is_directional: bool = True
    description: Optional[str] = None
```

### 2. UseCase層

#### 2.1 InteractionRuleGateway（インターフェース）
```python
class InteractionRuleGateway(ABC):
    @abstractmethod
    async def get_rules(self, file_path: str) -> List[InteractionRule]:
        pass
```

#### 2.2 InteractionRuleService
```python
class InteractionRuleService:
    def get_continuous_cultivation_impact(
        self,
        current_crop: Crop,
        previous_crop: Optional[Crop]
    ) -> float:
        """前作との連作をチェックし、影響係数を返す"""
```

**処理ロジック**:
1. 前作がない場合 → `1.0`（影響なし）
2. グループが設定されていない場合 → `1.0`
3. 前作と後作のグループを比較
4. マッチするruleがあれば`impact_ratio`を返す
5. 複数のruleがマッチする場合は乗算

### 3. Adapter層

#### 3.1 InteractionRuleGatewayImpl
```python
class InteractionRuleGatewayImpl(InteractionRuleGateway):
    """JSONファイルからInteractionRuleを読み込む"""
    
    async def get_rules(self, file_path: str) -> List[InteractionRule]:
        # FileRepositoryでJSON読み込み
        # InteractionRuleエンティティに変換
```

### 4. Optimizer統合

#### 4.1 MultiFieldCropAllocationGreedyInteractor の変更

**初期化**:
```python
def __init__(
    self,
    field_gateway: FieldGateway,
    crop_requirement_gateway: CropRequirementGateway,
    weather_gateway: WeatherGateway,
    config: Optional[OptimizationConfig] = None,
    interaction_rules: Optional[List[InteractionRule]] = None,  # ← 新規追加
):
    # InteractionRuleServiceを初期化
    self.interaction_rule_service = InteractionRuleService(
        rules=interaction_rules or []
    )
```

**AllocationCandidate の変更**:
```python
@dataclass
class AllocationCandidate:
    field: Field
    crop: Crop
    # ... 既存フィールド ...
    previous_crop: Optional[Crop] = None      # ← 新規追加
    interaction_impact: float = 1.0           # ← 新規追加
```

**収益計算への適用**:
```python
def get_metrics(self) -> OptimizationMetrics:
    # Apply interaction impact to revenue
    adjusted_revenue_per_area = None
    if self.crop.revenue_per_area is not None:
        adjusted_revenue_per_area = self.crop.revenue_per_area * self.interaction_impact
    
    adjusted_max_revenue = None
    if self.crop.max_revenue is not None:
        adjusted_max_revenue = self.crop.max_revenue * self.interaction_impact
    
    return OptimizationMetrics(
        area_used=self.area_used,
        revenue_per_area=adjusted_revenue_per_area,
        max_revenue=adjusted_max_revenue,
        # ...
    )
```

**Greedy Allocation での動的適用**:
```python
def _greedy_allocation(self, candidates, crop_requirements, optimization_objective):
    field_schedules = {}
    
    for candidate in sorted_candidates:
        # 現在のfield_schedulesから前作を取得し、impactを計算
        updated_candidate = self._apply_interaction_rules(candidate, field_schedules)
        
        # 更新された候補で割り当てを作成
        allocation = self._candidate_to_allocation(updated_candidate)
        field_schedules[field_id].append(allocation)
```

## 使用例

### JSONファイルの定義

#### 作物のグループ定義 (`tomato_requirement.json`)
```json
{
  "crop": {
    "crop_id": "tomato",
    "name": "Tomato",
    "area_per_unit": 0.5,
    "revenue_per_area": 50000,
    "groups": ["Solanaceae", "fruiting_vegetables"]
  },
  "stage_requirements": [...]
}
```

#### 相互作用規則の定義 (`interaction_rules.json`)
```json
[
  {
    "rule_id": "rule_001",
    "rule_type": "continuous_cultivation",
    "source_group": "Solanaceae",
    "target_group": "Solanaceae",
    "impact_ratio": 0.7,
    "is_directional": true,
    "description": "ナス科の連作障害により収益30%減"
  },
  {
    "rule_id": "rule_002",
    "rule_type": "continuous_cultivation",
    "source_group": "Brassicaceae",
    "target_group": "Brassicaceae",
    "impact_ratio": 0.8,
    "is_directional": true,
    "description": "アブラナ科の連作障害により収益20%減"
  }
]
```

### Pythonコードでの使用

```python
from agrr_core.adapter.gateways.interaction_rule_gateway_impl import InteractionRuleGatewayImpl
from agrr_core.framework.repositories.file_repository import FileRepository

# 1. InteractionRuleを読み込む
file_repository = FileRepository()
interaction_gateway = InteractionRuleGatewayImpl(file_repository)
rules = await interaction_gateway.get_rules("interaction_rules.json")

# 2. Optimizerを初期化（ルールを渡す）
optimizer = MultiFieldCropAllocationGreedyInteractor(
    field_gateway=field_gateway,
    crop_requirement_gateway=crop_requirement_gateway,
    weather_gateway=weather_gateway,
    interaction_rules=rules  # ← ルールを渡す
)

# 3. 最適化を実行（自動的に連作を考慮）
result = await optimizer.execute(request)
```

## 動作の流れ

### 候補評価時の処理

```
1. 候補をソート（利益率順）
   ↓
2. 各候補を順に評価
   ↓
3. 現在のfield_schedulesから前作を取得
   ↓
4. InteractionRuleServiceで連作をチェック
   ├─ 前作なし → impact = 1.0
   ├─ 異なる科 → impact = 1.0
   └─ 同じ科 → impact = 0.7（例）
   ↓
5. 候補のinteraction_impactを更新
   ↓
6. 更新後の候補でCropAllocationを作成
   ├─ revenue = base_revenue * interaction_impact
   └─ profit = revenue - cost
   ↓
7. field_schedulesに追加
```

### 収益計算の例

**ケース1: 前作なし（初回栽培）**
```
基本収益: 500㎡ × 50,000円/㎡ = 25,000,000円
interaction_impact: 1.0
最終収益: 25,000,000円
```

**ケース2: 連作（トマト → ナス、どちらもSolanaceae）**
```
基本収益: 500㎡ × 50,000円/㎡ = 25,000,000円
interaction_impact: 0.7（連作障害ルール適用）
最終収益: 25,000,000円 × 0.7 = 17,500,000円（30%減）
```

**ケース3: 異なる科（大豆 → トマト）**
```
基本収益: 500㎡ × 50,000円/㎡ = 25,000,000円
interaction_impact: 1.0（ルールマッチせず）
最終収益: 25,000,000円
```

## テスト結果

### テスト構成

| テストファイル | テスト数 | 内容 |
|-------------|---------|------|
| `test_crop_entity.py` | 18 | Cropエンティティのgroups |
| `test_interaction_rule_entity.py` | 21 | InteractionRuleエンティティ |
| `test_crop_groups_data_flow.py` | 11 | groupsフィールドの移送 |
| `test_interaction_rule_json_integration.py` | 7 | InteractionRuleのJSON変換 |
| `test_interaction_rule_gateway_impl.py` | 7 | Gatewayの実装 |
| `test_interaction_rule_service.py` | 12 | InteractionRuleService |
| `test_continuous_cultivation_impact.py` | 8 | Optimizer統合 |
| **合計** | **84** | **全て合格** ✅ |

### テスト実行結果
```bash
============================== 84 passed in 3.82s ===============================
```

## 実装ファイル一覧

### 新規作成

| カテゴリ | ファイル | 行数 |
|---------|---------|------|
| **Entity** | `interaction_rule_entity.py` | 169 |
| **UseCase Gateway** | `interaction_rule_gateway.py` | 29 |
| **UseCase Service** | `interaction_rule_service.py` | 120 |
| **Adapter Gateway** | `interaction_rule_gateway_impl.py` | 86 |
| **Tests** | `test_crop_entity.py` | 310 |
| **Tests** | `test_interaction_rule_entity.py` | 319 |
| **Tests** | `test_crop_groups_data_flow.py` | 410 |
| **Tests** | `test_interaction_rule_json_integration.py` | 365 |
| **Tests** | `test_interaction_rule_gateway_impl.py` | 205 |
| **Tests** | `test_interaction_rule_service.py` | 360 |
| **Tests** | `test_continuous_cultivation_impact.py` | 330 |
| **Docs** | `INTERACTION_RULE_USAGE.md` | 370 |
| **Docs** | `CLI_DATA_FLOW.md` | 430 |
| **Docs** | `CLI_INTEGRATION_TEST_SUMMARY.md` | 280 |

### 更新

| ファイル | 変更内容 |
|---------|---------|
| `crop_entity.py` | groupsフィールド追加 |
| `crop_requirement_mapper.py` | groups対応 |
| `crop_requirement_gateway_impl.py` | groups読み込み対応 |
| `multi_field_crop_allocation_greedy_interactor.py` | InteractionRule統合 |

## 設計の特徴

### 1. シンプル性
- グループ名は文字列のみ
- EntityType列挙型なし
- rule_typeだけで相互作用を表現

### 2. 汎用性
- 作物グループ、圃場、圃場グループなど任意のグループに対応
- 時間的（連作）、空間的（隣接）、その他の相互作用を表現可能

### 3. 拡張性
- 新しいrule_typeを追加するだけで機能拡張
- InteractionRuleはデータ駆動で外部から設定

### 4. パフォーマンス
- 動的評価: 候補選択時にfield_schedulesから前作を取得
- 効率的: 必要な時だけimpact計算

### 5. テスタビリティ
- 各層で独立したテスト
- モック不要（Clean Architecture）
- 84個のテストで品質保証

## 今後の拡張

### 実装済み
- ✅ 連作障害（continuous_cultivation）
- ✅ JSONファイルからのルール読み込み
- ✅ Optimizer統合

### 将来実装可能
- ⏳ 好相性輪作（beneficial_rotation）
- ⏳ コンパニオンプランツ（companion_planting）
- ⏳ 土壌適合性（soil_compatibility）
- ⏳ 3年輪作などの複雑なパターン

## まとめ

連作障害を表現するための**シンプルで汎用的な相互作用規則システム**を実装しました：

- **84個のテスト全て合格** ✅
- **既存機能に影響なし** ✅
- **外部から柔軟に設定可能** ✅
- **Optimizerに統合済み** ✅

グループ定義とInteractionRuleは外部のJSONファイルで管理し、最適化時に自動的に連作障害が考慮されます。

