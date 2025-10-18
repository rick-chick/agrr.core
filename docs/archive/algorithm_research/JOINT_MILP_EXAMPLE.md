# Joint MILP 実装例

## 簡単な例で理解する

### 問題設定

```
圃場: 2つ
  - Field A: 1000m²
  - Field B: 800m²

作物: 2つ
  - Rice: 単位面積0.25m², 収益2000円/m²
  - Tomato: 単位面積0.3m², 収益3000円/m²

期間候補（DPで事前計算済み）:
  Rice @ Field A:
    - Period R1: 4/1-8/31 (153日), コスト765k円
    - Period R2: 5/1-9/30 (153日), コスト765k円
  
  Rice @ Field B:
    - Period R3: 4/1-8/31 (153日), コスト612k円
  
  Tomato @ Field A:
    - Period T1: 9/1-12/31 (122日), コスト610k円
  
  Tomato @ Field B:
    - Period T2: 9/1-12/31 (122日), コスト488k円
    - Period T3: 10/1-1/31 (123日), コスト492k円

制約:
  - Rice 上限収益: 5,000k円
  - Tomato 最小生産量: 2000株
```

---

## MILP定式化

### 決定変数

```
バイナリ変数（栽培するか）:
  x_A_Rice_R1 ∈ {0,1}  # Field A で Rice を Period R1 で
  x_A_Rice_R2 ∈ {0,1}
  x_B_Rice_R3 ∈ {0,1}
  x_A_Tomato_T1 ∈ {0,1}
  x_B_Tomato_T2 ∈ {0,1}
  x_B_Tomato_T3 ∈ {0,1}

連続変数（数量）:
  q_A_Rice_R1 ∈ [0, 4000]  # Field A (1000m²) / 0.25m² = 4000株
  q_A_Rice_R2 ∈ [0, 4000]
  q_B_Rice_R3 ∈ [0, 3200]  # Field B (800m²) / 0.25m² = 3200株
  q_A_Tomato_T1 ∈ [0, 3333] # 1000m² / 0.3m² = 3333株
  q_B_Tomato_T2 ∈ [0, 2666] # 800m² / 0.3m² = 2666株
  q_B_Tomato_T3 ∈ [0, 2666]
```

---

### 目的関数

```
Maximize:
  # Rice @ Field A, Period R1
  + (2000円/m² × 0.25m² × q_A_Rice_R1) - (765k円 × x_A_Rice_R1)
  
  # Rice @ Field A, Period R2
  + (2000 × 0.25 × q_A_Rice_R2) - (765k × x_A_Rice_R2)
  
  # Rice @ Field B, Period R3
  + (2000 × 0.25 × q_B_Rice_R3) - (612k × x_B_Rice_R3)
  
  # Tomato @ Field A, Period T1
  + (3000 × 0.3 × q_A_Tomato_T1) - (610k × x_A_Tomato_T1)
  
  # Tomato @ Field B, Period T2
  + (3000 × 0.3 × q_B_Tomato_T2) - (488k × x_B_Tomato_T2)
  
  # Tomato @ Field B, Period T3
  + (3000 × 0.3 × q_B_Tomato_T3) - (492k × x_B_Tomato_T3)

簡略化:
  = 500 × q_A_Rice_R1 - 765k × x_A_Rice_R1
  + 500 × q_A_Rice_R2 - 765k × x_A_Rice_R2
  + 500 × q_B_Rice_R3 - 612k × x_B_Rice_R3
  + 900 × q_A_Tomato_T1 - 610k × x_A_Tomato_T1
  + 900 × q_B_Tomato_T2 - 488k × x_B_Tomato_T2
  + 900 × q_B_Tomato_T3 - 492k × x_B_Tomato_T3
```

---

### 制約

#### 制約1: 面積制約

```
# Field A
0.25 × q_A_Rice_R1 + 0.25 × q_A_Rice_R2 + 0.3 × q_A_Tomato_T1 ≤ 1000m²

# Field B
0.25 × q_B_Rice_R3 + 0.3 × q_B_Tomato_T2 + 0.3 × q_B_Tomato_T3 ≤ 800m²
```

