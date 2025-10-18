# Joint MILP: Period×Quantityの同時最適化

## 概要

**Joint MILP** = 混合整数線形計画法（Mixed Integer Linear Programming）による、Period（期間）とQuantity（数量/面積）の**同時最適化**

---

## 問題の定式化

### 決定変数

#### バイナリ変数（0-1変数）

```
x[f, c, p] ∈ {0, 1}

f: Field（圃場）
c: Crop（作物）
p: Period（期間候補）

x[f, c, p] = 1 のとき、圃場fで作物cを期間pで栽培する
x[f, c, p] = 0 のとき、栽培しない
```

#### 連続変数

```
q[f, c, p] ∈ [0, Q_max[f, c]]

q[f, c, p]: 圃場fで作物cを期間pで栽培する数量（株数）

制約:
  q[f, c, p] ≤ Q_max[f, c] × x[f, c, p]
  
  → x = 0 なら q = 0（栽培しないなら数量も0）
  → x = 1 なら q は自由（最大まで）
```

---

## 目的関数

### 利益最大化

```
Maximize: 
  Σ(f, c, p) [
    revenue[c] × q[f, c, p] × area_per_unit[c] 
    - 
    cost[f, p] × x[f, c, p]
  ]

where:
  revenue[c] = crop[c].revenue_per_area
  area_per_unit[c] = crop[c].area_per_unit
  cost[f, p] = days[p] × field[f].daily_fixed_cost
```

**重要**: 
- 収益はQuantity（数量）に比例
- コストはPeriod（期間の長さ）とField（圃場）に依存

---

## 制約条件

### 1. 面積制約（空間的制約）

```
Σ(c, p) q[f, c, p] × area_per_unit[c] ≤ field[f].area

for all f (各圃場で)

説明:
  同じ圃場で栽培するすべての作物・すべての期間の
  合計面積が、圃場の総面積を超えない
```

**注意**: これは時間的な重複も許容している（後述の制約で禁止）

---

### 2. 時間的非重複制約

```
Σ(c) x[f, c, p1] + x[f, c, p2] ≤ 1

for all f (各圃場で)
for all overlapping periods (p1, p2)

説明:
  同じ圃場で、重複する期間に複数の栽培はできない
```

**より正確な定式化**:

```
# 時間的重複を検出
overlap[p1, p2] = 1 if periods overlap, 0 otherwise

# 制約
Σ(c, p') x[f, c, p'] ≤ 1

for all f
for all p
where p' overlaps with p

説明:
  各圃場の各時点で、最大1つの栽培のみ
```

---

### 3. 数量と選択の結合

```
q[f, c, p] ≤ Q_max[f, c] × x[f, c, p]

where:
  Q_max[f, c] = field[f].area / crop[c].area_per_unit

説明:
  - x = 0（栽培しない）なら q = 0
  - x = 1（栽培する）なら q は 0 から Q_max まで自由
```

---

### 4. 上限収益制約（重要）⭐

```
Σ(f, p) revenue[c] × q[f, c, p] × area_per_unit[c] ≤ MaxRevenue[c]

for all c (各作物で)

説明:
  各作物の年間総収益が上限を超えない
  
  これにより、異なる期間での数量が相互に影響
  → Period×Quantityの同時最適化が必要になる理由
```

---

### 5. 最小・目標生産量制約

```
# 最小生産量
Σ(f, p) q[f, c, p] ≥ MinQuantity[c]  for all c

# 目標生産量（ソフト制約、ペナルティ項として）
deviation[c] = |Σ(f, p) q[f, c, p] - TargetQuantity[c]|

目的関数に追加:
  Maximize: Profit - Σ(c) penalty × deviation[c]
```

---

## 完全なMILP定式化

### 数学的モデル

