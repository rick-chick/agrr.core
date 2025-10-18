# 近傍操作のエラーハンドリング強化

## 問題認識

**ユーザーの懸念**: 「複雑なケースで失敗するのであれば、特定の近傍でエラーしている可能性もある」

これは非常に重要な観点です。ALNS/Local Searchの近傍操作で以下のエラーが発生する可能性があります：

1. **データ不整合**: 削除/挿入時のデータ破損
2. **制約違反**: 時間重複、面積超過
3. **NULL/None参照**: profit, revenueがNone
4. **インデックスエラー**: リスト範囲外アクセス
5. **数値エラー**: ゼロ除算、オーバーフロー

---

## 実装した対策

### 1. ALNSでのエラーハンドリング（完了）✅

```python
# src/agrr_core/usecase/services/alns_optimizer_service.py

def optimize(self, initial_solution, candidates, fields, crops, max_iterations):
    for iteration in range(max_iterations):
        # Destroy: remove part of solution
        try:
            partial, removed = destroy_op(current)
        except Exception as e:
            logger.warning(f"Destroy operator '{destroy_name}' failed: {e}")
            continue  # Skip this iteration
        
        # Repair: rebuild solution
        try:
            new_solution = repair_op(partial, removed, candidates, fields)
        except Exception as e:
            logger.warning(f"Repair operator '{repair_name}' failed: {e}")
            continue  # Skip this iteration
        
        # Continue with valid solution...
```

**効果**:
- ✅ エラーが発生してもプログラムは継続
- ✅ ログに警告を出力（デバッグ可能）
- ✅ 他のoperatorで改善を試みる

---

### 2. 各Destroy Operatorのガード（推奨）

#### random_removal

```python
def _random_removal(self, solution):
    """Randomly remove allocations with safety checks."""
    if not solution:
        return [], []  # Empty solution
    
    removal_rate = 0.3
    n_remove = max(1, int(len(solution) * removal_rate))
    
    # ✅ Safety: Ensure we don't remove more than available
    n_remove = min(n_remove, len(solution))
    
    try:
        removed = random.sample(solution, n_remove)
        remaining = [a for a in solution if a not in removed]
        return remaining, removed
    except ValueError as e:
        # Fallback: remove nothing
        return solution, []
```

#### worst_removal

```python
def _worst_removal(self, solution):
    """Remove worst allocations with NULL checks."""
    if not solution:
        return [], []
    
    # ✅ Safety: Filter out allocations with NULL profit
    valid_allocs = [a for a in solution if a.profit is not None]
    
    if not valid_allocs:
        # All allocations have NULL profit
        return solution, []
    
    removal_rate = 0.3
    n_remove = max(1, int(len(valid_allocs) * removal_rate))
    
    # Sort by profit (ascending)
    sorted_allocs = sorted(valid_allocs, key=lambda a: a.profit)
    
    removed = sorted_allocs[:n_remove]
    remaining = [a for a in solution if a not in removed]
    
    return remaining, removed
```

#### field_removal

```python
def _field_removal(self, solution):
    """Remove field allocations with empty check."""
    if not solution:
        return [], []
    
    # Get fields in solution
    fields_in_solution = list(set(a.field.field_id for a in solution))
    
    # ✅ Safety: Check if any fields exist
    if not fields_in_solution:
        return solution, []
    
    # Pick random field
    target_field = random.choice(fields_in_solution)
    
    removed = [a for a in solution if a.field.field_id == target_field]
    remaining = [a for a in solution if a.field.field_id != target_field]
    
    # ✅ Safety: Ensure we don't remove everything
    if not remaining:
        # Don't remove if it would leave solution empty
        return solution, []
    
    return remaining, removed
```

---

### 3. Repair Operatorのガード

#### greedy_insert

```python
def _greedy_insert(self, partial, removed, candidates, fields):
    """Greedily insert with validation."""
    current = partial.copy()
    
    # ✅ Safety: Check if removed is empty
    if not removed:
        return current
    
    # ✅ Safety: Filter out allocations with NULL profit_rate
    valid_removed = [
        a for a in removed 
        if hasattr(a, 'profit_rate') and a.profit_rate is not None
    ]
    
    if not valid_removed:
        return current
    
    # Sort by profit rate
    try:
        sorted_removed = sorted(
            valid_removed, 
            key=lambda a: a.profit_rate, 
            reverse=True
        )
    except Exception as e:
        # Sorting failed, return partial
        return current
    
    # Try to insert
    for alloc in sorted_removed:
        try:
            if self._is_feasible_to_add(current, alloc):
                current.append(alloc)
        except Exception as e:
            # Skip this allocation
            continue
    
    return current
```

---

### 4. 実行可能性チェックの強化

```python
# src/agrr_core/usecase/services/allocation_utils.py

@staticmethod
def is_feasible_to_add(
    current_solution: List[CropAllocation],
    new_allocation: CropAllocation,
    check_area: bool = False,
    max_area: float = None
) -> bool:
    """Check feasibility with comprehensive error handling."""
    
    # ✅ NULL checks
    if new_allocation is None:
        return False
    
    if not hasattr(new_allocation, 'field') or new_allocation.field is None:
        return False
    
    if not hasattr(new_allocation, 'start_date') or new_allocation.start_date is None:
        return False
    
    if not hasattr(new_allocation, 'completion_date') or new_allocation.completion_date is None:
        return False
    
    # Check time overlap
    try:
        for existing in current_solution:
            if existing.field.field_id == new_allocation.field.field_id:
                if AllocationUtils.allocation_overlaps(existing, new_allocation):
                    return False
    except Exception as e:
        # If overlap check fails, assume not feasible
        return False
    
    # Check area constraint
    if check_area and max_area is not None:
        try:
            field_id = new_allocation.field.field_id
            used_area = sum(
                a.area_used for a in current_solution
                if a.field.field_id == field_id and a.area_used is not None
            )
            if used_area + new_allocation.area_used > max_area:
                return False
        except Exception as e:
            # If area check fails, assume not feasible
            return False
    
    return True
```

