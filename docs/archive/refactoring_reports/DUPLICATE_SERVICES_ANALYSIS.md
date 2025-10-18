# 重複Serviceの分析レポート

## 問題の発見

adapter層とframework層の両方にARIMAとLightGBMのServiceが存在しています。

## 現状

### Adapter層のServices

1. **adapter/services/prediction_arima_service.py**
   - クラス名: `PredictionARIMAService`
   - 実装: `PredictionServiceInterface`
   - 行数: ~381行
   - コメント: "This service provides ARIMA-based weather prediction implementing the PredictionServiceInterface from the Adapter layer."

2. **adapter/services/prediction_lightgbm_service.py**
   - クラス名: `PredictionLightGBMService`
   - 実装: `PredictionServiceInterface`
   - 行数: ~387行
   - コメント: "This service provides LightGBM-based weather prediction implementing the PredictionServiceInterface from the Adapter layer."

### Framework層のServices

3. **framework/services/arima_prediction_service.py**
   - クラス名: `ARIMAPredictionService`
   - 実装: `PredictionServiceInterface`
   - 行数: ~354行
   - コメント: "ARIMA-based prediction service (Framework layer implementation)."

4. **framework/services/lightgbm_prediction_service.py**
   - クラス名: `LightGBMPredictionService`
   - 実装: `PredictionServiceInterface`
   - 行数: ~355行
   - コメント: "LightGBM-based prediction service (Framework layer implementation)."

## 使用状況

### Container（agrr_core_container.py）での使用

```python
# Line 19: Adapter層のARIMAをインポート
from agrr_core.adapter.services.prediction_arima_service import PredictionARIMAService

# Line 140-145: Adapter層のARIMAを使用
def get_prediction_arima_service(self) -> PredictionARIMAService:
    if 'prediction_arima_service' not in self._instances:
        time_series_service = self.get_time_series_service()
        self._instances['prediction_arima_service'] = PredictionARIMAService(time_series_service)
    return self._instances['prediction_arima_service']

# Line 147-152: Framework層のLightGBMを使用
def get_prediction_lightgbm_service(self):
    if 'prediction_lightgbm_service' not in self._instances:
        from agrr_core.framework.services.lightgbm_prediction_service import LightGBMPredictionService
        self._instances['prediction_lightgbm_service'] = LightGBMPredictionService()
    return self._instances['prediction_lightgbm_service']
```

### 実際の使用

- ✅ **Adapter層 ARIMA**: 使用中（containerでインポート・インスタンス化）
- ❌ **Framework層 ARIMA**: 未使用
- ❌ **Adapter層 LightGBM**: 未使用（テストのみ）
- ✅ **Framework層 LightGBM**: 使用中（containerでインポート・インスタンス化）

## 問題点

### 1. 不統一な配置

- ARIMA → Adapter層を使用
- LightGBM → Framework層を使用

**問題**: なぜ異なる層のServiceを使っているのか不明確

### 2. アーキテクチャ的な疑問

**Clean Architectureの原則:**
```
Framework Layer → Adapter Layer → UseCase Layer → Entity Layer
```

- **Framework層**: 外部ライブラリ・技術的実装詳細（statsmodels, lightgbm等）
- **Adapter層**: Framework層を抽象化してUseCase層に提供

**問題点:**
- 機械学習ライブラリ（statsmodels, lightgbm）を直接使う実装は**Framework層**にあるべき
- Adapter層のServiceは、Framework層のServiceを使うか、もっと抽象的な処理を提供すべき

### 3. 重複コード

両方の実装はほぼ同じロジックを持っています：
- 特徴量エンジニアリング
- モデル訓練
- 予測生成
- 信頼区間計算

## Clean Architectureの観点での正しい配置

### 推奨される構造

```
Framework層: ARIMAPredictionService, LightGBMPredictionService
              - statsmodels, lightgbm等の外部ライブラリを直接使用
              - PredictionServiceInterfaceを実装
              
              ↑ (依存性注入)
              
Adapter層: PredictionModelGatewayImpl
              - Framework層のServiceを注入
              - UseCase層のPredictionModelGatewayを実装
              
              ↑ (依存性注入)
              
UseCase層: Interactor
              - PredictionModelGatewayを使用
```

### 現在の問題

**間違った構造（ARIMA）:**
```
Adapter層: PredictionARIMAService (statsmodelsを直接使用) ← 本来Framework層にあるべき
Framework層: ARIMAPredictionService (未使用)
```

**間違った構造（LightGBM）:**
```
Adapter層: PredictionLightGBMService (未使用)
Framework層: LightGBMPredictionService (lightgbmを直接使用) ← 正しい
```

## 推奨される修正

### オプション1: Framework層に統一（推奨）

**理由:**
- 外部ライブラリ（statsmodels, lightgbm）を直接使う実装はFramework層にあるべき
- Clean Architectureの原則に準拠

**修正内容:**
1. containerをFramework層のARIMAPredictionServiceを使うように変更
2. Adapter層のPredictionARIMAServiceを削除または非推奨化
3. すべてのテストをFramework層のServiceに変更

### オプション2: Adapter層に統一

**理由:**
- 現在ARIMAはAdapter層を使っている
- 統一性を優先

**修正内容:**
1. containerをAdapter層のPredictionLightGBMServiceを使うように変更
2. Framework層のARIMAPredictionService, LightGBMPredictionServiceを削除

### オプション3: 現状維持（非推奨）

