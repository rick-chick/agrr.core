# 圃場ごとの作付面積比率の最適化

## 質問

**各圃場で、作物の作付面積の比率を個別に最適化できるか？**

---

## 現在の設計の確認

### 現状の前提

```python
# 現在の候補生成
for field in fields:
    for crop in crops:
        # 圃場全体を1つの作物で使うことを前提
        max_quantity = field.area / crop.area_per_unit
        
        candidate = AllocationCandidate(
            field=field,
            crop=crop,
            quantity=max_quantity,  # 圃場全体を使用
            area_used=field.area,   # 圃場全体
        )
```

**問題**: 圃場を複数作物で分割利用することを考慮していない

---

## 求められる最適化

### 例：圃場の分割利用

```
Field A (1000m²) での作付比率の最適化:

Option 1: Rice 100%
  Rice 4000株 (1000m²)
  利益: 1,500,000円

Option 2: Rice 50% + Tomato 50%
  Rice 2000株 (500m²)
  Tomato 1666株 (500m²)
  利益: 1,800,000円 ← より高い！

Option 3: Rice 30% + Tomato 50% + Wheat 20%
  Rice 1200株 (300m²)
  Tomato 1666株 (500m²)
  Wheat 1000株 (200m²)
  利益: 1,900,000円 ← さらに高い！
  
→ 最適な面積比率は？
```

---

## 2つのアプローチ

### Approach A: 離散的な組み合わせ最適化（現在の実装）

**方針**: 
- 各割り当ては独立
- 時間的に分離（Non-overlapping）
- 同じ圃場・同じ時期に1つの作物のみ

```
Field A (1000m²):
  期間1 (4/1-8/31): Rice 4000株 (1000m²全体)
  期間2 (9/1-12/31): Tomato 3333株 (1000m²全体)
  
特徴:
  ✓ 時間軸で分離
  ✓ 実装がシンプル
  ✗ 同時期の混植はできない
```

---

### Approach B: 連続的な面積比率最適化（新規検討）

**方針**:
- 各圃場で作物の面積比率を決定
- 同じ時期に複数作物を並行栽培
- 連続変数の最適化

```
Field A (1000m²):
  期間 (4/1-8/31):
    - Rice: 300m² (30%)
    - Tomato: 500m² (50%)
    - Wheat: 200m² (20%)
  合計: 1000m² (100%)
  
特徴:
  ✓ 同時期の混植が可能
  ✓ リスク分散
  ✗ 実装が複雑
```

---

## 面積比率最適化の数学的定式化

### 決定変数

```python
# 圃場 f、時期 t での作物 c の面積比率
ratio[f][t][c] ∈ [0, 1]

制約:
  Σ(c) ratio[f][t][c] = 1  # 各圃場・各時期で合計100%
  
数量:
  quantity[f][t][c] = (field[f].area × ratio[f][t][c]) / crop[c].area_per_unit
```

### 目的関数

```python
Maximize: Σ(f, t, c) [
  quantity[f][t][c] × (
    revenue_per_unit[c] - 
    cost_per_day[f] × growth_days[t][c] / quantity[f][t][c]
  )
]
```

---

## 実装方法

### Method 1: 離散的な比率（実装しやすい）

**方針**: 予め定義された比率パターンから選択

```python
# 事前定義された比率パターン
RATIO_PATTERNS = [
    {"rice": 1.0},                              # 100% Rice
    {"rice": 0.5, "tomato": 0.5},              # 50%-50%
    {"rice": 0.3, "tomato": 0.5, "wheat": 0.2}, # 30%-50%-20%
    {"rice": 0.7, "tomato": 0.3},              # 70%-30%
    # ... more patterns
]

# 各圃場で各パターンを評価
for field in fields:
    for pattern in RATIO_PATTERNS:
        profit = calculate_profit(field, pattern)
        candidates.append((field, pattern, profit))
```

**メリット**:
- ✓ 実装が簡単
- ✓ 計算量が少ない
- ✓ 既存フレームワークに統合しやすい

