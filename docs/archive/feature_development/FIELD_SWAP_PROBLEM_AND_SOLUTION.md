# Field Swapの問題と解決策

## 問題の発見

### 現状の実装の問題点

現在の`_swap_allocations_with_area_adjustment`は、**2つの割り当てのペアのみ**を考慮しており、**同じ圃場内の他の割り当て**を考慮していません。

### 問題のシナリオ

```
Before:
  Field 1 (1000m²): 
    - CropA 500m² (alloc_a1)
    - CropB 400m² (alloc_a2)
    合計: 900m² / 1000m² (90%使用、100m²空き)
  
  Field 2 (800m²):
    - CropC 600m² (alloc_b1)
    合計: 600m² / 800m² (75%使用、200m²空き)

Swap: alloc_a2 (CropB 400m²) ⟷ alloc_b1 (CropC 600m²)

After（面積等価調整）:
  Field 1 (1000m²):
    - CropA 500m²（そのまま）
    - CropC 600m²（CropBと交換）
    合計: 1100m² / 1000m² ← 超過！❌
  
  Field 2 (800m²):
    - CropB 400m²（CropCと交換）
    合計: 400m² / 800m² ← OK ✓
```

**問題**: Field 1で容量超過が発生するが、現在の実装では検出できない

---

## 現在の実装の問題箇所

```python
# 現在の実装（不完全）
def _swap_allocations_with_area_adjustment(alloc_a, alloc_b):
    # ...
    
    # Check if new quantities exceed field capacity
    if new_area_a_in_field_b > alloc_b.field.area:  # ← ここが問題
        return None
    if new_area_b_in_field_a > alloc_a.field.area:  # ← ここが問題
        return None
```

**問題点**:
- `alloc_b.field.area`と比較しているが、これは圃場の**総面積**
- **他の割り当てが使っている面積**を考慮していない
- 正しくは `available_area`（空き容量）と比較すべき

---

## 解決策

### Solution 1: 空き容量を計算してチェック（推奨）

```python
def _swap_allocations_with_area_adjustment(
    self,
    alloc_a: CropAllocation,
    alloc_b: CropAllocation,
    solution: List[CropAllocation],  # ← 全体の解を渡す
) -> Optional[tuple[CropAllocation, CropAllocation]]:
    """Swap with proper capacity checking."""
    
    # Calculate area-equivalent quantities
    area_a = alloc_a.quantity * alloc_a.crop.area_per_unit
    area_b = alloc_b.quantity * alloc_b.crop.area_per_unit
    
    new_quantity_a = area_b / alloc_a.crop.area_per_unit
    new_quantity_b = area_a / alloc_b.crop.area_per_unit
    
    new_area_a_in_field_b = new_quantity_a * alloc_a.crop.area_per_unit
    new_area_b_in_field_a = new_quantity_b * alloc_b.crop.area_per_unit
    
    # ★ 重要: 他の割り当てを考慮した空き容量を計算
    used_area_in_field_a = sum(
        alloc.area_used 
        for alloc in solution 
        if alloc.field.field_id == alloc_a.field.field_id 
        and alloc.allocation_id != alloc_a.allocation_id  # alloc_a自身は除外
    )
    
    used_area_in_field_b = sum(
        alloc.area_used 
        for alloc in solution 
        if alloc.field.field_id == alloc_b.field.field_id 
        and alloc.allocation_id != alloc_b.allocation_id  # alloc_b自身は除外
    )
    
    # 容量チェック（他の割り当てを考慮）
    if used_area_in_field_b + new_area_a_in_field_b > alloc_b.field.area:
        return None  # Field Bの容量超過
    
    if used_area_in_field_a + new_area_b_in_field_a > alloc_a.field.area:
        return None  # Field Aの容量超過
    
    # ... (残りの処理)
```

---

### Solution 2: 部分的なSwap（数量を調整）

交換できない場合でも、**部分的に交換**することで有効活用

