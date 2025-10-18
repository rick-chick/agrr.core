# テストカバレッジギャップ分析

## 調査結果

ユーザーの懸念は**正当**です。プライベートメソッドテストを削除すると、単体テストレベルでカバレッジにギャップが生じます。

---

## 現状のカバレッジ

### ✅ カバーされている機能

#### 1. OptimizationMetrics の基本機能（33件 - 全てパス）

**test_entity/test_optimization_objective.py:**
```
✅ test_metrics_with_cost_only
✅ test_metrics_with_cost_and_revenue
✅ test_profit_property_with_revenue
✅ test_max_revenue_constraint
✅ TestYieldFactorImpact (7件) - yield_factor の影響
✅ TestSoilRecoveryFactor (7件) - soil_recovery_factor の影響
```

### ❌ カバーされていない機能（単体テストレベル）

#### 1. OptimizationMetrics.calculate_interaction_impact() - **テストなし**

**公開メソッドだが単体テストが存在しない:**
```python
@staticmethod
def calculate_interaction_impact(
    crop: 'Crop',
    field: 'Field',
    start_date,
    field_schedules: dict,
    interaction_rules: Optional[List['InteractionRule']] = None
) -> float:
    """連作障害等の相互作用影響を計算（公開メソッド）"""
```

**現在のカバレッジ:**
- ❌ 単体テスト: なし
- ✅ 統合テスト: `test_with_interaction_rules`（ただし時間がかかる）

**ギャップ:** 🔴 **単体テストレベルでカバーされていない**

#### 2. OptimizationMetrics.calculate_crop_cumulative_revenue() - **テストなし**

**公開メソッドだが単体テストが存在しない:**
```python
@staticmethod
def calculate_crop_cumulative_revenue(
    crop_id: str, 
    current_allocations: List['CropAllocation']
) -> float:
    """作物の累積収益を計算（公開メソッド）"""
```

**現在のカバレッジ:**
- ❌ 単体テスト: なし
- ✅ DPテスト: 間接的にカバー
- ✅ 統合テスト: 間接的にカバー

**ギャップ:** 🟡 **単体テストレベルで明示的にテストされていない**

#### 3. OptimizationMetrics.calculate_soil_recovery_factor() - **テストなし**

**公開メソッド:**
```python
@staticmethod
def calculate_soil_recovery_factor(
    field: 'Field',
    start_date,
    field_schedules: dict,
    planning_start_date = None
) -> float:
    """休閑期間ボーナスを計算（公開メソッド）"""
```

**現在のカバレッジ:**
- ❌ 単体テスト: なし
- ✅ 統合テスト: 間接的にカバー

**ギャップ:** 🟡 **単体テストレベルで明示的にテストされていない**

---

## カバレッジギャップのまとめ

| 機能 | 公開メソッド | 単体テスト | 統合テスト | ギャップ |
|------|------------|-----------|-----------|---------|
| **基本的な収益・コスト計算** | OptimizationMetrics | ✅ 33件 | ✅ | なし |
| **連作障害（interaction_impact）** | `calculate_interaction_impact()` | ❌ **なし** | ✅ | 🔴 **大** |
| **市場需要制限（cumulative_revenue）** | `calculate_crop_cumulative_revenue()` | ❌ **なし** | ✅ | 🟡 中 |
| **休閑期間ボーナス（soil_recovery）** | `calculate_soil_recovery_factor()` | ❌ **なし** | ✅ | 🟡 中 |

---

## 解決策: 公開メソッドの単体テストを追加

### ✅ 正しいアプローチ

プライベートメソッドではなく、**公開メソッド**をテストします：

```python
# ❌ 削除: プライベートメソッドのテスト
def test_get_previous_crop():
    result = interactor._get_previous_crop(...)  # プライベート

# ❌ 削除: プライベートメソッドのテスト
def test_apply_interaction_rules():
    result = interactor._apply_interaction_rules(...)  # プライベート

# ✅ 追加: 公開メソッドのテスト
def test_calculate_interaction_impact():
    impact = OptimizationMetrics.calculate_interaction_impact(
        crop=tomato,
        field=field,
        start_date=datetime(2025, 9, 1),
        field_schedules={"f1": [previous_allocation]},
        interaction_rules=[continuous_cultivation_rule]
    )
    assert impact == 0.7  # 30%ペナルティ
```

---

## 新規テストの提案

### test_entity/test_optimization_metrics_interaction.py (新規)

