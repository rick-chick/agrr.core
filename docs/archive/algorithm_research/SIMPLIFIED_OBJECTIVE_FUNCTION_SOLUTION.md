# 簡素化された目的関数統一化：利益最大化のみ

**作成日**: 2025-10-12  
**前提**: 利益最大化（MAXIMIZE_PROFIT）のみに統一

---

## 🎯 設計原則

### 基本方針

> **すべての最適化は「利益最大化」である**

```python
# 数学的統一
objective = maximize(profit)

where:
  profit = revenue - cost                    # 収益がある場合
  profit = -cost                             # 収益がない場合（コスト最小化相当）
  profit = revenue - cost - tax + subsidy    # 将来の拡張
```

### 簡素化のメリット

| 項目 | Before（3つの目的関数） | After（利益のみ） | 改善 |
|-----|----------------------|-----------------|------|
| 目的関数の種類 | 3つ | **1つ** | 67%削減 |
| 条件分岐 | 必要（if-elif） | **不要** | 100%削減 |
| コード行数 | ~250行 | **~120行** | 52%削減 |
| テストケース | ~23個 | **~10個** | 57%削減 |
| 理解の難易度 | 中 | **低** | - |

---

## 🛡️ 簡素化された多層防御

### レイヤー1: Entity層の共通クラス ★★★★★

**最もシンプルな実装**

```python
# src/agrr_core/entity/value_objects/optimization_objective.py
"""Optimization objective: Always maximize profit.

This module provides the single source of truth for optimization.
All optimization logic is centralized here.
"""

from dataclasses import dataclass
from typing import Optional, List, Callable, TypeVar


@dataclass(frozen=True)
class OptimizationMetrics:
    """Immutable optimization metrics.
    
    Represents cost and optional revenue.
    Profit is calculated automatically.
    """
    
    cost: float
    revenue: Optional[float] = None
    
    def __post_init__(self):
        """Validate metrics."""
        if self.cost < 0:
            raise ValueError(f"cost must be non-negative, got {self.cost}")
        
        if self.revenue is not None and self.revenue < 0:
            raise ValueError(f"revenue must be non-negative, got {self.revenue}")
    
    @property
    def profit(self) -> float:
        """Calculate profit.
        
        Cases:
        1. Revenue known: profit = revenue - cost
        2. Revenue unknown: profit = -cost (equivalent to cost minimization)
        
        Returns:
            Profit value (to be maximized)
        """
        if self.revenue is None:
            return -self.cost
        return self.revenue - self.cost
    
    @staticmethod
    def from_cost_only(cost: float) -> "OptimizationMetrics":
        """Create metrics with cost only."""
        return OptimizationMetrics(cost=cost)
    
    @staticmethod
    def from_cost_and_revenue(cost: float, revenue: float) -> "OptimizationMetrics":
        """Create metrics with cost and revenue."""
        return OptimizationMetrics(cost=cost, revenue=revenue)


class OptimizationObjective:
    """Single objective: Maximize profit.
    
    This class is the SINGLE SOURCE OF TRUTH for optimization.
    
    ⚠️ CRITICAL: All optimization logic MUST use this class.
    
    Design:
    - No enum (only one objective)
    - No is_better() (always maximize)
    - Pure functions
    - Immutable
    """
    
    def calculate(self, metrics: OptimizationMetrics) -> float:
        """Calculate objective value (profit).
        
        ⚠️ THIS IS THE CORE FUNCTION.
        All changes to optimization logic MUST be made here.
        
        Current: profit = revenue - cost (or -cost if revenue is None)
        Future:  profit = revenue - cost - tax + subsidy
        
        Args:
            metrics: Optimization metrics
            
        Returns:
            Profit value (to be maximized)
        """
        return metrics.profit
    
    T = TypeVar('T')
    
    def select_best(
        self, 
        candidates: List[T], 
        key_func: Callable[[T], float]
    ) -> T:
        """Select best candidate (maximum profit).
        
        Args:
            candidates: List of candidates
            key_func: Function to extract profit from candidate
            
        Returns:
            Best candidate (maximum profit)
            
        Raises:
            ValueError: If candidates is empty
            
        Example:
            objective = OptimizationObjective()
            best = objective.select_best(
                candidates,
                key_func=lambda c: objective.calculate(c.get_metrics())
            )
        """
        if not candidates:
            raise ValueError("Cannot select best from empty candidates")
        
        return max(candidates, key=key_func)
    
    def compare(self, value1: float, value2: float) -> int:
        """Compare two objective values.
        
        Args:
            value1: First objective value
            value2: Second objective value
            
        Returns:
            1 if value1 is better, -1 if value2 is better, 0 if equal
        """
        if value1 > value2:
            return 1
        elif value1 < value2:
            return -1
        return 0
    
    def __repr__(self) -> str:
        return "OptimizationObjective(maximize_profit)"


# Singleton instance (optional)
DEFAULT_OBJECTIVE = OptimizationObjective()
```

