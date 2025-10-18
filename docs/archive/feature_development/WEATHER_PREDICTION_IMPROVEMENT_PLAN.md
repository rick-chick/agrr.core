# 天気予測精度向上計画

**作成日**: 2025年10月14日  
**目的**: ARIMAモデルの改善と、より高精度な予測モデルの導入

---

## 現状分析

### 現在の実装（ARIMA）

**実装ファイル**: `src/agrr_core/adapter/services/prediction_arima_service.py`

#### 特徴
- ARIMA(5,1,5)をデフォルト使用
- 季節調整機能あり（月別平均を適用）
- 信頼区間の計算可能
- 最小30日のデータ必要

#### 制限事項
1. **短期予測向き**（30-90日程度）
2. **長期予測の精度低下**
3. **複数の外部要因を考慮できない**（気温のみ）
4. **非線形パターンの捕捉が困難**

---

## 改善案

###  Level 1: ARIMAモデルの改善（短期実装）

#### 1.1 パラメータの自動最適化

**現状**: 固定パラメータ (5,1,5)

**改善**: Auto ARIMA（最適なp,d,qを自動選択）

```python
from pmdarima import auto_arima

# 自動パラメータ選択
model = auto_arima(
    data,
    start_p=1, max_p=7,
    start_q=1, max_q=7,
    d=None,  # 自動決定
    seasonal=True,
    m=7,  # 週次の季節性
    stepwise=True,
    suppress_warnings=True,
    error_action='ignore'
)
```

**期待効果**: 精度10-15%向上

#### 1.2 季節性SARIMA

**現状**: 非季節モデル + 月別調整

**改善**: SARIMA（季節性を統合）

```python
# SARIMA(p,d,q)(P,D,Q,s)
order = (5, 1, 5)
seasonal_order = (1, 1, 1, 7)  # 週次季節性

model = SARIMAX(
    data,
    order=order,
    seasonal_order=seasonal_order,
    enforce_stationarity=False,
    enforce_invertibility=False
)
```

**期待効果**: 季節パターンの精度20%向上

#### 1.3 外部変数の追加（SARIMAX）

**現状**: 気温のみ

**改善**: 複数変数を考慮

```python
# 説明変数の追加
exog_vars = pd.DataFrame({
    'day_of_year': [...],  # 1-365
    'temperature_lag1': [...],  # 前日の気温
    'precipitation_lag1': [...],  # 前日の降水量
    'is_winter': [...],  # 冬季フラグ
})

model = SARIMAX(
    data,
    exog=exog_vars,
    order=(5, 1, 5),
    seasonal_order=(1, 1, 1, 7)
)
```

**期待効果**: 精度15-25%向上

---

### Level 2: 機械学習モデルの導入（中期実装）

#### 2.1 LightGBM（推奨）

**特徴**:
- 非線形パターンの捕捉が得意
- 複数特徴量を効率的に処理
- 高速で軽量

```python
import lightgbm as lgb

# 特徴量エンジニアリング
features = pd.DataFrame({
    'day_of_year': [...],
    'month': [...],
    'day_of_week': [...],
    'temperature_lag1': [...],  # 過去1日
    'temperature_lag7': [...],  # 過去7日
    'temperature_lag30': [...],  # 過去30日
    'temperature_ma7': [...],  # 7日移動平均
    'temperature_ma30': [...],  # 30日移動平均
    'temperature_std7': [...],  # 7日標準偏差
})

# モデル訓練
model = lgb.LGBMRegressor(
    objective='regression',
    n_estimators=1000,
    learning_rate=0.01,
    max_depth=10,
    num_leaves=31,
    random_state=42
)

model.fit(features, target)
```

**期待効果**: 精度30-50%向上

#### 2.2 XGBoost

**特徴**:
- LightGBMと同等の性能
- やや重いが、解釈性が高い

```python
import xgboost as xgb

model = xgb.XGBRegressor(
    objective='reg:squarederror',
    n_estimators=1000,
    learning_rate=0.01,
    max_depth=10,
    random_state=42
)
```

**期待効果**: 精度30-45%向上

#### 2.3 Prophet（Facebook製）

**特徴**:
- 時系列データ専用
- 自動で季節性・祝日効果を検出
- 欠損値に強い

