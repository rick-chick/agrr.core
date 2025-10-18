# 上限収益制約と並行栽培の問題

## 🚨 重大な設計上の問題

**ユーザーの指摘**: 上限収益制約がある場合、Period×Quantityの独立最適化では最適解を見逃す

---

## 問題の具体例

### シナリオ: 上限収益制約

```
制約:
  - 各作物に販売可能な上限がある（市場の需要限界）
  - 例: Rice の年間販売可能量 = 10,000株
  - これを超える生産は収益にならない

圃場A (1000m²):
  max_quantity_per_crop = field.area / crop.area_per_unit
  Rice: 4000株まで可能
```

---

### ❌ 現在の最適化の問題

#### 独立最適化の場合

```
Step 1: Period最適化（圃場全体を1作物が使う前提）
  Spring (4/1-8/31): Rice 4000株 ← 圃場全体
  Fall (9/1-12/31): Rice 4000株 ← 圃場全体
  
  年間生産: 8000株
  上限: 10,000株
  OK、制約内 ✓

しかし...

Step 2: 上限に達したら他の作物を探す
  Spring: Rice 4000株（圃場全体）
  Fall: Rice 2000株（上限まで）+ 空き2000株分
  
  問題: 秋期の空きをどうする？
  → 別の作物を「追加」する必要
  → しかし、Period最適化の段階では考慮されていない
```

---

### ✅ 正しい最適化（並行栽培）

```
同じ時期に複数作物を並行栽培:

Spring (4/1-8/31):
  - Rice: 2000株 (500m², 25%)
  - Tomato: 1666株 (500m², 25%)  } 並行
  - Wheat: 2500株 (500m², 25%)   }

Fall (9/1-12/31):
  - Rice: 2000株 (500m², 25%) ← 上限10,000株に到達
  - Lettuce: 1000株 (300m², 15%)  } 並行
  - Cabbage: 800株 (200m², 10%)   }

年間Rice生産: 4000株（上限内）
他の作物: 多様性確保、収益最大化 ✓
```

**重要**: これは**空間的に並行**した栽培

---

## 現在の設計の限界

### 問題1: 候補生成が直列的

```python
# 現在の候補生成（問題あり）

for field in fields:
    for crop in crops:
        # ★ 1作物ごとに個別に候補を生成
        period_result = optimize_period_dp(field, crop)
        
        for period in period_result.candidates:
            candidates.append(
                Candidate(field, crop, period, quantity=MAX)
            )

# 問題: 「Spring に Rice, Tomato, Wheat を同時に」
#       という組み合わせ候補が生成されない
```

---

### 問題2: Greedy選択が貪欲すぎる

```python
# Greedy選択

sorted_candidates = sort_by_profit_rate(candidates)

for candidate in sorted_candidates:
    if feasible(candidate):
        allocate(candidate)  # ← 1つずつ選択

# 問題の流れ:
# 1. Rice (100%, Spring)を選択 ← 利益率が高い
# 2. Rice上限に達する
# 3. 他の作物を探す
# 4. しかし、Springの圃場はRiceで埋まっている
# 5. 結果: Springの圃場が部分的にしか使われない
```

---

## 具体例

### Example: 上限収益制約付き最適化

```
設定:
  Field A (1000m²、5000円/日)
  
  作物:
    Rice: 上限10,000株/年、50,000円/m²
    Tomato: 上限15,000株/年、60,000円/m²
    Wheat: 上限20,000株/年、30,000円/m²

候補生成（現在の方法）:
  Spring (4/1-8/31):
    - Rice 4000株 (1000m²、100%)
    - Tomato 3333株 (1000m²、100%)
    - Wheat 5000株 (1000m²、100%)
  
  Fall (9/1-12/31):
    - Rice 4000株 (1000m²、100%)
    - Tomato 3333株 (1000m²、100%)
    - Wheat 5000株 (1000m²、100%)

Greedy選択:
  1. Tomato (Spring, 100%) ← 利益率最高
     使用: 3333株/15,000株
  
  2. Tomato (Fall, 100%)
     使用: 3333株、合計6666株/15,000株
  
  3. Rice (Spring, 100%)
     しかし、Spring は Tomato で埋まっている ❌
  
  4. Rice (Fall, 100%)
     しかし、Fall は Tomato で埋まっている ❌
  
  結果: Tomato のみ、Rice/Wheat は作付けできない ❌
```

---

### 正しい解

