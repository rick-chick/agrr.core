# Rails側の修正が必要

## 問題

agrr.coreの新しいマルチメトリック予測フォーマットでは：
```json
{
  "predictions": [
    {
      "date": "2025-10-21",
      "predicted_value": 23.5,        ← 後方互換性のため追加済み
      "temperature": 23.5,
      "temperature_max": 26.4,        ← 新フィールド
      "temperature_min": 19.8,        ← 新フィールド
      "confidence_lower": 19.2,
      "confidence_upper": 27.8
    }
  ]
}
```

Rails側の`app/gateways/agrr/prediction_gateway.rb`の`transform_predictions_to_weather_data`メソッドを以下のように修正してください：

```ruby
def transform_predictions_to_weather_data(prediction_result, historical_data)
  # 履歴データから統計値を計算（降水量などの補完用）
  stats = calculate_historical_stats(historical_data['data'])
  
  # 予測データを完全な天気データ形式に変換
  weather_data = prediction_result['predictions'].map do |prediction|
    # 新しいフォーマット対応：temperature_max/temperature_min が直接含まれている場合
    if prediction['temperature_max'] && prediction['temperature_min']
      # LightGBMマルチメトリック予測の結果（新フォーマット）
      predicted_temp_mean = prediction['temperature'] || prediction['predicted_value']
      temp_max = prediction['temperature_max']
      temp_min = prediction['temperature_min']
    else
      # 従来のフォーマット（predicted_valueのみ）
      predicted_temp_mean = prediction['predicted_value']
      
      # 平均気温から最高気温・最低気温を推定
      # 履歴データの平均的な日較差を使用
      temp_max = predicted_temp_mean + stats[:temp_range_half]
      temp_min = predicted_temp_mean - stats[:temp_range_half]
    end
    
    {
      'time' => prediction['date'].split('T').first,
      'temperature_2m_max' => temp_max.to_f.round(2),
      'temperature_2m_min' => temp_min.to_f.round(2),
      'temperature_2m_mean' => predicted_temp_mean.to_f.round(2),
      'precipitation_sum' => stats[:avg_precipitation].to_f.round(2),
      'sunshine_duration' => stats[:avg_sunshine].to_f.round(2),
      'wind_speed_10m_max' => stats[:avg_wind_speed].to_f.round(2),
      'weather_code' => 0  # 晴れを仮定
    }
  end
  
  {
    'data' => weather_data
  }
end
```

## 効果

- ✅ **新フォーマット対応**: temperature_max/temperature_minを直接使用（飽和問題解決）
- ✅ **後方互換性**: predicted_valueのみの場合は従来通り計算
- ✅ **ARIMA予測も動作**: ARIMAモデルでも引き続き使用可能

## テスト

修正後、以下で動作確認：
```bash
# agrr.coreの予測を実行
cd agrr.core
python3 -m agrr_core.cli weather --location 35.6762,139.6503 --days 120 --json > /tmp/historical.json
python3 -m agrr_core.cli predict --input /tmp/historical.json --output /tmp/predictions.json --days 7 --model lightgbm

# 出力を確認
cat /tmp/predictions.json | jq '.predictions[0]'
# → temperature, temperature_max, temperature_min, predicted_value が全て含まれている

# Rails側でこのJSONを読み込んでテスト
```