**デメリット**:
- ✗ 最適比率を見逃す可能性
- ✗ パターン数が限定的

---

### Method 2: 連続最適化（線形計画法）

**方針**: 連続変数として比率を最適化

```python
from pulp import *

def optimize_area_ratios(field, crops, period):
    """線形計画法で面積比率を最適化"""
    prob = LpProblem(f"AreaRatio_{field.field_id}", LpMaximize)
    
    # 決定変数: ratio[crop] ∈ [0, 1]
    ratios = {
        crop.crop_id: LpVariable(f"ratio_{crop.crop_id}", 0, 1, LpContinuous)
        for crop in crops
    }
    
    # 制約: 比率の合計 = 1
    prob += lpSum(ratios.values()) == 1
    
    # 目的関数: 総利益の最大化
    profits = {}
    for crop in crops:
        quantity = (field.area * ratios[crop.crop_id]) / crop.area_per_unit
        revenue = quantity * crop.revenue_per_area * crop.area_per_unit
        cost = period.growth_days * field.daily_fixed_cost * ratios[crop.crop_id]
        profits[crop.crop_id] = revenue - cost
    
    prob += lpSum(profits.values())
    
    # 解く
    prob.solve()
    
    # 結果を取得
    optimal_ratios = {
        crop_id: var.varValue 
        for crop_id, var in ratios.items()
    }
    
    return optimal_ratios
```

**メリット**:
- ✓ 厳密な最適比率
- ✓ 柔軟性が高い

**デメリット**:
- ✗ 実装が複雑
- ✗ 外部ライブラリ必要（PuLP等）
- ✗ 計算時間増加

---

### Method 3: 貪欲法 + 微調整（推奨）

**方針**: 貪欲法で初期配分→数値最適化で微調整

```python
def optimize_area_ratios_greedy(field, crops, period):
    """貪欲法 + 微調整で面積比率を最適化"""
    
    # Phase 1: 貪欲法で初期配分
    allocations = []
    remaining_area = field.area
    
    # 利益率でソート
    sorted_crops = sorted(crops, key=lambda c: calculate_profit_rate(c), reverse=True)
    
    for crop in sorted_crops:
        if remaining_area <= 0:
            break
        
        # 貪欲に割り当て
        area_to_allocate = min(remaining_area, field.area * 0.5)  # 最大50%
        quantity = area_to_allocate / crop.area_per_unit
        
        allocations.append({
            'crop': crop,
            'area': area_to_allocate,
            'quantity': quantity
        })
        
        remaining_area -= area_to_allocate
    
    # Phase 2: 微調整（勾配法）
    # 各作物の面積を±10%調整して利益を最大化
    for iteration in range(10):
        improved = False
        
        for i in range(len(allocations)):
            for delta in [-0.1, -0.05, 0.05, 0.1]:  # ±10%, ±5%
                # 面積を調整
                new_area = allocations[i]['area'] * (1 + delta)
                
                # 他の作物から面積を取る/渡す
                if delta > 0:
                    # 他から取る
                    # ...
                
                new_profit = calculate_profit(new_allocations)
                if new_profit > current_profit:
                    allocations = new_allocations
                    improved = True
                    break
        
        if not improved:
            break
    
    return allocations
```

**メリット**:
- ✓ バランスが良い
- ✓ 実装が比較的簡単
- ✓ 実用的な品質

---

## 実装の難易度と効果

| Method | 実装難易度 | 計算時間 | 解の品質 | 推奨度 |
|--------|-----------|---------|---------|--------|
| **離散パターン** | ★☆☆☆☆ | 低 | 80-90% | ⭐⭐⭐⭐☆ |
| **連続最適化(LP)** | ★★★★☆ | 中 | 100% | ⭐⭐⭐☆☆ |
| **貪欲+微調整** | ★★★☆☆ | 中 | 90-95% | ⭐⭐⭐⭐⭐ |

---

## 実装の統合

### 現在の候補生成への統合