```python
def _swap_allocations_with_partial_adjustment(
    self,
    alloc_a: CropAllocation,
    alloc_b: CropAllocation,
    solution: List[CropAllocation],
) -> Optional[tuple[CropAllocation, CropAllocation]]:
    """Swap with partial quantity adjustment if full swap exceeds capacity."""
    
    # Calculate available space
    available_in_field_a = alloc_a.field.area - used_area_in_field_a
    available_in_field_b = alloc_b.field.area - used_area_in_field_b
    
    # Calculate what we want to swap
    area_a = alloc_a.quantity * alloc_a.crop.area_per_unit
    area_b = alloc_b.quantity * alloc_b.crop.area_per_unit
    
    # Calculate maximum swappable area
    max_swappable_to_field_a = available_in_field_a  # Field Aに入れられる最大
    max_swappable_to_field_b = available_in_field_b  # Field Bに入れられる最大
    
    # Adjust area if needed
    actual_area_to_a = min(area_b, max_swappable_to_field_a)
    actual_area_to_b = min(area_a, max_swappable_to_field_b)
    
    # Calculate adjusted quantities
    new_quantity_a = actual_area_to_b / alloc_a.crop.area_per_unit
    new_quantity_b = actual_area_to_a / alloc_b.crop.area_per_unit
    
    # If quantities become too small, reject swap
    if new_quantity_a < 0.1 * alloc_a.quantity or \
       new_quantity_b < 0.1 * alloc_b.quantity:
        return None  # Too small to be meaningful
    
    # ... (create new allocations)
```

---

### Solution 3: 複数割り当ての一括Swap

圃場全体を交換する操作

```python
def _swap_all_allocations_in_fields(
    field_a: Field,
    field_b: Field,
    solution: List[CropAllocation],
) -> Optional[List[CropAllocation]]:
    """Swap ALL allocations between two fields."""
    
    # Get all allocations in each field
    allocs_in_a = [a for a in solution if a.field.field_id == field_a.field_id]
    allocs_in_b = [a for a in solution if a.field.field_id == field_b.field_id]
    
    # Calculate total areas
    total_area_a = sum(a.area_used for a in allocs_in_a)
    total_area_b = sum(a.area_used for a in allocs_in_b)
    
    # Check if swap is possible
    if total_area_a > field_b.area or total_area_b > field_a.area:
        return None  # Cannot swap - capacity exceeded
    
    # Create new solution with swapped fields
    new_solution = []
    
    for alloc in solution:
        if alloc in allocs_in_a:
            # Move to field_b
            new_alloc = move_to_field(alloc, field_b)
            new_solution.append(new_alloc)
        elif alloc in allocs_in_b:
            # Move to field_a
            new_alloc = move_to_field(alloc, field_a)
            new_solution.append(new_alloc)
        else:
            # Keep unchanged
            new_solution.append(alloc)
    
    return new_solution
```

---

## 推奨する解決策

### ✅ 推奨: Solution 1（厳密な容量チェック）

**理由**:
1. 最も正確
2. 実装が明確
3. デバッグしやすい
4. 予期しない容量超過を防ぐ

**実装の修正**:

```python
def _generate_neighbors(self, solution, candidates):
    neighbors = []
    
    # Operation 1: Swap with proper capacity checking
    for i in range(len(solution)):
        for j in range(i + 1, len(solution)):
            if solution[i].field.field_id != solution[j].field.field_id:
                # ★ 解全体を渡して容量チェック
                swapped = self._swap_allocations_with_area_adjustment(
                    solution[i], 
                    solution[j],
                    solution  # ← 追加
                )
                if swapped is not None:
                    neighbor = solution.copy()
                    neighbor[i], neighbor[j] = swapped
                    neighbors.append(neighbor)
```

---

## 具体例での検証

### Example 1: 容量内のSwap（成功）

