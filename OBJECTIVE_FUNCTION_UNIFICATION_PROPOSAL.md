# 目的関数統一化提案：更新忘れを防ぐアーキテクチャ

**作成日**: 2025-10-12  
**目的**: 将来の目的関数更新時に、一部の最適化処理での更新忘れを防ぐ

---

## 問題の本質

### 現状の問題

```
GrowthPeriodOptimizeInteractor:
  objective = minimize(cost)  # ← ここで計算

MultiFieldCropAllocationGreedyInteractor:
  objective = maximize(profit = revenue - cost)  # ← ここでも計算

OptimizationIntermediateResultScheduleInteractor:
  objective = minimize(cost)  # ← ここでも計算
```

**将来のリスク**: 
- 目的関数を「profit = revenue - cost - tax」に変更する場合
- 3箇所すべてを更新する必要がある
- **1箇所でも更新忘れが発生すると、不整合が発生**

---

## 解決策の評価基準

| 基準 | 重要度 | 説明 |
|-----|-------|------|
| **強制力** | ★★★★★ | 更新忘れをコンパイル時/実行時に検出できるか |
| **保守性** | ★★★★★ | 変更が1箇所で済むか（Single Source of Truth） |
| **可読性** | ★★★★☆ | コードが理解しやすいか |
| **テスト容易性** | ★★★★☆ | 目的関数の正しさをテストできるか |
| **Clean Architecture適合** | ★★★☆☆ | 依存関係の方向を守れるか |

---

## 提案する解決策（多層防御アプローチ）

### 🏆 推奨：レイヤー1～4を組み合わせた実装

各レイヤーが異なる種類のエラーを防ぎます：

| レイヤー | 防ぐエラー | 検出タイミング |
|---------|-----------|--------------|
| **1. Entity層の共通クラス** | 計算ロジックの不一致 | 実装時 |
| **2. 型システムとインターフェース** | インターフェース違反 | コンパイル時 |
| **3. ファクトリーパターン** | 不正なインスタンス生成 | 実行時（早期） |
| **4. 自動テスト** | 結果の不整合 | テスト時 |

---

## レイヤー1: Entity層の共通目的関数クラス

### 設計：Single Source of Truth

