# 圃場移動（Field Move）操作の詳細説明

## 基本概念

### 定義

**圃場移動（Field Move）**: 1つの割り当てを、別の圃場に移動させる操作

```
固定: Crop（作物）、Period（期間）
変更: Field（圃場）
```

---

## 具体例

### 例1: 基本的な移動

```
Before:
┌────────────────────────┐  ┌────────────────────────┐
│ Field A (5000円/日)    │  │ Field B (4000円/日)    │
├────────────────────────┤  ├────────────────────────┤
│ Rice 2000株            │  │ [空き]                 │
│ 4/1-8/31               │  │                        │
│ 500m²使用、500m²空き   │  │ 1000m²空き             │
└────────────────────────┘  └────────────────────────┘

Operation: Field A の Rice を Field B に移動

After:
┌────────────────────────┐  ┌────────────────────────┐
│ Field A (5000円/日)    │  │ Field B (4000円/日)    │
├────────────────────────┤  ├────────────────────────┤
│ [空き]                 │  │ Rice 2000株            │
│                        │  │ 4/1-8/31               │
│ 1000m²空き             │  │ 500m²使用、500m²空き   │
└────────────────────────┘  └────────────────────────┘

効果:
  コスト: 153日 × 5000円 = 765,000円
      → 153日 × 4000円 = 612,000円
  削減: 153,000円 ✓ より低コストな圃場へ移動
```

---

## Field Move vs Field Swap の違い

### Field Swap（交換）

```
Before:
  Field A: Rice 2000株
  Field B: Tomato 1000株

After:
  Field A: Tomato 1666株（面積等価調整）
  Field B: Rice 1200株（面積等価調整）
  
特徴:
  - 2つの割り当てを同時に交換
  - 両方の割り当てが変更される
  - 面積等価の数量調整が必要
```

### Field Move（移動）

```
Before:
  Field A: Rice 2000株
  Field B: [空き]

After:
  Field A: [空き]
  Field B: Rice 2000株
  
特徴:
  - 1つの割り当てのみ移動
  - 移動元は空になる
  - 移動先に空きが必要
```

---

## 実装の詳細

### 基本的な実装

```python
def _move_operation(
    allocation: CropAllocation,
    target_field: Field,
    solution: List[CropAllocation],
) -> Optional[CropAllocation]:
    """Move allocation to a different field.
    
    Args:
        allocation: Allocation to move
        target_field: Target field to move to
        solution: Current complete solution
        
    Returns:
        New allocation in target field, or None if move is not possible
    """
    # Check if target field is different
    if allocation.field.field_id == target_field.field_id:
        return None  # Same field, no move needed
    
    # Calculate available area in target field
    used_area_in_target = sum(
        alloc.area_used 
        for alloc in solution 
        if alloc.field.field_id == target_field.field_id
    )
    available_area = target_field.area - used_area_in_target
    
    # Check if allocation fits
    required_area = allocation.area_used
    if required_area > available_area:
        return None  # Not enough space
    
    # Recalculate cost based on new field's daily_fixed_cost
    new_cost = allocation.growth_days * target_field.daily_fixed_cost
    
    # Revenue stays the same (same quantity)
    new_revenue = allocation.expected_revenue
    
    # Recalculate profit
    new_profit = (new_revenue - new_cost) if new_revenue is not None else None
    
    # Create new allocation in target field
    return CropAllocation(
        allocation_id=str(uuid.uuid4()),
        field=target_field,  # ← Changed
        crop=allocation.crop,  # Same
        quantity=allocation.quantity,  # Same
        start_date=allocation.start_date,  # Same
        completion_date=allocation.completion_date,  # Same
        growth_days=allocation.growth_days,  # Same
        accumulated_gdd=allocation.accumulated_gdd,  # Same
        total_cost=new_cost,  # ← Recalculated
        expected_revenue=new_revenue,  # Same
        profit=new_profit,  # ← Recalculated
        area_used=allocation.area_used,  # Same
    )
```

---

## ユースケース

### Use Case 1: コスト削減

```
問題:
  高コストな圃場で栽培している

解決:
  より低コストな圃場に移動
  
Before:
  Field A (6000円/日): Rice, 153日 → Cost: 918,000円
  Field B (4000円/日): [空き]

After:
  Field A: [空き]
  Field B (4000円/日): Rice, 153日 → Cost: 612,000円
  
削減: 306,000円 (33%減) ✓
```

---

### Use Case 2: 土壌条件の最適化

```
問題:
  作物と圃場の相性が悪い
  
解決:
  より適した圃場に移動
  
Before:
  Field A (水はけ悪い): Tomato → 病害リスク高
  Field B (水はけ良い): [空き]

After:
  Field A: [空き]
  Field B (水はけ良い): Tomato → リスク低減 ✓
```

---

### Use Case 3: 負荷分散