```python
"""OptimizationMetrics の相互作用計算に関する単体テスト"""

import pytest
from datetime import datetime
from agrr_core.entity.value_objects.optimization_objective import OptimizationMetrics
from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.entity.entities.interaction_rule_entity import InteractionRule
from agrr_core.entity.value_objects.rule_type import RuleType


class TestCalculateInteractionImpact:
    """Test OptimizationMetrics.calculate_interaction_impact() static method."""
    
    def test_no_previous_crop_returns_default_impact(self):
        """前作物がない場合、デフォルトの影響（1.0）を返す"""
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        crop = Crop("tomato", "Tomato", 0.5, groups=["Solanaceae"])
        
        impact = OptimizationMetrics.calculate_interaction_impact(
            crop=crop,
            field=field,
            start_date=datetime(2025, 4, 1),
            field_schedules={},  # 空 = 前作物なし
            interaction_rules=[]
        )
        
        assert impact == 1.0  # デフォルト（影響なし）
    
    def test_continuous_cultivation_penalty_applied(self):
        """連作障害ペナルティが適用される"""
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        tomato = Crop("tomato", "Tomato", 0.5, groups=["Solanaceae"])
        eggplant = Crop("eggplant", "Eggplant", 0.5, groups=["Solanaceae"])
        
        # 前作物: トマト（Solanaceae）
        previous_allocation = CropAllocation(
            allocation_id="prev",
            field=field,
            crop=tomato,
            area_used=500.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=150,
            accumulated_gdd=2000.0,
            total_cost=750000.0,
            expected_revenue=None,
            profit=None
        )
        
        # 連作障害ルール: Solanaceae → Solanaceae = 30%ペナルティ
        rule = InteractionRule(
            rule_id="rule_001",
            rule_type=RuleType.CONTINUOUS_CULTIVATION,
            source_group="Solanaceae",
            target_group="Solanaceae",
            impact_ratio=0.7,  # 30%減
            is_directional=True
        )
        
        # 現在の作物: ナス（Solanaceae）
        impact = OptimizationMetrics.calculate_interaction_impact(
            crop=eggplant,
            field=field,
            start_date=datetime(2025, 9, 1),  # トマトの後
            field_schedules={"f1": [previous_allocation]},
            interaction_rules=[rule]
        )
        
        assert impact == 0.7  # 30%ペナルティが適用
    
    def test_different_family_no_penalty(self):
        """異なる科の作物では連作障害が発生しない"""
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        tomato = Crop("tomato", "Tomato", 0.5, groups=["Solanaceae"])
        soybean = Crop("soybean", "Soybean", 0.15, groups=["Fabaceae"])
        
        # 前作物: トマト（Solanaceae）
        previous_allocation = CropAllocation(
            allocation_id="prev",
            field=field,
            crop=tomato,
            area_used=500.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=150,
            accumulated_gdd=2000.0,
            total_cost=750000.0,
            expected_revenue=None,
            profit=None
        )
        
        # 連作障害ルール: Solanaceae → Solanaceae
        rule = InteractionRule(
            rule_id="rule_001",
            rule_type=RuleType.CONTINUOUS_CULTIVATION,
            source_group="Solanaceae",
            target_group="Solanaceae",
            impact_ratio=0.7,
            is_directional=True
        )
        
        # 現在の作物: 大豆（Fabaceae - 異なる科）
        impact = OptimizationMetrics.calculate_interaction_impact(
            crop=soybean,
            field=field,
            start_date=datetime(2025, 9, 1),
            field_schedules={"f1": [previous_allocation]},
            interaction_rules=[rule]
        )
        
        assert impact == 1.0  # ペナルティなし（異なる科）
    
    def test_beneficial_rotation(self):
        """有益な輪作でボーナスが適用される"""
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        soybean = Crop("soybean", "Soybean", 0.15, groups=["Fabaceae"])
        rice = Crop("rice", "Rice", 0.25, groups=["Poaceae"])
        
        # 前作物: 大豆（Fabaceae）
        previous_allocation = CropAllocation(
            allocation_id="prev",
            field=field,
            crop=soybean,
            area_used=500.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=150,
            accumulated_gdd=2000.0,
            total_cost=750000.0,
            expected_revenue=None,
            profit=None
        )
        
        # 有益な輪作ルール: Fabaceae → Poaceae = 10%ボーナス
        rule = InteractionRule(
            rule_id="rule_002",
            rule_type=RuleType.BENEFICIAL_ROTATION,
            source_group="Fabaceae",
            target_group="Poaceae",
            impact_ratio=1.1,  # 10%増
            is_directional=True
        )
        
        # 現在の作物: 米（Poaceae）
        impact = OptimizationMetrics.calculate_interaction_impact(
            crop=rice,
            field=field,
            start_date=datetime(2025, 9, 1),
            field_schedules={"f1": [previous_allocation]},
            interaction_rules=[rule]
        )
        
        assert impact == 1.1  # 10%ボーナス
    
    def test_no_rules_provided_returns_default(self):
        """ルールが提供されない場合、デフォルト（1.0）を返す"""
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        tomato = Crop("tomato", "Tomato", 0.5, groups=["Solanaceae"])
        
        previous_allocation = CropAllocation(
            allocation_id="prev",
            field=field,
            crop=tomato,
            area_used=500.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=150,
            accumulated_gdd=2000.0,
            total_cost=750000.0,
            expected_revenue=None,
            profit=None
        )
        
        impact = OptimizationMetrics.calculate_interaction_impact(
            crop=tomato,
            field=field,
            start_date=datetime(2025, 9, 1),
            field_schedules={"f1": [previous_allocation]},
            interaction_rules=None  # ルールなし
        )
        
        assert impact == 1.0  # ルールなし = 影響なし


class TestCalculateCropCumulativeRevenue:
    """Test OptimizationMetrics.calculate_crop_cumulative_revenue() static method."""
    
    def test_no_allocations_returns_zero(self):
        """割り当てがない場合、0を返す"""
        cumulative = OptimizationMetrics.calculate_crop_cumulative_revenue(
            crop_id="tomato",
            current_allocations=[]
        )
        
        assert cumulative == 0.0
    
    def test_single_allocation_returns_revenue(self):
        """1つの割り当ての収益を返す"""
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        tomato = Crop("tomato", "Tomato", 0.5, revenue_per_area=50000.0)
        
        allocation = CropAllocation(
            allocation_id="a1",
            field=field,
            crop=tomato,
            area_used=500.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=150,
            accumulated_gdd=2000.0,
            total_cost=750000.0,
            expected_revenue=25000000.0,
            profit=24250000.0
        )
        
        cumulative = OptimizationMetrics.calculate_crop_cumulative_revenue(
            crop_id="tomato",
            current_allocations=[allocation]
        )
        
        assert cumulative == 25000000.0
    
    def test_multiple_allocations_sums_revenue(self):
        """複数の割り当ての収益を合計する"""
        field1 = Field("f1", "Field 1", 1000.0, 5000.0)
        field2 = Field("f2", "Field 2", 800.0, 4000.0)
        tomato = Crop("tomato", "Tomato", 0.5, revenue_per_area=50000.0)
        
        alloc1 = CropAllocation(
            allocation_id="a1",
            field=field1,
            crop=tomato,
            area_used=500.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=150,
            accumulated_gdd=2000.0,
            total_cost=750000.0,
            expected_revenue=25000000.0,
            profit=24250000.0
        )
        
        alloc2 = CropAllocation(
            allocation_id="a2",
            field=field2,
            crop=tomato,
            area_used=400.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=150,
            accumulated_gdd=2000.0,
            total_cost=600000.0,
            expected_revenue=20000000.0,
            profit=19400000.0
        )
        
        cumulative = OptimizationMetrics.calculate_crop_cumulative_revenue(
            crop_id="tomato",
            current_allocations=[alloc1, alloc2]
        )
        
        assert cumulative == 45000000.0  # 25M + 20M
    
    def test_different_crop_not_counted(self):
        """異なる作物の収益はカウントされない"""
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        tomato = Crop("tomato", "Tomato", 0.5, revenue_per_area=50000.0)
        rice = Crop("rice", "Rice", 0.25, revenue_per_area=30000.0)
        
        tomato_alloc = CropAllocation(
            allocation_id="a1",
            field=field,
            crop=tomato,
            area_used=500.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=150,
            accumulated_gdd=2000.0,
            total_cost=750000.0,
            expected_revenue=25000000.0,
            profit=24250000.0
        )
        
        rice_alloc = CropAllocation(
            allocation_id="a2",
            field=field,
            crop=rice,
            area_used=500.0,
            start_date=datetime(2025, 9, 1),
            completion_date=datetime(2026, 1, 31),
            growth_days=150,
            accumulated_gdd=1800.0,
            total_cost=750000.0,
            expected_revenue=15000000.0,
            profit=14250000.0
        )
        
        # トマトの累積収益（米は含まれない）
        cumulative = OptimizationMetrics.calculate_crop_cumulative_revenue(
            crop_id="tomato",
            current_allocations=[tomato_alloc, rice_alloc]
        )
        
        assert cumulative == 25000000.0  # トマトのみ
```

