# InteractionRule 使用ガイド

## 概要

`InteractionRule`（相互作用規則）は、作物グループ、圃場、圃場グループ間の相互作用を定義し、収益への影響を表現するためのシンプルなエンティティです。

連作障害、コンパニオンプランツ、土壌適合性など、様々な相互作用をモデル化できます。

## エンティティ構造

```python
from agrr_core.entity import InteractionRule, RuleType

@dataclass(frozen=True)
class InteractionRule:
    rule_id: str              # 規則の一意識別子
    rule_type: RuleType       # ルールのタイプ（Enum）
    source_group: str         # 影響を与える側のグループ
    target_group: str         # 影響を受ける側のグループ
    impact_ratio: float       # 収益への影響係数
    is_directional: bool = True   # 方向性（True=有向、False=無向）
    description: Optional[str] = None  # 説明（オプション）
```

### RuleType Enum

```python
class RuleType(str, Enum):
    CONTINUOUS_CULTIVATION = "continuous_cultivation"
    BENEFICIAL_ROTATION = "beneficial_rotation"
    COMPANION_PLANTING = "companion_planting"
    ALLELOPATHY = "allelopathy"
    SOIL_COMPATIBILITY = "soil_compatibility"
    CLIMATE_COMPATIBILITY = "climate_compatibility"
```

### フィールド詳細

#### `rule_type`（ルールのタイプ）

| タイプ | 説明 | 文脈 | 通常の方向性 |
|--------|------|------|-------------|
| `continuous_cultivation` | 連作障害 | 時間的（前作→後作） | 有向 |
| `beneficial_rotation` | 好相性輪作 | 時間的（前作→後作） | 有向 |
| `companion_planting` | コンパニオンプランツ | 空間的（隣接） | 無向 |
| `allelopathy` | 他感作用 | 空間的（隣接） | 有向 |
| `soil_compatibility` | 土壌適合性 | 圃場×作物 | 有向 |
| `climate_compatibility` | 気候適合性 | 圃場×作物 | 有向 |

#### `source_group` / `target_group`（グループ名）

グループ名は**任意の文字列**で、以下のような識別子を使用できます：

| 種類 | グループ名の例 |
|------|--------------|
| 作物科 | `Solanaceae`, `Fabaceae`, `Brassicaceae`, `Poaceae` |
| 機能グループ | `legumes`, `fruiting_vegetables`, `grains` |
| 特定圃場 | `field_001`, `field_002`, `north_field` |
| 圃場グループ | `acidic_soil`, `clay_soil`, `well_drained` |

#### `impact_ratio`（影響係数）

収益への影響を数値で表現：

| 値 | 意味 | 用途 |
|----|------|------|
| `1.0` | 影響なし | デフォルト |
| `0.7` | 30%減 | 中程度の連作障害 |
| `0.5` | 50%減 | 強い連作障害 |
| `1.1` | 10%増 | 弱い好影響 |
| `1.2` | 20%増 | 中程度の好影響 |
| `0.0` | 栽培不可 | 極端な不適合 |

#### `is_directional`（方向性）

| 値 | 意味 | マッチング |
|----|------|-----------|
| `True` | 有向（source → target のみ） | 順序が重要 |
| `False` | 無向（双方向） | どちらの順序でもマッチ |

## 使用例

### 例1: 連作障害（ナス科）

```python
from agrr_core.entity import InteractionRule, RuleType

# ナス科の連作障害（収益30%減）
rule = InteractionRule(
    rule_id="rule_001",
    rule_type=RuleType.CONTINUOUS_CULTIVATION,
    source_group="Solanaceae",
    target_group="Solanaceae",
    impact_ratio=0.7,
    is_directional=True,
    description="ナス科の連作障害により収益30%減"
)

# 使用例：前作トマト（Solanaceae）→ 後作ナス（Solanaceae）
impact = rule.get_impact("Solanaceae", "Solanaceae")
# impact = 0.7 （収益が70%になる）
```

### 例2: マメ科による窒素固定効果