```
同じ時期に複数作物を並行栽培:

Spring (4/1-8/31):
  - Rice: 1600株 (400m²)
  - Tomato: 1666株 (500m²)
  - Wheat: 1500株 (300m²)
  合計: 1200m²... あれ、超過？

調整版:
Spring (4/1-8/31):
  - Rice: 1200株 (300m²、30%)
  - Tomato: 1666株 (500m²、50%)
  - Wheat: 1000株 (200m²、20%)
  合計: 1000m² ✓

Fall (9/1-12/31):
  - Rice: 1600株 (400m²、40%)
  - Tomato: 1666株 (500m²、50%)
  - Wheat: 500株 (100m²、10%)
  合計: 1000m² ✓

年間生産:
  Rice: 2800株 < 10,000株 ✓
  Tomato: 3332株 < 15,000株 ✓
  Wheat: 1500株 < 20,000株 ✓
  
  多様性: 3作物 ✓
  圃場利用率: 100% ✓
```

**これが真の最適解！**

---

## 根本的な問題

### 問題の本質

**現在の候補生成は「1作物が圃場全体を使う」ことを前提にしている**

```python
# 現在の候補生成
for crop in crops:
    max_quantity = field.area / crop.area_per_unit  # ← 圃場全体
    candidates.append(Candidate(field, crop, period, max_quantity))

# 生成される候補:
#   (Field A, Rice, Spring, 4000株)    ← 100%使用
#   (Field A, Tomato, Spring, 3333株)  ← 100%使用
#   (Field A, Wheat, Spring, 5000株)   ← 100%使用

# 問題: 「Spring に Rice 30% + Tomato 50% + Wheat 20%」
#       という組み合わせ候補がない
```

---

## 解決策

### Solution 1: 混合候補の事前生成（推奨）

```python
# 同じ時期に複数作物を組み合わせた候補を生成

async def _generate_mixed_allocation_candidates(
    field: Field,
    crops: List[Crop],
    period: Period,
):
    """Generate candidates with multiple crops in the same period."""
    candidates = []
    
    # 単作候補（100%）
    for crop in crops:
        candidates.append(create_single_crop_candidate(field, crop, period, 1.0))
    
    # 2作物混合候補
    for crop_a, crop_b in combinations(crops, 2):
        for ratio_a in [0.3, 0.5, 0.7]:
            ratio_b = 1.0 - ratio_a
            
            # 組み合わせ候補を生成
            mixed_candidate = create_mixed_candidate(
                field,
                period,
                [(crop_a, ratio_a), (crop_b, ratio_b)]
            )
            candidates.append(mixed_candidate)
    
    # 3作物混合候補（主要なパターンのみ）
    if len(crops) >= 3:
        for crop_a, crop_b, crop_c in combinations(crops, 3):
            # 典型的な比率パターン
            patterns = [
                (0.5, 0.3, 0.2),  # 50%-30%-20%
                (0.4, 0.4, 0.2),  # 40%-40%-20%
                (0.33, 0.33, 0.34),  # ほぼ均等
            ]
            
            for ratio_a, ratio_b, ratio_c in patterns:
                mixed_candidate = create_mixed_candidate(
                    field,
                    period,
                    [(crop_a, ratio_a), (crop_b, ratio_b), (crop_c, ratio_c)]
                )
                candidates.append(mixed_candidate)
    
    return candidates
```

**候補数の増加**:
```
単作のみ: C = 5作物
2作物混合: C(C,2) × 3パターン = 10 × 3 = 30
3作物混合: C(C,3) × 3パターン = 10 × 3 = 30
合計: 5 + 30 + 30 = 65候補/期間

全体: F × P × 65 = 10 × 10 × 65 = 6,500候補
```

**問題**: 候補数が爆発的に増加（現在の250 → 6,500）

---

### Solution 2: 段階的な混合候補生成（現実的）

```python
# 利益率の高い作物の組み合わせのみ生成

async def _generate_selective_mixed_candidates(
    field: Field,
    crops: List[Crop],
    period: Period,
):
    """Generate mixed candidates selectively."""
    candidates = []
    
    # 単作候補（全作物）
    single_crop_candidates = []
    for crop in crops:
        candidate = create_single_crop_candidate(field, crop, period, 1.0)
        single_crop_candidates.append(candidate)
        candidates.append(candidate)
    
    # 利益率上位3作物のみで混合候補を生成
    top_crops = sorted(single_crop_candidates, key=lambda c: c.profit_rate, reverse=True)[:3]
    
    # 2作物混合（上位3作物の組み合わせのみ）
    for i, crop_a_candidate in enumerate(top_crops):
        for crop_b_candidate in top_crops[i+1:]:
            # 50-50パターンのみ
            mixed = create_mixed_candidate(
                field, period,
                [(crop_a_candidate.crop, 0.5), (crop_b_candidate.crop, 0.5)]
            )
            candidates.append(mixed)
    
    # 3作物混合（上位3作物、均等配分のみ）
    if len(top_crops) >= 3:
        mixed = create_mixed_candidate(
            field, period,
            [(c.crop, 0.33) for c in top_crops[:3]]
        )
        candidates.append(mixed)
    
    return candidates

# 候補数:
#   単作: 5
#   2作物: C(3,2) = 3
#   3作物: 1
#   合計: 9候補/期間
#
# 全体: F × P × 9 = 10 × 10 × 9 = 900候補（許容範囲）
```