```python
async def _generate_candidates(fields, crops, request):
    candidates = []
    
    for field in fields:
        # ★ 各圃場で面積比率を最適化
        optimal_ratios = optimize_area_ratios(field, crops, request)
        
        # 最適化された比率に基づいて候補を生成
        for crop_id, ratio in optimal_ratios.items():
            if ratio > 0.05:  # 5%以上なら候補として追加
                crop = find_crop(crops, crop_id)
                area = field.area * ratio
                quantity = area / crop.area_per_unit
                
                # Period はDPで最適化
                period_result = await optimize_period_dp(field, crop)
                
                candidates.append(AllocationCandidate(
                    field=field,
                    crop=crop,
                    quantity=quantity,  # 最適比率から計算
                    area_used=area,
                    # ...
                ))
    
    return candidates
```

---

## 具体例

### Example 1: 単一作物 vs 混植

```
Field A (1000m², 5000円/日)

Option 1: Rice 100%
┌─────────────────────────────────┐
│      Rice 4000株 (1000m²)       │
│                                 │
│ Cost: 765,000円                 │
│ Revenue: 2,500,000円            │
│ Profit: 1,735,000円             │
└─────────────────────────────────┘

Option 2: Rice 50% + Tomato 50%
┌─────────────┬───────────────────┐
│ Rice 2000株 │ Tomato 1666株     │
│   (500m²)   │    (500m²)        │
│             │                   │
│ Cost: 382,500円 + 382,500円     │
│ Revenue: 1,250,000 + 1,500,000  │
│ Profit: 1,985,000円 ✓ +250,000 │
└─────────────┴───────────────────┘

→ 混植の方が利益が高い！
```

---

### Example 2: 3作物の最適比率

```
Field A (1000m²)
Crops: Rice, Tomato, Wheat

離散パターンでの探索:

Pattern 1: 100%-0%-0%
  Profit: 1,735,000円

Pattern 2: 50%-50%-0%
  Profit: 1,985,000円

Pattern 3: 30%-50%-20%
  Rice 1200株 (300m²)
  Tomato 1666株 (500m²)
  Wheat 1000株 (200m²)
  Profit: 2,100,000円 ✓ 最良

Pattern 4: 33%-33%-33%
  Profit: 1,950,000円

→ 最適比率: 30%-50%-20%
```

---

## 時間軸との関係

### ケースA: 時間分離（現在の実装）

```
Field A (1000m²):
  4/1-8/31:  Rice 4000株 (1000m²全体)
  9/1-12/31: Tomato 3333株 (1000m²全体)
  
特徴:
  - 時期ごとに100%使用
  - 混植なし
  - Period最適化で解決済み
```

---

### ケースB: 空間分割（新規検討）

```
Field A (1000m²):
  4/1-8/31の間、同時に:
    - Rice: 300m² (30%)
    - Tomato: 500m² (50%)
    - Wheat: 200m² (20%)
  
特徴:
  - 同じ時期に複数作物
  - 面積比率の最適化が必要
  - より複雑
```

---

### ケースC: 時間×空間のマトリクス（最も複雑）

```
Field A (1000m²):

4/1-6/30:
  - Rice: 500m² (50%)
  - Tomato: 500m² (50%)

7/1-9/30:
  - Rice: 300m² (30%)  ← 継続（面積縮小）
  - Tomato: 500m² (50%) ← 継続
  - Wheat: 200m² (20%)  ← 新規追加

10/1-12/31:
  - Wheat: 500m² (50%)  ← 継続（面積拡大）
  - Lettuce: 500m² (50%) ← 新規

特徴:
  - 時間と空間の両方で最適化
  - 最も柔軟
  - 最も複雑
```

---

## 実装戦略

### Strategy 1: 時間分離のみ（現状維持）★ 推奨（Phase 1）

```python
# 同じ圃場・同じ時期に1作物のみ
# 時間軸で分離することで複数作物を栽培

Field A:
  [─────Rice─────][────Tomato────]
  4/1        8/31 9/1        12/31
  
実装: 現在の設計で対応可能
品質: 85-95%
複雑度: 低
```