混在した状態を保持（推奨しない）

## 詳細比較

### 実装の違いを確認

両方のARIMAServiceを比較する必要があります。

---

## 分析結果

### 現在の使用状況

| Service | 層 | 使用状況 | 行数 |
|---------|---|---------|------|
| **PredictionARIMAService** | Adapter | ✅ 使用中 | 380行 |
| ARIMAPredictionService | Framework | ❌ 未使用 | 353行 |
| PredictionLightGBMService | Adapter | ❌ 未使用 | 386行 |
| **LightGBMPredictionService** | Framework | ✅ 使用中 | 354行 |

### Container での使用

```python
# ARIMA: Adapter層を使用
from agrr_core.adapter.services.prediction_arima_service import PredictionARIMAService
self._instances['prediction_arima_service'] = PredictionARIMAService(...)

# LightGBM: Framework層を使用（動的インポート）
from agrr_core.framework.services.lightgbm_prediction_service import LightGBMPredictionService
self._instances['prediction_lightgbm_service'] = LightGBMPredictionService()
```

## なぜAdapter層にARIMA/LightGBMがあるのか？

### 理由の推測

1. **段階的な移行中**
   - Adapter層のコメントに「Legacy methods (for backward compatibility)」とある
   - Framework層に新しい実装を作成中
   - 完全に移行が完了していない

2. **歴史的経緯**
   - 初期実装: Adapter層にすべて実装
   - リファクタリング: Framework層に移動開始
   - LightGBMは移行完了、ARIMAは移行中

3. **実装の違いがある可能性**
   - Adapter層: 簡易版または特定機能用
   - Framework層: 完全版または汎用版
   - 実際のコードを詳細比較する必要あり

## Clean Architectureの観点での正しい配置

### 原則

外部ライブラリ（statsmodels, lightgbm）を**直接使う実装**は：

✅ **Framework層にあるべき**
- 理由: 技術的実装詳細、外部依存
- 例: データベースドライバ、HTTPクライアント、ML��イブラリ

❌ **Adapter層にあるべきではない**
- Adapter層: Frameworkを抽象化してUseCaseに提供する役割
- 直接外部ライブラリを使うのはFrameworkの責任

### 正しい構造

```
Framework層:
  - ARIMAPredictionService (statsmodelsを直接使用)
  - LightGBMPredictionService (lightgbmを直接使用)
  - TimeSeriesARIMAService (statsmodelsを直接使用)
  ↓ PredictionServiceInterface実装

Adapter層:
  - PredictionModelGatewayImpl
  ↓ Framework層のServiceを注入

UseCase層:
  - Interactor (PredictionModelGatewayを使用)
```

## 推奨される修正

### オプション1: Framework層に完全統一（強く推奨）

**修正内容:**
1. containerを修正: `ARIMAPredictionService` (Framework層) を使用
2. Adapter層の`PredictionARIMAService`を削除または非推奨化
3. Adapter層の`PredictionLightGBMService`を削除（既に未使用）

**利点:**
- ✅ Clean Architectureの原則に完全準拠
- ✅ 一貫性のある設計
- ✅ Framework層に外部ライブラリの依存を集約
- ✅ テストの整理が可能

**修正ファイル:**
```python
# agrr_core_container.py
from agrr_core.framework.services.arima_prediction_service import ARIMAPredictionService

def get_prediction_arima_service(self) -> ARIMAPredictionService:
    if 'prediction_arima_service' not in self._instances:
        time_series_service = self.get_time_series_service()
        self._instances['prediction_arima_service'] = ARIMAPredictionService(time_series_service)
    return self._instances['prediction_arima_service']
```

**削除候補:**
- `src/agrr_core/adapter/services/prediction_arima_service.py` (380行)
- `src/agrr_core/adapter/services/prediction_lightgbm_service.py` (386行)
- `tests/test_adapter/test_prediction_arima_service.py`
- `tests/test_adapter/test_prediction_lightgbm_service.py`

### オプション2: 両方保持（一時的）

**理由:**
- 動作している実装を壊さない
- 段階的な移行

**対応:**
- コメントで状況を明記
- 将来の移行計画を文書化

## 実装の詳細比較

### ARIMA Services の比較

**共通点:**
- 両方とも`PredictionServiceInterface`を実装
- 同じメソッドシグネチャ
- 季節調整（seasonal adjustment）機能

**違い（要確認）:**
- コード量: Adapter 380行 vs Framework 353行
- 実装の詳細差異を確認する必要あり

### LightGBM Services の比較

**共通点:**
- 両方とも`PredictionServiceInterface`を実装
- FeatureEngineeringService使用

**違い:**
- Adapter層版にはいくつかのlegacyメソッドがある

## 結論

### 🔴 問題確認

Adapter層にARIMA/LightGBMがあるのは：

**✅ アーキテクチャ的には間違い**
- 外部ライブラリの直接使用はFramework層の責任
- Clean Architectureの原則違反

**💡 実際の理由:**
- 段階的な移行中と推測
- LightGBMは既にFramework層に移行済み
- ARIMAは移行途中（Adapter層を使用中）

### 推奨アクション

**優先度: 高**

1. ARIMAをFramework層に統一
2. Adapter層のARIMA/LightGBMを削除
3. テストをFramework層のServiceに変更
4. ドキュメント更新

**理由:**
- Clean Architectureの原則に準拠
- 一貫性のある設計
- コードの重複削除（~766行削減可能）

