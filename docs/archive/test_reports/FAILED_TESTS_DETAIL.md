# 失敗テスト詳細リスト

## 実行サマリー

```
pytest実行結果: 20 failed, 897 passed, 2 skipped, 46 deselected, 11 errors in 22.08s
```

- ✅ **成功:** 897/930 (96.5%)
- ❌ **失敗:** 20/930 (2.2%)
- ⚠️  **エラー:** 11/930 (1.2%)
- ⏭️  **スキップ:** 2/930 (0.2%)

---

## エラー (11件)

### tests/test_unit/test_alns_optimizer.py

すべてのテストが `OptimizationConfig` の初期化エラーで失敗:

```
TypeError: OptimizationConfig.__init__() got an unexpected keyword argument 'alns_initial_temp'
```

| # | テスト名 | エラー内容 | 修正内容 |
|---|----------|------------|----------|
| 1 | `test_initialization` | `alns_initial_temp` パラメータが存在しない | fixtureから削除 |
| 2 | `test_random_removal` | 同上 | 同上 |
| 3 | `test_worst_removal` | 同上 | 同上 |
| 4 | `test_field_removal_empty_solution` | 同上 | 同上 |
| 5 | `test_time_slice_removal` | 同上 | 同上 |
| 6 | `test_greedy_insert` | 同上 | 同上 |
| 7 | `test_greedy_insert_with_overlap` | 同上 | 同上 |
| 8 | `test_calculate_profit` | 同上 | 同上 |
| 9 | `test_is_feasible_to_add_non_overlapping` | 同上 | 同上 |
| 10 | `test_is_feasible_to_add_overlapping` | 同上 | 同上 |
| 11 | `test_calculate_relatedness` | 同上 | 同上 |

**修正箇所:**
- ファイル: `tests/test_unit/test_alns_optimizer.py`
- 行: 186-192 (fixture `config`)

**修正前:**
```python
@pytest.fixture
def config(self):
    """Create test configuration."""
    return OptimizationConfig(
        enable_alns=True,
        alns_iterations=10,
        alns_initial_temp=1000.0,  # ❌ 削除
        alns_cooling_rate=0.95,  # ❌ 削除
        alns_removal_rate=0.3,
    )
```

**修正後:**
```python
@pytest.fixture
def config(self):
    """Create test configuration."""
    return OptimizationConfig(
        enable_alns=True,
        alns_iterations=10,
        alns_removal_rate=0.3,
    )
```

---

## 失敗 (20件)

### tests/test_usecase/test_continuous_cultivation_impact.py (8件)

すべてのテストが `AllocationCandidate` の初期化エラーで失敗:

```
TypeError: AllocationCandidate.__init__() got an unexpected keyword argument 'previous_crop'
```

| # | テスト名 | エラー行 | 削除されたパラメータ | 修正難易度 |
|---|----------|----------|---------------------|-----------|
| 1 | `test_candidate_with_no_impact` | 40 | `previous_crop`, `interaction_impact` | 中 |
| 2 | `test_candidate_with_continuous_cultivation_penalty` | 64 | 同上 | 中 |
| 3 | `test_candidate_with_max_revenue_limit_and_impact` | 96 | 同上 | 中 |
| 4 | `test_get_previous_crop_no_allocations` | ? | 同上 | 中 |
| 5 | `test_get_previous_crop_with_prior_allocation` | ? | 同上 | 中 |
| 6 | `test_apply_interaction_rules_no_previous_crop` | ? | 同上 | 中 |
| 7 | `test_apply_interaction_rules_continuous_cultivation_detected` | ? | 同上 | 中 |
| 8 | `test_apply_interaction_rules_no_continuous_cultivation` | ? | 同上 | 中 |

**修正方針:**
1. `AllocationCandidate` から `previous_crop` と `interaction_impact` パラメータを削除
2. 前作物の情報を `CropAllocation` として作成
3. `field_schedules` パラメータに設定
4. `InteractionRule` オブジェクトを作成
5. `interaction_rules` パラメータに設定
6. `get_metrics()` メソッドにコンテキストを渡す

**例:**
```python
# 前作物の割り当て
previous_allocation = CropAllocation(
    field_id="f1",
    crop_id="tomato",
    start_date=datetime(2025, 4, 1),
    completion_date=datetime(2025, 8, 31),
    growth_days=150,
    area_used=500.0,
    accumulated_gdd=2000.0,
    expected_revenue=None,
    profit=None
)

# 相互作用ルール
rule = InteractionRule(
    rule_type=RuleType.CONTINUOUS_CULTIVATION,
    crop_family_a="Solanaceae",
    crop_family_b="Solanaceae",
    impact_ratio=0.7,  # 30%ペナルティ
    is_directional=False
)

# 候補作成
candidate = AllocationCandidate(...)

# メトリクス取得
metrics = candidate.get_metrics(
    current_allocations=[],
    field_schedules={"f1": [previous_allocation]},
    interaction_rules=[rule]
)
```