---

## 修正された推奨アクション

### Phase 1: プライベートメソッドテストを削除 (5分) ✂️

**削除: 8件**（11件から3件は修正に変更）

- `test_continuous_cultivation_impact.py` - TestInteractionRuleServiceIntegration (5件) ❌
- `test_multi_field_crop_allocation_dp.py` - TestDPAllocation (3件) ❌
- `test_multi_field_crop_allocation_dp.py` - TestEnforceMaxRevenueConstraint (3件) ❌

**修正: 3件**（削除ではなく修正）

- `test_continuous_cultivation_impact.py` - TestAllocationCandidateWithInteractionImpact (3件) 🔧
  - これは `AllocationCandidate.get_metrics()` の単体テスト
  - 公開メソッドなので適切

### Phase 2: 公開メソッドの単体テストを追加 (45分-1時間) ➕

**新規ファイル: `test_entity/test_optimization_metrics_interaction.py`**

```python
TestCalculateInteractionImpact (5-7件):
  ✅ test_no_previous_crop_returns_default_impact
  ✅ test_continuous_cultivation_penalty_applied
  ✅ test_different_family_no_penalty
  ✅ test_beneficial_rotation
  ✅ test_no_rules_provided_returns_default
  ✅ test_multiple_rules_applied_in_order
  ✅ test_non_directional_rule_applies_both_ways

TestCalculateCropCumulativeRevenue (4-5件):
  ✅ test_no_allocations_returns_zero
  ✅ test_single_allocation_returns_revenue
  ✅ test_multiple_allocations_sums_revenue
  ✅ test_different_crop_not_counted
  ✅ test_none_revenue_is_skipped

TestCalculateSoilRecoveryFactor (4-5件):
  ✅ test_no_previous_crop_returns_default
  ✅ test_short_fallow_period_small_bonus
  ✅ test_medium_fallow_period_medium_bonus
  ✅ test_long_fallow_period_maximum_bonus
  ✅ test_no_fallow_period_required_returns_one
```