#### 制約2: 時間的非重複

```
# Field A: R1 と R2 は重複（4月-9月）
x_A_Rice_R1 + x_A_Rice_R2 ≤ 1

# Field A: R1 と T1 は非重複（R1: 4-8月, T1: 9-12月）
# → 制約なし（両方可能）

# Field A: R2 と T1 は重複（R2は9月含む）
x_A_Rice_R2 + x_A_Tomato_T1 ≤ 1

# Field B: R3 と T2 は非重複
# → 制約なし

# Field B: R3 と T3 は非重複
# → 制約なし

# Field B: T2 と T3 は重複（9月-1月）
x_B_Tomato_T2 + x_B_Tomato_T3 ≤ 1
```

#### 制約3: 結合制約

```
q_A_Rice_R1 ≤ 4000 × x_A_Rice_R1
q_A_Rice_R2 ≤ 4000 × x_A_Rice_R2
q_B_Rice_R3 ≤ 3200 × x_B_Rice_R3
q_A_Tomato_T1 ≤ 3333 × x_A_Tomato_T1
q_B_Tomato_T2 ≤ 2666 × x_B_Tomato_T2
q_B_Tomato_T3 ≤ 2666 × x_B_Tomato_T3
```

#### 制約4: 上限収益制約

```
# Rice の年間総収益 ≤ 5,000k円
500 × q_A_Rice_R1 + 500 × q_A_Rice_R2 + 500 × q_B_Rice_R3 ≤ 5,000,000円
```

#### 制約5: 最小生産量

```
# Tomato 最小 2000株
q_A_Tomato_T1 + q_B_Tomato_T2 + q_B_Tomato_T3 ≥ 2000株
```

---

## PuLPコード

