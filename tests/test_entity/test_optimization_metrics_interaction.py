"""Unit tests for OptimizationMetrics interaction calculation methods.

This test suite verifies the public static methods of OptimizationMetrics class
that calculate various impacts on revenue (interaction, cumulative, soil recovery).

These tests replace the deleted private method tests from multi_field_crop_allocation
by testing the public API directly in the Entity layer.
"""

import pytest
from datetime import datetime, timedelta
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
    
    def test_crop_without_groups_returns_default(self):
        """グループが設定されていない作物はデフォルト（1.0）を返す"""
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        crop_no_group = Crop("custom", "Custom Crop", 0.5, groups=None)
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
        
        rule = InteractionRule(
            rule_id="rule_001",
            rule_type=RuleType.CONTINUOUS_CULTIVATION,
            source_group="Solanaceae",
            target_group="Solanaceae",
            impact_ratio=0.7,
            is_directional=True
        )
        
        impact = OptimizationMetrics.calculate_interaction_impact(
            crop=crop_no_group,  # グループなし
            field=field,
            start_date=datetime(2025, 9, 1),
            field_schedules={"f1": [previous_allocation]},
            interaction_rules=[rule]
        )
        
        assert impact == 1.0  # グループなし = 影響なし


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
    
    def test_none_revenue_allocations_skipped(self):
        """expected_revenueがNoneの割り当てはスキップされる"""
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        tomato = Crop("tomato", "Tomato", 0.5, revenue_per_area=50000.0)
        
        alloc1 = CropAllocation(
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
            profit=None
        )
        
        alloc2 = CropAllocation(
            allocation_id="a2",
            field=field,
            crop=tomato,
            area_used=400.0,
            start_date=datetime(2025, 9, 1),
            completion_date=datetime(2026, 1, 31),
            growth_days=150,
            accumulated_gdd=2000.0,
            total_cost=600000.0,
            expected_revenue=None,  # None
            profit=None
        )
        
        cumulative = OptimizationMetrics.calculate_crop_cumulative_revenue(
            crop_id="tomato",
            current_allocations=[alloc1, alloc2]
        )
        
        assert cumulative == 25000000.0  # alloc1のみカウント