---

## 追加の防御的プログラミング

### 5. 利益計算のNULLチェック

```python
# src/agrr_core/usecase/services/allocation_utils.py

@staticmethod
def calculate_total_profit(solution: List[CropAllocation]) -> float:
    """Calculate total profit with NULL handling."""
    if not solution:
        return 0.0
    
    total = 0.0
    for alloc in solution:
        # ✅ Multiple NULL checks
        if alloc is None:
            continue
        
        if not hasattr(alloc, 'profit'):
            continue
        
        if alloc.profit is None:
            continue
        
        try:
            total += float(alloc.profit)
        except (TypeError, ValueError):
            # Skip invalid profit values
            continue
    
    return total
```

---

### 6. ログ出力の強化

```python
# src/agrr_core/usecase/services/alns_optimizer_service.py

import logging

class ALNSOptimizer:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        # ... existing code ...
    
    def optimize(self, ...):
        # Add debug logging
        self.logger.info(f"ALNS starting with {len(initial_solution)} allocations")
        
        for iteration in range(iterations):
            # Log every 50 iterations
            if iteration % 50 == 0:
                self.logger.debug(
                    f"ALNS iteration {iteration}/{iterations}: "
                    f"profit={current_profit:,.0f}, "
                    f"temp={temp:.2f}"
                )
            
            # ... existing code ...
            
            # Log operator performance
            if iteration % 100 == 0:
                self.logger.info(
                    f"Operator performance at iteration {iteration}:\n"
                    f"  Destroy: {self.destroy_weights.operators}\n"
                    f"  Repair: {self.repair_weights.operators}"
                )
```

---

## テスト戦略

### 1. エッジケースのテスト

```python
# tests/test_unit/test_alns_error_handling.py

class TestALNSErrorHandling:
    """Test ALNS error handling."""
    
    def test_empty_solution(self, optimizer):
        """Test ALNS with empty solution."""
        result = optimizer.optimize(
            initial_solution=[],
            candidates=[],
            fields=[],
            crops=[],
        )
        # Should not crash
        assert result == []
    
    def test_single_allocation(self, optimizer):
        """Test ALNS with single allocation."""
        result = optimizer.optimize(
            initial_solution=[alloc1],
            candidates=[],
            fields=[field1],
            crops=[crop1],
        )
        # Should return input unchanged
        assert len(result) == 1
    
    def test_null_profit_allocations(self, optimizer):
        """Test ALNS with NULL profit values."""
        alloc_null = CropAllocation(
            # ... fields ...
            profit=None,  # NULL profit
        )
        
        result = optimizer.optimize(
            initial_solution=[alloc_null],
            # ...
        )
        # Should handle gracefully
        assert result is not None
    
    def test_destroy_operator_failure(self, optimizer):
        """Test handling of destroy operator failure."""
        # Mock destroy to raise exception
        def failing_destroy(solution):
            raise ValueError("Simulated error")
        
        optimizer.destroy_operators['test_failing'] = failing_destroy
        
        # Should not crash
        result = optimizer.optimize(
            initial_solution=[alloc1, alloc2],
            # ...
        )
        assert result is not None
```

---

## 実装チェックリスト

### 完了済み ✅

- [x] ALNSでのtry-catchエラーハンドリング
- [x] AllocationUtilsのNULLチェック
- [x] テストスクリプト作成（simple, realistic）

### 推奨追加実装

- [ ] Destroy operatorの個別ガード強化
- [ ] Repair operatorの個別ガード強化
- [ ] ログ出力の追加（デバッグ用）
- [ ] エッジケーステスト追加

---

## デバッグのためのログ有効化

```bash
# ログレベルを設定して実行
export PYTHONPATH=/home/akishige/projects/agrr.core/src
python3 -c "
import logging
logging.basicConfig(level=logging.DEBUG)

import asyncio
# ... run test ...
"
```

または、スクリプトに追加：

```python
# scripts/realistic_alns_test.py の最初に追加

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

---

## まとめ

### 実装した対策

1. ✅ **ALNSのtry-catch**: destroy/repairでエラーが出ても継続
2. ✅ **AllocationUtilsのNULLチェック**: 各メソッドで防御的プログラミング
3. ✅ **Algorithm名の修正**: "DP + ALNS"が正しく表示
4. ✅ **現実的なテストスクリプト**: 10圃場、200イテレーション

### 実行中のテスト

```bash
# 10圃場、6作物、200 ALNSイテレーション
python scripts/realistic_alns_test.py
```

このテストで：
- より大きい問題でALNSの効果を検証
- エラーハンドリングが適切に機能するか確認
- 実際の改善率を測定

### 次のステップ

1. テスト結果を待つ
2. エラーが出れば、ログから特定のoperatorを特定
3. 必要に応じて個別のガードを強化
4. エッジケーステストを追加

**正攻法で、堅牢な実装を目指します！** 🎯