```python
# マメ科→他の作物への好影響（収益10%増）
rule = InteractionRule(
    rule_id="rule_002",
    rule_type=RuleType.BENEFICIAL_ROTATION,
    source_group="Fabaceae",
    target_group="Poaceae",
    impact_ratio=1.1,
    is_directional=True,
    description="マメ科による窒素固定効果でイネ科の収益10%増"
)

# 使用例：前作大豆（Fabaceae）→ 後作イネ（Poaceae）
impact = rule.get_impact("Fabaceae", "Poaceae")
# impact = 1.1 （収益が110%になる）

# 逆方向は適用されない
impact_reverse = rule.get_impact("Poaceae", "Fabaceae")
# impact_reverse = 1.0 （影響なし）
```

### 例3: 圃場と作物の土壌適合性

```python
# 特定の圃場がナス科に適している（収益20%増）
rule = InteractionRule(
    rule_id="rule_003",
    rule_type=RuleType.SOIL_COMPATIBILITY,
    source_group="field_001",
    target_group="Solanaceae",
    impact_ratio=1.2,
    is_directional=True,
    description="圃場001の土壌はナス科に適している"
)

# 使用例：圃場001でトマト（Solanaceae）を栽培
impact = rule.get_impact("field_001", "Solanaceae")
# impact = 1.2 （収益が120%になる）
```

### 例4: 圃場グループと作物グループの適合性

```python
# 酸性土壌ではアブラナ科の収益が下がる（収益20%減）
rule = InteractionRule(
    rule_id="rule_004",
    rule_type=RuleType.SOIL_COMPATIBILITY,
    source_group="acidic_soil",
    target_group="Brassicaceae",
    impact_ratio=0.8,
    is_directional=True,
    description="酸性土壌ではアブラナ科の収益が20%減"
)

# 使用例：酸性土壌の圃場でキャベツ（Brassicaceae）を栽培
# 圃場に groups=["acidic_soil"] が設定されている場合
impact = rule.get_impact("acidic_soil", "Brassicaceae")
# impact = 0.8 （収益が80%になる）
```

### 例5: コンパニオンプランツ（無向）

```python
# トマトとバジルの隣接栽培（相互に収益15%増）
rule = InteractionRule(
    rule_id="rule_005",
    rule_type=RuleType.COMPANION_PLANTING,
    source_group="Solanaceae",
    target_group="Lamiaceae",
    impact_ratio=1.15,
    is_directional=False,  # 双方向
    description="トマトとバジルの隣接栽培で相互に収益15%増"
)

# 無向なので、どちらの順序でも適用される
impact1 = rule.get_impact("Solanaceae", "Lamiaceae")
# impact1 = 1.15

impact2 = rule.get_impact("Lamiaceae", "Solanaceae")
# impact2 = 1.15
```

## JSON での定義

### 作物のグループ定義

```json
{
  "crop_id": "tomato",
  "name": "トマト",
  "area_per_unit": 0.5,
  "variety": "Aiko",
  "revenue_per_area": 50000,
  "groups": [
    "Solanaceae",
    "fruiting_vegetables",
    "warm_season"
  ]
}
```

