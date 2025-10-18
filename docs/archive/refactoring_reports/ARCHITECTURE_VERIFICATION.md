# Clean Architectureアーキテクチャ検証

**検証日**: 2025年10月14日  
**対象**: 予測モデルのアーキテクチャ

---

## ✅ 正しいアーキテクチャ

### レイヤー構造

```
┌─────────────────────────────────────────────────────┐
│              UseCase層（ビジネスロジック）            │
│   • Interactors                                    │
│   • DTOs                                          │
│   • Ports (Input/Output)                          │
├─────────────────────────────────────────────────────┤
│                    ↑ uses                          │
├─────────────────────────────────────────────────────┤
│              Adapter層（技術詳細の橋渡し）            │
│                                                     │
│  【Interface定義】                                   │
│   • PredictionServiceInterface                     │← Framework層が実装
│                                                     │
│  【Gateway実装】                                     │
│   • PredictionModelGatewayImpl                     │
│      - Serviceをインジェクト受け取り                 │
│      - モデル選択                                   │
│      - アンサンブル制御                             │
├─────────────────────────────────────────────────────┤
│        ↑ implements (Interface)                    │
│        ↓ injects (Service)                         │
├─────────────────────────────────────────────────────┤
│           Framework層（技術実装の詳細）              │
│                                                     │
│  【Service実装】                                     │
│   • ARIMAPredictionService                         │← implements Interface
│   • LightGBMPredictionService                      │← implements Interface
│   • FeatureEngineeringService                      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 重要なポイント

### 1. Interface定義の場所 ✅

**正**: Adapter層で定義
```
src/agrr_core/adapter/interfaces/
└─ prediction_service_interface.py
```

**誤**: UseCase層で定義（❌ アーキテクチャ違反）
```
src/agrr_core/usecase/interfaces/  ← ここに置いてはいけない
```

**理由**:
- UseCase層は技術詳細（ARIMA、LightGBMなど）を知らない
- Adapter層が「Framework層に何を要求するか」を定義
- Framework層がAdapter層のinterfaceを実装

### 2. Framework層の実装 ✅

```python
# Framework層のサービスは、Adapter層のinterfaceを実装
from agrr_core.adapter.interfaces.prediction_service_interface import PredictionServiceInterface

class ARIMAPredictionService(PredictionServiceInterface):
    """Framework layer implementation."""
    pass
```

### 3. Gatewayへのインジェクション ✅

```python
# Adapter層のGatewayは、Framework層のサービスをインジェクト
from agrr_core.adapter.interfaces.prediction_service_interface import PredictionServiceInterface

class PredictionModelGatewayImpl:
    def __init__(
        self,
        arima_service: PredictionServiceInterface,     # ← interfaceで受け取る
        lightgbm_service: PredictionServiceInterface   # ← interfaceで受け取る
    ):
        # Serviceをインジェクト
        self.models = {
            'arima': arima_service,
            'lightgbm': lightgbm_service
        }
```

---

## 依存関係の流れ

### 正しい依存方向

```
UseCase層（Interactor）
  ↓ uses
Adapter層（Gateway）
  ├─ Interface定義 ──→ Framework層が implements
  └─ Gateway実装  ←── Framework層を inject
```

### インジェクションの流れ

```
1. Framework層でServiceを作成
   arima = ARIMAPredictionService(...)
   lgb = LightGBMPredictionService(...)

2. Adapter層のGatewayにインジェクト
   gateway = PredictionModelGatewayImpl(
       arima_service=arima,    ← inject
       lightgbm_service=lgb    ← inject
   )

3. UseCase層でGatewayを使用
   interactor = WeatherPredictInteractor(
       prediction_gateway=gateway  ← inject
   )
```

---

## ファイル配置の検証

### ✅ 現在の配置（正しい）

```
src/agrr_core/
├─ usecase/
│   ├─ interactors/
│   │   └─ weather_predict_interactor.py
│   └─ (interfaceなし - ビジネスロジックのみ)
│
├─ adapter/
│   ├─ interfaces/
│   │   └─ prediction_service_interface.py    ✅ Adapter層でinterface定義
│   └─ gateways/
│       └─ prediction_model_gateway_impl.py   ✅ Serviceをインジェクト
│
└─ framework/
    └─ services/
        ├─ arima_prediction_service.py        ✅ interfaceを実装
        ├─ lightgbm_prediction_service.py     ✅ interfaceを実装
        └─ feature_engineering_service.py
```

---

## Clean Architecture原則の遵守

### 1. 依存性逆転の原則（DIP）✅

```
Adapter層がinterfaceを定義
  ↑
Framework層がinterfaceを実装

→ Framework層がAdapter層に依存（interfaceを介して）
→ UseCase層はどちらにも依存しない
```

### 2. 単一責任の原則（SRP）✅

- **UseCase層**: ビジネスロジックのみ
- **Adapter層**: インターフェース定義とGateway実装
- **Framework層**: 技術実装の詳細

### 3. 開放閉鎖の原則（OCP）✅

新しいモデル（Prophet、XGBoostなど）を追加する場合：

```python
# 1. Framework層に実装追加（interfaceを実装）
class ProphetPredictionService(PredictionServiceInterface):
    pass

# 2. Gatewayにインジェクト
gateway = PredictionModelGatewayImpl(
    arima_service=arima,
    lightgbm_service=lgb,
    prophet_service=prophet  # ← 追加するだけ
)
```

既存コードの変更不要！

---

## テスト結果

```bash
pytest tests/test_adapter/test_prediction* -v

✅ 31/31 PASSED

- test_prediction_model_gateway_impl.py: 13 tests
- test_prediction_lightgbm_service.py: 18 tests
```

---

## まとめ

### ✅ 修正完了事項

1. ✅ Interface を UseCase層 → Adapter層 に移動
2. ✅ クラス名を PredictionModelInterface → PredictionServiceInterface に変更
3. ✅ Framework層が Adapter層のinterface を実装
4. ✅ Gateway が Framework層のService をインジェクト
5. ✅ 全テストがパス（31/31）

### ✅ Clean Architecture準拠

- Adapter層: Interface定義とGateway実装
- Framework層: Interface実装（技術詳細）
- UseCase層: ビジネスロジックのみ（技術詳細を知らない）

### ✅ 原則遵守

- 依存性逆転の原則（DIP）
- 単一責任の原則（SRP）
- 開放閉鎖の原則（OCP）

---

**アーキテクチャ修正完了 ✅**

すべてのコンポーネントがClean Architectureの原則に正しく準拠しました。