```
決定変数:
  x[f, c, p] ∈ {0, 1}         # バイナリ変数
  q[f, c, p] ∈ [0, Q_max]    # 連続変数

パラメータ:
  F: 圃場の集合
  C: 作物の集合
  P: 期間候補の集合
  
  area[f]: 圃場fの面積
  area_per_unit[c]: 作物cの単位面積
  revenue_per_area[c]: 作物cの単位面積あたり収益
  daily_cost[f]: 圃場fの日次コスト
  days[p]: 期間pの日数
  
  MaxRevenue[c]: 作物cの年間最大収益

目的関数:
  Maximize:
    Σ(f∈F, c∈C, p∈P) [
      revenue_per_area[c] × area_per_unit[c] × q[f,c,p]
      -
      daily_cost[f] × days[p] × x[f,c,p]
    ]

制約:
  (1) 面積制約:
      Σ(c∈C, p∈P) area_per_unit[c] × q[f,c,p] ≤ area[f]
      for all f∈F

  (2) 時間的非重複:
      Σ(c∈C) x[f,c,p'] ≤ 1
      for all f∈F, p∈P, p' overlapping with p

  (3) 数量と選択の結合:
      q[f,c,p] ≤ (area[f] / area_per_unit[c]) × x[f,c,p]
      for all f∈F, c∈C, p∈P

  (4) 上限収益制約:
      Σ(f∈F, p∈P) revenue_per_area[c] × area_per_unit[c] × q[f,c,p] 
      ≤ MaxRevenue[c]
      for all c∈C

  (5) 最小生産量:
      Σ(f∈F, p∈P) q[f,c,p] ≥ MinQuantity[c]
      for all c∈C

  (6) 非負制約:
      x[f,c,p] ∈ {0, 1}
      q[f,c,p] ≥ 0
```

---

## Python実装（PuLP使用）

### 基本的な実装