---

### tests/test_usecase/test_field_dto_to_interactor_response.py (4件)

| # | テスト名 | エラー内容 | 修正難易度 |
|---|----------|------------|-----------|
| 1 | `test_response_dto_contains_field_and_costs` | `previous_crop` パラメータエラー | 低 |
| 2 | `test_response_dto_cost_consistency` | 同上 | 低 |
| 3 | `test_field_entity_unchanged_during_flow` | 同上 | 低 |
| 4 | `test_zero_cost_field_flows_correctly` | 同上 | 低 |

**修正方針:**
- `AllocationCandidate` の初期化から `previous_crop` を削除
- 必要に応じて `get_metrics()` にコンテキストを渡す
- シンプルなテストケースなので、パラメータ削除のみで対応可能

---

### tests/test_usecase/test_multi_field_crop_allocation_dp.py (7件)

| # | テスト名 | 問題内容 | 修正難易度 |
|---|----------|----------|-----------|
| 1 | `test_dp_allocation_single_field_no_constraints` | `revenue`/`profit` の直接参照 | 中 |
| 2 | `test_dp_allocation_max_revenue_constraint` | 同上 | 中 |
| 3 | `test_dp_allocation_multiple_fields` | 同上 | 中 |
| 4 | `test_no_constraint` | 同上 | 中 |
| 5 | `test_constraint_satisfied` | 同上 | 中 |
| 6 | `test_constraint_violated_removes_low_profit_rate` | 同上 | 中 |
| 7 | (不明) | 同上 | 中 |

**修正方針:**
1. `candidate.revenue` → `candidate.get_metrics().revenue`
2. `candidate.profit` → `candidate.get_metrics().profit`
3. 必要に応じて `current_allocations` を渡す (市場需要制限テスト用)

**例:**
```python
# 修正前
assert candidate.revenue == expected_revenue
assert candidate.profit == expected_profit

# 修正後
metrics = candidate.get_metrics(
    current_allocations=[],  # または既存の割り当てリスト
    field_schedules={},
    interaction_rules=[]
)
assert metrics.revenue == expected_revenue
assert metrics.profit == expected_profit
```

---

### tests/test_usecase/test_multi_field_crop_allocation_complete.py (1件)

| # | テスト名 | 問題内容 | 修正難易度 |
|---|----------|----------|-----------|
| 1 | `test_crop_insert_adds_new_allocation` | `previous_crop` パラメータエラー | 低 |

**修正方針:**
- `AllocationCandidate` の初期化から `previous_crop` を削除

---

### tests/test_usecase/test_multi_field_crop_allocation_swap_operation.py (1件)

| # | テスト名 | 問題内容 | 修正難易度 |
|---|----------|----------|-----------|
| 1 | `test_swap_with_area_adjustment_basic` | `previous_crop` パラメータエラー | 低 |

**修正方針:**
- `AllocationCandidate` の初期化から `previous_crop` を削除

---

## 修正の優先順位

### 優先度1: すぐ修正可能 (13件)

単純なパラメータ削除で対応可能:

1. **test_alns_optimizer.py (11件)** - fixture修正のみ
2. **test_field_dto_to_interactor_response.py (4件)** - パラメータ削除のみ
3. **test_multi_field_crop_allocation_complete.py (1件)** - パラメータ削除のみ
4. **test_multi_field_crop_allocation_swap_operation.py (1件)** - パラメータ削除のみ

**推定修正時間:** 30分

### 優先度2: 中程度の修正 (15件)

テストロジックの再設計が必要:

1. **test_continuous_cultivation_impact.py (8件)** - コンテキスト設定が必要
2. **test_multi_field_crop_allocation_dp.py (7件)** - メトリクス取得方法の変更

**推定修正時間:** 2-3時間

---

## 修正後の検証

すべてのテストを修正した後、以下を実行して検証:

```bash
# すべてのテストを実行
pytest -v

# 特定のファイルのみ実行
pytest tests/test_unit/test_alns_optimizer.py -v
pytest tests/test_usecase/test_continuous_cultivation_impact.py -v
pytest tests/test_usecase/test_multi_field_crop_allocation_dp.py -v

# カバレッジ付きで実行
pytest --cov=src/agrr_core --cov-report=html
```

---

## 関連ドキュメント

- [TEST_FAILURE_ANALYSIS.md](./TEST_FAILURE_ANALYSIS.md) - 失敗の背景と変更内容
- [TEST_FIX_GUIDE.md](./TEST_FIX_GUIDE.md) - 詳細な修正例とガイド

