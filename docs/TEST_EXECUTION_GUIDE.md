# テスト実行ガイド

## テストの分類とマーキング

このプロジェクトでは、テスト実行速度を最適化するため、テストを以下のように分類しています：

### マーカー一覧

| マーカー | 説明 | デフォルト | 実行時間 |
|---------|------|-----------|---------|
| **なし** | 通常の高速テスト | ✅ 実行 | <1秒 |
| `@pytest.mark.slow` | 計算負荷の高いテスト | ❌ スキップ | 5-80秒 |
| `@pytest.mark.e2e` | 外部API呼び出しテスト | ❌ スキップ | 10-60秒 |
| `@pytest.mark.asyncio` | 非同期テスト | ✅ 実行 | - |

---

## テスト実行方法

### 1. 通常のテスト実行（デフォルト・推奨）

```bash
# 高速テストのみ実行（slow, e2e除外）
pytest

# 結果例:
# === 897 passed, 46 deselected in 22.54s ===
```

**実行時間**: 約23秒  
**用途**: 開発中の継続的テスト、CI/CDのPull Request時

---

### 2. Slowテストを含める

```bash
# E2Eは除外、Slowは実行
pytest -m "not e2e"

# 結果例:
# === 912 passed, 28 deselected in 371.75s ===
```

**実行時間**: 約6分  
**用途**: マージ前の最終確認、主要機能の動作確認

---

### 3. 全テスト実行（E2E含む）

```bash
# 全てのテストを実行
pytest -m ""

# または
pytest --override-ini="addopts="
```

**実行時間**: 約8-10分  
**用途**: リリース前、nightly build

---

### 4. 特定マーカーのテストのみ実行

```bash
# Slowテストのみ
pytest -m slow

# E2Eテストのみ
pytest -m e2e

# IntegrationテストでSlowでないもの
pytest -m "integration and not slow"
```

---

## テスト実行時間の比較

| パターン | 実行時間 | テスト数 | 用途 |
|---------|---------|---------|------|
| **デフォルト** | 23秒 | 897 | 開発中 |
| **Slow含む** | 6分12秒 | 912 | マージ前 |
| **全て（E2E含む）** | 8-10分 | 940+ | リリース前 |

---

## Slowテストの内訳

### test_filter_redundant_comparison.py (8テスト)

最適化候補のフィルタリング機能の包括的テスト。

| テスト | 実行時間 | 内容 |
|-------|---------|------|
| `test_scenario_5_diverse_crops` | 82秒 | 多様な作物での最適化 |
| `test_scenario_4_mixed_crops` | 54秒 | 混合作物での最適化 |
| `test_filter_1000_candidates_with_duplicates` | 25秒 | 1000候補のフィルタリング性能 |
| `test_filter_50_candidates_in_realistic_time` | 12秒 | 50候補のフィルタリング性能 |
| その他 | 5-10秒 | 各種シナリオテスト |

**合計**: 約182秒（全体の約50%）

### test_allocation_adjust_integration.py (一部)

| テスト | 実行時間 | 内容 |
|-------|---------|------|
| `test_complete_adjust_workflow` | 2.2秒 | 完全なワークフローテスト |
| その他adjust関連 | 2-5秒 | アルゴリズム比較、E2Eシナリオ |

---

## CI/CD推奨設定

### Pull Request時

```yaml
- name: Run fast tests
  run: pytest
  # デフォルトで slow, e2e は除外される
```

**実行時間**: ~30秒  
**目的**: 高速フィードバック

### マージ前

```yaml
- name: Run tests including slow
  run: pytest -m "not e2e"
```

**実行時間**: ~6分  
**目的**: 機能の完全性確認

### Nightly Build

```yaml
- name: Run all tests
  run: pytest -m ""
```

**実行時間**: ~10分  
**目的**: 外部依存を含む完全テスト

---

## 新しいテストの追加ガイドライン

### Slowマークが必要な基準

以下のいずれかに該当する場合、`@pytest.mark.slow`を追加してください：

- **実行時間が5秒以上**
- **大量のデータを処理**（100件以上の候補など）
- **複雑な最適化アルゴリズムの実行**
- **複数回の最適化を比較**

```python
@pytest.mark.asyncio
@pytest.mark.slow  # ← 5秒以上かかる場合は必須
async def test_large_optimization():
    # 計算負荷の高いテスト
    pass
```

### E2Eマークが必要な基準

以下のいずれかに該当する場合、`@pytest.mark.e2e`を追加してください：

- **実際の外部APIを呼び出す**
- **インターネット接続が必要**
- **外部サービスの可用性に依存**

```python
@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.e2e  # ← 外部API呼び出しがある場合は必須
async def test_real_api():
    # 実際のAPIを使用するテスト
    pass
```

---

## トラブルシューティング

### テストが予期せずスキップされる

```bash
# マーカーを確認
pytest --markers | grep -E "slow|e2e"

# 実際に除外されているテストを確認
pytest --collect-only -q | grep deselected

# 設定を確認
cat pytest.ini | grep addopts
```

### Slowテストが実行されない

`pytest.ini`の設定により、デフォルトで除外されています。明示的に実行してください：

```bash
# Slowテストを含める
pytest -m "not e2e"

# またはSlowテストのみ
pytest -m slow
```

### E2Eテストの失敗

E2Eテストは外部依存があるため、以下を確認：

- インターネット接続
- 外部APIの状態
- レート制限

---

## ベストプラクティス

### 開発フロー

1. **コード変更**
   ```bash
   pytest  # 高速テスト（23秒）
   ```

2. **機能完成**
   ```bash
   pytest -m "not e2e"  # Slow含む（6分）
   ```

3. **マージ前**
   ```bash
   pytest -m ""  # 全テスト（10分）
   ```

### テスト作成時

- **まず高速テストで基本動作を確認**
- **必要な場合のみSlowテストを追加**
- **E2Eテストは最小限に**（重要な統合ポイントのみ）
- **適切なマーカーを必ず付ける**

---

## 設定ファイル

### pytest.ini

```ini
[pytest]
addopts = 
    -m "not e2e and not slow"  # デフォルトで除外

markers =
    slow: marks tests as slow running (deselect with '-m "not slow"')
    e2e: marks tests as end-to-end tests (skipped by default)
```

---

## まとめ

| 実行パターン | コマンド | 時間 | 用途 |
|-------------|---------|------|------|
| 🚀 **高速** | `pytest` | 23秒 | 開発中 |
| ⚡ **標準** | `pytest -m "not e2e"` | 6分 | マージ前 |
| 🔍 **完全** | `pytest -m ""` | 10分 | リリース前 |

**推奨**: 通常は`pytest`（23秒）を使用し、マージ前に`pytest -m "not e2e"`で確認してください。

---

**最終更新**: 2025-10-18  
**テスト高速化**: 約94%削減（371秒 → 23秒）