```
Before:
  Field 1 (1000m²):
    - CropA 500m² (alloc_a1)
    - CropB 300m² (alloc_a2)
    合計: 800m²、空き: 200m²
  
  Field 2 (800m²):
    - CropC 400m² (alloc_b1)
    合計: 400m²、空き: 400m²

Swap: alloc_a2 (CropB 300m²) ⟷ alloc_b1 (CropC 400m²)

Check:
  Field 1に入れる: CropC 400m²
  既存: CropA 500m²
  合計: 900m² ≤ 1000m² ✓ OK
  
  Field 2に入れる: CropB 300m²
  既存: なし
  合計: 300m² ≤ 800m² ✓ OK

Result: Swap成功！
```

### Example 2: 容量超過のSwap（失敗）

```
Before:
  Field 1 (1000m²):
    - CropA 500m² (alloc_a1)
    - CropB 400m² (alloc_a2)
    合計: 900m²、空き: 100m²
  
  Field 2 (800m²):
    - CropC 600m² (alloc_b1)
    合計: 600m²、空き: 200m²

Swap: alloc_a2 (CropB 400m²) ⟷ alloc_b1 (CropC 600m²)

Check:
  Field 1に入れる: CropC 600m²
  既存: CropA 500m²
  合計: 1100m² > 1000m² ❌ 超過！
  
  Field 2に入れる: CropB 400m²
  既存: なし
  合計: 400m² ≤ 800m² ✓ OK

Result: Swap拒否（Field 1で容量超過）
```

### Example 3: 面積等価調整後の容量超過（複雑）

```
Before:
  Field 1 (1000m²):
    - Rice 2000株 (500m², 0.25m²/株) (alloc_a1)
    - Wheat 2000株 (400m², 0.2m²/株) (alloc_a2)
    合計: 900m²、空き: 100m²
  
  Field 2 (800m²):
    - Tomato 1000株 (300m², 0.3m²/株) (alloc_b1)
    合計: 300m²、空き: 500m²

Swap: alloc_a1 (Rice 500m²) ⟷ alloc_b1 (Tomato 300m²)

面積等価調整:
  Rice → Field 2: 300m² / 0.25 = 1200株 (300m²)
  Tomato → Field 1: 500m² / 0.3 = 1666.67株 (500m²)

Check:
  Field 1に入れる: Tomato 500m²
  既存: Wheat 400m²
  合計: 900m² ≤ 1000m² ✓ OK
  
  Field 2に入れる: Rice 300m²
  既存: なし
  合計: 300m² ≤ 800m² ✓ OK

Result: Swap成功！
```

---

## 修正版の実装

### 改善版1: 厳密な容量チェック

```python
def _swap_allocations_with_area_adjustment(
    self,
    alloc_a: CropAllocation,
    alloc_b: CropAllocation,
    solution: List[CropAllocation],  # ★ 追加
) -> Optional[tuple[CropAllocation, CropAllocation]]:
    """Swap two allocations between fields with area-equivalent quantity adjustment.
    
    This method now properly checks available capacity in each field by considering
    other allocations in the same field.
    """
    # Calculate area-equivalent quantities
    area_a = alloc_a.quantity * alloc_a.crop.area_per_unit
    area_b = alloc_b.quantity * alloc_b.crop.area_per_unit
    
    if alloc_a.crop.area_per_unit <= 0 or alloc_b.crop.area_per_unit <= 0:
        return None
    
    new_quantity_a = area_b / alloc_a.crop.area_per_unit
    new_quantity_b = area_a / alloc_b.crop.area_per_unit
    
    new_area_a_in_field_b = new_quantity_a * alloc_a.crop.area_per_unit
    new_area_b_in_field_a = new_quantity_b * alloc_b.crop.area_per_unit
    
    # ★ 改善: 他の割り当てを考慮した空き容量を計算
    # Field Aで使用中の面積（alloc_a以外）
    used_area_in_field_a = sum(
        alloc.area_used 
        for alloc in solution 
        if alloc.field.field_id == alloc_a.field.field_id 
        and alloc.allocation_id != alloc_a.allocation_id
    )
    
    # Field Bで使用中の面積（alloc_b以外）
    used_area_in_field_b = sum(
        alloc.area_used 
        for alloc in solution 
        if alloc.field.field_id == alloc_b.field.field_id 
        and alloc.allocation_id != alloc_b.allocation_id
    )
    
    # ★ 改善: 空き容量と比較
    available_in_field_a = alloc_a.field.area - used_area_in_field_a
    available_in_field_b = alloc_b.field.area - used_area_in_field_b
    
    # Capacity check with other allocations considered
    if new_area_b_in_field_a > available_in_field_a:
        return None  # Field Aで容量超過
    
    if new_area_a_in_field_b > available_in_field_b:
        return None  # Field Bで容量超過
    
    # ... (残りの処理)
```