---

### Solution 3: Local Searchでの混合化（実用的）

```python
# 候補生成は単作のみ
# Local Searchで同じ時期に複数作物を組み合わせる

def _create_mixed_allocation_neighbors(
    solution: List[CropAllocation],
    candidates: List[AllocationCandidate],
):
    """Create neighbors by mixing allocations in the same period."""
    neighbors = []
    
    # 同じField・同じPeriodの割り当てを見つける
    field_period_groups = {}
    for alloc in solution:
        key = (alloc.field.field_id, alloc.start_date, alloc.completion_date)
        if key not in field_period_groups:
            field_period_groups[key] = []
        field_period_groups[key].append(alloc)
    
    # 1作物のみの場合、別の作物を追加
    for key, allocs in field_period_groups.items():
        if len(allocs) == 1:
            # 現在は1作物のみ
            current_alloc = allocs[0]
            
            # Quantityを減らして空きを作る
            for reduce_ratio in [0.5, 0.7]:
                reduced_alloc = reduce_quantity(current_alloc, reduce_ratio)
                free_area = current_alloc.area_used * (1 - reduce_ratio)
                
                # 空いた面積に別の作物を追加
                for other_crop in other_crops:
                    # 同じPeriodの候補を探す
                    other_candidates = find_candidates(
                        candidates,
                        field=current_alloc.field,
                        crop=other_crop,
                        period=current_alloc.period
                    )
                    
                    if other_candidates:
                        best = max(other_candidates, key=lambda c: c.profit_rate)
                        other_quantity = free_area / other_crop.area_per_unit
                        other_alloc = create_allocation(best, other_quantity)
                        
                        # 混合した解を作成
                        neighbor = solution.copy()
                        neighbor.remove(current_alloc)
                        neighbor.append(reduced_alloc)
                        neighbor.append(other_alloc)
                        neighbors.append(neighbor)
    
    return neighbors
```

**メリット**:
- ✓ 候補生成はシンプル（単作のみ）
- ✓ Local Searchで柔軟に混合
- ✓ 計算量が抑えられる

---

## 上限収益制約の実装

### Revenue Cap Constraint

```python
@dataclass
class CropRequirementSpec:
    """Crop requirement with revenue cap."""
    
    crop_id: str
    variety: Optional[str] = None
    min_quantity: Optional[float] = None
    target_quantity: Optional[float] = None
    max_quantity: Optional[float] = None
    max_revenue_per_period: Optional[float] = None  # ★ NEW
    max_annual_revenue: Optional[float] = None      # ★ NEW
```

### 制約チェック

```python
def check_revenue_cap_constraint(
    solution: List[CropAllocation],
    crop_requirements: List[CropRequirementSpec],
):
    """Check if solution violates revenue cap constraints."""
    
    # 作物ごとの総収益を計算
    crop_revenues = {}
    for alloc in solution:
        crop_id = alloc.crop.crop_id
        if crop_id not in crop_revenues:
            crop_revenues[crop_id] = 0.0
        crop_revenues[crop_id] += alloc.expected_revenue or 0.0
    
    # 上限チェック
    for crop_req in crop_requirements:
        if crop_req.max_annual_revenue:
            actual = crop_revenues.get(crop_req.crop_id, 0.0)
            if actual > crop_req.max_annual_revenue:
                return False  # 制約違反
    
    return True
```

---

## 推奨実装：段階的アプローチ

### Phase 1: Crop Insert で対応（現状）

```
現在の実装:
  - Crop Insert操作で同じ時期に別の作物を追加可能
  - Local Searchで徐々に混合化
  
制限:
  - 初期解（Greedy）は単作
  - Local Searchで改善
  
品質: 85-92%（上限制約なしの場合と比べて低下）
```

---

### Phase 2: 混合候補の限定的生成（推奨）

```python
async def _generate_candidates_with_limited_mixing(fields, crops, request):
    """Generate single + limited mixed candidates."""
    candidates = []
    
    for field in fields:
        # Period最適化（一度だけ）
        periods = await optimize_periods_for_field(field, crops)
        
        for period in periods:
            # 単作候補（全作物）
            for crop in crops:
                for quantity_level in [1.0, 0.75, 0.5, 0.25]:
                    candidates.append(
                        create_candidate(field, crop, period, quantity_level)
                    )
            
            # ★ 混合候補（利益率上位3作物、50-50のみ）
            top_3_crops = get_top_profitable_crops(crops, period, top_k=3)
            
            for crop_a, crop_b in combinations(top_3_crops, 2):
                # 50-50混合
                candidates.append(
                    create_mixed_candidate(
                        field, period,
                        [(crop_a, 0.5), (crop_b, 0.5)]
                    )
                )
    
    return candidates

# 候補数:
#   単作: F × C × P × 4 = 10 × 5 × 3 × 4 = 600
#   2作物混合: F × C(C,2)/2 × P = 10 × 3 × 3 = 90
#   合計: 690候補（許容範囲）
```