```python
from pulp import *
from datetime import datetime
from typing import List, Dict

def optimize_joint_milp(
    fields: List[Field],
    crops: List[Crop],
    period_candidates: Dict[tuple, List[Period]],  # (field, crop) -> periods
    crop_requirements: Dict[str, CropRequirementSpec],
):
    """Joint MILP optimization for Period × Quantity."""
    
    # Create problem
    prob = LpProblem("CropAllocation_Joint", LpMaximize)
    
    # ===== Decision Variables =====
    
    # Binary variables: x[f, c, p]
    x = {}
    for field in fields:
        for crop in crops:
            periods = period_candidates.get((field.field_id, crop.crop_id), [])
            for period in periods:
                var_name = f"x_{field.field_id}_{crop.crop_id}_{period.id}"
                x[(field.field_id, crop.crop_id, period.id)] = LpVariable(
                    var_name,
                    cat='Binary'
                )
    
    # Continuous variables: q[f, c, p]
    q = {}
    for field in fields:
        for crop in crops:
            periods = period_candidates.get((field.field_id, crop.crop_id), [])
            max_quantity = field.area / crop.area_per_unit
            
            for period in periods:
                var_name = f"q_{field.field_id}_{crop.crop_id}_{period.id}"
                q[(field.field_id, crop.crop_id, period.id)] = LpVariable(
                    var_name,
                    lowBound=0,
                    upBound=max_quantity,
                    cat='Continuous'
                )
    
    # ===== Objective Function =====
    
    objective = []
    
    for field in fields:
        for crop in crops:
            periods = period_candidates.get((field.field_id, crop.crop_id), [])
            
            for period in periods:
                key = (field.field_id, crop.crop_id, period.id)
                
                # Revenue (quantity-dependent)
                revenue = (
                    crop.revenue_per_area * 
                    crop.area_per_unit * 
                    q[key]
                )
                
                # Cost (period-dependent, quantity-independent in fixed cost model)
                cost = (
                    field.daily_fixed_cost * 
                    period.days * 
                    x[key]
                )
                
                objective.append(revenue - cost)
    
    prob += lpSum(objective)
    
    # ===== Constraints =====
    
    # (1) Area constraint: Total area per field
    for field in fields:
        area_usage = []
        
        for crop in crops:
            periods = period_candidates.get((field.field_id, crop.crop_id), [])
            for period in periods:
                key = (field.field_id, crop.crop_id, period.id)
                area_usage.append(crop.area_per_unit * q[key])
        
        prob += lpSum(area_usage) <= field.area, f"Area_{field.field_id}"
    
    # (2) Non-overlapping constraint
    for field in fields:
        # Get all periods for this field
        all_periods = []
        for crop in crops:
            periods = period_candidates.get((field.field_id, crop.crop_id), [])
            all_periods.extend([(crop.crop_id, p) for p in periods])
        
        # For each time point, at most one allocation
        for i, (crop_i, period_i) in enumerate(all_periods):
            for j, (crop_j, period_j) in enumerate(all_periods[i+1:], start=i+1):
                if periods_overlap(period_i, period_j):
                    key_i = (field.field_id, crop_i, period_i.id)
                    key_j = (field.field_id, crop_j, period_j.id)
                    
                    prob += (
                        x[key_i] + x[key_j] <= 1,
                        f"NoOverlap_{field.field_id}_{i}_{j}"
                    )
    
    # (3) Coupling constraint: q <= Q_max × x
    for key in q.keys():
        field_id, crop_id, period_id = key
        field = find_field(fields, field_id)
        crop = find_crop(crops, crop_id)
        max_quantity = field.area / crop.area_per_unit
        
        prob += (
            q[key] <= max_quantity * x[key],
            f"Coupling_{key}"
        )
    
    # (4) Revenue cap constraint ⭐
    for crop in crops:
        crop_req = crop_requirements.get(crop.crop_id)
        if crop_req and crop_req.max_annual_revenue:
            total_revenue = []
            
            for field in fields:
                periods = period_candidates.get((field.field_id, crop.crop_id), [])
                for period in periods:
                    key = (field.field_id, crop.crop_id, period.id)
                    revenue = crop.revenue_per_area * crop.area_per_unit * q[key]
                    total_revenue.append(revenue)
            
            prob += (
                lpSum(total_revenue) <= crop_req.max_annual_revenue,
                f"RevenueCap_{crop.crop_id}"
            )
    
    # (5) Minimum quantity constraint
    for crop in crops:
        crop_req = crop_requirements.get(crop.crop_id)
        if crop_req and crop_req.min_quantity:
            total_quantity = []
            
            for field in fields:
                periods = period_candidates.get((field.field_id, crop.crop_id), [])
                for period in periods:
                    key = (field.field_id, crop.crop_id, period.id)
                    total_quantity.append(q[key])
            
            prob += (
                lpSum(total_quantity) >= crop_req.min_quantity,
                f"MinQuantity_{crop.crop_id}"
            )
    
    # ===== Solve =====
    
    solver = PULP_CBC_CMD(msg=1, timeLimit=300)  # 5 minutes limit
    status = prob.solve(solver)
    
    # ===== Extract Solution =====
    
    allocations = []
    
    for key, var in x.items():
        if var.varValue == 1:  # Selected
            field_id, crop_id, period_id = key
            quantity = q[key].varValue
            
            allocation = create_allocation(
                field_id, crop_id, period_id, quantity
            )
            allocations.append(allocation)
    
    return allocations, value(prob.objective)
```

---

## 詳細な制約の説明

### 制約1: 面積制約（Area Constraint）

```
Σ(c, p) area_per_unit[c] × q[f, c, p] ≤ area[f]

物理的意味:
  圃場fで使用する総面積 ≤ 圃場fの面積

例:
  Field A (1000m²):
    Rice (Spring): 2000株 × 0.25m² = 500m²
    Tomato (Fall): 1666株 × 0.3m² = 500m²
    合計: 1000m² ≤ 1000m² ✓

注意:
  この制約だけでは、同じ時期に複数作物が可能
  → 時間的非重複制約が必要
```

---

### 制約2: 時間的非重複（Non-overlapping Constraint）

```
x[f, c1, p1] + x[f, c2, p2] ≤ 1

if p1 と p2 が時間的に重複

物理的意味:
  同じ圃場の重複する期間には、最大1つの栽培のみ

例:
  Spring (4/1-8/31) と Summer (6/1-10/31) は重複
  → x[A, Rice, Spring] + x[A, Tomato, Summer] ≤ 1

しかし:
  Spring (4/1-8/31) と Fall (9/1-12/31) は非重複
  → x[A, Rice, Spring] + x[A, Tomato, Fall] ≤ 2（両方可能）
```