```
問題:
  一部の圃場に負荷が集中
  
解決:
  空いている圃場に分散
  
Before:
  Field A: Rice + Tomato + Wheat（過密）
  Field B: [ほぼ空き]
  Field C: [ほぼ空き]

After:
  Field A: Rice
  Field B: Tomato ← 移動
  Field C: Wheat ← 移動
  
効果: 作業の分散、リスク分散 ✓
```

---

## Field Moveの制約

### 制約1: 空き容量

```python
# 移動先に十分な空きがあるか
required_area = allocation.area_used
available_area = target_field.area - used_area_in_target

if required_area > available_area:
    return None  # 移動不可
```

### 制約2: 時間的重複

```python
# 移動先の同じ時期に他の割り当てがないか
for existing in target_field_allocations:
    if time_overlaps(allocation, existing):
        return None  # 移動不可
```

### 制約3: 最小意味のある移動

```python
# コストが変わらない場合は移動の意味がない
old_cost = allocation.growth_days * allocation.field.daily_fixed_cost
new_cost = allocation.growth_days * target_field.daily_fixed_cost

if abs(new_cost - old_cost) < threshold:
    return None  # 移動の効果が小さい
```

---

## 数量調整の有無

### パターンA: そのまま移動（基本）

```python
# 移動先に十分な空きがある場合
Before:
  Field A: Rice 2000株 (500m²)
  Field B: [800m²空き]

After:
  Field A: [空き]
  Field B: Rice 2000株 (500m²)  # そのまま移動
  
数量: 変更なし
面積: 変更なし
```

---

### パターンB: 縮小して移動（空き不足）

```python
# 移動先の空きが不足する場合
Before:
  Field A: Rice 2000株 (500m²)
  Field B: [300m²空き]  # 不足

After:
  Field A: Rice 800株 (200m²)  # 一部残る
  Field B: Rice 1200株 (300m²)  # 移動可能な分のみ
  
または
  
After:
  Field A: [空き]
  Field B: Rice 1200株 (300m²)  # 縮小して移動
  
数量: 縮小（2000→1200）
面積: 縮小（500m²→300m²）
```

**実装方針**: パターンA（そのまま移動）を基本とし、空き不足なら拒否（None）

---

## 他の操作との組み合わせ

### Move + Period Re-selection

```python
# Field を変更したら、その Field での最適 Period に変更

Before:
  Field A (5000円/日): Rice, 4/1-8/31 (153日)
  
Move to Field B:
  Field B (4000円/日): Rice, ???
  
  # Field B での Rice の最適 Period を候補から選択
  # 候補生成時にすでに計算済み
  best_period = find_candidate(
      candidates,
      field=Field B,
      crop=Rice
  )
  
After:
  Field B (4000円/日): Rice, 4/15-9/15 (154日)
  # Field B での最適 Period に調整
```

**重要**: Period は候補から選ぶので、DPの厳密解を維持 ✓

---

## 実装例（詳細）

```python
def _field_move_neighbors(
    self,
    solution: List[CropAllocation],
    candidates: List[AllocationCandidate],
    fields: List[Field],
) -> List[List[CropAllocation]]:
    """Generate neighbors by moving allocations to different fields."""
    neighbors = []
    
    # Try moving each allocation to each other field
    for i, alloc in enumerate(solution):
        for target_field in fields:
            # Skip if same field
            if target_field.field_id == alloc.field.field_id:
                continue
            
            # Calculate available area in target field
            used_area_in_target = sum(
                a.area_used 
                for a in solution 
                if a.field.field_id == target_field.field_id
            )
            available_area = target_field.area - used_area_in_target
            
            # Check if fits
            if alloc.area_used > available_area:
                continue  # Not enough space
            
            # Check time overlap
            has_overlap = False
            for existing in solution:
                if (existing.field.field_id == target_field.field_id and
                    alloc.overlaps_with(existing)):
                    has_overlap = True
                    break
            
            if has_overlap:
                continue
            
            # Find best period candidate for this field + crop combination
            period_candidates = [
                c for c in candidates
                if c.field.field_id == target_field.field_id and
                   c.crop.crop_id == alloc.crop.crop_id
            ]
            
            if not period_candidates:
                continue
            
            # Select best period (by profit rate)
            best_candidate = max(period_candidates, key=lambda c: c.profit_rate)
            
            # Create new allocation with target field and best period
            new_alloc = self._create_allocation_from_candidate(
                best_candidate,
                quantity=alloc.quantity,  # Keep same quantity if possible
            )
            
            # Create neighbor solution
            neighbor = solution.copy()
            neighbor[i] = new_alloc
            neighbors.append(neighbor)
    
    return neighbors
```

---

## Field MoveとField Swapの使い分け

### Field Move（移動）

**使うべき場合**:
- ✅ より低コストな圃場に移動したい
- ✅ 移動先に空きがある
- ✅ 移動元の圃場を別の用途に使いたい

