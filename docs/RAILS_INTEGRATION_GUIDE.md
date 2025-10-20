# Rails側での新agrr.core統合ガイド

## 🎯 修正が必要な理由

新しいagrr.coreは**マルチメトリック予測**を行い、以下のフォーマットで出力します：

```json
{
  "predictions": [
    {
      "date": "2025-10-21T00:00:00",
      "predicted_value": 23.5,
      "temperature": 23.5,
      "temperature_max": 26.4,
      "temperature_min": 19.8,
      "confidence_lower": 19.2,
      "confidence_upper": 27.8
    }
  ]
}
```

Rails側の`transform_predictions_to_weather_data`メソッドは、`temperature_max`/`temperature_min`が**直接含まれている**場合にそれを使う必要があります。

---

## 📝 必要な修正

### ファイル: `app/gateways/agrr/prediction_gateway.rb`

#### 修正箇所: `transform_predictions_to_weather_data` メソッド

**Before（現在のコード）:**
```ruby
def transform_predictions_to_weather_data(prediction_result, historical_data)
  stats = calculate_historical_stats(historical_data['data'])
  
  weather_data = prediction_result['predictions'].map do |prediction|
    predicted_temp_mean = prediction['predicted_value']
    
    # 平均気温から最高気温・最低気温を推定 ← ここが飽和の原因！
    temp_max = predicted_temp_mean + stats[:temp_range_half]
    temp_min = predicted_temp_mean - stats[:temp_range_half]
    
    {
      'time' => prediction['date'].split('T').first,
      'temperature_2m_max' => temp_max.to_f.round(2),
      'temperature_2m_min' => temp_min.to_f.round(2),
      'temperature_2m_mean' => predicted_temp_mean.to_f.round(2),
      'precipitation_sum' => stats[:avg_precipitation].to_f.round(2),
      'sunshine_duration' => stats[:avg_sunshine].to_f.round(2),
      'wind_speed_10m_max' => stats[:avg_wind_speed].to_f.round(2),
      'weather_code' => 0
    }
  end
  
  { 'data' => weather_data }
end
```

**After（修正後）:**
```ruby
def transform_predictions_to_weather_data(prediction_result, historical_data)
  stats = calculate_historical_stats(historical_data['data'])
  
  weather_data = prediction_result['predictions'].map do |prediction|
    # 新フォーマット対応：temperature_max/temperature_min が含まれているか確認
    if prediction['temperature_max'] && prediction['temperature_min']
      # ✅ LightGBMマルチメトリック予測（新フォーマット）
      # モデルが予測した値をそのまま使用（飽和問題を解決）
      predicted_temp_mean = prediction['temperature'] || prediction['predicted_value']
      temp_max = prediction['temperature_max']
      temp_min = prediction['temperature_min']
      
      Rails.logger.debug "🆕 [AGRR] Using multi-metric predictions (temp_max: #{temp_max}, temp_min: #{temp_min})"
    else
      # ❌ 従来フォーマット（predicted_valueのみ）
      # 平均気温から最高気温・最低気温を推定（飽和する）
      predicted_temp_mean = prediction['predicted_value']
      temp_max = predicted_temp_mean + stats[:temp_range_half]
      temp_min = predicted_temp_mean - stats[:temp_range_half]
      
      Rails.logger.debug "📊 [AGRR] Using legacy format (estimated temp_max/min)"
    end
    
    {
      'time' => prediction['date'].split('T').first,
      'temperature_2m_max' => temp_max.to_f.round(2),
      'temperature_2m_min' => temp_min.to_f.round(2),
      'temperature_2m_mean' => predicted_temp_mean.to_f.round(2),
      'precipitation_sum' => stats[:avg_precipitation].to_f.round(2),
      'sunshine_duration' => stats[:avg_sunshine].to_f.round(2),
      'wind_speed_10m_max' => stats[:avg_wind_speed].to_f.round(2),
      'weather_code' => 0
    }
  end
  
  { 'data' => weather_data }
end
```

---

## ✅ 修正の効果

### Before（飽和していた）
```
予測: 平均 21.66°C
↓（単純計算）
最高: 21.66 + 4.0 = 25.66°C
最低: 21.66 - 4.0 = 17.66°C
日較差: 8.0°C（固定）← 飽和！
```

### After（改善後）
```
予測: 平均 23.5°C、最高 26.4°C、最低 19.8°C（全てモデル予測）
日較差: 6.6°C（変動）← リアル！
```

---

## 🔧 修正手順

### 1. Rails側のファイルを編集
```bash
cd /home/akishige/projects/agrr
vi app/gateways/agrr/prediction_gateway.rb
```

### 2. `transform_predictions_to_weather_data` メソッドを上記のコードで置き換え

### 3. 動作確認
```bash
# Railsコンソールで確認
rails c

# 予測を実行してログを確認
farm = Farm.last
farm.predict_weather(days: 7)

# ログに以下が出力されることを確認：
# 🆕 [AGRR] Using multi-metric predictions (temp_max: 26.4, temp_min: 19.8)
```

### 4. ブラウザで確認
```
http://localhost:3000/us/farms/87
```

温度チャートが正しく表示され、エラーが出ないことを確認

---

## 🚀 予測される改善効果

1. **飽和問題の解消**: 最高・最低気温が現実的な値になる
2. **予測精度向上**: 独立したモデルで学習するため精度UP
3. **日較差の正確性**: 6-15°Cの変動を正しく表現

---

## ⚠️ 注意事項

### 後方互換性
- ✅ ARIMAモデル: 従来通り動作（predicted_valueのみ）
- ✅ 古いLightGBM出力: 従来通り推定計算
- ✅ 新しいLightGBM出力: temperature_max/minを直接使用

### エラーハンドリング
```ruby
# nilチェックを追加（安全性向上）
predicted_temp_mean = prediction['temperature'] || prediction['predicted_value'] || 15.0
temp_max = prediction['temperature_max'] || (predicted_temp_mean + stats[:temp_range_half])
temp_min = prediction['temperature_min'] || (predicted_temp_mean - stats[:temp_range_half])
```

---

## 📊 確認方法

修正後、以下のコマンドで出力を確認：

```bash
# tmp/debug ディレクトリのログを確認
tail -f log/development.log | grep AGRR

# デバッグファイルを確認
cat tmp/debug/prediction_output_*.json | jq '.predictions[0]'
```

**この修正により、飽和問題が完全に解決されます！** 🎉