---

### 改善版2: 部分的なSwap（柔軟な対応）

完全な交換ができない場合、**可能な範囲で部分的に交換**

```python
def _swap_allocations_with_flexible_adjustment(
    self,
    alloc_a: CropAllocation,
    alloc_b: CropAllocation,
    solution: List[CropAllocation],
) -> Optional[tuple[CropAllocation, CropAllocation]]:
    """Swap with flexible quantity adjustment to fit available capacity."""
    
    # Calculate available capacity
    available_in_field_a = calculate_available_area(solution, alloc_a.field, exclude=alloc_a)
    available_in_field_b = calculate_available_area(solution, alloc_b.field, exclude=alloc_b)
    
    # Calculate desired areas
    area_a = alloc_a.quantity * alloc_a.crop.area_per_unit
    area_b = alloc_b.quantity * alloc_b.crop.area_per_unit
    
    # Adjust to fit available capacity
    actual_area_to_a = min(area_b, available_in_field_a)
    actual_area_to_b = min(area_a, available_in_field_b)
    
    # Calculate adjusted quantities
    new_quantity_a = actual_area_to_b / alloc_a.crop.area_per_unit
    new_quantity_b = actual_area_to_a / alloc_b.crop.area_per_unit
    
    # Reject if quantities become too small (< 10% of original)
    min_ratio = 0.1
    if new_quantity_a < min_ratio * alloc_a.quantity or \
       new_quantity_b < min_ratio * alloc_b.quantity:
        return None  # Too small to be meaningful
    
    # ... (create new allocations with adjusted quantities)
```

**メリット**: より多くのSwapが可能になる  
**デメリット**: 数量が変わるため、目標達成への影響を考慮が必要

---

## テストケース

### Test 1: 単純なケース（他の割り当てなし）

```python
def test_swap_simple_case_no_other_allocations():
    """Test swap when each field has only one allocation."""
    field_a = Field("f1", "Field 1", 1000.0, 5000.0)
    field_b = Field("f2", "Field 2", 800.0, 6000.0)
    
    rice = Crop("rice", "Rice", 0.25)
    tomato = Crop("tomato", "Tomato", 0.3)
    
    alloc_a = create_allocation(field_a, rice, 2000, 500.0)
    alloc_b = create_allocation(field_b, tomato, 1000, 300.0)
    
    solution = [alloc_a, alloc_b]
    
    # Swap should succeed
    result = interactor._swap_allocations_with_area_adjustment(
        alloc_a, alloc_b, solution
    )
    
    assert result is not None
```

### Test 2: 容量超過のケース（複数割り当て）