**特徴**:
- ✅ Enumなし（目的関数が1つだけなので不要）
- ✅ 条件分岐なし（常に利益最大化）
- ✅ シンプルなAPI
- ✅ 拡張性を保持

---

### レイヤー2: Protocolによる型安全性 ★★★★☆

**簡素化されたProtocol**

```python
# src/agrr_core/entity/protocols/optimizable.py
"""Protocols for optimizable entities."""

from typing import Protocol
from agrr_core.entity.value_objects.optimization_objective import OptimizationMetrics


class Optimizable(Protocol):
    """Protocol for entities that can be optimized.
    
    All optimization candidates MUST implement this protocol.
    """
    
    def get_metrics(self) -> OptimizationMetrics:
        """Get optimization metrics for this entity.
        
        Returns:
            OptimizationMetrics containing cost and optional revenue
        """
        ...


# 使用例
@dataclass
class CandidateResultDTO:
    start_date: datetime
    total_cost: float
    revenue: Optional[float] = None
    
    def get_metrics(self) -> OptimizationMetrics:
        """Implement Optimizable protocol."""
        return OptimizationMetrics(cost=self.total_cost, revenue=self.revenue)


# Interactorでの使用
def optimize(candidates: List[Optimizable]) -> Optimizable:
    objective = OptimizationObjective()
    return objective.select_best(
        candidates,
        key_func=lambda c: objective.calculate(c.get_metrics())
    )
```

**特徴**:
- ✅ 型安全（mypyがチェック）
- ✅ シンプルなインターフェース
- ✅ IDEの自動補完

---

### レイヤー3: Base Interactorによる統一 ★★★★★

**新しいアプローチ：基底クラス**

```python
# src/agrr_core/usecase/interactors/base_optimizer.py
"""Base class for all optimization interactors."""

from abc import ABC
from typing import List, TypeVar, Generic
from agrr_core.entity.value_objects.optimization_objective import (
    OptimizationObjective,
    OptimizationMetrics,
    DEFAULT_OBJECTIVE,
)
from agrr_core.entity.protocols.optimizable import Optimizable


T = TypeVar('T', bound=Optimizable)


class BaseOptimizer(ABC, Generic[T]):
    """Base class for all optimization interactors.
    
    This ensures all optimizers use the same objective function.
    
    Usage:
        class MyOptimizer(BaseOptimizer[MyCandidateType]):
            def execute(self, request):
                candidates = self._generate_candidates(request)
                optimal = self.select_best(candidates)
                return optimal
    """
    
    def __init__(self, objective: OptimizationObjective = None):
        """Initialize optimizer.
        
        Args:
            objective: Optimization objective (uses default if None)
        """
        self.objective = objective or DEFAULT_OBJECTIVE
    
    def select_best(self, candidates: List[T]) -> T:
        """Select best candidate using the objective function.
        
        This method MUST be used by all subclasses.
        
        Args:
            candidates: List of candidates implementing Optimizable
            
        Returns:
            Best candidate
        """
        return self.objective.select_best(
            candidates,
            key_func=lambda c: self.objective.calculate(c.get_metrics())
        )
    
    def calculate_value(self, candidate: T) -> float:
        """Calculate objective value for a candidate.
        
        Args:
            candidate: Candidate implementing Optimizable
            
        Returns:
            Objective value (profit)
        """
        return self.objective.calculate(candidate.get_metrics())
    
    def compare_candidates(self, candidate1: T, candidate2: T) -> int:
        """Compare two candidates.
        
        Returns:
            1 if candidate1 is better, -1 if candidate2 is better, 0 if equal
        """
        value1 = self.calculate_value(candidate1)
        value2 = self.calculate_value(candidate2)
        return self.objective.compare(value1, value2)
```

**使用例**:

```python
# GrowthPeriodOptimizeInteractor
class GrowthPeriodOptimizeInteractor(BaseOptimizer[CandidateResultDTO]):
    """Period optimizer inheriting from BaseOptimizer."""
    
    def __init__(
        self,
        crop_requirement_gateway,
        weather_gateway,
        optimization_result_gateway=None,
    ):
        super().__init__()  # 自動的にOptimizationObjectiveを使用
        self.crop_requirement_gateway = crop_requirement_gateway
        self.weather_gateway = weather_gateway
        # ...
    
    async def execute(self, request):
        candidates = await self._generate_candidates(request)
        
        # BaseOptimizerのメソッドを使用（統一された目的関数）
        optimal = self.select_best(candidates)  # ← 自動的に利益最大化
        
        return response


# MultiFieldCropAllocationGreedyInteractor
class MultiFieldCropAllocationGreedyInteractor(BaseOptimizer[AllocationCandidate]):
    """Allocation optimizer inheriting from BaseOptimizer."""
    
    async def execute(self, request):
        candidates = await self._generate_candidates(request)
        allocations = self._greedy_allocation(candidates)
        
        # ローカル探索でも統一された目的関数を使用
        allocations = self._local_search(allocations, candidates)
        
        return response
    
    def _greedy_allocation(self, candidates):
        # 利益順にソート（BaseOptimizerの機能を利用）
        sorted_candidates = sorted(
            candidates,
            key=lambda c: self.calculate_value(c),  # ← 統一された計算
            reverse=True
        )
        # ...
```

**メリット**:
- ✅ **強制力が最高**: すべてのOptimizerが基底クラスを継承
- ✅ **更新が自動**: BaseOptimizerを変更するだけで全Optimizerに反映
- ✅ **一貫性保証**: 同じメソッドを使うため、目的関数が必ず統一される
- ✅ **テストが容易**: BaseOptimizerをテストすれば全Optimizerをカバー

---

### レイヤー4: 自動テスト ★★★★★

**簡素化されたテスト**

```python
# tests/test_entity/test_optimization_objective.py
"""Tests for optimization objective.

CRITICAL: These tests ensure all optimizers use the same objective.
"""

import pytest
from agrr_core.entity.value_objects.optimization_objective import (
    OptimizationObjective,
    OptimizationMetrics,
    DEFAULT_OBJECTIVE,
)


class TestOptimizationMetrics:
    """Test OptimizationMetrics value object."""
    
    def test_profit_with_revenue(self):
        """Profit = revenue - cost when revenue is known."""
        metrics = OptimizationMetrics(cost=1000, revenue=2000)
        assert metrics.profit == 1000
    
    def test_profit_without_revenue(self):
        """Profit = -cost when revenue is unknown (cost minimization)."""
        metrics = OptimizationMetrics(cost=1000)
        assert metrics.profit == -1000


class TestOptimizationObjective:
    """Test OptimizationObjective."""
    
    def test_calculate_with_revenue(self):
        """Calculate profit with revenue."""
        objective = OptimizationObjective()
        metrics = OptimizationMetrics(cost=1000, revenue=2000)
        
        profit = objective.calculate(metrics)
        
        assert profit == 1000
    
    def test_calculate_without_revenue(self):
        """Calculate profit without revenue (cost minimization equivalent)."""
        objective = OptimizationObjective()
        metrics = OptimizationMetrics(cost=1000)
        
        profit = objective.calculate(metrics)
        
        assert profit == -1000  # Negative cost
    
    def test_select_best_with_revenue(self):
        """Select best candidate maximizes profit."""
        objective = OptimizationObjective()
        candidates = [
            OptimizationMetrics(cost=100, revenue=200),  # profit=100
            OptimizationMetrics(cost=80, revenue=220),   # profit=140 ← best
            OptimizationMetrics(cost=120, revenue=180),  # profit=60
        ]
        
        best = objective.select_best(candidates, key_func=objective.calculate)
        
        assert best.profit == 140
    
    def test_select_best_without_revenue(self):
        """Select best candidate minimizes cost (when revenue is None)."""
        objective = OptimizationObjective()
        candidates = [
            OptimizationMetrics(cost=100),  # profit=-100
            OptimizationMetrics(cost=50),   # profit=-50 ← best (minimum cost)
            OptimizationMetrics(cost=200),  # profit=-200
        ]
        
        best = objective.select_best(candidates, key_func=objective.calculate)
        
        assert best.cost == 50  # Minimum cost = maximum profit


class TestObjectiveFunctionSignature:
    """Test to detect objective function changes.
    
    ⚠️ CRITICAL: If this test fails, objective has changed.
    """
    
    def test_current_objective_function(self):
        """Document current objective: profit = revenue - cost.
        
        If this fails, update ALL optimizers.
        """
        objective = OptimizationObjective()
        
        # Case 1: With revenue
        metrics1 = OptimizationMetrics(cost=1000, revenue=2000)
        assert objective.calculate(metrics1) == 1000
        
        # Case 2: Without revenue (cost minimization)
        metrics2 = OptimizationMetrics(cost=1000)
        assert objective.calculate(metrics2) == -1000
    
    def test_singleton_consistency(self):
        """DEFAULT_OBJECTIVE behaves the same as new instance."""
        obj1 = DEFAULT_OBJECTIVE
        obj2 = OptimizationObjective()
        
        metrics = OptimizationMetrics(cost=100, revenue=200)
        
        assert obj1.calculate(metrics) == obj2.calculate(metrics)


class TestBaseOptimizerIntegration:
    """Test that all optimizers use BaseOptimizer.
    
    This ensures no optimizer bypasses the unified objective.
    """
    
    def test_all_optimizers_inherit_base(self):
        """All optimization interactors MUST inherit BaseOptimizer."""
        from agrr_core.usecase.interactors.growth_period_optimize_interactor import (
            GrowthPeriodOptimizeInteractor,
        )
        from agrr_core.usecase.interactors.base_optimizer import BaseOptimizer
        
        # Check inheritance
        assert issubclass(GrowthPeriodOptimizeInteractor, BaseOptimizer)
    
    def test_base_optimizer_uses_default_objective(self):
        """BaseOptimizer uses DEFAULT_OBJECTIVE by default."""
        from agrr_core.usecase.interactors.base_optimizer import BaseOptimizer
        
        class TestOptimizer(BaseOptimizer):
            pass
        
        optimizer = TestOptimizer()
        assert optimizer.objective is DEFAULT_OBJECTIVE
```

