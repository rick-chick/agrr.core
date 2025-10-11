# Quantity最適化：第4の決定変数

## 重要な指摘

**「RatioとQuantityは同義である」**

```
Ratio = Quantity / Max_Quantity
Quantity = Field.area × Ratio / Crop.area_per_unit

→ 本質的に同じ変数
→ Quantityの最適化 = 圃場の使用面積比率の最適化
```

---

## 現在の設計の問題点

### 問題: Quantityが固定されている

```python
# 現在の候補生成
max_quantity = field.area / crop.area_per_unit

candidate = AllocationCandidate(
    field=field,
    crop=crop,
    quantity=max_quantity,  # ← 常に最大値（100%使用）
    area_used=field.area,   # ← 圃場全体
)
```

**制限**:
- ❌ 圃場を100%使うことを前提
- ❌ 部分的な使用を考慮していない
- ❌ Quantityの最適化ができない

---

## Quantityが最適化変数である理由

### 理由1: 圃場の部分利用

```
Field A (1000m²):

Option 1: Rice 4000株 (100%使用)
  利益: 1,735,000円
  
Option 2: Rice 2000株 (50%使用)
  利益: 867,500円 × 1作 = 867,500円
  
  しかし、残り500m²で別の作物を栽培可能！
  
Option 2': Rice 2000株 (50%) + Tomato 1666株 (50%)
  利益: 867,500円 + 1,132,500円 = 2,000,000円 ✓
  
→ Option 2' が最適！
→ Quantityを調整することで利益が15%向上
```

---

### 理由2: 制約との兼ね合い

```
制約: Riceを最低5000株生産する必要

Field A: Rice 2000株
Field B: Rice 2000株
Field C: Rice 1000株
合計: 5000株 ✓

ここで、Field Aの Quantity を増やすと：

Field A: Rice 3000株 ← +1000株
Field C: Rice 0株    ← 削除可能
→ Field Cを他の作物に使える ✓
```

---

### 理由3: 連続作の調整

```
Field A:
  前期: Rice 4000株 (100%使用)
  後期: Tomato できない（スペースなし）

調整後:
  前期: Rice 2000株 (50%使用)
  後期: Tomato 1666株 (50%使用)
  合計利益: 向上 ✓
```

---

## Quantityを最適化変数とする定式化

### 決定変数

```
x[field, crop, period] ∈ {0, 1}  # 割り当ての有無
quantity[field, crop, period] ∈ [0, max_quantity]  # 連続変数

制約:
  quantity ≤ max_quantity × x
  
  # 圃場の面積制約（同時期）
  Σ(crop) quantity × area_per_unit ≤ field.area
  
  # 作物の目標生産量
  Σ(field, period) quantity ≥ target_quantity
```

---

## 実装方法

### Method 1: 離散的なQuantity候補（推奨）

**方針**: 複数のQuantityレベルで候補を生成

```python
QUANTITY_LEVELS = [1.0, 0.75, 0.5, 0.25]  # 100%, 75%, 50%, 25%

def _generate_candidates_with_quantity_variation(fields, crops, request):
    """Quantityを変化させた候補を生成"""
    candidates = []
    
    for field in fields:
        for crop in crops:
            max_quantity = field.area / crop.area_per_unit
            
            # 複数のQuantityレベルで候補を生成
            for level in QUANTITY_LEVELS:
                quantity = max_quantity * level
                area_used = quantity * crop.area_per_unit
                
                # Period はDPで最適化
                period_result = await optimize_period_dp(field, crop)
                
                for period in period_result.candidates[:3]:
                    # コスト・収益を計算
                    cost = period.growth_days * field.daily_fixed_cost
                    revenue = quantity * crop.revenue_per_area * crop.area_per_unit
                    profit = revenue - cost
                    
                    candidates.append(AllocationCandidate(
                        field=field,
                        crop=crop,
                        quantity=quantity,  # 可変
                        area_used=area_used,  # 可変
                        # ...
                    ))
    
    return candidates

# 候補数: F × C × P × Q = 10 × 5 × 3 × 4 = 600候補
# 許容範囲内
```

**メリット**:
- ✓ 実装が簡単
- ✓ 計算量が予測可能
- ✓ 既存フレームワークに統合しやすい

**デメリット**:
- ⚠️ 離散的（25%, 50%等）
- ⚠️ 最適値がレベル間にある場合を見逃す

---

### Method 2: Quantity調整の近傍操作（推奨）

**方針**: 局所探索でQuantityを調整

