# Integration Tests

統合テストのディレクトリ。複数のコンポーネントを組み合わせた動作を検証します。

## 主要なテストファイル

### 候補生成戦略の比較テスト

**`test_candidate_strategy_comparison.py`**
- Period Template方式（新） vs Candidate Pool方式（レガシー）の比較
- 3データセット × 2アルゴリズムで検証
- **実行コマンド**:
  ```bash
  pytest tests/test_integration/test_candidate_strategy_comparison.py -v -s
  ```

**ベンチマーク結果**:
- 平均改善率: Greedy +22.10%, DP +29.56%
- 最大改善率: +75.97%（Standard dataset, DP）
- 詳細: `docs/technical/PERIOD_TEMPLATE_DESIGN.md`

---

### Period Template統合テスト

**`test_period_template_integration.py`**
- Period Template方式の各種アルゴリズム統合テスト
- 7テストケース（Greedy, DP, Local Search, ALNS, メモリ効率など）
- **実行コマンド**:
  ```bash
  pytest tests/test_integration/test_period_template_integration.py -v
  ```

---

### その他の統合テスト

- `test_multi_field_crop_allocation_*` - 複数圃場配置の統合テスト
- `test_growth_period_optimize_*` - 栽培期間最適化の統合テスト
- など

---

## テスト実行

### 全統合テスト実行
```bash
pytest tests/test_integration/ -v
```

### カバレッジ付き実行
```bash
pytest tests/test_integration/ --cov=src/agrr_core --cov-report=html
```

### 特定のテストのみ実行
```bash
# 比較ベンチマーク
pytest tests/test_integration/test_candidate_strategy_comparison.py::test_comprehensive_benchmark_all_datasets -v -s

# Period Template統合
pytest tests/test_integration/test_period_template_integration.py -v
```