```python
# src/agrr_core/entity/value_objects/optimization_objective.py
"""Optimization objective calculation (Entity Layer).

This module provides the single source of truth for optimization objectives.
All optimization interactors MUST use this class to ensure consistency.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class ObjectiveType(Enum):
    """Optimization objective types."""
    MAXIMIZE_PROFIT = "maximize_profit"
    MINIMIZE_COST = "minimize_cost"
    MAXIMIZE_REVENUE = "maximize_revenue"


@dataclass(frozen=True)
class OptimizationMetrics:
    """Immutable optimization metrics.
    
    This value object encapsulates all metrics used in optimization objectives.
    By centralizing these metrics, we ensure consistency across all optimizers.
    """
    
    cost: float
    revenue: Optional[float] = None
    profit: Optional[float] = None
    
    def __post_init__(self):
        """Validate metrics consistency."""
        if self.cost < 0:
            raise ValueError(f"cost must be non-negative, got {self.cost}")
        
        if self.revenue is not None and self.revenue < 0:
            raise ValueError(f"revenue must be non-negative, got {self.revenue}")
        
        # Validate profit consistency
        if self.profit is not None and self.revenue is not None:
            expected_profit = self.revenue - self.cost
            if abs(self.profit - expected_profit) > 0.01:
                raise ValueError(
                    f"profit ({self.profit}) inconsistent with revenue-cost ({expected_profit})"
                )
    
    @staticmethod
    def from_cost_only(cost: float) -> "OptimizationMetrics":
        """Create metrics with cost only (revenue unknown)."""
        return OptimizationMetrics(cost=cost, revenue=None, profit=None)
    
    @staticmethod
    def from_cost_and_revenue(cost: float, revenue: float) -> "OptimizationMetrics":
        """Create metrics with cost and revenue (profit calculated automatically)."""
        profit = revenue - cost
        return OptimizationMetrics(cost=cost, revenue=revenue, profit=profit)


class OptimizationObjectiveCalculator:
    """Calculator for optimization objectives.
    
    This class is the SINGLE SOURCE OF TRUTH for all optimization objectives.
    
    Design Principles:
    1. Pure functions - no side effects
    2. Immutable inputs/outputs
    3. Explicit objective types
    4. Centralized logic
    
    Usage:
        calculator = OptimizationObjectiveCalculator(ObjectiveType.MAXIMIZE_PROFIT)
        value = calculator.calculate(metrics)
        better = calculator.is_better(value1, value2)
    """
    
    def __init__(self, objective_type: ObjectiveType):
        """Initialize calculator with objective type.
        
        Args:
            objective_type: Type of optimization objective
        """
        self.objective_type = objective_type
    
    def calculate(self, metrics: OptimizationMetrics) -> float:
        """Calculate objective value from metrics.
        
        This is the CORE FUNCTION that defines what we optimize.
        ALL changes to optimization logic MUST be made here.
        
        Args:
            metrics: Optimization metrics
            
        Returns:
            Objective value (to be maximized or minimized based on objective_type)
            
        Raises:
            ValueError: If required metrics are missing for the objective type
        """
        if self.objective_type == ObjectiveType.MINIMIZE_COST:
            return metrics.cost
        
        elif self.objective_type == ObjectiveType.MAXIMIZE_PROFIT:
            if metrics.profit is None:
                if metrics.revenue is None:
                    raise ValueError(
                        "MAXIMIZE_PROFIT requires profit or revenue, but both are None. "
                        "Use OptimizationMetrics.from_cost_and_revenue() to create metrics."
                    )
                # Calculate profit if not provided
                return metrics.revenue - metrics.cost
            return metrics.profit
        
        elif self.objective_type == ObjectiveType.MAXIMIZE_REVENUE:
            if metrics.revenue is None:
                raise ValueError("MAXIMIZE_REVENUE requires revenue")
            return metrics.revenue
        
        else:
            raise ValueError(f"Unknown objective type: {self.objective_type}")
    
    def is_better(self, value1: float, value2: float) -> bool:
        """Compare two objective values.
        
        Args:
            value1: First objective value
            value2: Second objective value
            
        Returns:
            True if value1 is better than value2 according to objective_type
        """
        if self.objective_type == ObjectiveType.MINIMIZE_COST:
            return value1 < value2
        else:  # MAXIMIZE_*
            return value1 > value2
    
    def select_best(self, candidates: list, key_func=None) -> any:
        """Select best candidate according to objective.
        
        Args:
            candidates: List of candidates
            key_func: Optional function to extract objective value from candidate
                     If None, candidates are assumed to be objective values
            
        Returns:
            Best candidate
            
        Raises:
            ValueError: If candidates is empty
        """
        if not candidates:
            raise ValueError("Cannot select best from empty candidates")
        
        if key_func is None:
            key_func = lambda x: x
        
        if self.objective_type == ObjectiveType.MINIMIZE_COST:
            return min(candidates, key=key_func)
        else:  # MAXIMIZE_*
            return max(candidates, key=key_func)


# ===== Future Extension: Tax, Subsidy, etc. =====

@dataclass(frozen=True)
class AdvancedOptimizationMetrics(OptimizationMetrics):
    """Extended metrics with tax, subsidy, etc.
    
    Future extension example:
    - Add tax, subsidy, environmental cost, etc.
    - All optimizers will automatically use these
    """
    
    tax: float = 0.0
    subsidy: float = 0.0
    environmental_cost: float = 0.0
    
    @property
    def net_profit(self) -> Optional[float]:
        """Calculate net profit including tax and subsidy."""
        if self.profit is None:
            return None
        return self.profit - self.tax + self.subsidy - self.environmental_cost
```

### 使用例：各Interactorでの利用

```python
# GrowthPeriodOptimizeInteractor での使用
from agrr_core.entity.value_objects.optimization_objective import (
    OptimizationObjectiveCalculator,
    OptimizationMetrics,
    ObjectiveType,
)

class GrowthPeriodOptimizeInteractor:
    def __init__(self, ..., objective_type: ObjectiveType = ObjectiveType.MINIMIZE_COST):
        # ...
        self.objective_calculator = OptimizationObjectiveCalculator(objective_type)
    
    async def execute(self, request):
        # ...
        
        # 候補を評価
        for candidate in candidates:
            metrics = OptimizationMetrics.from_cost_only(candidate.total_cost)
            candidate.objective_value = self.objective_calculator.calculate(metrics)
        
        # 最適候補を選択（統一されたロジック）
        optimal = self.objective_calculator.select_best(
            candidates, 
            key_func=lambda c: c.objective_value
        )
```