```python
def _adjust_quantity_neighbors(
    solution: List[CropAllocation],
    fields: List[Field],
) -> List[List[CropAllocation]]:
    """Quantityを調整する近傍操作"""
    neighbors = []
    
    for i, alloc in enumerate(solution):
        # 圃場の空き容量を計算
        used_area_in_field = sum(
            a.area_used 
            for a in solution 
            if a.field.field_id == alloc.field.field_id
        )
        available_area = alloc.field.area - used_area_in_field + alloc.area_used
        
        # Quantityを増減
        for multiplier in [0.8, 0.9, 1.1, 1.2, 1.5]:  # ±20%, ±10%, +50%
            new_quantity = alloc.quantity * multiplier
            new_area = new_quantity * alloc.crop.area_per_unit
            
            # 容量チェック
            if new_area > available_area:
                continue
            
            # 収益・コストを再計算
            new_revenue = None
            if alloc.crop.revenue_per_area:
                new_revenue = new_quantity * alloc.crop.revenue_per_area * alloc.crop.area_per_unit
            
            new_cost = alloc.total_cost  # コストは日数で決まる（数量無関係）
            new_profit = (new_revenue - new_cost) if new_revenue else None
            
            # 新しい割り当てを作成
            new_alloc = CropAllocation(
                allocation_id=str(uuid.uuid4()),
                field=alloc.field,
                crop=alloc.crop,
                quantity=new_quantity,  # ← 調整
                start_date=alloc.start_date,
                completion_date=alloc.completion_date,
                growth_days=alloc.growth_days,
                accumulated_gdd=alloc.accumulated_gdd,
                total_cost=new_cost,
                expected_revenue=new_revenue,
                profit=new_profit,
                area_used=new_area,  # ← 調整
            )
            
            neighbor = solution.copy()
            neighbor[i] = new_alloc
            neighbors.append(neighbor)
    
    return neighbors
```

**メリット**:
- ✓ より細かい調整が可能
- ✓ 局所探索の枠組みに統合
- ✓ 空き容量を有効活用

---

### Method 3: 連続最適化（高度）

**方針**: 線形計画法で厳密な最適Quantityを求める

```python
from pulp import *

def optimize_quantities_lp(allocations, fields):
    """線形計画法でQuantityを最適化"""
    prob = LpProblem("QuantityOptimization", LpMaximize)
    
    # 決定変数: quantity[allocation] ∈ [0, max_quantity]
    quantities = {}
    for alloc in allocations:
        max_qty = alloc.field.area / alloc.crop.area_per_unit
        quantities[alloc.allocation_id] = LpVariable(
            f"qty_{alloc.allocation_id}",
            lowBound=0,
            upBound=max_qty,
            cat='Continuous'
        )
    
    # 制約: 圃場の面積制約
    for field in fields:
        field_allocs = [a for a in allocations if a.field.field_id == field.field_id]
        prob += lpSum([
            quantities[a.allocation_id] * a.crop.area_per_unit
            for a in field_allocs
        ]) <= field.area
    
    # 目的関数: 総利益
    for alloc in allocations:
        revenue = quantities[alloc.allocation_id] * alloc.crop.revenue_per_area * alloc.crop.area_per_unit
        cost = alloc.growth_days * alloc.field.daily_fixed_cost  # 数量無関係
        prob += revenue - cost
    
    prob.solve()
    
    return {aid: var.varValue for aid, var in quantities.items()}
```

**メリット**:
- ✓ 厳密な最適Quantity
- ✓ 連続的な最適化

**デメリット**:
- ✗ 実装が複雑
- ✗ 外部ライブラリ必要
- ✗ 計算時間増加

---

## 重要な洞察：コストの性質

### コストは数量に依存しない！

```python
# 圃場のコスト
total_cost = growth_days × field.daily_fixed_cost

# ★ 重要: Quantityに依存しない
# 圃場を使っている日数で決まる
```

### 収益は数量に比例する

```python
revenue = quantity × crop.revenue_per_area × crop.area_per_unit

# ★ 重要: Quantityに比例
```

### 利益の性質

```python
profit = revenue - cost
       = (quantity × revenue_per_unit) - (days × daily_cost)

# Quantityを増やすと:
#   - 収益: 増加（比例）
#   - コスト: 不変
#   - 利益: 増加

→ Quantityは多いほど良い？
```

**待って！これは正しくない**

---

## 正しいコストモデル

### 現在のモデルの問題

```python
# 現在: 圃場全体のコスト
cost = growth_days × field.daily_fixed_cost

# 問題: 圃場の一部だけ使う場合もこのコスト？
```

