# テスト失敗サマリー: Remove unused revenue/profit calculations

## 状況

「Remove unused revenue/profit calculations」リファクタリングによって、**31件のテスト**が失敗しています。

### テスト実行結果

```
pytest実行結果: 20 failed, 897 passed, 2 skipped, 46 deselected, 11 errors in 22.08s
```

- ✅ **成功:** 897/930 (96.5%)
- ❌ **失敗:** 20/930 (2.2%)
- ⚠️  **エラー:** 11/930 (1.2%)

---

## 原因

### 1. AllocationCandidate インターフェース変更

**削除されたパラメータ:**
- `previous_crop: Optional[Crop]`
- `interaction_impact: float`

**理由:**
利益計算を `OptimizationMetrics` クラスに統一し、すべての要素（連作障害、休閑期間、温度ストレス、市場需要制限）を考慮した正確な計算を実現するため。

**影響するテスト:** 20件

### 2. OptimizationConfig パラメータ削除

**削除されたパラメータ:**
- `alns_initial_temp: float`
- `alns_cooling_rate: float`

**理由:**
ALNS実装で焼きなまし法の温度パラメータが不要になったため。

**影響するテスト:** 11件

---

## 失敗テストの内訳

### 優先度1: 簡単な修正 (11件) - 推定30分

**test_alns_optimizer.py (11件エラー)**

すべて同じfixtureを使用しているため、1箇所の修正で全て解決:

```python
# 修正前 (186-192行目)
@pytest.fixture
def config(self):
    return OptimizationConfig(
        enable_alns=True,
        alns_iterations=10,
        alns_initial_temp=1000.0,  # ❌ 削除
        alns_cooling_rate=0.95,  # ❌ 削除
        alns_removal_rate=0.3,
    )

# 修正後
@pytest.fixture
def config(self):
    return OptimizationConfig(
        enable_alns=True,
        alns_iterations=10,
        alns_removal_rate=0.3,
    )
```

### 優先度2: 中程度の修正 (8件) - 推定2-3時間

**test_continuous_cultivation_impact.py (8件失敗)**

連作障害のテストは、コンテキスト情報の設定方法が変更:

```python
# 修正前
candidate = AllocationCandidate(
    field=field,
    crop=crop,
    start_date=datetime(2025, 9, 1),
    completion_date=datetime(2026, 1, 31),
    growth_days=150,
    accumulated_gdd=2000.0,
    area_used=500.0,
    previous_crop=previous_crop,  # ❌ 削除
    interaction_impact=0.7  # ❌ 削除
)
assert candidate.revenue == 17500000.0

# 修正後
# 1. 前作物の割り当てを作成
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

# 2. 相互作用ルールを定義
rule = InteractionRule(
    rule_type=RuleType.CONTINUOUS_CULTIVATION,
    crop_family_a="Solanaceae",
    crop_family_b="Solanaceae",
    impact_ratio=0.7,  # 30%ペナルティ
    is_directional=False
)

# 3. 候補作成（シンプル）
candidate = AllocationCandidate(
    field=field,
    crop=crop,
    start_date=datetime(2025, 9, 1),
    completion_date=datetime(2026, 1, 31),
    growth_days=150,
    accumulated_gdd=2000.0,
    area_used=500.0,
)

# 4. コンテキスト付きでメトリクス取得
metrics = candidate.get_metrics(
    current_allocations=[],
    field_schedules={"f1": [previous_allocation]},
    interaction_rules=[rule]
)
assert metrics.revenue == 17500000.0
```

### 優先度3: その他の修正 (12件) - 推定1-2時間

**test_field_dto_to_interactor_response.py (4件)**
**test_multi_field_crop_allocation_dp.py (7件)**
**test_multi_field_crop_allocation_complete.py (1件)**

主に `previous_crop` パラメータの削除と、`get_metrics()` の使用:

```python
# 修正前
candidate = AllocationCandidate(..., previous_crop=None)
assert candidate.revenue == expected_revenue

# 修正後
candidate = AllocationCandidate(...)
metrics = candidate.get_metrics()
assert metrics.revenue == expected_revenue
```

---

## 修正の利点

このリファクタリングによる改善点:

### 1. **単一責任の原則**
すべての利益計算が `OptimizationMetrics` に集約され、計算ロジックが一箇所に集中。

### 2. **完全な計算**
以下の要素がすべて考慮される:
- ✅ `soil_recovery_factor` - 休閑期間ボーナス
- ✅ `interaction_impact` - 連作障害ペナルティ
- ✅ `yield_factor` - 温度ストレス
- ✅ `max_revenue` - 市場需要制限

旧設計では、これらの一部が考慮されず、不正確な計算になっていた。

### 3. **コード削減**
不要な重複計算コードを約24行削減。

### 4. **保守性向上**
計算ロジックの変更が一箇所で済むため、メンテナンスが容易。

---

## 修正手順

### ステップ1: 優先度1のテストを修正 (30分)

```bash
# test_alns_optimizer.py のfixture修正
vim tests/test_unit/test_alns_optimizer.py

# 186-192行目を編集
# alns_initial_temp と alns_cooling_rate を削除

# テスト実行
pytest tests/test_unit/test_alns_optimizer.py -v
```

### ステップ2: 優先度2のテストを修正 (2-3時間)

```bash
# test_continuous_cultivation_impact.py を修正
vim tests/test_usecase/test_continuous_cultivation_impact.py

# 各テストケースで:
# 1. previous_allocation を作成
# 2. InteractionRule を作成
# 3. get_metrics() にコンテキストを渡す

# テスト実行
pytest tests/test_usecase/test_continuous_cultivation_impact.py -v
```

### ステップ3: 優先度3のテストを修正 (1-2時間)

```bash
# 各テストファイルを修正
vim tests/test_usecase/test_field_dto_to_interactor_response.py
vim tests/test_usecase/test_multi_field_crop_allocation_dp.py
vim tests/test_usecase/test_multi_field_crop_allocation_complete.py

# 主に previous_crop パラメータを削除
# get_metrics() を使用

# テスト実行
pytest tests/test_usecase/ -v
```

### ステップ4: 全テスト実行

```bash
# すべてのテストを実行
pytest -v

# カバレッジ確認
pytest --cov=src/agrr_core --cov-report=html
```

---

## 推定修正時間

- **優先度1 (11件):** 30分
- **優先度2 (8件):** 2-3時間
- **優先度3 (12件):** 1-2時間
- **合計:** **4-6時間**

---

## 関連ドキュメント

1. **[TEST_FAILURE_ANALYSIS.md](./TEST_FAILURE_ANALYSIS.md)**
   - 変更の背景と詳細な分析

2. **[TEST_FIX_GUIDE.md](./TEST_FIX_GUIDE.md)**
   - 修正方法の詳細ガイドと例

3. **[FAILED_TESTS_DETAIL.md](./FAILED_TESTS_DETAIL.md)**
   - 各テストの詳細情報と修正内容

---

## コミット履歴

関連するコミット:

```
e31238f - refactor: Remove unused revenue/profit calculations from neighbor operations
af522b9 - refactor: unify profit calculation and fix max_revenue handling
f34851e - feat: improve greedy allocation with dynamic re-sorting and max_revenue constraint
```

---

## 結論

このリファクタリングは、計算ロジックの正確性と保守性を大幅に向上させる重要な変更です。テストの修正は必要ですが、新しい設計の方がより堅牢で正確です。

**推奨アクション:**
1. まず優先度1のテスト (test_alns_optimizer.py) を修正して、11件のエラーを解消
2. 次に優先度2のテスト (test_continuous_cultivation_impact.py) を修正
3. 最後に残りのテストを修正
4. 全テストがパスすることを確認

**総修正時間:** 4-6時間程度

