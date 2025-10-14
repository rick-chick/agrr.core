# 最適化処理の目的関数統一性検証レポート

**検証日**: 2025-10-12  
**検証対象**: 最適化の目的関数（何を最適化しているか）

---

## ⚠️ エグゼクティブサマリー

プロジェクト内の最適化処理を検証した結果、**目的関数が統一されていない**ことが判明しました。

### 発見された不統一

| 最適化処理 | 目的関数 | 収益の考慮 |
|-----------|---------|----------|
| **GrowthPeriodOptimizeInteractor** | ❌ コスト最小化 | ❌ なし |
| **MultiFieldCropAllocationGreedyInteractor** | ✅ 利益最大化 (または コスト最小化) | ✅ あり |
| **OptimizationIntermediateResultScheduleInteractor** | ❌ コスト最小化 | ❌ なし |

**重大な問題**: 
- 単一圃場の期間最適化では**収益を考慮せずコストのみ最小化**
- 複数圃場の配置最適化では**収益-コストの利益を最大化**

これらは**異なる目的関数**を使用しています。

---

## 1. 詳細検証結果

### 1.1 GrowthPeriodOptimizeInteractor (成長期間最適化)

**ファイル**: `src/agrr_core/usecase/interactors/growth_period_optimize_interactor.py`

#### 目的関数

```python
# 3-11行目のコメント
"""
This interactor finds the optimal cultivation start date that minimizes total cost
based on daily fixed costs, while ensuring completion by a specified deadline.

The optimization follows this logic:
1. Generate candidate start dates from earliest_start_date to completion_deadline
2. For each candidate, calculate cultivation progress until 100% completion
3. Filter out candidates that cannot complete by the deadline
4. Calculate total cost = growth_days * daily_fixed_cost for valid candidates
5. Select the candidate with minimum total cost  # ← コスト最小化
"""
```

#### 実装

```python
# 112行目
optimal_candidate = min(valid_candidates, key=lambda c: c.total_cost)
```

**目的**: コスト最小化のみ  
**収益の考慮**: なし

#### RequestDTO

```python
# growth_period_optimize_request_dto.py 4行目
"""
This DTO carries the input parameters needed to find the optimal growth period
that minimizes total cost based on field's daily fixed costs.  # ← コスト最小化
"""
```

✅ **検証結果**: **コスト最小化のみで、収益は考慮していない**

---

### 1.2 MultiFieldCropAllocationGreedyInteractor (複数圃場作物配置最適化)

**ファイル**: `src/agrr_core/usecase/interactors/multi_field_crop_allocation_greedy_interactor.py`

#### 目的関数

```python
# 221-228行目: 収益と利益の計算
revenue = (quantity * crop.revenue_per_area * crop.area_per_unit) if crop.revenue_per_area else 0

# Cost (fixed cost model - doesn't depend on quantity)
cost = candidate_period.total_cost

profit = revenue - cost
profit_rate = (profit / cost) if cost > 0 else 0
```

#### 実装: 目的に応じた選択

```python
# 422-427行目
if optimization_objective == "maximize_profit":
    # Sort by profit rate (descending)
    sorted_candidates = sorted(candidates, key=lambda c: c.profit_rate, reverse=True)
else:  # minimize_cost
    # Sort by cost (ascending)
    sorted_candidates = sorted(candidates, key=lambda c: c.cost)
```

**目的**: 
- `maximize_profit`モード: **利益最大化** (利益率順)
- `minimize_cost`モード: **コスト最小化**

**収益の考慮**: あり

#### RequestDTO

```python
# multi_field_crop_allocation_request_dto.py 41行目
optimization_objective: str = "maximize_profit"  # or "minimize_cost"
```

✅ **検証結果**: **利益最大化（デフォルト）またはコスト最小化を選択可能**

---

### 1.3 OptimizationIntermediateResultScheduleInteractor

**ファイル**: `src/agrr_core/usecase/interactors/optimization_intermediate_result_schedule_interactor.py`

#### 目的関数

