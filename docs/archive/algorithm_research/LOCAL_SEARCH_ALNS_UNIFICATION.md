# Local Search と ALNS の統合・共通化

## 🎯 概要

既存の**Local Search（Hill Climbing）**と新規の**ALNS**で、多くの近傍操作が共通化できます。

---

## 📊 既存のLocal Search操作

現在実装されている8つの操作：

```python
# src/agrr_core/usecase/services/neighbor_generator_service.py

operations = [
    FieldSwapOperation(),         # F1. フィールド間でスワップ
    FieldMoveOperation(),         # F2. フィールド間で移動
    FieldReplaceOperation(),      # F3. フィールドで置換
    FieldRemoveOperation(),       # F4. フィールドから削除 ★
    CropInsertOperation(),        # C1. 作物を挿入 ★★
    CropChangeOperation(),        # C2. 作物を変更
    PeriodReplaceOperation(),     # P1. 期間を置換
    AreaAdjustOperation(),        # A1. 面積を調整
]
```

---

## 🔄 ALNSの操作

### Destroy（削除）操作

```python
# src/agrr_core/usecase/services/alns_optimizer_service.py

destroy_operators = {
    'random_removal',      # ランダムに削除 ★
    'worst_removal',       # 低利益率を削除 ★
    'related_removal',     # 関連する割当を削除
    'field_removal',       # 圃場単位で削除 ★
    'time_slice_removal',  # 時期単位で削除
}
```

### Repair（修復）操作

```python
repair_operators = {
    'greedy_insert',  # 貪欲に挿入 ★★
    'regret_insert',  # 後悔基準で挿入 ★★
}
```

---

## ✅ 共通化できる操作

### 🔥 高優先度：Insertロジック

#### 既存：CropInsertOperation

```python
# src/agrr_core/usecase/services/neighbor_operations/crop_insert_operation.py

class CropInsertOperation(NeighborOperation):
    """Insert new crop allocation from unused candidates."""
    
    def generate_neighbors(self, solution, context):
        neighbors = []
        candidates = context.get("candidates", [])
        
        # 使用済み候補を除外
        used_ids = {(a.field.field_id, a.crop.crop_id, a.start_date) for a in solution}
        
        # 未使用候補を試す
        for candidate in candidates:
            if candidate_id in used_ids:
                continue
            
            # ✅ 面積制約チェック
            # ✅ 時間重複チェック
            # ✅ 挿入
            
            neighbor = solution + [new_alloc]
            neighbors.append(neighbor)
        
        return neighbors
```

#### ALNS：greedy_insert / regret_insert

```python
# src/agrr_core/usecase/services/alns_optimizer_service.py

def _greedy_insert(self, partial, removed, candidates, fields):
    """Greedily re-insert removed allocations."""
    current = partial.copy()
    sorted_removed = sorted(removed, key=lambda a: a.profit_rate, reverse=True)
    
    for alloc in sorted_removed:
        # ✅ 同じ制約チェック
        if self._is_feasible_to_add(current, alloc):
            current.append(alloc)
    
    return current
```

**共通点**：
- ✅ 時間重複チェック
- ✅ 面積制約チェック
- ✅ 候補から選んで挿入

**違い**：
- Local Search: 未使用候補から挿入
- ALNS: 削除された割当を再挿入

---

### 🔥 高優先度：Removeロジック

#### 既存：FieldRemoveOperation

```python
class FieldRemoveOperation(NeighborOperation):
    """Remove one allocation."""
    
    def generate_neighbors(self, solution, context):
        neighbors = []
        
        for i in range(len(solution)):
            neighbor = solution[:i] + solution[i+1:]  # 1つ削除
            neighbors.append(neighbor)
        
        return neighbors
```

#### ALNS：random_removal / worst_removal

```python
def _random_removal(self, solution):
    """Randomly remove allocations."""
    removal_rate = 0.3
    n_remove = max(1, int(len(solution) * removal_rate))
    
    removed = random.sample(solution, n_remove)  # 複数削除
    remaining = [a for a in solution if a not in removed]
    
    return remaining, removed
```

**共通点**：
- ✅ リストからの削除操作

**違い**：
- Local Search: 1つずつ削除
- ALNS: 30%をまとめて削除

---

### 🔥 中優先度：Feasibility Check

**両方で使用される共通ロジック**：