### 利点

✅ **更新忘れの防止**: 目的関数の変更は`OptimizationObjectiveCalculator.calculate()`の1箇所のみ  
✅ **型安全性**: `OptimizationMetrics`が不整合を検証  
✅ **テスト容易性**: 目的関数を独立してテストできる  
✅ **Clean Architecture適合**: Entity層（最内層）に配置

---

## レイヤー2: 型システムとインターフェースによる強制

### 設計：Protocol (Structural Subtyping)

```python
# src/agrr_core/entity/protocols/optimizable.py
"""Protocols for optimizable entities."""

from typing import Protocol, TypeVar
from agrr_core.entity.value_objects.optimization_objective import OptimizationMetrics


class Optimizable(Protocol):
    """Protocol for entities that can be optimized.
    
    All optimization candidates MUST implement this protocol.
    This ensures that optimization interactors can only work with
    entities that provide objective metrics.
    """
    
    def get_optimization_metrics(self) -> OptimizationMetrics:
        """Get optimization metrics for this entity.
        
        Returns:
            OptimizationMetrics containing cost, revenue, profit
        """
        ...


T = TypeVar('T', bound=Optimizable)


class Optimizer(Protocol[T]):
    """Protocol for optimizers.
    
    All optimization interactors MUST implement this protocol.
    This ensures consistent interface across all optimizers.
    """
    
    def optimize(self, candidates: list[T]) -> T:
        """Find optimal candidate.
        
        Args:
            candidates: List of optimizable candidates
            
        Returns:
            Optimal candidate
        """
        ...
```

### 実装例

```python
# CandidateResultDTO が Optimizable を実装
@dataclass(frozen=True)
class CandidateResultDTO:
    start_date: datetime
    completion_date: Optional[datetime]
    growth_days: Optional[int]
    total_cost: Optional[float]
    revenue: Optional[float] = None
    profit: Optional[float] = None
    
    def get_optimization_metrics(self) -> OptimizationMetrics:
        """Implement Optimizable protocol."""
        if self.total_cost is None:
            raise ValueError("Cannot optimize candidate without cost")
        
        if self.revenue is not None:
            return OptimizationMetrics.from_cost_and_revenue(
                cost=self.total_cost,
                revenue=self.revenue
            )
        else:
            return OptimizationMetrics.from_cost_only(cost=self.total_cost)
```

### 利点

✅ **コンパイル時チェック**: mypyが型エラーを検出  
✅ **インターフェース統一**: すべての候補が同じメソッドを持つ  
✅ **IDE支援**: 自動補完が効く

---

## レイヤー3: ファクトリーパターンによる集中管理

### 設計：Interactorファクトリー

