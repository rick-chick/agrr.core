# Tests

AGRRプロジェクトのテストスイート。Clean Architectureの各層に対応したテスト構造。

## テスト構造

```
tests/
├── test_entity/          # Entity層のテスト
├── test_usecase/         # UseCase層のテスト
├── test_adapter/         # Adapter層のテスト
├── test_integration/     # 統合テスト（複数層）
├── test_e2e/             # E2Eテスト（外部API含む）
└── conftest.py           # 共通fixture定義
```

## テスト実行

### 全テスト実行
```bash
pytest tests/ -v
```

### 層別実行
```bash
# Entity層のみ
pytest tests/test_entity/ -v

# UseCase層のみ
pytest tests/test_usecase/ -v

# Adapter層のみ
pytest tests/test_adapter/ -v

# 統合テスト
pytest tests/test_integration/ -v
```

### カバレッジ確認
```bash
pytest tests/ --cov=src/agrr_core --cov-report=html
# 結果: htmlcov/index.html
```

---

## 重要なテスト

### ⭐⭐⭐ 候補生成戦略の比較テスト（必見）
**ファイル**: `test_integration/test_candidate_strategy_comparison.py`

Period Template方式とCandidate Pool方式の実測比較。

**結果**:
- 平均改善率: Greedy +22.10%, DP +29.56%
- 最大改善率: +75.97%

**実行**:
```bash
pytest tests/test_integration/test_candidate_strategy_comparison.py::test_comprehensive_benchmark_all_datasets -v -s
```

---

## テスト統計

- **総テスト数**: 1,107件 (集計中: 78件スキップ)
- **成功率**: 100%
- **カバレッジ**: 29%
- **実行時間**: 約70秒

### テスト圧縮結果 (2025/01実施)

重複テストの圧縮により最適化を実施:
- Optimizer テスト: 21件 → 19件 (-2件)
- Weather JMA Repository: 25件 → 22件 (-3件)
- DTO テスト: 6ファイル削除（バリデーションロジックなしの単純なデータホルダー）
- **合計削減**: 約15件の冗長テストを削減

---

## 関連ドキュメント

- [test_integration/README.md](test_integration/README.md) - 統合テストの詳細
- [test_e2e/README.md](test_e2e/README.md) - E2Eテストの詳細
- [../docs/guides/TEST_EXECUTION_GUIDE.md](../docs/guides/TEST_EXECUTION_GUIDE.md) - テスト実行ガイド