```python
# 4行目のコメント
"""
This interactor implements the weighted interval scheduling algorithm to find
the minimum cost combination of non-overlapping cultivation periods.  # ← コスト最小化
"""

# 106行目
def _find_minimum_cost_schedule(
    self, sorted_results: List[OptimizationIntermediateResult]
) -> Tuple[float, List[int]]:
    """Find minimum cost schedule using dynamic programming."""
```

**目的**: コスト最小化のみ  
**収益の考慮**: なし

✅ **検証結果**: **コスト最小化のみで、収益は考慮していない**

---

## 2. 収益モデルの分析

### 2.1 収益の計算式

```python
# Cropエンティティ (crop_entity.py)
@dataclass(frozen=True)
class Crop:
    crop_id: str
    name: str
    area_per_unit: float
    variety: Optional[str] = None
    revenue_per_area: Optional[float] = None  # ← 面積あたり収益

# 収益計算 (multi_field_crop_allocation_greedy_interactor.py 221行目)
revenue = quantity * crop.revenue_per_area * crop.area_per_unit
```

### 2.2 収益の依存関係

収益は以下に依存：
- ✅ 数量 (quantity)
- ✅ 作物の面積あたり収益 (crop.revenue_per_area)
- ✅ 作物の単位面積 (crop.area_per_unit)

収益は以下に**依存しない**：
- ❌ 栽培期間 (growth_days)
- ❌ 開始日 (start_date)
- ❌ 完了日 (completion_date)

**重要な含意**: 
- 収益は期間に依存しないため、理論的には期間をコスト最小化するだけで利益も最大化される
- **ただし、これは現実的ではない**（後述）

---

## 3. 問題点の分析

### 3.1 ⚠️ 現在のモデルの限界

#### 問題1: 収穫時期による価格変動を考慮できない

**現実の農業**:
```
早い収穫（春）: 高値で売れる（需要>供給）
標準収穫（夏）: 標準価格
遅い収穫（秋）: 安値（供給過多）
```

**現在のモデル**:
```python
revenue = quantity × crop.revenue_per_area × crop.area_per_unit
# ← 時期に関係なく一定
```

**影響**:
- GrowthPeriodOptimizeInteractorはコスト最小の期間を選ぶが、それが収益最大の期間とは限らない
- 例: コストが安い秋収穫を選んでも、価格暴落で利益が減る可能性

#### 問題2: 機会利益を考慮できない

**現実の経営判断**:
```
短期作物（60日）: 早く終わるので次の作物を植えられる
長期作物（120日）: 次の機会を失う
```

**現在のモデル**:
```python
# 期間は独立して最適化され、連続栽培の機会は考慮されない
```

#### 問題3: 面積依存コストを考慮できない

**ユーザー指摘の通り**:
```
農薬散布コスト: 面積に比例
肥料コスト: 面積に比例
灌漑コスト: 面積に比例
```

**現在のモデル**:
```python
cost = growth_days × field.daily_fixed_cost
# ← 面積に依存しない（固定コストのみ）
```

---

### 3.2 最適化処理間の不整合

#### シナリオ: 期間最適化の結果が利益最適ではない

**ステップ1**: GrowthPeriodOptimizeInteractor
```python
候補A: 開始4/1, 完了6/1 (60日), コスト=60万円
候補B: 開始4/15, 完了6/30 (75日), コスト=75万円

選択: 候補A (コスト最小) ← ここで決定
```

**ステップ2**: MultiFieldCropAllocationGreedyInteractor
```python
# GrowthPeriodOptimizeInteractorから候補Aのみを受け取る

候補A: 
  revenue = 100万円 (4-6月の標準価格)
  cost = 60万円
  profit = 40万円

# 実は候補Bの方が有利だった可能性:
候補B (未評価):
  revenue = 120万円 (6月下旬の高値時期)
  cost = 75万円
  profit = 45万円  # ← こちらが本当の最適解
```

**問題**: GrowthPeriodOptimizeInteractorが候補Aを最適と判断したため、候補Bは検討されない

---