**推定: 15-20件の単体テスト**

### Phase 3: その他のテストを修正 (1-2時間) 🔧

残り9件（DTO修正、実装検証等）

---

## カバレッジ比較

### 削除のみの場合（現在の提案）

```
単体テスト:
  OptimizationMetrics 基本機能: 33件 ✅
  interaction_impact 計算: 0件 ❌
  cumulative_revenue 計算: 0件 ❌
  soil_recovery 計算: 0件 ❌

統合テスト:
  全機能: カバー済み ✅ (ただし時間がかかる)

ギャップ: 🔴 大きい
```

### 削除 + 公開メソッドテスト追加（修正版提案）

```
単体テスト:
  OptimizationMetrics 基本機能: 33件 ✅
  interaction_impact 計算: 5-7件 ✅ ← 追加
  cumulative_revenue 計算: 4-5件 ✅ ← 追加
  soil_recovery 計算: 4-5件 ✅ ← 追加
  AllocationCandidate: 3件 ✅ ← 修正

統合テスト:
  全機能: カバー済み ✅

ギャップ: ✅ なし
```

---

## 最終推奨（修正版）

### ✅ プライベートメソッドテスト8件を削除

**削除対象:**
- `TestInteractionRuleServiceIntegration` (5件) - インターフェースに依存
- `TestDPAllocation` (3件) - プライベートメソッド `_dp_allocation()`
- `TestEnforceMaxRevenueConstraint` (3件) - 削除されたメソッド

### 🔧 AllocationCandidateテスト3件を修正

**修正対象:**
- `test_candidate_with_no_impact`
- `test_candidate_with_continuous_cultivation_penalty`
- `test_candidate_with_max_revenue_limit_and_impact`

**理由:** これらは公開メソッド `get_metrics()` のテストなので適切

### ➕ OptimizationMetrics の公開メソッドテストを追加

**新規ファイル:** `test_entity/test_optimization_metrics_interaction.py`

**追加テスト:** 15-20件
- `TestCalculateInteractionImpact` (5-7件)
- `TestCalculateCropCumulativeRevenue` (4-5件)
- `TestCalculateSoilRecoveryFactor` (4-5件)

---

## 結論

**機能カバレッジは維持されます** ✅

**方法:**
1. ❌ プライベートメソッドテスト8件を削除
2. 🔧 AllocationCandidateテスト3件を修正（公開メソッドなので適切）
3. ➕ OptimizationMetricsの公開メソッドテスト15-20件を追加

**メリット:**
- ✅ 単体テストレベルでカバレッジを確保（統合テストに頼らない）
- ✅ Clean Architecture準拠（公開APIのみテスト）
- ✅ テストの実行時間が短い（単体テスト）
- ✅ リファクタリングに強い

**推定作業時間:** 2-3時間
- 削除: 5分
- AllocationCandidate修正: 30-45分
- OptimizationMetrics追加: 1-1.5時間
- その他修正: 30分-1時間

作業しますか？