class TestCalculateSoilRecoveryFactor:
    """Test OptimizationMetrics.calculate_soil_recovery_factor() static method."""
    
    def test_no_previous_crop_with_planning_start(self):
        """前作物がなく、計画開始日からの期間で休閑期間ボーナスを計算"""
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=28)
        
        planning_start = datetime(2025, 1, 1)
        start_date = datetime(2025, 3, 1)  # 59日後 (1月31日 + 28日(2月) = 59日)
        
        factor = OptimizationMetrics.calculate_soil_recovery_factor(
            field=field,
            start_date=start_date,
            field_schedules={},  # 前作物なし
            planning_start_date=planning_start
        )
        
        # 59日の休閑期間 → 30-59日カテゴリ → 1.05
        assert factor == 1.05
    
    def test_short_fallow_period_small_bonus(self):
        """短い休閑期間（15-29日）で小さなボーナス"""
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=28)
        tomato = Crop("tomato", "Tomato", 0.5)
        
        # 前作物
        previous_allocation = CropAllocation(
            allocation_id="prev",
            field=field,
            crop=tomato,
            area_used=500.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 6, 30),  # 6月30日完了
            growth_days=90,
            accumulated_gdd=1000.0,
            total_cost=450000.0,
            expected_revenue=None,
            profit=None
        )
        
        # 次の栽培: 7月20日開始 (20日後)
        start_date = datetime(2025, 7, 20)
        
        factor = OptimizationMetrics.calculate_soil_recovery_factor(
            field=field,
            start_date=start_date,
            field_schedules={"f1": [previous_allocation]},
            planning_start_date=datetime(2025, 4, 1)
        )
        
        # 20日の休閑期間 → 15-29日カテゴリ → 1.02
        assert factor == 1.02
    
    def test_medium_fallow_period_medium_bonus(self):
        """中程度の休閑期間（30-59日）で中程度のボーナス"""
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=28)
        tomato = Crop("tomato", "Tomato", 0.5)
        
        previous_allocation = CropAllocation(
            allocation_id="prev",
            field=field,
            crop=tomato,
            area_used=500.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 6, 30),
            growth_days=90,
            accumulated_gdd=1000.0,
            total_cost=450000.0,
            expected_revenue=None,
            profit=None
        )
        
        # 次の栽培: 8月10日開始 (41日後)
        start_date = datetime(2025, 8, 10)
        
        factor = OptimizationMetrics.calculate_soil_recovery_factor(
            field=field,
            start_date=start_date,
            field_schedules={"f1": [previous_allocation]},
            planning_start_date=datetime(2025, 4, 1)
        )
        
        # 41日の休閑期間 → 30-59日カテゴリ → 1.05
        assert factor == 1.05
    
    def test_long_fallow_period_maximum_bonus(self):
        """長い休閑期間（60日以上）で最大ボーナス"""
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=28)
        tomato = Crop("tomato", "Tomato", 0.5)
        
        previous_allocation = CropAllocation(
            allocation_id="prev",
            field=field,
            crop=tomato,
            area_used=500.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 6, 30),
            growth_days=90,
            accumulated_gdd=1000.0,
            total_cost=450000.0,
            expected_revenue=None,
            profit=None
        )
        
        # 次の栽培: 9月10日開始 (72日後)
        start_date = datetime(2025, 9, 10)
        
        factor = OptimizationMetrics.calculate_soil_recovery_factor(
            field=field,
            start_date=start_date,
            field_schedules={"f1": [previous_allocation]},
            planning_start_date=datetime(2025, 4, 1)
        )
        
        # 72日の休閑期間 → 60日以上カテゴリ → 1.10
        assert factor == 1.10
    
    def test_very_short_fallow_period_no_bonus(self):
        """非常に短い休閑期間（0-14日）でボーナスなし"""
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=28)
        tomato = Crop("tomato", "Tomato", 0.5)
        
        previous_allocation = CropAllocation(
            allocation_id="prev",
            field=field,
            crop=tomato,
            area_used=500.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 6, 30),
            growth_days=90,
            accumulated_gdd=1000.0,
            total_cost=450000.0,
            expected_revenue=None,
            profit=None
        )
        
        # 次の栽培: 7月5日開始 (5日後)
        start_date = datetime(2025, 7, 5)
        
        factor = OptimizationMetrics.calculate_soil_recovery_factor(
            field=field,
            start_date=start_date,
            field_schedules={"f1": [previous_allocation]},
            planning_start_date=datetime(2025, 4, 1)
        )
        
        # 5日の休閑期間 → 0-14日カテゴリ → 1.00
        assert factor == 1.00


class TestCreateForAllocation:
    """Test OptimizationMetrics.create_for_allocation() factory method."""
    
    def test_create_with_all_context(self):
        """全てのコンテキストを含めて作成"""
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=28)
        tomato = Crop("tomato", "Tomato", 0.5, revenue_per_area=50000.0, groups=["Solanaceae"])
        eggplant = Crop("eggplant", "Eggplant", 0.5, revenue_per_area=50000.0, groups=["Solanaceae"])
        
        # 前作物
        previous_allocation = CropAllocation(
            allocation_id="prev",
            field=field,
            crop=tomato,
            area_used=500.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 6, 30),
            growth_days=90,
            accumulated_gdd=1000.0,
            total_cost=450000.0,
            expected_revenue=None,
            profit=None
        )
        
        # 連作障害ルール
        rule = InteractionRule(
            rule_id="rule_001",
            rule_type=RuleType.CONTINUOUS_CULTIVATION,
            source_group="Solanaceae",
            target_group="Solanaceae",
            impact_ratio=0.7,
            is_directional=True
        )
        
        # Metricsを作成
        metrics = OptimizationMetrics.create_for_allocation(
            area_used=500.0,
            revenue_per_area=50000.0,
            max_revenue=None,
            growth_days=150,
            daily_fixed_cost=5000.0,
            crop_id="eggplant",
            crop=eggplant,
            field=field,
            start_date=datetime(2025, 8, 1),  # 32日後
            current_allocations=[],
            field_schedules={"f1": [previous_allocation]},
            interaction_rules=[rule],
            planning_start_date=datetime(2025, 4, 1)
        )
        
        # 検証
        assert metrics.interaction_impact == 0.7  # 連作障害
        assert metrics.soil_recovery_factor == 1.05  # 32日休閑期間
        assert metrics.crop_cumulative_revenue == 0.0  # 累積収益なし
        
        # 収益計算: 500 * 50000 * 0.7 * 1.05 = 18,375,000
        expected_revenue = 500.0 * 50000.0 * 0.7 * 1.05
        assert metrics.revenue == pytest.approx(expected_revenue, rel=0.001)
    
    def test_create_without_interaction_rules(self):
        """相互作用ルールなしで作成"""
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        tomato = Crop("tomato", "Tomato", 0.5, revenue_per_area=50000.0)
        
        metrics = OptimizationMetrics.create_for_allocation(
            area_used=500.0,
            revenue_per_area=50000.0,
            max_revenue=None,
            growth_days=150,
            daily_fixed_cost=5000.0,
            crop_id="tomato",
            crop=tomato,
            field=field,
            start_date=datetime(2025, 4, 1),
            current_allocations=[],
            field_schedules={},
            interaction_rules=None,  # ルールなし
        )
        
        assert metrics.interaction_impact == 1.0  # デフォルト
    
    def test_create_with_market_demand_limit(self):
        """市場需要制限を含めて作成"""
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        tomato = Crop("tomato", "Tomato", 0.5, revenue_per_area=50000.0, max_revenue=10000000.0)
        
        # 既存の割り当て（累積収益8M）
        existing_alloc = CropAllocation(
            allocation_id="existing",
            field=field,
            crop=tomato,
            area_used=160.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 6, 30),
            growth_days=90,
            accumulated_gdd=1000.0,
            total_cost=450000.0,
            expected_revenue=8000000.0,
            profit=7550000.0
        )
        
        metrics = OptimizationMetrics.create_for_allocation(
            area_used=500.0,  # これだけで25M稼げるが...
            revenue_per_area=50000.0,
            max_revenue=10000000.0,  # 最大10M
            growth_days=150,
            daily_fixed_cost=5000.0,
            crop_id="tomato",
            crop=tomato,
            field=field,
            start_date=datetime(2025, 7, 1),
            current_allocations=[existing_alloc],  # 既に8M使用済み
            field_schedules={},
            interaction_rules=[],
        )
        
        # 累積収益が計算されている
        assert metrics.crop_cumulative_revenue == 8000000.0
        
        # 収益は残りの容量（2M）に制限される
        # 500 * 50000 * 1.1 (soil) = 27.5M だが、残り容量2Mに制限
        assert metrics.revenue == pytest.approx(2000000.0, rel=0.001)