**実装の工夫**:

```python
def periods_overlap(p1: Period, p2: Period) -> bool:
    """Check if two periods overlap."""
    return not (
        p1.end_date < p2.start_date or 
        p2.end_date < p1.start_date
    )

# すべての期間ペアをチェック
for p1 in periods:
    for p2 in periods:
        if p1 != p2 and periods_overlap(p1, p2):
            prob += x[f, c1, p1] + x[f, c2, p2] <= 1
```

**計算量**: O(P²) 制約が生成される

---

### 制約3: 結合制約（Coupling Constraint）

```
q[f, c, p] ≤ Q_max × x[f, c, p]

物理的意味:
  栽培しない（x=0）なら数量もゼロ
  栽培する（x=1）なら数量は自由

これがないと:
  x = 0 でも q > 0 が可能になってしまう
  → 論理的矛盾

線形化のテクニック:
  このままで線形制約（Big-M制約の一種）
```

---

### 制約4: 上限収益制約（Revenue Cap）⭐

```
Σ(f, p) revenue_per_area[c] × area_per_unit[c] × q[f, c, p] 
≤ MaxRevenue[c]

物理的意味:
  作物cの年間総収益が上限を超えない
  市場の需要限界を表現

重要性:
  この制約により、異なる期間での数量配分が相互に影響
  
  例:
    Spring で Rice を多く作る
    → Fall で Rice を減らす必要
    
  → Period×Quantityの結合が生じる理由 ⭐
```

---

## Big-M法による非線形制約の線形化

### 問題: 条件付き制約

```
If x[f, c, p] = 1 then:
  q[f, c, p] ≥ MinQuantity
  
これは非線形（If-then）
```

### 解決: Big-M法

```
# 線形化
q[f, c, p] ≥ MinQuantity × x[f, c, p]

説明:
  x = 0 なら q ≥ 0（自明）
  x = 1 なら q ≥ MinQuantity（制約が有効）
```

---

## Period候補の準備

### Period候補の生成（事前処理）

```python
async def prepare_period_candidates(fields, crops, weather_data):
    """各Field×CropでDP最適化してPeriod候補を準備"""
    
    period_candidates = {}
    
    for field in fields:
        for crop in crops:
            # DPで最適Period を見つける（既存実装）
            result = await GrowthPeriodOptimizeInteractor.execute(
                field_id=field.field_id,
                crop_id=crop.crop_id,
                evaluation_period_start=start,
                evaluation_period_end=end,
                weather_data_file=weather_file,
            )
            
            # 上位5-10候補を保存
            candidates = []
            for candidate in result.candidates[:10]:
                if candidate.completion_date and candidate.total_cost:
                    period = Period(
                        id=f"{field.field_id}_{crop.crop_id}_{candidate.start_date.isoformat()}",
                        start_date=candidate.start_date,
                        end_date=candidate.completion_date,
                        days=candidate.growth_days,
                        cost=candidate.total_cost,
                    )
                    candidates.append(period)
            
            period_candidates[(field.field_id, crop.crop_id)] = candidates
    
    return period_candidates

# 結果:
# period_candidates[(field_a, rice)] = [
#   Period(4/1-8/31, 153日, 765k円),
#   Period(4/15-9/15, 154日, 770k円),
#   Period(5/1-9/30, 153日, 765k円),
# ]
```

---

## 完全な実装例