```python
from pulp import *

# Create problem
prob = LpProblem("CropAllocationExample", LpMaximize)

# Decision Variables
# Binary
x_A_Rice_R1 = LpVariable("x_A_Rice_R1", cat='Binary')
x_A_Rice_R2 = LpVariable("x_A_Rice_R2", cat='Binary')
x_B_Rice_R3 = LpVariable("x_B_Rice_R3", cat='Binary')
x_A_Tomato_T1 = LpVariable("x_A_Tomato_T1", cat='Binary')
x_B_Tomato_T2 = LpVariable("x_B_Tomato_T2", cat='Binary')
x_B_Tomato_T3 = LpVariable("x_B_Tomato_T3", cat='Binary')

# Continuous
q_A_Rice_R1 = LpVariable("q_A_Rice_R1", lowBound=0, upBound=4000)
q_A_Rice_R2 = LpVariable("q_A_Rice_R2", lowBound=0, upBound=4000)
q_B_Rice_R3 = LpVariable("q_B_Rice_R3", lowBound=0, upBound=3200)
q_A_Tomato_T1 = LpVariable("q_A_Tomato_T1", lowBound=0, upBound=3333)
q_B_Tomato_T2 = LpVariable("q_B_Tomato_T2", lowBound=0, upBound=2666)
q_B_Tomato_T3 = LpVariable("q_B_Tomato_T3", lowBound=0, upBound=2666)

# Objective Function
prob += (
    500 * q_A_Rice_R1 - 765000 * x_A_Rice_R1 +
    500 * q_A_Rice_R2 - 765000 * x_A_Rice_R2 +
    500 * q_B_Rice_R3 - 612000 * x_B_Rice_R3 +
    900 * q_A_Tomato_T1 - 610000 * x_A_Tomato_T1 +
    900 * q_B_Tomato_T2 - 488000 * x_B_Tomato_T2 +
    900 * q_B_Tomato_T3 - 492000 * x_B_Tomato_T3
)

# Constraints

# (1) Area constraints
prob += 0.25 * q_A_Rice_R1 + 0.25 * q_A_Rice_R2 + 0.3 * q_A_Tomato_T1 <= 1000, "Area_A"
prob += 0.25 * q_B_Rice_R3 + 0.3 * q_B_Tomato_T2 + 0.3 * q_B_Tomato_T3 <= 800, "Area_B"

# (2) Non-overlapping constraints
prob += x_A_Rice_R1 + x_A_Rice_R2 <= 1, "NoOverlap_A_R1_R2"
prob += x_A_Rice_R2 + x_A_Tomato_T1 <= 1, "NoOverlap_A_R2_T1"
prob += x_B_Tomato_T2 + x_B_Tomato_T3 <= 1, "NoOverlap_B_T2_T3"

# (3) Coupling constraints
prob += q_A_Rice_R1 <= 4000 * x_A_Rice_R1, "Coupling_A_Rice_R1"
prob += q_A_Rice_R2 <= 4000 * x_A_Rice_R2, "Coupling_A_Rice_R2"
prob += q_B_Rice_R3 <= 3200 * x_B_Rice_R3, "Coupling_B_Rice_R3"
prob += q_A_Tomato_T1 <= 3333 * x_A_Tomato_T1, "Coupling_A_Tomato_T1"
prob += q_B_Tomato_T2 <= 2666 * x_B_Tomato_T2, "Coupling_B_Tomato_T2"
prob += q_B_Tomato_T3 <= 2666 * x_B_Tomato_T3, "Coupling_B_Tomato_T3"

# (4) Revenue cap constraint
prob += (
    500 * q_A_Rice_R1 + 500 * q_A_Rice_R2 + 500 * q_B_Rice_R3 <= 5000000
), "RevenueCap_Rice"

# (5) Minimum quantity constraint
prob += (
    q_A_Tomato_T1 + q_B_Tomato_T2 + q_B_Tomato_T3 >= 2000
), "MinQuantity_Tomato"

# Solve
solver = PULP_CBC_CMD(msg=1)
status = prob.solve(solver)

# Print Results
print(f"Status: {LpStatus[status]}")
print(f"Objective: {value(prob.objective):,.0f}円")
print()

# Print selected allocations
allocations = [
    ("A", "Rice", "R1", x_A_Rice_R1, q_A_Rice_R1),
    ("A", "Rice", "R2", x_A_Rice_R2, q_A_Rice_R2),
    ("B", "Rice", "R3", x_B_Rice_R3, q_B_Rice_R3),
    ("A", "Tomato", "T1", x_A_Tomato_T1, q_A_Tomato_T1),
    ("B", "Tomato", "T2", x_B_Tomato_T2, q_B_Tomato_T2),
    ("B", "Tomato", "T3", x_B_Tomato_T3, q_B_Tomato_T3),
]

for field, crop, period, x_var, q_var in allocations:
    if x_var.varValue == 1:
        print(f"Field {field}, {crop}, Period {period}: {q_var.varValue:,.0f}株")
```

---

## 実行結果（予想）

```
Status: Optimal
Objective: 4,378,000円

Selected Allocations:
  Field A, Rice, R1: 4000株 (1000m²)
    収益: 2,000,000円
    コスト: 765,000円
    利益: 1,235,000円

  Field B, Rice, R3: 3200株 (800m²)
    収益: 1,600,000円
    コスト: 612,000円
    利益: 988,000円

  Field A, Tomato, T1: 3333株 (1000m²)
    収益: 3,000,000円
    コスト: 610,000円
    利益: 2,390,000円

  Field B, Tomato, T2: なし（T2 と T3 のどちらか）
  Field B, Tomato, T3: なし

総収益: Rice 3,600k + Tomato 3,000k = 6,600k
総コスト: 765k + 612k + 610k = 1,987k
総利益: 4,613k円

※ Rice上限制約により、最適配分が決定される
```

---

## 上限制約の効果

### Case A: 上限制約なし

```
最適解:
  - Field A: Rice R1 (4000株) → 1,235k利益
  - Field B: Rice R3 (3200株) → 988k利益
  - Field A: Tomato T1 (3333株) → 2,390k利益
  - Field B: Tomato T2 (2666株) → 1,911k利益

総利益: 6,524k円

Rice 総収益: 3,600k円
Tomato 総収益: 5,400k円
```