```python
def test_swap_fails_when_capacity_exceeded():
    """Test swap is rejected when capacity would be exceeded."""
    field_a = Field("f1", "Field 1", 1000.0, 5000.0)
    field_b = Field("f2", "Field 2", 800.0, 6000.0)
    
    rice = Crop("rice", "Rice", 0.25)
    wheat = Crop("wheat", "Wheat", 0.2)
    tomato = Crop("tomato", "Tomato", 0.3)
    
    # Field 1: Rice 500m² + Wheat 400m² = 900m² (100m² free)
    alloc_a1 = create_allocation(field_a, rice, 2000, 500.0)
    alloc_a2 = create_allocation(field_a, wheat, 2000, 400.0)
    
    # Field 2: Tomato 600m² (200m² free)
    alloc_b1 = create_allocation(field_b, tomato, 2000, 600.0)
    
    solution = [alloc_a1, alloc_a2, alloc_b1]
    
    # Try to swap alloc_a2 (Wheat 400m²) with alloc_b1 (Tomato 600m²)
    result = interactor._swap_allocations_with_area_adjustment(
        alloc_a2, alloc_b1, solution
    )
    
    # Should be rejected because:
    # Field 1: Rice 500m² + Tomato 600m² = 1100m² > 1000m² ❌
    assert result is None
```

### Test 3: 容量内のケース（ぎりぎり成功）

```python
def test_swap_succeeds_when_within_capacity():
    """Test swap succeeds when total fits within capacity."""
    field_a = Field("f1", "Field 1", 1000.0, 5000.0)
    field_b = Field("f2", "Field 2", 800.0, 6000.0)
    
    rice = Crop("rice", "Rice", 0.25)
    wheat = Crop("wheat", "Wheat", 0.2)
    tomato = Crop("tomato", "Tomato", 0.3)
    
    # Field 1: Rice 500m² + Wheat 300m² = 800m² (200m² free)
    alloc_a1 = create_allocation(field_a, rice, 2000, 500.0)
    alloc_a2 = create_allocation(field_a, wheat, 1500, 300.0)
    
    # Field 2: Tomato 400m² (400m² free)
    alloc_b1 = create_allocation(field_b, tomato, 1333, 400.0)
    
    solution = [alloc_a1, alloc_a2, alloc_b1]
    
    # Try to swap alloc_a2 (Wheat 300m²) with alloc_b1 (Tomato 400m²)
    result = interactor._swap_allocations_with_area_adjustment(
        alloc_a2, alloc_b1, solution
    )
    
    # Should succeed:
    # Field 1: Rice 500m² + Tomato 400m² = 900m² ≤ 1000m² ✓
    # Field 2: Wheat 300m² ≤ 800m² ✓
    assert result is not None
```

---

## 実装の修正内容

### 変更点1: メソッドシグネチャ

```python
# Before
def _swap_allocations_with_area_adjustment(
    self, alloc_a, alloc_b
)

# After
def _swap_allocations_with_area_adjustment(
    self, alloc_a, alloc_b, solution  # ← 追加
)
```

### 変更点2: 容量チェックロジック

```python
# Before（不完全）
if new_area_a_in_field_b > alloc_b.field.area:  # 総面積と比較
    return None

# After（正しい）
used_area = sum(a.area_used for a in solution 
                if a.field.field_id == field_b.field_id 
                and a.allocation_id != alloc_b.allocation_id)
available = field_b.area - used_area

if new_area_a_in_field_b > available:  # 空き容量と比較
    return None
```

### 変更点3: 呼び出し元の修正

```python
# Before
swapped = self._swap_allocations_with_area_adjustment(solution[i], solution[j])

# After
swapped = self._swap_allocations_with_area_adjustment(
    solution[i], solution[j], solution  # ← solutionを渡す
)
```

---

## まとめ

### 発見された問題

✅ **現在の実装の問題点を特定**:
- 個別の割り当てしかチェックしていない
- 同じ圃場内の他の割り当てを考慮していない
- 容量超過の可能性がある

### 推奨する解決策

✅ **Solution 1: 厳密な容量チェック**:
- 他の割り当てを考慮した空き容量を計算
- Swap前に容量超過をチェック
- 超過する場合は`None`を返して拒否

### 実装の修正

必要な修正:
1. メソッドに`solution`パラメータを追加
2. 空き容量の計算ロジックを追加
3. テストケースの追加

### 期待される効果

- ✅ 容量超過の防止
- ✅ より正確な最適化
- ✅ バグの削減
- ✅ 実行可能性の保証

次に、この修正を実装しますか？