```python
from pulp import *
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class Period:
    """Period candidate from DP optimization."""
    id: str
    start_date: datetime
    end_date: datetime
    days: int
    cost: float

@dataclass
class Solution:
    """MILP solution."""
    allocations: List[CropAllocation]
    total_profit: float
    solve_time: float
    gap: float  # Optimality gap


class JointMILPOptimizer:
    """Joint MILP optimizer for Period × Quantity."""
    
    def __init__(
        self,
        fields: List[Field],
        crops: List[Crop],
        period_candidates: Dict[tuple, List[Period]],
        crop_requirements: Dict[str, CropRequirementSpec],
    ):
        self.fields = fields
        self.crops = crops
        self.period_candidates = period_candidates
        self.crop_requirements = crop_requirements
    
    def optimize(
        self,
        time_limit: int = 300,  # seconds
        gap_tolerance: float = 0.01,  # 1%
    ) -> Solution:
        """Run joint MILP optimization."""
        
        # Create problem
        prob = LpProblem("JointOptimization", LpMaximize)
        
        # Create variables
        x = self._create_binary_variables()
        q = self._create_quantity_variables()
        
        # Set objective
        prob += self._create_objective(x, q)
        
        # Add constraints
        self._add_area_constraints(prob, q)
        self._add_non_overlapping_constraints(prob, x)
        self._add_coupling_constraints(prob, x, q)
        self._add_revenue_cap_constraints(prob, q)
        self._add_quantity_constraints(prob, q)
        
        # Solve
        solver = PULP_CBC_CMD(
            msg=1,
            timeLimit=time_limit,
            gapRel=gap_tolerance
        )
        
        import time
        start_time = time.time()
        status = prob.solve(solver)
        solve_time = time.time() - start_time
        
        # Extract solution
        if status == LpStatusOptimal or status == LpStatusNotSolved:
            allocations = self._extract_solution(x, q)
            total_profit = value(prob.objective)
            gap = self._calculate_gap(prob)
            
            return Solution(
                allocations=allocations,
                total_profit=total_profit,
                solve_time=solve_time,
                gap=gap
            )
        else:
            raise ValueError(f"MILP solver failed with status: {LpStatus[status]}")
    
    def _create_objective(self, x, q):
        """Create objective function."""
        objective_terms = []
        
        for field in self.fields:
            for crop in self.crops:
                periods = self.period_candidates.get((field.field_id, crop.crop_id), [])
                
                for period in periods:
                    key = (field.field_id, crop.crop_id, period.id)
                    
                    # Revenue
                    revenue = (
                        crop.revenue_per_area * 
                        crop.area_per_unit * 
                        q[key]
                    )
                    
                    # Cost
                    cost = period.cost * x[key]
                    
                    objective_terms.append(revenue - cost)
        
        return lpSum(objective_terms)
    
    def _add_revenue_cap_constraints(self, prob, q):
        """Add revenue cap constraints."""
        
        for crop in self.crops:
            crop_req = self.crop_requirements.get(crop.crop_id)
            
            if crop_req and crop_req.max_annual_revenue:
                revenue_terms = []
                
                for field in self.fields:
                    periods = self.period_candidates.get((field.field_id, crop.crop_id), [])
                    
                    for period in periods:
                        key = (field.field_id, crop.crop_id, period.id)
                        revenue = (
                            crop.revenue_per_area * 
                            crop.area_per_unit * 
                            q[key]
                        )
                        revenue_terms.append(revenue)
                
                prob += (
                    lpSum(revenue_terms) <= crop_req.max_annual_revenue,
                    f"RevenueCap_{crop.crop_id}"
                )
    
    # ... (other constraint methods)
```

---

## MILPの特徴

### 利点

```
1. 厳密最適解（小中規模）
   - Gurobi: 数百万変数まで
   - CBC: 数万変数まで

2. Period×Quantityの相互作用を完全に捉える
   - 上限制約の影響
   - 非重複制約
   
3. 宣言的な記述
   - 「何を最適化するか」を記述するだけ
   - ソルバーが自動で解く

4. 複雑な制約も自然に表現
   - 線形制約なら何でも
```

### 欠点

```
1. 計算時間が予測困難
   - 問題によって数秒～数時間
   
2. 大規模問題では困難
   - 指数時間（最悪ケース）
   
3. 実装が専門的
   - MILP定式化の知識が必要
   
4. デバッグが困難
   - ソルバー内部が見えない
```

---

## 計算量の分析

### 変数数

```
バイナリ変数: F × C × P
連続変数: F × C × P

合計: 2 × F × C × P

例: F=10, C=5, P=10
  → 1,000変数
```

### 制約数