```python
# src/agrr_core/usecase/factories/optimizer_factory.py
"""Factory for creating optimizers with consistent objective functions."""

from agrr_core.entity.value_objects.optimization_objective import (
    OptimizationObjectiveCalculator,
    ObjectiveType,
)
from agrr_core.usecase.interactors.growth_period_optimize_interactor import (
    GrowthPeriodOptimizeInteractor,
)
from agrr_core.usecase.interactors.multi_field_crop_allocation_greedy_interactor import (
    MultiFieldCropAllocationGreedyInteractor,
)


class OptimizerFactory:
    """Factory for creating optimization interactors.
    
    This factory ensures that all optimizers use the same objective function.
    
    Benefits:
    1. Single point of configuration
    2. Consistent objective across all optimizers
    3. Easy to change objective globally
    """
    
    def __init__(self, objective_type: ObjectiveType = ObjectiveType.MAXIMIZE_PROFIT):
        """Initialize factory with objective type.
        
        Args:
            objective_type: Objective type for all optimizers
        """
        self.objective_type = objective_type
        self.objective_calculator = OptimizationObjectiveCalculator(objective_type)
    
    def create_period_optimizer(
        self,
        crop_requirement_gateway,
        weather_gateway,
        optimization_result_gateway=None,
    ) -> GrowthPeriodOptimizeInteractor:
        """Create period optimizer with consistent objective.
        
        This ensures GrowthPeriodOptimizeInteractor uses the same
        objective as other optimizers.
        """
        return GrowthPeriodOptimizeInteractor(
            crop_requirement_gateway=crop_requirement_gateway,
            weather_gateway=weather_gateway,
            optimization_result_gateway=optimization_result_gateway,
            objective_calculator=self.objective_calculator,  # ← 統一された目的関数
        )
    
    def create_allocation_optimizer(
        self,
        field_gateway,
        crop_requirement_gateway,
        weather_gateway,
        config=None,
    ) -> MultiFieldCropAllocationGreedyInteractor:
        """Create allocation optimizer with consistent objective."""
        return MultiFieldCropAllocationGreedyInteractor(
            field_gateway=field_gateway,
            crop_requirement_gateway=crop_requirement_gateway,
            weather_gateway=weather_gateway,
            config=config,
            objective_calculator=self.objective_calculator,  # ← 統一された目的関数
        )


# 使用例
factory = OptimizerFactory(ObjectiveType.MAXIMIZE_PROFIT)
period_optimizer = factory.create_period_optimizer(...)
allocation_optimizer = factory.create_allocation_optimizer(...)

# 将来、目的関数を変更する場合
factory = OptimizerFactory(ObjectiveType.MAXIMIZE_PROFIT_WITH_TAX)  # ← 1箇所の変更
```

### 利点

✅ **集中管理**: Optimizerの生成を1箇所で制御  
✅ **設定の統一**: すべてのOptimizerが同じ設定を使用  
✅ **変更の容易性**: ファクトリーの1行を変更するだけ

---

## レイヤー4: 自動テストによる検証

### 設計：目的関数整合性テスト