```python
# ✅ 共通化すべきヘルパーメソッド

def _time_overlaps(alloc1, alloc2) -> bool:
    """Check if two allocations overlap in time."""
    return not (
        alloc1.completion_date < alloc2.start_date or
        alloc2.completion_date < alloc1.start_date
    )

def _is_feasible_to_add(current, new_alloc) -> bool:
    """Check if adding new_alloc is feasible."""
    for existing in current:
        if existing.field.field_id == new_alloc.field.field_id:
            if _time_overlaps(existing, new_alloc):
                return False
    return True

def _candidate_to_allocation(candidate):
    """Convert AllocationCandidate to CropAllocation."""
    return CropAllocation(
        allocation_id=str(uuid.uuid4()),
        field=candidate.field,
        crop=candidate.crop,
        # ... fields mapping
    )
```

---

## 🏗️ 統合アーキテクチャ提案

### Option 1: 共通ユーティリティクラス（推奨）⭐

```python
# src/agrr_core/usecase/services/allocation_utils.py

class AllocationUtils:
    """Shared utility methods for Local Search and ALNS."""
    
    @staticmethod
    def time_overlaps(alloc1, alloc2) -> bool:
        """Check time overlap between two allocations."""
        return not (
            alloc1.completion_date < alloc2.start_date or
            alloc2.completion_date < alloc1.start_date
        )
    
    @staticmethod
    def is_feasible_to_add(
        current: List[CropAllocation],
        new_alloc: CropAllocation
    ) -> bool:
        """Check if adding new allocation is feasible."""
        for existing in current:
            if existing.field.field_id == new_alloc.field.field_id:
                if AllocationUtils.time_overlaps(existing, new_alloc):
                    return False
        return True
    
    @staticmethod
    def candidate_to_allocation(candidate) -> CropAllocation:
        """Convert AllocationCandidate to CropAllocation."""
        return CropAllocation(
            allocation_id=str(uuid.uuid4()),
            field=candidate.field,
            crop=candidate.crop,
            area_used=candidate.area_used,
            start_date=candidate.start_date,
            completion_date=candidate.completion_date,
            growth_days=candidate.growth_days,
            accumulated_gdd=candidate.accumulated_gdd,
            total_cost=candidate.cost,
            expected_revenue=candidate.revenue,
            profit=candidate.profit,
        )
    
    @staticmethod
    def calculate_field_usage(
        solution: List[CropAllocation]
    ) -> Dict[str, Dict]:
        """Calculate area usage per field."""
        field_usage = {}
        for alloc in solution:
            field_id = alloc.field.field_id
            if field_id not in field_usage:
                field_usage[field_id] = {
                    'allocations': [],
                    'used_area': 0.0
                }
            field_usage[field_id]['allocations'].append(alloc)
            field_usage[field_id]['used_area'] += alloc.area_used
        return field_usage
    
    @staticmethod
    def remove_allocations(
        solution: List[CropAllocation],
        to_remove: List[CropAllocation]
    ) -> List[CropAllocation]:
        """Remove allocations from solution."""
        remove_ids = {a.allocation_id for a in to_remove}
        return [a for a in solution if a.allocation_id not in remove_ids]
```

---

### 使用例：Local Search

```python
# src/agrr_core/usecase/services/neighbor_operations/crop_insert_operation.py

from agrr_core.usecase.services.allocation_utils import AllocationUtils

class CropInsertOperation(NeighborOperation):
    """Insert new crop allocation."""
    
    def generate_neighbors(self, solution, context):
        neighbors = []
        candidates = context.get("candidates", [])
        
        # ✅ Use shared utility
        field_usage = AllocationUtils.calculate_field_usage(solution)
        
        for candidate in candidates:
            # ✅ Use shared utility
            new_alloc = AllocationUtils.candidate_to_allocation(candidate)
            
            # ✅ Use shared utility
            if AllocationUtils.is_feasible_to_add(solution, new_alloc):
                neighbor = solution + [new_alloc]
                neighbors.append(neighbor)
        
        return neighbors
```

---

### 使用例：ALNS

```python
# src/agrr_core/usecase/services/alns_optimizer_service.py

from agrr_core.usecase.services.allocation_utils import AllocationUtils

class ALNSOptimizer:
    """ALNS optimizer."""
    
    def _greedy_insert(self, partial, removed, candidates, fields):
        """Greedy insert repair operator."""
        current = partial.copy()
        sorted_removed = sorted(removed, key=lambda a: a.profit_rate, reverse=True)
        
        for alloc in sorted_removed:
            # ✅ Use shared utility
            if AllocationUtils.is_feasible_to_add(current, alloc):
                current.append(alloc)
        
        return current
    
    def _is_feasible_to_add(self, current, new_alloc):
        """Wrapper for shared utility."""
        # ✅ Use shared utility
        return AllocationUtils.is_feasible_to_add(current, new_alloc)
```