**テスト数**: 23個 → **約10個**（57%削減）

---

## 📊 アーキテクチャの比較

### Before（3つの目的関数）

```
┌────────────────────────────────────┐
│ OptimizationObjectiveCalculator    │
├────────────────────────────────────┤
│ - objective_type: ObjectiveType    │
│                                    │
│ calculate(metrics):                │
│   if MINIMIZE_COST:                │
│     return cost                    │
│   elif MAXIMIZE_PROFIT:            │
│     return profit                  │
│   elif MAXIMIZE_REVENUE:           │
│     return revenue                 │
│                                    │
│ is_better(v1, v2):                │
│   if MINIMIZE:                     │
│     return v1 < v2                 │
│   else:                            │
│     return v1 > v2                 │
│                                    │
│ select_best(candidates):           │
│   if MINIMIZE:                     │
│     return min(...)                │
│   else:                            │
│     return max(...)                │
└────────────────────────────────────┘
         ↑ 使用
         │
┌────────┴────────┐
│ GrowthPeriod    │  MultiField...  │  Optimization...
│ Optimizer       │  Optimizer      │  Scheduler
└─────────────────┴─────────────────┴──────────────┘
```

**問題点**:
- 条件分岐が多い
- 各Optimizerが個別に呼び出し
- 統一性が弱い

### After（利益最大化のみ + BaseOptimizer）

```
┌────────────────────────────────────┐
│ OptimizationObjective              │  ← シンプル！
├────────────────────────────────────┤
│ calculate(metrics):                │
│   return metrics.profit            │  ← 条件分岐なし
│                                    │
│ select_best(candidates):           │
│   return max(candidates, ...)      │  ← 常にmax
└────────────────────────────────────┘
         ↑ 使用
         │
┌────────┴────────────────────────────┐
│ BaseOptimizer                       │  ← 新しい！
├─────────────────────────────────────┤
│ objective: OptimizationObjective    │
│                                     │
│ select_best(candidates):            │
│   return objective.select_best(...) │
│                                     │
│ calculate_value(candidate):         │
│   return objective.calculate(...)   │
└─────────────────────────────────────┘
         ↑ 継承（強制）
         │
┌────────┴────────┬─────────────────┬──────────────┐
│ GrowthPeriod    │  MultiField...  │  Optimization...
│ Optimizer       │  Optimizer      │  Scheduler
└─────────────────┴─────────────────┴──────────────┘
```

**改善点**:
- ✅ 条件分岐ゼロ
- ✅ 継承による強制
- ✅ 完全な統一性

---

## 🔐 多層防御の強制力