```python
from prophet import Prophet

# データ準備
df = pd.DataFrame({
    'ds': dates,  # 日付
    'y': temperatures,  # 気温
})

# モデル訓練
model = Prophet(
    seasonality_mode='multiplicative',
    yearly_seasonality=True,
    weekly_seasonality=True,
    daily_seasonality=False,
    changepoint_prior_scale=0.05
)

model.fit(df)

# 予測
future = model.make_future_dataframe(periods=90)
forecast = model.predict(future)
```

**期待効果**: 精度25-40%向上

---

### Level 3: ディープラーニングモデル（長期実装）

#### 3.1 LSTM（Long Short-Term Memory）

**特徴**:
- 時系列の長期依存性を捕捉
- 複雑なパターンに対応

```python
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

# モデル構築
model = Sequential([
    LSTM(128, activation='relu', return_sequences=True, input_shape=(30, n_features)),
    Dropout(0.2),
    LSTM(64, activation='relu', return_sequences=True),
    Dropout(0.2),
    LSTM(32, activation='relu'),
    Dense(16, activation='relu'),
    Dense(1)
])

model.compile(optimizer='adam', loss='mse', metrics=['mae'])
```

**期待効果**: 精度40-60%向上（データ量依存）

#### 3.2 Transformer（最新）

**特徴**:
- 注意機構（Attention）による文脈理解
- 長期予測に強い

```python
from temporal_fusion_transformer import TemporalFusionTransformer

# 設定
model = TemporalFusionTransformer(
    input_size=n_features,
    output_size=1,
    hidden_size=128,
    attention_heads=4,
    dropout=0.1,
    num_encoder_steps=30,
    num_decoder_steps=90
)
```

**期待効果**: 精度50-70%向上（データ量が十分な場合）

---

## アンサンブル手法

複数モデルを組み合わせて精度向上

### 4.1 シンプルアンサンブル

```python
# 3つのモデルの平均
prediction_arima = arima_model.predict()
prediction_lgb = lgb_model.predict()
prediction_prophet = prophet_model.predict()

final_prediction = (
    0.3 * prediction_arima +
    0.4 * prediction_lgb +
    0.3 * prediction_prophet
)
```

**期待効果**: 各モデルより5-15%向上

### 4.2 スタッキング

```python
from sklearn.ensemble import StackingRegressor

# レベル0モデル
level0_models = [
    ('arima', ARIMAWrapper()),
    ('lgb', lgb.LGBMRegressor()),
    ('prophet', ProphetWrapper())
]

# メタモデル
meta_model = xgb.XGBRegressor()

# スタッキング
stacking_model = StackingRegressor(
    estimators=level0_models,
    final_estimator=meta_model,
    cv=5
)
```

**期待効果**: 各モデルより10-20%向上

---

## 推奨実装ロードマップ

### フェーズ1（1-2週間）: ARIMAの改善

**優先度**: 🔥🔥🔥 高

1. ✅ Auto ARIMA導入
2. ✅ SARIMA実装
3. ✅ 外部変数追加（SARIMAX）

**必要パッケージ**:
```bash
pip install pmdarima statsmodels
```

**期待精度**: MAE 1.08°C → **0.8-0.9°C**

---

### フェーズ2（2-3週間）: LightGBM導入

**優先度**: 🔥🔥 中高

1. ✅ 特徴量エンジニアリング
2. ✅ LightGBMモデル実装
3. ✅ ハイパーパラメータチューニング
4. ✅ ARIMA+LightGBMのアンサンブル

**必要パッケージ**:
```bash
pip install lightgbm scikit-learn optuna
```

**期待精度**: MAE 0.8°C → **0.6-0.7°C**

---

### フェーズ3（2-3週間）: Prophet追加

**優先度**: 🔥 中

1. ✅ Prophet実装
2. ✅ 3モデルアンサンブル
3. ✅ モデル選択機能（CLI）

**必要パッケージ**:
```bash
pip install prophet
```

**期待精度**: MAE 0.6°C → **0.5-0.6°C**

---

### フェーズ4（オプション）: ディープラーニング

**優先度**: 低（データ量が十分な場合のみ）

1. LSTM実装
2. 大量データ収集（3-5年分）
3. GPU環境構築

**必要パッケージ**:
```bash
pip install tensorflow torch
```

---

## 実装例（フェーズ1: Auto ARIMA）

### ファイル構成