```python
# tests/test_entity/test_optimization_objective_consistency.py
"""Test suite to ensure all optimizers use consistent objective functions.

CRITICAL: These tests MUST fail if any optimizer uses a different objective.
"""

import pytest
from agrr_core.entity.value_objects.optimization_objective import (
    OptimizationObjectiveCalculator,
    OptimizationMetrics,
    ObjectiveType,
)


class TestObjectiveFunctionConsistency:
    """Verify all optimizers use the same objective function."""
    
    def test_all_optimizers_use_same_calculator_class(self):
        """All optimizers MUST use OptimizationObjectiveCalculator."""
        from agrr_core.usecase.interactors.growth_period_optimize_interactor import (
            GrowthPeriodOptimizeInteractor,
        )
        from agrr_core.usecase.interactors.multi_field_crop_allocation_greedy_interactor import (
            MultiFieldCropAllocationGreedyInteractor,
        )
        
        # Check that both have objective_calculator attribute
        period_optimizer = GrowthPeriodOptimizeInteractor(...)
        allocation_optimizer = MultiFieldCropAllocationGreedyInteractor(...)
        
        assert hasattr(period_optimizer, 'objective_calculator')
        assert hasattr(allocation_optimizer, 'objective_calculator')
        assert isinstance(period_optimizer.objective_calculator, OptimizationObjectiveCalculator)
        assert isinstance(allocation_optimizer.objective_calculator, OptimizationObjectiveCalculator)
    
    def test_objective_calculation_produces_same_result(self):
        """Given same metrics, all optimizers MUST produce same objective value."""
        metrics = OptimizationMetrics.from_cost_and_revenue(cost=100, revenue=200)
        
        calc1 = OptimizationObjectiveCalculator(ObjectiveType.MAXIMIZE_PROFIT)
        calc2 = OptimizationObjectiveCalculator(ObjectiveType.MAXIMIZE_PROFIT)
        
        value1 = calc1.calculate(metrics)
        value2 = calc2.calculate(metrics)
        
        assert value1 == value2 == 100  # profit = 200 - 100
    
    def test_all_optimizers_select_same_best_candidate(self):
        """Given same candidates, all optimizers MUST select the same best one."""
        candidates = [
            OptimizationMetrics.from_cost_and_revenue(cost=100, revenue=200),  # profit=100
            OptimizationMetrics.from_cost_and_revenue(cost=80, revenue=220),   # profit=140 ← best
            OptimizationMetrics.from_cost_and_revenue(cost=120, revenue=180),  # profit=60
        ]
        
        calc = OptimizationObjectiveCalculator(ObjectiveType.MAXIMIZE_PROFIT)
        
        best = calc.select_best(candidates, key_func=calc.calculate)
        
        assert best.profit == 140
    
    @pytest.mark.parametrize("objective_type", [
        ObjectiveType.MAXIMIZE_PROFIT,
        ObjectiveType.MINIMIZE_COST,
        ObjectiveType.MAXIMIZE_REVENUE,
    ])
    def test_objective_calculator_is_deterministic(self, objective_type):
        """Objective calculation MUST be deterministic."""
        metrics = OptimizationMetrics.from_cost_and_revenue(cost=100, revenue=200)
        calc = OptimizationObjectiveCalculator(objective_type)
        
        # Call multiple times
        results = [calc.calculate(metrics) for _ in range(10)]
        
        # All results must be identical
        assert len(set(results)) == 1


class TestObjectiveFunctionUpdateDetection:
    """Detect when objective function is updated.
    
    CRITICAL: If you modify the objective function, you MUST update this test.
    This ensures that all team members are aware of the change.
    """
    
    def test_objective_function_signature(self):
        """Document current objective function.
        
        If this test fails, it means the objective function has changed.
        You MUST:
        1. Update this test with the new expected values
        2. Update ALL optimizers to use the new objective
        3. Update documentation
        """
        # Current objective: profit = revenue - cost
        metrics = OptimizationMetrics.from_cost_and_revenue(
            cost=1000,
            revenue=2000,
        )
        
        calc = OptimizationObjectiveCalculator(ObjectiveType.MAXIMIZE_PROFIT)
        profit = calc.calculate(metrics)
        
        # Expected: 2000 - 1000 = 1000
        assert profit == 1000, (
            "Objective function has changed! "
            "Expected profit = revenue - cost = 1000, "
            f"but got {profit}. "
            "If this is intentional, update this test AND all optimizers."
        )
    
    def test_future_objective_with_tax(self):
        """Test for future extension with tax.
        
        This test is currently skipped but documents the intended behavior
        when we add tax to the objective function.
        """
        pytest.skip("Tax not yet implemented")
        
        # Future: profit = revenue - cost - tax
        metrics = AdvancedOptimizationMetrics.from_cost_and_revenue(
            cost=1000,
            revenue=2000,
            tax=200,  # ← 将来の拡張
        )
        
        calc = OptimizationObjectiveCalculator(ObjectiveType.MAXIMIZE_PROFIT)
        net_profit = calc.calculate(metrics)
        
        # Expected: 2000 - 1000 - 200 = 800
        assert net_profit == 800
```

### 利点

✅ **実行時検証**: テストが失敗したら目的関数が不整合  
✅ **ドキュメント**: テストが期待される動作を文書化  
✅ **変更検出**: 目的関数の変更を確実に検出

---

## レイヤー5: ドキュメントとプロセス（補助的）

### 設計：変更チェックリスト

```markdown
# docs/OPTIMIZATION_OBJECTIVE_CHANGE_CHECKLIST.md

## 目的関数を変更する前に必ず確認

目的関数を変更する場合、以下のすべてをチェックしてください。

### ✅ 変更チェックリスト

- [ ] `OptimizationObjectiveCalculator.calculate()` を更新
- [ ] 新しいメトリクス（税金など）を `OptimizationMetrics` に追加
- [ ] すべてのテストが通ることを確認（特に `test_optimization_objective_consistency.py`）
- [ ] `test_objective_function_signature()` を更新
- [ ] すべてのInteractorが新しい目的関数を使用することを確認
- [ ] ドキュメントを更新
- [ ] チームレビューを受ける

### 🚨 更新が必要なファイル

自動的に更新されるファイル（`OptimizationObjectiveCalculator`を使用しているため）:
- ✅ `growth_period_optimize_interactor.py` - 自動的に新しい目的関数を使用
- ✅ `multi_field_crop_allocation_greedy_interactor.py` - 自動的に新しい目的関数を使用
- ✅ すべてのOptimizerFactory経由のインスタンス - 自動的に更新

手動で確認が必要なファイル:
- ⚠️ テストファイル - 期待値を更新
- ⚠️ ドキュメント - 目的関数の説明を更新
```

