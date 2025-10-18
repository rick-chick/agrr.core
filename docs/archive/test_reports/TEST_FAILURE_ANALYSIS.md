# テスト失敗分析: Remove unused revenue/profit calculations

## 概要

コミット `e31238f` (refactor: Remove unused revenue/profit calculations from neighbor operations) および関連する一連のリファクタリングによって、20個のテストが失敗し、11個のエラーが発生しています。

## 変更の背景

### 主要な変更点

1. **利益計算の統一** (コミット `af522b9`)
   - すべての利益計算を `OptimizationMetrics` クラスに統一
   - `AllocationCandidate` から `previous_crop` と `interaction_impact` パラメータを削除
   - `get_metrics()` メソッドに `field_schedules` と `interaction_rules` をオプションパラメータとして追加
   - `OptimizationMetrics.create_for_allocation()` ファクトリメソッドを追加

2. **近傍操作の不要な計算削除** (コミット `e31238f`)
   - 近傍操作で計算される revenue と profit の値は、すぐに `OptimizationMetrics.recalculate_allocations_with_context()` で上書きされていた
   - これらの不完全な計算を削除し、None を設定するように変更
   - 以下の要素が考慮されていなかった:
     - soil_recovery_factor (休閑期間ボーナス)
     - interaction_impact (連作障害ペナルティ)
     - yield_factor (温度ストレス)
     - max_revenue (市場需要制限)

3. **OptimizationConfig の変更**
   - `alns_initial_temp` パラメータの削除
   - `alns_cooling_rate` パラメータの削除
   - 残されたパラメータ: `enable_alns`, `alns_iterations`, `alns_removal_rate`

## 失敗しているテスト

### 1. AllocationCandidate インターフェース変更関連 (20件)

#### test_continuous_cultivation_impact.py (8件)
- `test_candidate_with_no_impact`
- `test_candidate_with_continuous_cultivation_penalty`
- `test_candidate_with_max_revenue_limit_and_impact`
- `test_get_previous_crop_no_allocations`
- `test_get_previous_crop_with_prior_allocation`
- `test_apply_interaction_rules_no_previous_crop`
- `test_apply_interaction_rules_continuous_cultivation_detected`
- `test_apply_interaction_rules_no_continuous_cultivation`

**問題点:**
```python
# 旧インターフェース (削除された)
candidate = AllocationCandidate(
    field=field,
    crop=crop,
    start_date=...,
    completion_date=...,
    growth_days=...,
    accumulated_gdd=...,
    area_used=...,
    previous_crop=previous_crop,  # ❌ 削除されたパラメータ
    interaction_impact=0.7  # ❌ 削除されたパラメータ
)
```

**修正方針:**
```python
# 新インターフェース
candidate = AllocationCandidate(
    field=field,
    crop=crop,
    start_date=...,
    completion_date=...,
    growth_days=...,
    accumulated_gdd=...,
    area_used=...,
)

# コンテキストを含めてメトリクスを取得
metrics = candidate.get_metrics(
    current_allocations=[...],  # 市場需要追跡用
    field_schedules={field_id: [allocations]},  # 相互作用ルール用
    interaction_rules=[...]  # 連作障害ルール
)
```

#### test_field_dto_to_interactor_response.py (4件)
- `test_response_dto_contains_field_and_costs`
- `test_response_dto_cost_consistency`
- `test_field_entity_unchanged_during_flow`
- `test_zero_cost_field_flows_correctly`

**問題点:** 同様の `AllocationCandidate` インターフェース変更

#### test_multi_field_crop_allocation_dp.py (7件)
- `test_dp_allocation_single_field_no_constraints`
- `test_dp_allocation_max_revenue_constraint`
- `test_dp_allocation_multiple_fields`
- `test_no_constraint`
- `test_constraint_satisfied`
- `test_constraint_violated_removes_low_profit_rate`

**問題点:** DP アルゴリズムのテストが `revenue` と `profit` の直接計算を期待している

#### test_multi_field_crop_allocation_complete.py (1件)
- `test_crop_insert_adds_new_allocation`

**問題点:** 近傍操作のテストが古いインターフェースを使用

#### test_multi_field_crop_allocation_swap_operation.py (1件)
- `test_swap_with_area_adjustment_basic`

**問題点:** swap操作のテストが古いインターフェースを使用

### 2. OptimizationConfig インターフェース変更関連 (11件エラー)

#### test_alns_optimizer.py (11件)
- `test_initialization`
- `test_random_removal`
- `test_worst_removal`
- `test_field_removal_empty_solution`
- `test_time_slice_removal`
- `test_greedy_insert`
- `test_greedy_insert_with_overlap`
- `test_calculate_profit`
- `test_is_feasible_to_add_non_overlapping`
- `test_is_feasible_to_add_overlapping`
- `test_calculate_relatedness`

**問題点:**
```python
# 旧インターフェース (削除されたパラメータ)
config = OptimizationConfig(
    enable_alns=True,
    alns_iterations=10,
    alns_initial_temp=1000.0,  # ❌ 削除された
    alns_cooling_rate=0.95,  # ❌ 削除された
    alns_removal_rate=0.3,
)
```

**修正方針:**
```python
# 新インターフェース
config = OptimizationConfig(
    enable_alns=True,
    alns_iterations=10,
    alns_removal_rate=0.3,
)
```

## 修正の必要性

これらのテストは、旧インターフェースに基づいているため、新しい設計に合わせて更新する必要があります。

### テスト修正の優先順位

1. **高優先度:** `test_alns_optimizer.py` (11件エラー)
   - `OptimizationConfig` のパラメータ削除に対応
   - 比較的簡単な修正

2. **中優先度:** `test_continuous_cultivation_impact.py` (8件)
   - `AllocationCandidate` インターフェース変更に対応
   - 相互作用ルールのテストロジックを再設計

3. **中優先度:** `test_multi_field_crop_allocation_dp.py` (7件)
   - DP アルゴリズムのテストを新しいメトリクス計算方法に対応

4. **低優先度:** その他 (5件)
   - 個別のテストケースの修正

## 新しい設計の利点

1. **単一責任の原則:** すべての利益計算が `OptimizationMetrics` に集約
2. **完全な計算:** すべての要素を考慮した正確な計算
   - soil_recovery_factor
   - interaction_impact
   - yield_factor
   - max_revenue
3. **コード削減:** 不要な重複計算を削除 (~24行削減)
4. **保守性の向上:** 計算ロジックが一箇所に集約

## 次のステップ

1. 各テストファイルを新しいインターフェースに合わせて修正
2. テストが新しい設計の意図を正しく検証していることを確認
3. 必要に応じて、テストの目的を再評価

## テスト実行結果

```
20 failed, 897 passed, 2 skipped, 46 deselected, 11 errors
```

合計930テストのうち:
- ✅ 成功: 897 (96.5%)
- ❌ 失敗: 20 (2.2%)
- ⚠️  エラー: 11 (1.2%)
- ⏭️  スキップ: 2 (0.2%)