### 正しいコストモデルの検討

#### Model A: 面積比例コスト

```python
# 使用面積に比例してコスト配分
area_ratio = allocation.area_used / field.area
cost = growth_days × field.daily_fixed_cost × area_ratio

例:
  Field A (1000m²、5000円/日):
    Rice 500m² (50%使用)
    Cost = 153日 × 5000円 × 0.5 = 382,500円
```

#### Model B: 固定コスト + 変動コスト

```python
# 固定コスト: 圃場を使うだけで発生
# 変動コスト: 使用面積に比例

fixed_cost = field.fixed_daily_cost × growth_days
variable_cost = field.variable_cost_per_area × area_used × growth_days

total_cost = fixed_cost + variable_cost

例:
  Field A (1000m²):
    固定コスト: 2000円/日
    変動コスト: 3円/m²/日
    
  Rice 500m² (50%使用):
    固定: 153日 × 2000円 = 306,000円
    変動: 153日 × 500m² × 3円 = 229,500円
    合計: 535,500円
```

#### Model C: 固定コスト（現在のモデル）

```python
# 圃場を使うと固定コスト（面積無関係）
cost = growth_days × field.daily_fixed_cost

例:
  Field A:
    Rice 2000株でも4000株でもコストは同じ
    
→ Quantityを増やすほど利益が増える
→ 常に100%使用が最適
```

---

## コストモデルによる最適化の変化

### Model A（面積比例）の場合

```
Field A (1000m²、5000円/日):

Option 1: Rice 100%
  Quantity: 4000株
  Area: 1000m²
  Cost: 153日 × 5000円 × 1.0 = 765,000円
  Revenue: 2,500,000円
  Profit: 1,735,000円

Option 2: Rice 50% + Tomato 50%
  Rice: 2000株 (500m²)
    Cost: 153日 × 5000円 × 0.5 = 382,500円
    Revenue: 1,250,000円
    Profit: 867,500円
  
  Tomato: 1666株 (500m²)
    Cost: 122日 × 5000円 × 0.5 = 305,000円
    Revenue: 1,500,000円
    Profit: 1,195,000円
  
  合計利益: 2,062,500円 ✓ より高い！
```

**結論**: 面積比例コストなら、Quantity最適化が重要

---

### Model C（固定コスト）の場合

```
Field A (1000m²、5000円/日):

Option 1: Rice 100%
  Cost: 765,000円（固定）
  Revenue: 2,500,000円
  Profit: 1,735,000円

Option 2: Rice 50%
  Cost: 765,000円（同じ！）
  Revenue: 1,250,000円（半減）
  Profit: 485,000円 ← 悪化！
  
→ 常に100%使用が最適
```

**結論**: 固定コストなら、常に100%使用が最適

---

## 実際の農業でのコスト構造

### 実際のコスト分析

```
圃場のコスト構成:

1. 固定コスト（面積無関係）:
   - 管理者の人件費
   - 保険料
   - 固定資産税
   
2. 変動コスト（面積比例）:
   - 肥料代
   - 農薬代
   - 収穫作業費
   - 灌漑費用

実際の割合:
  固定: 30-50%
  変動: 50-70%
```

**結論**: **混合モデル（固定+変動）が現実的**

---

## 推奨：混合コストモデルの導入

### 新しいFieldエンティティ

```python
@dataclass(frozen=True)
class Field:
    """Field with cost breakdown."""
    
    field_id: str
    name: str
    area: float
    
    # ★ コストを分離
    fixed_daily_cost: float      # 固定コスト（円/日）
    variable_cost_per_area: float  # 変動コスト（円/m²/日）
    
    @property
    def total_daily_cost(self) -> float:
        """従来互換性のため"""
        return self.fixed_daily_cost + (self.variable_cost_per_area * self.area)
```

### コスト計算の修正

```python
def calculate_allocation_cost(allocation: CropAllocation) -> float:
    """混合コストモデルでコストを計算"""
    # 固定コスト
    fixed_cost = allocation.growth_days * allocation.field.fixed_daily_cost
    
    # 変動コスト
    variable_cost = (
        allocation.growth_days * 
        allocation.area_used * 
        allocation.field.variable_cost_per_area
    )
    
    return fixed_cost + variable_cost

# 例:
# Field A (1000m²):
#   固定: 2000円/日
#   変動: 3円/m²/日
#
# Rice 2000株 (500m²、153日):
#   固定: 153 × 2000 = 306,000円
#   変動: 153 × 500 × 3 = 229,500円
#   合計: 535,500円
```

---

