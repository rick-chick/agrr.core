# E2E Tests

## 概要

このディレクトリには、実際のOpen-Meteo APIを呼び出すEnd-to-End (E2E) テストが含まれています。

## 特徴

- ✅ **実APIコール**: モックではなく、実際のOpen-Meteo APIにリクエストを送信
- ⚠️ **インターネット接続必須**: オフラインでは実行できません
- ⏱️ **実行時間**: 通常のテストより遅い（6-10秒程度）
- 🔄 **不安定性**: ネットワーク状況やAPI状態に依存

## 実行方法

**⚠️ デフォルト動作: E2Eテストはスキップされます**

`tests/conftest.py`の`pytest_collection_modifyitems`フックにより、通常のテスト実行ではE2Eテストは自動的にスキップされます。

### 通常のテスト実行（E2E除外）

```bash
# デフォルトでE2Eをスキップ（6 skipped と表示されます）
pytest

# または
pytest -v
```

### E2Eテストのみ実行

```bash
# E2Eテストのみ実行
pytest -m e2e

# または詳細表示
pytest -m e2e -v
```

### 全テスト実行（E2E含む）

```bash
# すべてのテスト（E2E含む）を実行
pytest -m ""

# またはディレクトリを明示的に指定
pytest tests/ --override-ini="addopts="
```

## テスト内容

| テスト | 説明 |
|-------|------|
| `test_real_api_call_tokyo` | 東京の座標で実APIコール |
| `test_real_api_call_new_york` | ニューヨークの座標で実APIコール |
| `test_real_api_call_single_day` | 1日分のデータ取得 |
| `test_real_api_data_completeness` | データの完全性確認 |
| `test_real_api_edge_case_extreme_coordinates` | 極端な座標（アイスランド）でテスト |
| `test_real_api_response_time` | レスポンス時間の測定 |

## CI/CDでの扱い

E2Eテストはネットワーク依存のため、CI/CDでは以下のように扱うことを推奨：

```yaml
# .github/workflows/test.yml 例
- name: Run unit and integration tests
  run: pytest -m "not e2e" -v

- name: Run E2E tests (optional)
  run: pytest -m e2e -v
  continue-on-error: true  # E2Eテストの失敗でビルドを止めない
```

## トラブルシューティング

### タイムアウトエラー

```
Read timed out. (read timeout=30)
```

**原因**: ネットワークが遅い、またはAPIサーバーが過負荷

**対処法**:
- 時間をおいて再実行
- タイムアウト時間を延長（リポジトリの`timeout=30`を変更）

### レート制限

Open-Meteo APIは無料プランでも十分な制限がありますが、頻繁に実行すると制限に達する可能性があります。

## 注意事項

⚠️ **timezone ハードコード問題**

現在のリポジトリ実装では、タイムゾーンが`Asia/Tokyo`にハードコードされています。
これは今後修正が必要な既知の問題です。

```python
# src/agrr_core/adapter/repositories/open_meteo_weather_repository.py
params = {
    # ...
    "timezone": "Asia/Tokyo"  # ← ハードコード
}
```

**TODO**: `timezone: "auto"`を使用して、座標に応じた自動タイムゾーンを取得するように修正。