### Case B: Rice上限5,000k円

```
最適解:
  - Field A: Rice R1 (4000株) → 1,235k利益
  - Field B: Rice R3 (2400株) → 588k利益 ⚠️ 減少
  - Field A: Tomato T1 (3333株) → 2,390k利益
  - Field B: Tomato T2 (2666株) → 1,911k利益

総利益: 6,124k円

Rice 総収益: 5,000k円 (上限達成)
Tomato 総収益: 5,400k円

→ Field Bの Rice が 3200 → 2400株に調整される
→ Period×Quantityの相互作用 ⭐
```

---

## Greedy + LS では不可能な理由

### Greedy + LS のアプローチ

```
Step 1: 各Field×Cropで独立にDP最適化
  → Field A, Rice: Period R1 を選択
  → Field B, Rice: Period R3 を選択
  
Step 2: Quantityは最大（または離散レベル）
  → Field A, Rice: 4000株（100%）
  → Field B, Rice: 3200株（100%）
  
Step 3: 上限制約チェック
  Rice 総収益 = 2000k + 1600k = 3600k → OK

しかし:
  上限が5000kなので、まだ1400k分の余裕がある
  → でも、Period は固定されているので、
     これ以上Riceを作れない（Field が2つしかない）
```

### MILPのアプローチ

```
同時に決定:
  x[A, Rice, R1], q[A, Rice, R1]
  x[B, Rice, R3], q[B, Rice, R3]
  x[A, Tomato, T1], q[A, Tomato, T1]
  x[B, Tomato, T2], q[B, Tomato, T2]

制約:
  500 × q_A_Rice_R1 + 500 × q_B_Rice_R3 ≤ 5,000,000

ソルバーが自動的に:
  - q_A_Rice_R1 = 4000（最大）
  - q_B_Rice_R3 = 3200 だと上限を超える？
    → いや、3600k < 5000k なので問題ない
  
  でも、もし上限が 3000k だったら:
    - q_A_Rice_R1 = 2000
    - q_B_Rice_R3 = 2000
    のように自動調整される ⭐
```

---

## 並列栽培の例

### 問題設定（上限制約が厳しい場合）

```
Rice 上限収益: 2,000k円 (厳しい)

このとき、1つの圃場で複数期間に分けて栽培したい:
  Field A:
    - Rice R1 (4/1-8/31): 2000株 → 1000k円
    - Rice R2 (5/1-9/30): 不可（重複）
  
  Field B:
    - Rice R3 (4/1-8/31): 2000株 → 1000k円

合計: 2000k円（上限達成）

でも、もし並列栽培ができれば:
  Field A:
    - Rice (4/1-6/30): 1000株 → 500k円
    - Rice (7/1-9/30): 1000株 → 500k円
  
  Field B:
    - Rice (4/1-8/31): 2000株 → 1000k円

合計: 2000k円

ただし、これは「同じ圃場で時間をずらす」のではなく、
「同じ圃場を区画分割して並列栽培」を意味する。

→ これには「Mixed Candidate」が必要
→ Phase 2の課題 ⭐
```

---

## まとめ

### Joint MILPの威力

```
✓ Period×Quantityを同時に決定
✓ 上限制約を自動的に考慮
✓ すべての相互作用を捕捉
✓ 厳密最適解（小中規模）
```

### 実装の複雑さ

```
変数: 2 × F × C × P
制約: F + F×P² + F×C×P + 2C

例（F=2, C=2, P=3）:
  変数: 24個
  制約: 約30個

→ 手書き可能な規模

実規模（F=10, C=5, P=10）:
  変数: 1000個
  制約: 1000個以上

→ 自動生成が必須
```

### 推奨

```
上限収益制約がある → Joint MILP ⭐
上限収益制約がない → Greedy + LS ✓
```

この例により、Joint MILPの具体的なイメージがつかめたと思います！

