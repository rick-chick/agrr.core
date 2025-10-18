# Repository移行計画

## 目的

標準的なClean Architectureに準拠するため、Repository実装を`adapter/repositories/`から`framework/repositories/`に移動する。

## 移行対象（8ファイル）

### Weather関連（3ファイル）
1. `weather_api_open_meteo_repository.py`
2. `weather_jma_repository.py`
3. `weather_file_repository.py`

### Crop関連（2ファイル）
4. `crop_profile_file_repository.py`
5. `crop_profile_llm_repository.py`

### その他（3ファイル）
6. `field_file_repository.py`
7. `interaction_rule_file_repository.py`
8. `prediction_storage_repository.py`

## 影響範囲

インポート文の変更が必要なファイル（13箇所）:
1. `framework/agrr_core_container.py` (3箇所)
2. `adapter/controllers/growth_period_optimize_cli_controller.py` (1箇所)
3. `cli.py` (8箇所)
4. `adapter/gateways/crop_profile_gateway_impl.py` (1箇所)

## 移行手順

### ステップ1: ファイル移動
```bash
mv src/agrr_core/adapter/repositories/*.py src/agrr_core/framework/repositories/
```

### ステップ2: インポート文更新
すべての`from agrr_core.adapter.repositories`を`from agrr_core.framework.repositories`に変更

### ステップ3: __init__.py更新
- `adapter/repositories/__init__.py` 削除
- `framework/repositories/__init__.py` 更新

### ステップ4: テスト実行
```bash
python3 -m pytest tests/
```

### ステップ5: クリーンアップ
```bash
rm -rf src/agrr_core/adapter/repositories/
```

## リスク

- **低リスク**: インポートパスの変更のみ
- **影響範囲**: 限定的（4ファイル、13箇所）
- **ロールバック**: 容易（gitで戻せる）

## 実施