### 相互作用規則の定義

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
    "rule_type": "beneficial_rotation",
    "source_group": "Fabaceae",
    "target_group": "Poaceae",
    "impact_ratio": 1.1,
    "is_directional": true,
    "description": "マメ科による窒素固定効果"
  },
  {
    "rule_id": "rule_003",
    "rule_type": "soil_compatibility",
    "source_group": "field_001",
    "target_group": "Solanaceae",
    "impact_ratio": 1.2,
    "is_directional": true,
    "description": "圃場001はナス科に適した土壌"
  },
  {
    "rule_id": "rule_004",
    "rule_type": "companion_planting",
    "source_group": "Solanaceae",
    "target_group": "Lamiaceae",
    "impact_ratio": 1.15,
    "is_directional": false,
    "description": "トマトとバジルのコンパニオンプランツ効果"
  }
]
```

## 一般的な作物グループと規則

### 主要な作物科と連作障害

| 科名 | グループID | 代表作物 | 連作障害の強さ | 推奨impact_ratio |
|------|-----------|----------|---------------|-----------------|
| ナス科 | `Solanaceae` | トマト、ナス、ピーマン | 強い | 0.5 - 0.7 |
| アブラナ科 | `Brassicaceae` | キャベツ、白菜、大根 | 中程度 | 0.7 - 0.8 |
| マメ科 | `Fabaceae` | 大豆、エンドウ、ラッカセイ | 中程度 | 0.7 - 0.8 |
| イネ科 | `Poaceae` | イネ、トウモロコシ、麦 | 弱い | 0.8 - 0.9 |
| キク科 | `Asteraceae` | レタス、ゴボウ、シュンギク | 中程度 | 0.7 - 0.8 |
| ウリ科 | `Cucurbitaceae` | キュウリ、カボチャ、メロン | 強い | 0.5 - 0.7 |

### 好相性の組み合わせ（輪作）

| 前作グループ | 後作グループ | 効果 | impact_ratio |
|------------|------------|------|-------------|
| `Fabaceae` (マメ科) | `Poaceae` (イネ科) | 窒素固定 | 1.1 - 1.2 |
| `Fabaceae` (マメ科) | `Brassicaceae` (アブラナ科) | 窒素固定 | 1.1 - 1.2 |
| `Poaceae` (イネ科) | `Solanaceae` (ナス科) | 病害リスク低減 | 1.0 - 1.1 |

### コンパニオンプランツ（空間的・無向）

| グループ1 | グループ2 | 効果 | impact_ratio |
|----------|----------|------|-------------|
| `Solanaceae` (トマト) | `Lamiaceae` (バジル) | 害虫忌避 | 1.1 - 1.2 |
| `Brassicaceae` (キャベツ) | `Apiaceae` (ニンジン) | 害虫忌避 | 1.1 - 1.15 |
| `Allium` (ネギ類) | `Solanaceae` (トマト) | 病害予防 | 1.1 - 1.15 |

## rule_type による暗黙的な意味

`rule_type`は単なるラベルではなく、適用される文脈や方向性を暗黙的に表現します：

| rule_type | 暗黙的な文脈 | 通常の方向性 | 説明 |
|-----------|------------|-------------|------|
| `continuous_cultivation` | 時間的継承 | 有向 | 同じグループを連続栽培すると収益減 |
| `beneficial_rotation` | 時間的継承 | 有向 | 前作が後作に良い影響 |
| `companion_planting` | 空間的隣接 | **無向** | 隣接栽培で相互に良い影響 |
| `allelopathy` | 空間的隣接 | 有向 | 一方が他方を阻害 |
| `soil_compatibility` | 圃場×作物 | 有向 | 圃場の土壌が作物に適合 |

## Optimizer での使用（将来実装）

```python
def calculate_adjusted_revenue(
    base_revenue: float,
    applicable_rules: List[InteractionRule],
    crop_groups: List[str],
    previous_crop_groups: Optional[List[str]] = None,
    field_groups: Optional[List[str]] = None
) -> float:
    """適用可能な規則に基づいて調整後の収益を計算
    
    Args:
        base_revenue: 基本収益
        applicable_rules: 相互作用規則のリスト
        crop_groups: 現在の作物のグループ
        previous_crop_groups: 前作物のグループ（連作判定用）
        field_groups: 圃場のグループ（土壌適合性判定用）
    
    Returns:
        調整後の収益
    """
    adjusted_revenue = base_revenue
    
    # 時間的：前作との相互作用
    if previous_crop_groups:
        for prev_group in previous_crop_groups:
            for curr_group in crop_groups:
                for rule in applicable_rules:
                    if rule.rule_type in ["continuous_cultivation", "beneficial_rotation"]:
                        impact = rule.get_impact(prev_group, curr_group)
                        if impact != 1.0:
                            adjusted_revenue *= impact
    
    # 空間的：圃場との相互作用
    if field_groups:
        for field_group in field_groups:
            for crop_group in crop_groups:
                for rule in applicable_rules:
                    if rule.rule_type == "soil_compatibility":
                        impact = rule.get_impact(field_group, crop_group)
                        if impact != 1.0:
                            adjusted_revenue *= impact
    
    return adjusted_revenue


# 使用例
base_revenue = 100000  # 基本収益: 10万円
rules = [
    InteractionRule("rule_001", "continuous_cultivation", "Solanaceae", "Solanaceae", 0.7),
    InteractionRule("rule_002", "soil_compatibility", "field_001", "Solanaceae", 1.2),
]