```
src/agrr_core/adapter/services/
├── prediction_arima_service.py  # 既存
├── prediction_arima_auto_service.py  # 新規（Auto ARIMA）
├── prediction_sarima_service.py  # 新規（SARIMA）
└── prediction_sarimax_service.py  # 新規（SARIMAX）
```

### コード例

```python
# prediction_arima_auto_service.py
"""Auto ARIMA prediction service with automatic parameter selection."""

from pmdarima import auto_arima
import numpy as np
from typing import List, Dict, Any

from agrr_core.entity import WeatherData, Forecast
from agrr_core.usecase.gateways.prediction_model_gateway import PredictionModelGateway


class PredictionAutoARIMAService(PredictionModelGateway):
    """Auto ARIMA service with automatic parameter optimization."""
    
    async def _predict_single_metric(
        self,
        historical_data: List[WeatherData],
        metric: str,
        model_config: Dict[str, Any]
    ) -> List[Forecast]:
        """Predict using Auto ARIMA."""
        
        # Extract data
        data = self._extract_metric_data(historical_data, metric)
        
        # Auto ARIMA model selection
        model = auto_arima(
            data,
            start_p=1, max_p=7,
            start_q=1, max_q=7,
            d=None,  # Auto-determine differencing
            seasonal=True,
            m=7,  # Weekly seasonality
            start_P=0, max_P=2,
            start_Q=0, max_Q=2,
            D=None,  # Auto-determine seasonal differencing
            trace=False,
            error_action='ignore',
            suppress_warnings=True,
            stepwise=True,
            n_jobs=-1
        )
        
        # Make predictions
        prediction_days = model_config.get('prediction_days', 30)
        predictions, conf_int = model.predict(
            n_periods=prediction_days,
            return_conf_int=True,
            alpha=0.05  # 95% confidence interval
        )
        
        # Create forecasts
        forecasts = []
        start_date = historical_data[-1].time + timedelta(days=1)
        
        for i, (pred, (lower, upper)) in enumerate(zip(predictions, conf_int)):
            forecast_date = start_date + timedelta(days=i)
            
            forecast = Forecast(
                date=forecast_date,
                predicted_value=float(pred),
                confidence_lower=float(lower),
                confidence_upper=float(upper)
            )
            forecasts.append(forecast)
        
        return forecasts
```

---

## CLI拡張

```bash
# 現在
agrr predict --input historical.json --output predictions.json --days 30

# 改善後
agrr predict --input historical.json --output predictions.json \
  --days 30 \
  --model auto-arima \  # auto-arima, sarima, sarimax, lightgbm, prophet, ensemble
  --confidence-level 0.95 \
  --enable-seasonal \
  --forecast-quality high  # low, medium, high (計算時間とトレードオフ)
```

---

## 評価指標

### 現在（ARIMA）

| 指標 | 30日予測 | 60日予測 | 90日予測 |
|------|---------|---------|---------|
| MAE | 1.5°C | 2.5°C | 3.5°C |
| RMSE | 2.0°C | 3.2°C | 4.5°C |

### 目標（Auto ARIMA + 季節性）

| 指標 | 30日予測 | 60日予測 | 90日予測 |
|------|---------|---------|---------|
| MAE | **1.0°C** | **1.8°C** | **2.5°C** |
| RMSE | **1.3°C** | **2.3°C** | **3.2°C** |

### 目標（LightGBM + アンサンブル）

| 指標 | 30日予測 | 60日予測 | 90日予測 |
|------|---------|---------|---------|
| MAE | **0.7°C** | **1.2°C** | **1.8°C** |
| RMSE | **0.9°C** | **1.5°C** | **2.3°C** |

---

## 次のステップ

### すぐに実施

1. ✅ Auto ARIMAの実装とテスト
2. ✅ 既存テストケースの拡張
3. ✅ ドキュメント更新

### 中期的に実施

1. LightGBM実装
2. 特徴量エンジニアリング
3. アンサンブル手法

### 長期的に検討

1. Prophet導入
2. ディープラーニング（データ量次第）
3. リアルタイム予測更新

---

## 参考資料

- [pmdarima Documentation](https://alkaline-ml.com/pmdarima/)
- [LightGBM Documentation](https://lightgbm.readthedocs.io/)
- [Prophet Documentation](https://facebook.github.io/prophet/)
- [Time Series Forecasting Best Practices](https://github.com/microsoft/forecasting)

---

**作成者**: AI分析システム  
**最終更新**: 2025年10月14日