## 4. なぜこの設計になっているか（推測）

### 4.1 実装の段階的進化

```
Phase 1 (初期): 単一圃場・単一作物の期間最適化
  → コスト最小化のみで十分（収益は固定）
  → GrowthPeriodOptimizeInteractor実装

Phase 2 (拡張): 複数圃場・複数作物の配置最適化
  → 利益最大化が必要
  → MultiFieldCropAllocationGreedyInteractor実装
  → 既存のGrowthPeriodOptimizeInteractorを内部で使用
```

### 4.2 設計上の仮定

**暗黙の仮定**:
1. 収益は期間に依存しない（crop.revenue_per_areaが一定）
2. コストは面積に依存しない（固定コストのみ）
3. 単一作物の場合、収益が一定なのでコスト最小化=利益最大化

**この仮定が成立する限り、現在の設計は妥当**

---

## 5. 統一性の評価

### 5.1 形式的には不統一

| 観点 | 評価 |
|-----|------|
| **目的関数の一貫性** | ❌ 不統一（コスト最小化 vs 利益最大化） |
| **収益の考慮** | ❌ 不統一（考慮なし vs 考慮あり） |
| **実装の一貫性** | ⚠️ 部分的（コスト計算式は統一） |

### 5.2 実質的には条件付きで整合

**条件**:
1. 収益が期間に依存しない
2. コストが数量/面積に依存しない

**この条件下では**:
- GrowthPeriodOptimizeInteractorのコスト最小化 = 実質的に利益最大化
- MultiFieldCropAllocationGreedyInteractorが正しい利益を計算できる

**結論**: **暗黙の仮定の下では動作するが、形式的には不統一**

---

## 6. 現実的な影響

### 6.1 現在のシステムで問題が顕在化するケース

#### ケース1: 季節価格変動がある場合

```python
# 現在のモデルでは表現できない
crop.revenue_per_area = 1000  # 一定

# 本来は:
def get_revenue(crop, completion_date):
    if completion_date.month in [4, 5]:  # 春
        return 1500  # 高値
    elif completion_date.month in [6, 7]:  # 初夏
        return 1000  # 標準
    else:  # 盛夏以降
        return 700   # 安値
```

#### ケース2: 面積依存コストがある場合

```python
# 現在のモデル
cost = growth_days × field.daily_fixed_cost

# 本来は:
cost = growth_days × field.daily_fixed_cost + 
       area_used × field.variable_cost_per_area
```

### 6.2 影響度の評価

| ケース | 影響度 | 理由 |
|-------|-------|------|
| **小規模農家（単一作物）** | 低 | 収益変動が少なく、固定コストモデルでも十分 |
| **大規模農家（複数作物）** | 中 | 面積依存コストの影響が大きい |
| **商業農業（市場価格連動）** | 高 | 季節価格変動の影響が大きい |
| **研究・シミュレーション** | 高 | 正確なモデルが必要 |

---

## 7. 推奨事項

### 7.1 短期的対応（優先度: 高）

#### 1. ドキュメントの明確化

**現状の仮定を明記**:
```markdown
## 最適化モデルの前提条件

### 収益モデル
- 収益は期間に依存しない（crop.revenue_per_areaが一定）
- 季節価格変動は考慮していない

### コストモデル
- 固定コストのみ（面積に依存しない）
- 変動コスト（農薬、肥料など）は将来実装予定

### 制約
- この前提下では、GrowthPeriodOptimizeInteractorのコスト最小化は
  実質的に利益最大化と等価
```

#### 2. テストの追加

```python
def test_period_optimization_implicit_profit_maximization():
    """
    収益が一定の場合、コスト最小化が利益最大化と等価であることを検証
    """
    # 収益固定、期間によってコストが変わる
    # コスト最小の期間 = 利益最大の期間
    assert True
```

### 7.2 中期的対応（優先度: 中）

#### 1. GrowthPeriodOptimizeInteractorの拡張

**オプションで利益最大化モードを追加**:

```python
@dataclass
class OptimalGrowthPeriodRequestDTO:
    crop_id: str
    variety: Optional[str]
    evaluation_period_start: datetime
    evaluation_period_end: datetime
    weather_data_file: str
    field: Field
    optimization_objective: str = "minimize_cost"  # or "maximize_profit"
    crop: Optional[Crop] = None  # 利益最大化に必要
    quantity: Optional[float] = None  # 利益計算に必要
```

```python
# 実装
if request.optimization_objective == "maximize_profit":
    if request.crop and request.quantity:
        # 各候補で利益を計算
        for candidate in candidates:
            revenue = request.quantity * request.crop.revenue_per_area * request.crop.area_per_unit
            candidate.profit = revenue - candidate.total_cost
        # 利益最大の候補を選択
        optimal_candidate = max(valid_candidates, key=lambda c: c.profit)
    else:
        raise ValueError("maximize_profit requires crop and quantity")
else:
    # 従来通りコスト最小化
    optimal_candidate = min(valid_candidates, key=lambda c: c.total_cost)
```

#### 2. 面積依存コストの実装

**Fieldエンティティの拡張**:
```python
@dataclass(frozen=True)
class Field:
    field_id: str
    name: str
    area: float
    daily_fixed_cost: float
    variable_cost_per_area: float = 0.0  # NEW: 面積あたり変動コスト
    location: Optional[str] = None
```

**コスト計算の更新**:
```python
fixed_cost = growth_days × field.daily_fixed_cost
variable_cost = growth_days × area_used × field.variable_cost_per_area
total_cost = fixed_cost + variable_cost
```

### 7.3 長期的対応（優先度: 低）

#### 1. 時間依存収益モデル

```python
@dataclass
class Crop:
    crop_id: str
    name: str
    area_per_unit: float
    variety: Optional[str] = None
    base_revenue_per_area: float = 0.0
    seasonal_price_multiplier: Optional[Dict[int, float]] = None  # 月ごとの価格係数

def calculate_revenue(crop: Crop, quantity: float, completion_date: datetime) -> float:
    base_revenue = quantity * crop.base_revenue_per_area * crop.area_per_unit
    if crop.seasonal_price_multiplier:
        multiplier = crop.seasonal_price_multiplier.get(completion_date.month, 1.0)
        return base_revenue * multiplier
    return base_revenue
```

#### 2. 統合最適化

**期間と配置を同時最適化**:
- 現在: 期間最適化 → 配置最適化（段階的）
- 提案: 統合最適化（ただし計算量増加）

---

## 8. まとめ

### 8.1 発見事項

1. ❌ **目的関数は統一されていない**
   - GrowthPeriodOptimizeInteractor: コスト最小化
   - MultiFieldCropAllocationGreedyInteractor: 利益最大化（デフォルト）

2. ⚠️ **暗黙の仮定により実質的には動作する**
   - 収益が期間に依存しない
   - コストが面積に依存しない
   - これらの条件下では、コスト最小化 ≈ 利益最大化

3. ⚠️ **ユーザー指摘の面積依存コスト**
   - 現状は実装されていない
   - 将来的な拡張が必要

### 8.2 評価

| 項目 | 評価 | 理由 |
|-----|------|------|
| **形式的統一性** | ❌ 低 | 目的関数が異なる |
| **実質的整合性** | ⚠️ 中 | 暗黙の仮定下では動作 |
| **拡張性** | ⚠️ 中 | 面積依存コスト、時間依存収益に対応困難 |
| **現実適合性** | ⚠️ 中 | 簡単な農業経営には十分だが、高度な最適化には不足 |

### 8.3 最終結論

**プロジェクトの最適化処理は、目的関数が形式的には統一されていないが、暗黙の仮定（収益・コストの独立性）の下では実質的に動作している。**

ただし、以下の改善が推奨される：
1. **短期**: ドキュメントで前提条件を明記
2. **中期**: 面積依存コストの実装
3. **長期**: 時間依存収益モデルの実装

---

**報告者**: AI Assistant  
**レビュー推奨**: プロジェクトオーナー