# 圃場001で、前作トマト→後作ナス（どちらもSolanaceae）
adjusted = calculate_adjusted_revenue(
    base_revenue=100000,
    applicable_rules=rules,
    crop_groups=["Solanaceae"],
    previous_crop_groups=["Solanaceae"],
    field_groups=["field_001"]
)
# 結果: 100000 * 0.7 (連作障害) * 1.2 (土壌適合) = 84000円
```

## ベストプラクティス

### 1. グループの命名規則

- **科レベル**: 学名を使用（例: `Solanaceae`, `Fabaceae`）
- **機能グループ**: 英語の説明的な名前（例: `legumes`, `fruiting_vegetables`）
- **圃場**: 識別子（例: `field_001`, `north_field`）
- **圃場グループ**: 特性を表す名前（例: `acidic_soil`, `well_drained`）

### 2. 影響係数の設定ガイド

| 影響の程度 | impact_ratio | 用途 |
|-----------|-------------|------|
| 栽培不可 | 0.0 | 極端な不適合 |
| 強い負の影響 | 0.5 - 0.7 | 強い連作障害、アレロパシー |
| 中程度の負の影響 | 0.7 - 0.8 | 中程度の連作障害、土壌不適合 |
| 弱い負の影響 | 0.8 - 0.9 | 弱い連作障害 |
| 影響なし | 1.0 | デフォルト |
| 弱い正の影響 | 1.05 - 1.1 | 弱い好相性 |
| 中程度の正の影響 | 1.1 - 1.2 | 窒素固定、コンパニオンプランツ |
| 強い正の影響 | 1.2 - 1.3 | 理想的な適合性 |

### 3. 方向性の選択

| ケース | is_directional | 理由 |
|--------|---------------|------|
| 連作障害 | `True` | 前作→後作の順序が重要 |
| 好相性輪作 | `True` | 前作→後作の順序が重要 |
| コンパニオンプランツ | `False` | 相互に影響 |
| アレロパシー | `True` | 一方的な阻害 |
| 土壌適合性 | `True` | 圃場→作物の関係 |

### 4. 規則の優先順位と累積

複数の規則が適用される場合、通常は**乗算**で組み合わせます：

```
最終影響 = rule1.impact_ratio × rule2.impact_ratio × ...
```

例：
- 連作障害: 0.7
- 土壌適合: 1.2
- 最終影響: 0.7 × 1.2 = 0.84 (16%減)

## 典型的な規則セット例

```json
[
  {
    "rule_id": "cc_solanaceae",
    "rule_type": "continuous_cultivation",
    "source_group": "Solanaceae",
    "target_group": "Solanaceae",
    "impact_ratio": 0.6,
    "is_directional": true,
    "description": "ナス科の連作障害（40%減）"
  },
  {
    "rule_id": "cc_brassicaceae",
    "rule_type": "continuous_cultivation",
    "source_group": "Brassicaceae",
    "target_group": "Brassicaceae",
    "impact_ratio": 0.75,
    "is_directional": true,
    "description": "アブラナ科の連作障害（25%減）"
  },
  {
    "rule_id": "rot_legumes_grains",
    "rule_type": "beneficial_rotation",
    "source_group": "Fabaceae",
    "target_group": "Poaceae",
    "impact_ratio": 1.15,
    "is_directional": true,
    "description": "マメ科→イネ科の窒素固定効果（15%増）"
  },
  {
    "rule_id": "comp_tomato_basil",
    "rule_type": "companion_planting",
    "source_group": "Solanaceae",
    "target_group": "Lamiaceae",
    "impact_ratio": 1.1,
    "is_directional": false,
    "description": "トマトとバジルのコンパニオンプランツ（10%増）"
  }
]
```

## まとめ

### シンプルな設計

- ✅ `rule_type`だけで相互作用の種類を表現
- ✅ グループ名は任意の文字列（作物科、圃場、カスタムグループ）
- ✅ `is_directional`で有向・無向を制御
- ✅ `impact_ratio`で収益への影響を直接指定

### 拡張性

新しい`rule_type`を定義するだけで機能拡張が可能：

- `nutrient_depletion`: 栄養消耗
- `pest_resistance`: 病害虫耐性
- `water_competition`: 水分競合
- `seasonal_rotation`: 季節輪作

など、必要に応じて自由に追加できます。