## Quantity最適化の実装

### Phase 1: 離散Quantity候補（推奨）

```python
# 候補生成時に複数のQuantityレベル
def _generate_candidates_multi_quantity(fields, crops, request):
    candidates = []
    
    for field in fields:
        for crop in crops:
            max_quantity = field.area / crop.area_per_unit
            
            # 100%, 75%, 50%, 25% の候補
            for level in [1.0, 0.75, 0.5, 0.25]:
                quantity = max_quantity * level
                area_used = quantity * crop.area_per_unit
                
                # コスト（混合モデル）
                fixed_cost = period.growth_days * field.fixed_daily_cost
                variable_cost = period.growth_days * area_used * field.variable_cost_per_area
                total_cost = fixed_cost + variable_cost
                
                # 収益
                revenue = quantity * crop.revenue_per_area * crop.area_per_unit
                profit = revenue - total_cost
                
                candidates.append(Candidate(
                    field, crop, period,
                    quantity=quantity,
                    area_used=area_used,
                    profit=profit
                ))
    
    return candidates
```

**実装工数**: 2-3日  
**効果**: +3-5%  

---

### Phase 2: Quantity調整の近傍操作

```python
# 局所探索でQuantityを微調整
def _quantity_adjustment_neighbors(solution):
    """Quantityを±10%, ±20%調整"""
    neighbors = []
    
    for i, alloc in enumerate(solution):
        # 空き容量を計算
        available = calculate_available_area(solution, alloc.field)
        
        for multiplier in [0.8, 0.9, 1.1, 1.2]:
            new_quantity = alloc.quantity * multiplier
            new_area = new_quantity * alloc.crop.area_per_unit
            
            # 容量チェック
            if new_area > available + alloc.area_used:
                continue
            
            # 新しい割り当て
            new_alloc = adjust_quantity(alloc, new_quantity)
            
            neighbor = solution.copy()
            neighbor[i] = new_alloc
            neighbors.append(neighbor)
    
    return neighbors
```

**実装工数**: 2日  
**効果**: +1-2%（Phase 1との組み合わせ）

---

### Phase 3: 連続最適化（LP）

```python
# すべての割り当てのQuantityを同時に最適化
def optimize_all_quantities_lp(solution, fields):
    prob = LpProblem("QuantityOpt", LpMaximize)
    
    # 決定変数
    quantities = {
        alloc.allocation_id: LpVariable(
            f"qty_{alloc.allocation_id}",
            lowBound=0,
            upBound=alloc.field.area / alloc.crop.area_per_unit,
        )
        for alloc in solution
    }
    
    # 制約: 圃場の面積（同時期の割り当て）
    for field in fields:
        for time_period in get_time_periods():
            allocs_in_period = get_allocations_in_period(solution, field, time_period)
            prob += lpSum([
                quantities[a.allocation_id] * a.crop.area_per_unit
                for a in allocs_in_period
            ]) <= field.area
    
    # 目的関数: 総利益
    for alloc in solution:
        qty_var = quantities[alloc.allocation_id]
        
        # 収益（数量比例）
        revenue_per_unit = alloc.crop.revenue_per_area * alloc.crop.area_per_unit
        revenue = qty_var * revenue_per_unit
        
        # コスト（混合モデル）
        # 簡略化: 固定コストは配分、変動コストは面積比例
        cost = alloc.total_cost  # ここでは簡略化
        
        prob += revenue - cost
    
    prob.solve()
    
    return {aid: var.varValue for aid, var in quantities.items()}
```

**実装工数**: 5-7日  
**効果**: +5-8%（理論上）

---

## 実装の統合

### 修正された候補生成

```python
async def _generate_candidates(fields, crops, request):
    """Quantityを可変にした候補生成"""
    candidates = []
    
    for field in fields:
        for crop in crops:
            max_quantity = field.area / crop.area_per_unit
            
            # ★ 複数のQuantityレベルで候補を生成
            for quantity_level in [1.0, 0.75, 0.5, 0.25]:
                quantity = max_quantity * quantity_level
                area_used = quantity * crop.area_per_unit
                
                # Period はDPで最適化
                period_result = await self.growth_period_optimizer.execute(
                    field_id=field.field_id,
                    crop_id=crop.crop_id,
                    # ...
                )
                
                for period_candidate in period_result.candidates[:3]:
                    # コスト計算（混合モデル）
                    fixed_cost = period_candidate.growth_days * field.fixed_daily_cost
                    variable_cost = period_candidate.growth_days * area_used * field.variable_cost_per_area
                    total_cost = fixed_cost + variable_cost
                    
                    # 収益計算
                    revenue = quantity * crop.revenue_per_area * crop.area_per_unit if crop.revenue_per_area else 0
                    profit = revenue - total_cost
                    profit_rate = profit / total_cost if total_cost > 0 else 0
                    
                    candidates.append(AllocationCandidate(
                        field=field,
                        crop=crop,
                        quantity=quantity,  # ★ 可変
                        area_used=area_used,  # ★ 可変
                        cost=total_cost,
                        revenue=revenue,
                        profit=profit,
                        profit_rate=profit_rate,
                        # ...
                    ))
    
    return candidates
```