class TestIntegrationOfAllFactors:
    """Test that all factors (interaction, soil, yield, market) work together."""
    
    def test_all_factors_applied_in_correct_order(self):
        """全ての要素が正しい順序で適用される"""
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=28)
        tomato = Crop("tomato", "Tomato", 0.5, revenue_per_area=50000.0, max_revenue=30000000.0, groups=["Solanaceae"])
        
        # 前作物（トマト）
        previous_allocation = CropAllocation(
            allocation_id="prev",
            field=field,
            crop=tomato,
            area_used=500.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 6, 30),
            growth_days=90,
            accumulated_gdd=1000.0,
            total_cost=450000.0,
            expected_revenue=None,
            profit=None
        )
        
        # 連作障害ルール
        rule = InteractionRule(
            rule_id="rule_001",
            rule_type=RuleType.CONTINUOUS_CULTIVATION,
            source_group="Solanaceae",
            target_group="Solanaceae",
            impact_ratio=0.8,  # 20%ペナルティ
            is_directional=True
        )
        
        # 現在の栽培（トマト - 連作）
        metrics = OptimizationMetrics.create_for_allocation(
            area_used=500.0,
            revenue_per_area=50000.0,
            max_revenue=30000000.0,
            growth_days=150,
            daily_fixed_cost=5000.0,
            crop_id="tomato",
            crop=tomato,
            field=field,
            start_date=datetime(2025, 8, 1),  # 32日後
            current_allocations=[],
            field_schedules={"f1": [previous_allocation]},
            interaction_rules=[rule],
            yield_factor=0.95,  # 5%の温度ストレス
            planning_start_date=datetime(2025, 4, 1)
        )
        
        # 計算順序の検証:
        # 1. Base: 500 * 50000 = 25,000,000
        # 2. × yield_factor (0.95) = 23,750,000
        # 3. × interaction_impact (0.8) = 19,000,000
        # 4. × soil_recovery_factor (1.05, 32日休閑) = 19,950,000
        # 5. max_revenue: min(19,950,000, 30,000,000) = 19,950,000
        
        assert metrics.yield_factor == 0.95
        assert metrics.interaction_impact == 0.8
        assert metrics.soil_recovery_factor == 1.05
        
        expected_revenue = 500.0 * 50000.0 * 0.95 * 0.8 * 1.05
        assert metrics.revenue == pytest.approx(expected_revenue, rel=0.001)