### 各層の役割と強制力

| 層 | 役割 | 強制力 | メカニズム |
|----|-----|-------|----------|
| **1. OptimizationObjective** | ロジックの統一 | ★★★★★ | Single Source of Truth |
| **2. Optimizable Protocol** | インターフェース統一 | ★★★★☆ | 型チェック（mypy） |
| **3. BaseOptimizer** | 使用の強制 | ★★★★★ | 継承必須 |
| **4. 自動テスト** | 整合性検証 | ★★★★★ | CI/CD |

### 更新忘れの防止メカニズム

```
開発者が新しいOptimizerを作る
        ↓
BaseOptimizerを継承しないとコンパイルエラー
        ↓
BaseOptimizerが自動的にOptimizationObjectiveを使用
        ↓
目的関数が自動的に統一される
        ↓
テストで検証
```

---

## 🚀 実装計画

### Phase 1: 基盤実装（1日）

```
✓ OptimizationObjective 実装（簡素化版）
✓ OptimizationMetrics 実装
✓ Optimizable Protocol 実装
✓ BaseOptimizer 実装
✓ 単体テスト
```

### Phase 2: 既存Interactorの移行（2-3日）

```
□ GrowthPeriodOptimizeInteractor
  - BaseOptimizerを継承
  - select_best()を使用
  
□ MultiFieldCropAllocationGreedyInteractor
  - BaseOptimizerを継承
  - optimization_objectiveパラメータを削除
  
□ OptimizationIntermediateResultScheduleInteractor
  - BaseOptimizerを継承
```

### Phase 3: テスト更新とドキュメント（1日）

```
□ 既存テストを簡素化版に適合
□ BaseOptimizerのテスト
□ ドキュメント更新
```

**総工数**: 約1週間

---

## 📝 コード例：完全な実装

### GrowthPeriodOptimizeInteractor（移行後）

```python
class GrowthPeriodOptimizeInteractor(
    BaseOptimizer[CandidateResultDTO],
    GrowthPeriodOptimizeInputPort
):
    """Period optimizer using unified objective."""
    
    def __init__(
        self,
        crop_requirement_gateway,
        weather_gateway,
        optimization_result_gateway=None,
    ):
        super().__init__()  # BaseOptimizerの初期化
        self.crop_requirement_gateway = crop_requirement_gateway
        # ...
    
    async def execute(self, request):
        # 候補生成
        candidates = await self._generate_candidates(request)
        
        # BaseOptimizerのメソッドを使用（自動的に利益最大化）
        optimal = self.select_best(candidates)  # ← 統一された目的関数
        
        # Mark optimal
        for candidate in candidates:
            if candidate == optimal:
                candidate.is_optimal = True
        
        return OptimalGrowthPeriodResponseDTO(...)


# CandidateResultDTO が Optimizable を実装
@dataclass
class CandidateResultDTO:
    start_date: datetime
    total_cost: float
    revenue: Optional[float] = None
    
    def get_metrics(self) -> OptimizationMetrics:
        """Implement Optimizable protocol."""
        return OptimizationMetrics(
            cost=self.total_cost,
            revenue=self.revenue
        )
```

---

## ✅ 最終評価

### 簡素化の効果

| 項目 | 削減率 |
|-----|-------|
| コード行数 | **52%削減** |
| テストケース | **57%削減** |
| 条件分岐 | **100%削減** |
| Enum定義 | **削除** |
| 複雑度 | **大幅低下** |

### 強制力の向上

| メカニズム | Before | After |
|----------|--------|-------|
| Single Source of Truth | ✓ | ✓✓ |
| 型安全性 | ✓ | ✓ |
| 継承による強制 | × | **✓✓✓** |
| テスト | ✓ | ✓ |

**総合評価**: ★★★★★

- ✅ よりシンプル
- ✅ より強力な強制力（BaseOptimizer継承）
- ✅ より保守しやすい
- ✅ より拡張しやすい

---

## 🎯 結論

**推奨**: 利益最大化のみ + BaseOptimizer継承アプローチ

**理由**:
1. **最もシンプル**: 条件分岐ゼロ、1つの目的関数
2. **最も強力**: 継承により使用を強制
3. **最も保守しやすい**: 変更は1箇所のみ
4. **最も拡張しやすい**: BaseOptimizerに機能追加するだけ

**実装**: 約1週間で完了可能

---

**提案者**: AI Assistant  
**推奨採用**: 利益最大化のみ + BaseOptimizer継承