---

## 候補数の増加への対応

### 候補数の変化

```
現状（Quantity固定）:
  F × C × P = 10 × 5 × 3 = 150候補

+ Quantity変動（4レベル）:
  F × C × P × Q = 10 × 5 × 3 × 4 = 600候補

増加: 4倍
```

### 対策

#### 対策1: Quantityレベルを絞る

```python
# 必要最小限のレベル
QUANTITY_LEVELS = [1.0, 0.5]  # 100% と 50% のみ

候補数: F × C × P × 2 = 300候補（2倍）
```

#### 対策2: 候補のフィルタリング

```python
# 利益率が低い候補を削除
candidates = [c for c in candidates if c.profit_rate > threshold]

# 各(Field, Crop)で上位N候補のみ保持
candidates = filter_top_n_per_field_crop(candidates, n=5)
```

#### 対策3: 2段階最適化

```python
# Stage 1: Quantity=100%で最適化
allocations_100 = optimize(candidates_with_100_percent)

# Stage 2: 選ばれた割り当てのみQuantity微調整
for alloc in allocations_100:
    fine_tuned = adjust_quantity(alloc, [0.8, 0.9, 1.1, 1.2])
```

---

## 推奨実装プラン

### Phase 1: コストモデルの明確化（Week 1）

```
1. Fieldエンティティの拡張
   - fixed_daily_cost
   - variable_cost_per_area
   
2. コスト計算の修正
   - 混合モデルの実装
   
3. テスト
   - 既存機能が壊れないことを確認
```

**工数**: 2-3日

---

### Phase 2: 離散Quantity候補（Week 2）

```
4. 候補生成の修正
   - 4レベルのQuantity候補（100%, 75%, 50%, 25%）
   
5. 候補フィルタリング
   - 上位候補のみ保持
   
6. テスト
   - Quantityが最適化されることを確認
```

**工数**: 2-3日  
**効果**: +3-5%

---

### Phase 3: Quantity調整の近傍操作（Week 3）

```
7. Quantity Adjustment操作の実装
   - ±10%, ±20%の調整
   
8. 局所探索への統合
   
9. テスト
```

**工数**: 2日  
**効果**: +1-2%

---

## まとめ

### ご質問への回答

**「圃場ごとの作物のQuantityは個別に最適化できないか？」**

**答え: はい、できます！そして重要な最適化次元です！**

### 重要な洞察

1. **Ratio = Quantity の正規化表現**
   ```
   Ratio = Quantity / Max_Quantity
   → 本質的に同じ
   ```

2. **Quantityは第4の決定変数**
   ```
   x[Field, Crop, Period, Quantity]
                          ^^^^^^^^
                          重要！
   ```

3. **コストモデルが重要**
   ```
   固定コスト → Quantity最適化は不要
   混合コスト → Quantity最適化が重要
   ```

---

### 実装の推奨

```
Step 1: コストモデルの明確化
  → 固定 vs 変動の比率を決定

Step 2: 離散Quantity候補の生成
  → 100%, 75%, 50%, 25%

Step 3: Quantity調整の近傍操作
  → ±10%, ±20%の微調整

期待効果: +4-7%
実装工数: 6-8日
```

---

### 決定変数の完全な定義

```
x[Field, Crop, Period, Quantity]
   │      │      │        │
   │      │      │        └─ 作付け数量（最適化対象）★NEW
   │      │      └────────── 栽培期間（DP最適化済み）
   │      └───────────────── 作物の種類（近傍操作）
   └──────────────────────── 圃場の選択（近傍操作）

最適化:
  - Period: DP（厳密解、100%）
  - Field: 近傍操作（Swap, Move）
  - Crop: 近傍操作（Change, Insert）
  - Quantity: 離散候補 + 近傍操作（Adjust）★NEW
```

この**第4の次元（Quantity）**を最適化することで、さらに4-7%の品質向上が期待できます！

実装しますか？
