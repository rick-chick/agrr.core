# Fixture Migration Guide

このガイドは、新しいfixture命名規則への移行を説明します。

## 概要

fixtureをクリーンアーキテクチャの層ごとに整理し、命名規則を統一しました。
**後方互換性エイリアスは全て削除されており、新しい命名規則のみを使用してください。**

## 新しい命名規則

### Entity Layer
- `entity_*` - ドメインエンティティやバリューオブジェクト
- 例: `entity_weather_data`, `entity_crop_requirement_aggregate`

### UseCase Layer
- `gateway_*` - Gatewayインターフェース（モック）
- `input_port_*` - Input Port（Interactorのインターフェース）
- `output_port_*` - Output Port（Presenterのインターフェース）
- 例: `gateway_weather`, `output_port_crop_requirement`

### Adapter Layer
- `repository_*` - Repositoryの実装（Adapter層）
- `service_*` - Serviceの実装（Adapter層）
- `presenter_*` - Presenterの実装
- `controller_*` - Controllerの実装
- 例: `repository_weather_data`, `service_prophet`

### Framework Layer
- `external_*` - 外部サービス（HTTPクライアントなど）
- 例: `external_http_service`

## 完了した移行

全ての後方互換性エイリアスは**削除済み**です。全テストが新しい命名規則に移行されました。

| 旧名（削除済み） | 新名（現在使用中） |
|------|------|
| `mock_weather_data` | `entity_weather_data` |
| `sample_weather_data_list` | `entity_weather_data_list` |
| `sample_forecast_list` | `entity_forecast_list` |
| `mock_crop_requirement_gateway` | `gateway_crop_requirement` |
| `mock_crop_requirement_output_port` | `output_port_crop_requirement` |
| `mock_weather_data_repository` | `repository_weather_data` |
| `mock_prophet_service` | `service_prophet` |
| `mock_growth_progress_*` | `gateway_*` (標準化済み) |

## テスト記述方法

**全てのテストで新しい命名規則を使用してください：**

```python
def test_feature(entity_weather_data, gateway_weather):
    # テストコード
    pass
```

## 主な改善点

1. **アーキテクチャ層による整理**
   - Entity, UseCase, Adapter, Framework層ごとにセクション分け
   - 各層の責任が明確に

2. **命名規則の統一**
   - 層とコンポーネントタイプが名前から分かる
   - 一貫性のあるプレフィックス

3. **fixture内の依存関係修正**
   - fixture内で他のfixtureを関数として呼び出す問題を修正
   - 正しくfixtureパラメータとして注入

4. **重複の削除**
   - 似たようなfixtureを統合
   - 必要なものだけを残す

## テスト結果（移行完了後）

全テストスイート: **685 passed, 2 skipped, 4 xfailed, 3 xpassed**
- カバレッジ: **80%**
- 全てのテストが新しい命名規則で動作
- 後方互換性エイリアスは完全に削除

## 詳細情報

- メインのconftest: `tests/conftest.py`
- Adapter層のconftest: `tests/test_adapter/conftest.py`
- アーキテクチャドキュメント: `ARCHITECTURE.md`