**推奨理由**:
- ✓ すでに実装済み
- ✓ 十分な品質
- ✓ 実装がシンプル

---

### Strategy 2: 離散的な空間分割（Phase 2） ★ 推奨

```python
# 事前定義された比率パターンから選択
AREA_RATIO_PATTERNS = [
    {"rice": 1.0},                      # 単作
    {"rice": 0.5, "tomato": 0.5},      # 50-50
    {"rice": 0.3, "tomato": 0.5, "wheat": 0.2},  # 30-50-20
    {"rice": 0.7, "tomato": 0.3},      # 70-30
    # ... 10-20パターン
]

# 各圃場・各時期で最良のパターンを選択
for field in fields:
    for period in periods:
        best_pattern = None
        best_profit = 0
        
        for pattern in AREA_RATIO_PATTERNS:
            profit = calculate_profit(field, period, pattern)
            if profit > best_profit:
                best_pattern = pattern
                best_profit = profit
        
        # 最良パターンで候補を生成
        for crop_id, ratio in best_pattern.items():
            area = field.area * ratio
            quantity = area / crop.area_per_unit
            candidates.append(Candidate(field, crop, period, quantity, area))
```

**実装難易度**: ★★☆☆☆  
**効果**: +3-5%  
**推奨**: ⭐⭐⭐⭐☆

---

### Strategy 3: 連続最適化（Phase 3）

```python
from pulp import *

def optimize_continuous_ratios(field, crops, period):
    """連続的な面積比率の最適化"""
    prob = LpProblem(f"AreaRatio_{field.field_id}", LpMaximize)
    
    # 決定変数: ratio[crop] ∈ [0, 1]
    ratios = {
        crop.crop_id: LpVariable(
            f"ratio_{crop.crop_id}", 
            lowBound=0, 
            upBound=1, 
            cat='Continuous'
        )
        for crop in crops
    }
    
    # 制約: 合計100%
    prob += lpSum(ratios.values()) == 1
    
    # 目的関数: 利益最大化
    for crop in crops:
        quantity = (field.area * ratios[crop.crop_id]) / crop.area_per_unit
        revenue = quantity * crop.revenue_per_area * crop.area_per_unit
        cost_share = field.daily_fixed_cost * period.growth_days * ratios[crop.crop_id]
        prob += revenue - cost_share
    
    prob.solve()
    
    return {crop_id: var.varValue for crop_id, var in ratios.items()}
```

**実装難易度**: ★★★★☆  
**効果**: +5-10%  
**推奨**: ⭐⭐⭐☆☆（オプション）

---

## 実装の優先順位

### Phase 1: 時間分離のみ（現状）

```
実装: 完了済み ✓
品質: 85-95%
複雑度: 低

結論: まずこれで十分
```

---

### Phase 2: 離散パターン追加

```
実装工数: 3-5日
品質: 88-96% (+3-5%)
複雑度: 中

タイミング: Field・Crop最適化が完成後
優先度: ⭐⭐⭐⭐☆（推奨）
```

**実装イメージ**:

```python
# 候補生成時にパターンを考慮
def _generate_candidates_with_patterns(fields, crops, request):
    candidates = []
    
    for field in fields:
        # 単作候補
        for crop in crops:
            candidates.append(create_single_crop_candidate(field, crop))
        
        # 混植候補（2作物）
        for crop_a, crop_b in combinations(crops, 2):
            for ratio_a in [0.3, 0.5, 0.7]:
                ratio_b = 1.0 - ratio_a
                candidates.append(create_mixed_candidate(
                    field, 
                    [(crop_a, ratio_a), (crop_b, ratio_b)]
                ))
        
        # 混植候補（3作物）- オプション
        for crop_a, crop_b, crop_c in combinations(crops, 3):
            candidates.append(create_mixed_candidate(
                field,
                [(crop_a, 0.3), (crop_b, 0.5), (crop_c, 0.2)]
            ))
    
    return candidates
```

---

### Phase 3: 連続最適化（オプション）