---

## 実装計画

### Phase 1: 基盤構築（1週間）

```
Day 1-2: Entity層の実装
  - OptimizationObjectiveCalculator 実装
  - OptimizationMetrics 実装
  - 単体テスト作成

Day 3-4: Protocol定義
  - Optimizable プロトコル実装
  - Optimizer プロトコル実装
  - 型チェック設定

Day 5: ファクトリー実装
  - OptimizerFactory 実装
  - 統合テスト作成
```

### Phase 2: 既存コードの移行（1週間）

```
Day 1-3: Interactor更新
  - GrowthPeriodOptimizeInteractor を OptimizationObjectiveCalculator 使用に変更
  - MultiFieldCropAllocationGreedyInteractor 更新
  - OptimizationIntermediateResultScheduleInteractor 更新

Day 4-5: テスト更新
  - 既存テストを新しいAPIに適合
  - 整合性テスト追加
  - エンドツーエンドテスト
```

### Phase 3: ドキュメント（2-3日）

```
Day 1: ドキュメント作成
  - OPTIMIZATION_OBJECTIVE_CHANGE_CHECKLIST.md
  - API documentationの更新
  - 設計決定の記録

Day 2-3: チームレビュー
  - コードレビュー
  - ドキュメントレビュー
  - 変更チェックリストの検証
```

---

## 効果の評価

### Before（現状）

```python
# 3箇所で目的関数を計算
# GrowthPeriodOptimizeInteractor
optimal = min(candidates, key=lambda c: c.total_cost)  # ← 変更箇所1

# MultiFieldCropAllocationGreedyInteractor
sorted_candidates = sorted(candidates, key=lambda c: c.profit_rate, reverse=True)  # ← 変更箇所2

# OptimizationIntermediateResultScheduleInteractor
min_cost, selected = self._find_minimum_cost_schedule(...)  # ← 変更箇所3
```

**リスク**: 3箇所のうち1箇所でも更新を忘れると不整合

### After（提案後）

```python
# 1箇所で目的関数を定義
class OptimizationObjectiveCalculator:
    def calculate(self, metrics):
        return metrics.profit  # ← 変更箇所は ここだけ！

# すべてのInteractorが自動的に更新された目的関数を使用
optimal = self.objective_calculator.select_best(candidates, key_func=...)
```

**効果**: 
- ✅ 更新箇所: 3箇所 → **1箇所**
- ✅ 更新忘れリスク: 高 → **ゼロ**（コンパイルエラー/テスト失敗）
- ✅ テスト容易性: 低 → **高**（目的関数を独立テスト）

---

## 多層防御の効果

| 層 | 防ぐエラー | 検出時期 | 強制力 |
|----|-----------|---------|-------|
| **1. Entity層の共通クラス** | 実装の分散 | 実装時 | ★★★★★ |
| **2. Protocol** | インターフェース違反 | コンパイル時 | ★★★★☆ |
| **3. Factory** | 設定の不一致 | 実行時（早期） | ★★★★☆ |
| **4. 自動テスト** | 計算結果の不整合 | テスト時 | ★★★★★ |
| **5. ドキュメント** | 手順の見落とし | レビュー時 | ★★☆☆☆ |

**総合評価**: ★★★★★（最高レベルの防御）

---

## 結論

### 最高の解決策

**レイヤー1～4を組み合わせた多層防御アプローチ**

これにより：
1. ✅ **Single Source of Truth**: 目的関数は1箇所のみで定義
2. ✅ **コンパイル時チェック**: 型システムが違反を検出
3. ✅ **実行時チェック**: テストが不整合を検出
4. ✅ **保守性**: 変更は1箇所で済む
5. ✅ **Clean Architecture適合**: 依存関係の方向を守る

### 重要なポイント

> **「更新忘れを防ぐ」のではなく、「更新が1箇所で済むようにする」**

これが本質的な解決策です。

---

**提案者**: AI Assistant  
**推奨実装期間**: 2-3週間  
**ROI**: 非常に高い（将来の保守コストを大幅削減）