---

## 🎯 統合の利点

### 1. コードの重複削減

**現状**：
- Local Search: `_time_overlaps_candidate` (117行)
- ALNS: `_time_overlaps` (alns_optimizer_service.py)
- Interactor: `_time_overlaps` (multi_field_crop_allocation_greedy_interactor.py)

**統合後**：
- ✅ 1箇所に集約（`AllocationUtils.time_overlaps`）
- ✅ テストも1箇所
- ✅ バグ修正も1箇所

---

### 2. 一貫性の保証

**現状**：
- 各実装で微妙に異なるロジック
- 更新が漏れる可能性

**統合後**：
- ✅ 全ての操作で同じロジック
- ✅ 1回の変更で全体に反映

---

### 3. テストの簡素化

**現状**：
- 各操作で同じチェックをテスト

**統合後**：
- ✅ ユーティリティのテストのみ
- ✅ 各操作のテストはシンプルに

---

## 📝 実装ロードマップ

### Phase 1: ユーティリティクラス作成（1-2日）

```python
# 1. allocation_utils.pyを作成
# 2. 共通ロジックを実装
# 3. ユニットテスト作成
```

---

### Phase 2: Local Search移行（1-2日）

```python
# 4. CropInsertOperationを更新
# 5. FieldRemoveOperationを更新
# 6. 他の操作も順次更新
# 7. 既存テストが通ることを確認
```

---

### Phase 3: ALNS移行（1日）

```python
# 8. ALNSOptimizerを更新
# 9. テスト確認
```

---

### Phase 4: Interactor移行（1日）

```python
# 10. MultiFieldCropAllocationGreedyInteractorを更新
# 11. 統合テスト
```

---

## 💻 実装例

### 1. allocation_utils.py（新規作成）

