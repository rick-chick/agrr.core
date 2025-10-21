# agrr.core Interface Specification

## 厳密なインターフェース定義

### LightGBM 出力フォーマット（厳密）

```json
{
  "predictions": [
    {
      "date": "2024-11-01T00:00:00",
      "temperature": 18.5,
      "temperature_max": 22.0,
      "temperature_min": 15.0,
      "temperature_confidence_lower": 16.2,
      "temperature_confidence_upper": 20.8,
      "temperature_max_confidence_lower": 19.0,
      "temperature_max_confidence_upper": 25.0,
      "temperature_min_confidence_lower": 12.0,
      "temperature_min_confidence_upper": 18.0
    }
  ],
  "model_type": "LightGBM",
  "prediction_days": 30,
  "metrics": ["temperature", "temperature_max", "temperature_min"]
}
```

### ARIMA 出力フォーマット（厳密）

```json
{
  "predictions": [
    {
      "date": "2024-11-01T00:00:00",
      "predicted_value": 18.5,
      "confidence_lower": 16.2,
      "confidence_upper": 20.8
    }
  ],
  "model_type": "ARIMA",
  "prediction_days": 30
}
```

## 禁止事項

1. **後方置換（Backward Compatibility）は一切禁止**
2. **`predicted_value`フィールドはARIMAのみ許可**
3. **LightGBMで`predicted_value`を使用した場合はエラー**
4. **不正な入力は即座にエラー**

## エラー条件

- LightGBM出力に`predicted_value`が含まれる場合
- ARIMA出力に`temperature_max`/`temperature_min`が含まれる場合
- 不正なメトリック指定
- 不足データ（90日未満でLightGBM使用）

## 実装方針

- IFに従わないコードは即座にエラー
- 後方置換コードは削除
- 厳密なバリデーション実装