```
面積制約: F
非重複制約: F × C(P, 2) = F × P²/2（最悪ケース）
結合制約: F × C × P
上限制約: C
最小制約: C

合計: F + F×P² + F×C×P + 2C

例: F=10, C=5, P=10
  → 10 + 500 + 500 + 10 = 1,020制約
```

### 求解時間（推定）

```
CBC（無料ソルバー）:
  小規模（F=5, C=3, P=5）: 1-10秒
  中規模（F=10, C=5, P=10）: 30秒-5分
  大規模（F=20, C=10, P=20）: 数分-数時間

Gurobi（商用、高性能）:
  中規模: 5-30秒
  大規模: 30秒-5分
  超大規模: 数分-数十分
```

---

## Greedy + LS vs MILP の比較

| 項目 | Greedy + LS | Joint MILP |
|------|------------|------------|
| **実装難易度** | 中（★★☆☆☆） | 高（★★★★☆） |
| **計算時間** | 5-20秒 | 30秒-5分 |
| **解の品質** | 85-95% | 95-100% |
| **スケーラビリティ** | 高 | 中 |
| **デバッグ** | 容易 | 困難 |
| **上限制約対応** | 弱い | 強い ⭐ |
| **保守性** | 高 | 中 |

---

## 使い分けのガイドライン

### Greedy + LS を使うべき場合

```
✓ 上限収益制約がない
✓ 線形モデル
✓ リアルタイム性が重要（< 10秒）
✓ 実装・保守の容易さ重視
✓ 小中規模問題

→ 現在の実装
```

### Joint MILP を使うべき場合

```
✓ 上限収益制約がある ⭐
✓ 厳密な最適解が必要
✓ 複雑な制約が多数
✓ 計算時間に余裕（数分OK）
✓ 予算あり（商用ソルバー）

→ Phase 2で実装推奨
```

---

## 実装のロードマップ

### Phase 1: Greedy + LS（完了）✅

```
状況: 実装完了
品質: 92-97%（上限制約なし）
適用: 基本的なユースケース
評価: ✅ 実用的
```

### Phase 2: Joint MILP（推奨）

```
実装工数: 2-3週間

Step 1: Period候補の事前準備（3日）
  - DPで各Field×CropのPeriod候補を生成
  - 上位10候補を保存

Step 2: MILP定式化（5日）
  - 変数定義（x, q）
  - 制約実装（5種類）
  - 目的関数

Step 3: PuLP実装（4日）
  - ソルバー統合
  - 解の抽出

Step 4: テスト（3日）
  - 小規模データ
  - 上限制約ケース

品質: 95-98%（上限制約ありでも）
適用: 上限収益制約がある場合
```

### Phase 3: ハイブリッド（将来）

```
戦略:
  小規模部分問題: MILP（厳密解）
  大規模調整: Greedy + LS（高速）

品質: 93-97%
計算時間: 最適化
```

---

## まとめ

### Joint MILPとは

**Period（期間）とQuantity（数量）を同時に決定変数として最適化する手法**

```
決定変数:
  x[f, c, p] ∈ {0, 1}: 栽培するか
  q[f, c, p] ∈ [0, max]: 数量

目的:
  Maximize Profit = Revenue(q) - Cost(p, x)

制約:
  - 面積制約
  - 時間的非重複
  - 上限収益制約 ⭐
  - 数量制約
```

### いつ使うべきか

```
必須:
  ✓ 上限収益制約がある場合 ⭐
  ✓ 複雑な相互依存制約

推奨:
  ✓ 厳密解が必要
  ✓ 中規模問題（< 1000変数）

不要:
  ✓ 線形モデル + 制約が緩い
  ✓ リアルタイム性重視
  → Greedy + LS で十分
```

### 実装の推奨

```
Phase 1（現状）: Greedy + LS
  → 基本ケースで実用化 ✓

Phase 2（条件付き）: Joint MILP
  → 上限収益制約がある場合に実装 ⭐
  → 工数: 2-3週間
  → 品質: 95-98%
```

**上限収益制約の有無で判断することを推奨します！**