```python
# src/agrr_core/usecase/services/allocation_utils.py

"""Shared utility functions for allocation optimization.

This module provides common functionality used by both Local Search
and ALNS optimization algorithms.
"""

import uuid
from typing import List, Dict, Any
from datetime import datetime

from agrr_core.entity.entities.crop_allocation_entity import CropAllocation


class AllocationUtils:
    """Shared utility methods for allocation optimization."""
    
    @staticmethod
    def time_overlaps(
        start1: datetime,
        end1: datetime,
        start2: datetime,
        end2: datetime
    ) -> bool:
        """Check if two time periods overlap.
        
        Args:
            start1: Start time of period 1
            end1: End time of period 1
            start2: Start time of period 2
            end2: End time of period 2
            
        Returns:
            True if periods overlap, False otherwise
        """
        return not (end1 < start2 or end2 < start1)
    
    @staticmethod
    def allocation_overlaps(
        alloc1: CropAllocation,
        alloc2: CropAllocation
    ) -> bool:
        """Check if two allocations overlap in time.
        
        Args:
            alloc1: First allocation
            alloc2: Second allocation
            
        Returns:
            True if allocations overlap, False otherwise
        """
        return AllocationUtils.time_overlaps(
            alloc1.start_date,
            alloc1.completion_date,
            alloc2.start_date,
            alloc2.completion_date
        )
    
    @staticmethod
    def is_feasible_to_add(
        current_solution: List[CropAllocation],
        new_allocation: CropAllocation,
        check_area: bool = False,
        max_area: float = None
    ) -> bool:
        """Check if adding a new allocation is feasible.
        
        Args:
            current_solution: Current allocation solution
            new_allocation: New allocation to add
            check_area: If True, also check area constraints
            max_area: Maximum area per field (required if check_area=True)
            
        Returns:
            True if feasible, False otherwise
        """
        # Check time overlap in same field
        for existing in current_solution:
            if existing.field.field_id == new_allocation.field.field_id:
                if AllocationUtils.allocation_overlaps(existing, new_allocation):
                    return False
        
        # Check area constraint
        if check_area and max_area is not None:
            field_id = new_allocation.field.field_id
            used_area = sum(
                a.area_used for a in current_solution
                if a.field.field_id == field_id
            )
            if used_area + new_allocation.area_used > max_area:
                return False
        
        return True
    
    @staticmethod
    def candidate_to_allocation(candidate: Any) -> CropAllocation:
        """Convert AllocationCandidate to CropAllocation.
        
        Args:
            candidate: AllocationCandidate object
            
        Returns:
            CropAllocation entity
        """
        return CropAllocation(
            allocation_id=str(uuid.uuid4()),
            field=candidate.field,
            crop=candidate.crop,
            area_used=candidate.area_used,
            start_date=candidate.start_date,
            completion_date=candidate.completion_date,
            growth_days=candidate.growth_days,
            accumulated_gdd=candidate.accumulated_gdd,
            total_cost=candidate.cost,
            expected_revenue=candidate.revenue,
            profit=candidate.profit,
        )
    
    @staticmethod
    def calculate_field_usage(
        solution: List[CropAllocation]
    ) -> Dict[str, Dict[str, Any]]:
        """Calculate area usage and allocations per field.
        
        Args:
            solution: Current allocation solution
            
        Returns:
            Dictionary mapping field_id to usage info:
            {
                'field_id': {
                    'allocations': List[CropAllocation],
                    'used_area': float,
                    'allocation_count': int
                }
            }
        """
        field_usage = {}
        
        for alloc in solution:
            field_id = alloc.field.field_id
            
            if field_id not in field_usage:
                field_usage[field_id] = {
                    'allocations': [],
                    'used_area': 0.0,
                    'allocation_count': 0
                }
            
            field_usage[field_id]['allocations'].append(alloc)
            field_usage[field_id]['used_area'] += alloc.area_used
            field_usage[field_id]['allocation_count'] += 1
        
        return field_usage
    
    @staticmethod
    def remove_allocations(
        solution: List[CropAllocation],
        to_remove: List[CropAllocation]
    ) -> List[CropAllocation]:
        """Remove specific allocations from solution.
        
        Args:
            solution: Current solution
            to_remove: Allocations to remove
            
        Returns:
            New solution without removed allocations
        """
        remove_ids = {a.allocation_id for a in to_remove}
        return [a for a in solution if a.allocation_id not in remove_ids]
    
    @staticmethod
    def calculate_total_profit(solution: List[CropAllocation]) -> float:
        """Calculate total profit of solution.
        
        Args:
            solution: Allocation solution
            
        Returns:
            Total profit
        """
        return sum(a.profit for a in solution if a.profit is not None)
```

---

### 2. テスト（新規作成）

```python
# tests/test_unit/test_allocation_utils.py

import pytest
from datetime import datetime, timedelta

from agrr_core.usecase.services.allocation_utils import AllocationUtils
from agrr_core.entity.entities.crop_allocation_entity import CropAllocation


class TestAllocationUtils:
    """Test allocation utility functions."""
    
    def test_time_overlaps_true(self):
        """Test time overlap detection (overlapping case)."""
        start1 = datetime(2025, 1, 1)
        end1 = datetime(2025, 3, 1)
        start2 = datetime(2025, 2, 1)
        end2 = datetime(2025, 4, 1)
        
        assert AllocationUtils.time_overlaps(start1, end1, start2, end2) is True
    
    def test_time_overlaps_false(self):
        """Test time overlap detection (non-overlapping case)."""
        start1 = datetime(2025, 1, 1)
        end1 = datetime(2025, 2, 1)
        start2 = datetime(2025, 3, 1)
        end2 = datetime(2025, 4, 1)
        
        assert AllocationUtils.time_overlaps(start1, end1, start2, end2) is False
    
    # ... more tests ...
```

---

## 🎯 結論

### 共通化できる部分

1. ✅ **時間重複チェック**
2. ✅ **面積制約チェック**
3. ✅ **実行可能性チェック**
4. ✅ **候補→割当変換**
5. ✅ **圃場使用状況計算**
6. ✅ **削除操作**
7. ✅ **挿入操作**

### 共通化の効果

- **コード削減**: 約200-300行削減
- **保守性向上**: 1箇所の変更で全体に反映
- **品質向上**: テストが集約され、バグが減る
- **開発効率**: 新しい操作の追加が容易

### 推奨実装順序

1. **Week 1**: `AllocationUtils`作成（2日）
2. **Week 2**: Local Search移行（2日）
3. **Week 3**: ALNS移行（1日）
4. **Week 4**: 統合テスト（2日）

**合計**: 約1週間で完全統合 🚀

---

**次のステップ**: `allocation_utils.py`を実装しましょう！

