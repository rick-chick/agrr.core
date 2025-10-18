# E2E（End-to-End）テスト

このディレクトリには、実際の外部APIやサービスを呼び出すE2Eテストが含まれています。

## 特徴

- **実際のAPIを使用**: モックではなく、本物のNOAA、JMA、Open-Meteo等のAPIを使用
- **時間がかかる**: ネットワーク通信を行うため、単体テストより時間がかかる
- **デフォルトでスキップ**: `pytest.ini`の設定により、通常のテスト実行では自動的にスキップされる

## マーカー

全てのE2Eテストは`@pytest.mark.e2e`でマークされています：

```python
@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.e2e
class TestWeatherAPIReal:
    """E2E test with real API calls."""
    pass
```

## テスト実行方法

### 通常のテスト実行（E2Eを除外）

```bash
# デフォルト - E2Eテストは自動的にスキップされる
pytest

# または明示的に
pytest -m "not e2e"
```

**結果**: E2Eテストは`deselected`として表示され、実行されません。

### E2Eテストのみ実行

```bash
# E2Eテストのみを実行
pytest -m e2e

# 特定のE2Eテストファイルを実行
pytest tests/test_e2e/test_noaa_us_cities.py -m e2e

# 詳細出力で実行
pytest -m e2e -v
```

### E2Eテストを含めて全て実行

```bash
# 全てのテストを実行（E2Eも含む）
pytest -m ""

# または
pytest --override-ini="addopts="
```

## 含まれるテスト

### test_weather_api_open_meteo_real.py
- Open-Meteo APIの実際の動作確認
- 東京の天気データ取得テスト

### test_weather_jma_real.py
- 気象庁（JMA）のWebスクレイピング動作確認
- 東京、大阪、札幌のデータ取得テスト

### test_jma_47_prefectures.py
- 気象庁の47都道府県データ取得テスト
- 全県庁所在地の天気データ確認

### test_noaa_us_cities.py
- NOAA APIのアメリカ主要都市テスト
- New York, Los Angeles, Chicagoのデータ取得

### test_noaa_ftp_long_term.py
- NOAA FTPサーバーからの長期データ取得
- 2000年以降のhistoricalデータ確認

## CI/CDでの扱い

### 推奨設定

**通常のCI実行**: E2Eテストをスキップ（高速）
```yaml
- name: Run tests
  run: pytest  # デフォルトで -m "not e2e" が適用される
```

**nightly build**: E2Eテストも実行（完全テスト）
```yaml
- name: Run all tests including E2E
  run: pytest -m ""
```

## 注意事項

### ネットワーク依存
- インターネット接続が必要
- APIの利用制限に注意
- タイムアウトエラーの可能性あり

### レートリミット
- 外部APIには利用制限がある場合があります
- 頻繁な実行は避けてください
- CI/CDでは適切な間隔を設定してください

### データの変動
- 実際のAPIデータを使用するため、結果が変動する可能性があります
- 過去のデータは安定していますが、リアルタイムデータは変化します

## トラブルシューティング

### テストがスキップされない
```bash
# pytest.iniを確認
cat pytest.ini | grep "not e2e"

# 明示的にマーカーを確認
pytest --markers | grep e2e
```

### E2Eテストが失敗する
- ネットワーク接続を確認
- APIのステータスページを確認
- タイムアウト値を調整（必要に応じて）

## 開発ガイドライン

### 新しいE2Eテストの追加

1. **適切なマーカーを付ける**:
```python
@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.e2e  # 必須
class TestNewE2E:
    pass
```

2. **ファイル配置**: `tests/test_e2e/`ディレクトリに配置

3. **テストの設計**:
   - 外部依存を明確にドキュメント化
   - 適切なタイムアウトを設定
   - エラーハンドリングを適切に実装

### ベストプラクティス

- E2Eテストは最小限に（重要な統合ポイントのみ）
- 単体テストで代用できる部分は単体テストで
- 実際のAPIキーが必要な場合は環境変数で管理
- 外部サービスの変更に対応できる柔軟なアサーション

---

**最終更新**: 2025-10-18  
**pytest.ini設定**: デフォルトで`-m "not e2e"`が適用されます