**例**:
```
高コスト圃場 → 低コスト圃場
専用圃場 → 汎用圃場
遠い圃場 → 近い圃場
```

---

### Field Swap（交換）

**使うべき場合**:
- ✅ 両方の圃場が埋まっている
- ✅ 作物と圃場の相性を最適化したい
- ✅ 双方向の改善を狙いたい

**例**:
```
Field A: Rice（水田向け）+ Field B: Tomato（畑向け）
→ Field A: Tomato + Field B: Rice
（相性が逆だったのを修正）
```

---

## 実際の農業での意味

### シナリオ1: 段階的な圃場拡大

```
Year 1:
  Field A (既存): Rice, Tomato
  Field B (新規): [未使用]
  Field C (新規): [未使用]

Year 2: 段階的に拡大
  Field A: Rice
  Field B: Tomato ← Field Aから移動
  Field C: [未使用]

Year 3: さらに拡大
  Field A: Rice
  Field B: Tomato
  Field C: Wheat ← 新規作物
```

---

### シナリオ2: 連作障害の回避

```
Year 1:
  Field A: Rice
  Field B: Tomato

Year 2: 移動で輪作
  Field A: Tomato ← Field Bから移動
  Field B: Rice ← Field Aから移動
  
効果: 連作障害を避ける
```

---

### シナリオ3: コスト最適化

```
圃場のコスト構造:
  Field A (遠い、管理費高): 6000円/日
  Field B (近い、管理費低): 4000円/日
  Field C (中間): 5000円/日

最適化:
  利益率の低い作物 → Field B（低コスト圃場）
  利益率の高い作物 → Field A（コストは高いが許容）
```

---

## 実装のポイント

### Point 1: Period の再選択

```python
# Field を変更したら、その Field での最適 Period を選ぶ
# （候補生成時にすでに計算済み）

def move_with_period_reselection(alloc, target_field, candidates):
    # target_field での最適 Period 候補を探す
    period_candidates = [
        c for c in candidates
        if c.field.field_id == target_field.field_id and
           c.crop.crop_id == alloc.crop.crop_id
    ]
    
    if not period_candidates:
        return None
    
    # 最も利益率が高い Period を選択
    best = max(period_candidates, key=lambda c: c.profit_rate)
    
    return create_allocation_in_new_field(alloc, target_field, best.period)
```

**重要**: Period は候補から選ぶので、DPの厳密解を維持 ✓

---

### Point 2: 容量チェック

```python
# 移動先の空き容量を確認
used_area = sum(
    a.area_used 
    for a in solution 
    if a.field.field_id == target_field.field_id
)
available = target_field.area - used_area

if allocation.area_used > available:
    return None  # 移動不可
```

---

### Point 3: 時間的重複チェック

```python
# 移動先の同じ期間に他の割り当てがないか
for existing in solution:
    if (existing.field.field_id == target_field.field_id and
        allocation.overlaps_with(existing)):
        return None  # 移動不可（時間的衝突）
```

---

## 計算量

### 近傍サイズ

```
n個の割り当て × (F-1)個の移動先
= n × (F-1) 個の近傍

例: n=20, F=10
  → 20 × 9 = 180個の近傍
```

### 計算量

```
O(n × F × n)
= O(n² × F)

例: n=20, F=10
  → 20 × 10 × 20 = 4,000回の操作
  → 約0.5秒
```

---

## Field Moveの効果

### コスト削減効果

```
圃場のコスト差が20%の場合:
  Before: 153日 × 6000円 = 918,000円
  After:  153日 × 4800円 = 734,400円
  削減: 183,600円 (20%減)

1割り当てで20%改善
10割り当てで移動可能なら → 全体で2-3%改善
```

### 期待される品質向上

```
Field Move追加による改善: +2-3%

現状: 88-92%
  ↓
+ Field Move: 90-95% ✓
```

---

## まとめ

### Field Move とは

**1つの割り当てを別の圃場に移動する操作**

```
変更: Field（圃場）
固定: Crop（作物）、Period（期間）、Quantity（数量）
再計算: Cost（圃場のコストに依存）
```

### Field Swap との違い

| 項目 | Field Move | Field Swap |
|------|-----------|------------|
| 移動数 | 1つ | 2つ（交換） |
| 前提条件 | 移動先に空き | 両方埋まっている |
| 数量調整 | 基本的になし | 面積等価調整（必須） |
| 複雑度 | 低 | 中 |
| 効果 | コスト削減 | 相性最適化 |

### 実装の優先度

```
Priority 2: Field Move（推奨実装）
  工数: 3-4日
  効果: +2-3%
  
Field Swap より実装が簡単で、効果も高い
```

### 実用的な価値

- ✅ コスト削減（圃場のコスト差を活用）
- ✅ 土壌適性の最適化
- ✅ 負荷分散
- ✅ 段階的な圃場拡大への対応

**結論**: Field Move は実用的で効果的な操作です！

実装を進めますか？