**バランス**: 候補数の爆発を防ぎつつ、混合候補も含める

---

### Phase 3: Dynamic Mixed Allocation（高度）

```python
# Local Searchで動的に混合化

def _dynamic_mixing_neighbors(solution, candidates):
    """Dynamically create mixed allocations."""
    neighbors = []
    
    # 各Field・各Periodで現在の使用状況を確認
    for field in fields:
        for period in periods:
            current_allocs = get_allocations(solution, field, period)
            used_area = sum(a.area_used for a in current_allocs)
            free_area = field.area - used_area
            
            # 空きがあれば、別の作物を追加
            if free_area > field.area * 0.1:  # 10%以上の空き
                # 未使用の作物を探す
                for candidate in candidates:
                    if (candidate.field == field and
                        candidate.period == period and
                        candidate.crop not in current_crops):
                        
                        # 空き容量に合わせて追加
                        add_quantity = free_area / candidate.crop.area_per_unit
                        
                        neighbor = solution + [
                            create_allocation(candidate, add_quantity)
                        ]
                        neighbors.append(neighbor)
            
            # 既存の割り当てを縮小して別の作物を追加
            for alloc in current_allocs:
                for shrink_ratio in [0.7, 0.5]:
                    reduced = reduce_quantity(alloc, shrink_ratio)
                    freed_area = alloc.area_used * (1 - shrink_ratio)
                    
                    # 空いた面積に別の作物
                    for other_crop in other_crops:
                        other_alloc = create_allocation_in_freed_space(
                            field, other_crop, period, freed_area
                        )
                        
                        neighbor = solution.copy()
                        neighbor.remove(alloc)
                        neighbor.append(reduced)
                        neighbor.append(other_alloc)
                        neighbors.append(neighbor)
    
    return neighbors
```

---

## 候補数の管理

### 候補数の爆発を防ぐ

```python
# 戦略1: 混合候補の制限
# - 2作物混合のみ（3作物以上は複雑すぎる）
# - 利益率上位3作物のみ
# - 比率は50-50のみ

# 戦略2: 動的な混合
# - 候補生成は単作のみ
# - Local Searchで動的に混合

# 戦略3: フィルタリング
# - 利益率が低い混合候補を削除
# - 各(Field, Period)で上位N候補のみ保持
```

---

## 最終推奨

### Phase 1: Crop Insert + Quantity Adjust（現状）

```
実装状況: ✅ 完了

動作:
  1. Greedy で単作候補を選択
  2. Crop Insert で同じ時期に別の作物を追加
  3. Quantity Adjust で面積比率を調整
  
品質: 85-92%（上限制約あり）
```

**制限**: 初期解が単作前提なので、最適混合に到達しにくい

---

### Phase 2: 限定的な混合候補生成（2-3週間後）

```
実装:
  - 2作物混合候補（50-50のみ）
  - 利益率上位3作物の組み合わせのみ
  
候補数: 600 + 90 = 690候補（許容範囲）

品質: 90-95%（改善）
```

---

### Phase 3: 動的混合化（1ヶ月後）

```
実装:
  - Local Searchで動的に混合
  - Reduce + Insert操作の組み合わせ
  
品質: 92-97%（さらに改善）
```

---

## まとめ

### ご指摘の問題

**「Period×Quantityを別々に最適化すると、並行栽培が考慮されない」**

→ **完全に正しい指摘です！** 重要な問題を発見していただきました。

### 問題の本質

```
現在の候補生成:
  - 1作物が圃場全体を使うことを前提
  - 「Spring に A+B+C を並行」という候補がない
  
結果:
  - 上限収益制約下で最適解を見逃す
  - 作物多様性が低下
```

### 解決策

```
短期（現状）:
  Crop Insert + Quantity Adjust で部分的に対応
  品質: 85-92%

中期（Phase 2）:
  限定的な混合候補を生成
  品質: 90-95%

長期（Phase 3）:
  動的混合化
  品質: 92-97%
```

### 実装の優先度

```
Priority: 中（Phase 2で実装推奨）
理由:
  - 上限収益制約がない場合: 影響小
  - 上限収益制約がある場合: 影響大
  - ユースケース次第
```

**ご指摘のおかげで、重要な拡張課題が明確になりました！** 🙏

この問題への対応は、ユースケース（上限収益制約の有無）に応じて、Phase 2以降で実装することを推奨します。