```
実装工数: 5-7日
品質: 90-98% (+2-5%)
複雑度: 高

タイミング: 厳密解が必要になった時
優先度: ⭐⭐☆☆☆（低）
```

---

## 問題の複雑度

### 候補数の爆発

```
現状（単作のみ）:
  F × C × P = 10 × 5 × 5 = 250候補

離散パターン（2作物混植）:
  単作: F × C × P = 250
  混植: F × C(C-1)/2 × P × 3パターン = 10 × 10 × 5 × 3 = 1,500
  合計: 1,750候補 ← 約7倍

離散パターン（3作物混植も含む）:
  単作: 250
  2作物混植: 1,500
  3作物混植: F × C(C-1)(C-2)/6 × P = 10 × 10 × 5 = 500
  合計: 2,250候補 ← 約9倍
```

**結論**: 候補数が爆発的に増加するため、慎重な実装が必要

---

## 推奨実装プラン

### 📍 現状（Phase 1）

```
方針: 時間分離のみ
実装: 完了 ✓
品質: 85-95%

結論: まずこれで実用化
```

---

### 📍 Phase 2（2-3週間後）

```
方針: 離散パターン（限定的）
実装内容:
  1. 2作物混植パターン（50-50のみ）
  2. 利益率の高い組み合わせのみ
  3. 候補数を制限（×2-3倍程度に抑える）

期待効果: +2-3%
実装工数: 3-5日
```

**実装例**:

```python
# 限定的な混植パターン
def generate_limited_mixed_patterns(field, crops):
    """利益率の高い組み合わせのみ生成"""
    candidates = []
    
    # 単作（必須）
    for crop in crops:
        candidates.append((field, [(crop, 1.0)]))
    
    # 2作物混植（利益率上位3組のみ）
    crop_pairs = get_top_profitable_pairs(crops, top_k=3)
    for crop_a, crop_b in crop_pairs:
        # 50-50パターンのみ
        candidates.append((field, [(crop_a, 0.5), (crop_b, 0.5)]))
    
    return candidates

# 候補数: C + 3 = 5 + 3 = 8候補/圃場
# 全体: F × 8 = 10 × 8 = 80候補（許容範囲）
```

---

### 📍 Phase 3（将来）

```
方針: 連続最適化（LP）
実装: 厳密解が必要になったら
期待効果: +3-5%
実装工数: 5-7日
```

---

## まとめ

### 質問への回答

**「圃場ごとの作物の作付面積の比率は個別に最適化できるか？」**

**答え: はい、できます！**

ただし、実装方法によって複雑度が異なります：

| Approach | 実装難易度 | 品質 | 推奨 |
|----------|-----------|------|------|
| **時間分離** | 低 | 85-95% | ✅ Phase 1 |
| **離散パターン** | 中 | 88-96% | ✅ Phase 2 |
| **連続最適化** | 高 | 90-98% | △ Phase 3 |

---

### 推奨実装順序

```
Week 1-3: 時間分離（現状維持）
  → Field・Crop の組み合わせ最適化に集中

Week 4-5: 離散パターン追加
  → 2作物混植（50-50パターン）のみ
  → 候補数を制限

Week 6-: 連続最適化（オプション）
  → 厳密な最適比率が必要な場合
```

---

### 段階的な品質向上

```
Phase 1: 時間分離のみ
  品質: 85-95%
  実装: 簡単

Phase 2: + 離散パターン
  品質: 88-96% (+2-3%)
  実装: 中程度

Phase 3: + 連続最適化
  品質: 90-98% (+2-3%)
  実装: 複雑
```

---

## 結論

### 短期的な推奨

**現状の時間分離で十分** ✓
- 同じ圃場で時期をずらして複数作物を栽培
- 実装済み
- 品質85-95%で実用的

### 中期的な拡張

**離散パターンの追加** ⭐
- 50-50混植パターンを追加
- 候補数を制限して実装
- 品質+2-3%向上

### 長期的なオプション

**連続最適化（LP）**
- 厳密な最適比率
- 必要になったら実装

この段階的アプローチにより、**早期に価値を提供しながら、継続的に改善**できます！

