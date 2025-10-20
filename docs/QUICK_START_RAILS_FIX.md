# 🚀 Rails側修正 クイックスタート

## 🎯 やること（1箇所だけ）

### ファイル
```
app/gateways/agrr/prediction_gateway.rb
```

### メソッド
```
transform_predictions_to_weather_data
```

---

## 📝 修正内容（コピペOK）

### 現在のコード（70-73行目あたり）を探す：
```ruby
predicted_temp_mean = prediction['predicted_value']

# 平均気温から最高気温・最低気温を推定
temp_max = predicted_temp_mean + stats[:temp_range_half]
temp_min = predicted_temp_mean - stats[:temp_range_half]
```

### ↓ 以下に置き換える：
```ruby
# 新フォーマット対応（temperature_max/minが含まれているか確認）
if prediction['temperature_max'] && prediction['temperature_min']
  # LightGBMマルチメトリック予測の結果（モデルが予測した値を使用）
  predicted_temp_mean = prediction['temperature'] || prediction['predicted_value']
  temp_max = prediction['temperature_max']
  temp_min = prediction['temperature_min']
else
  # 従来フォーマット（ARIMAや古いLightGBM）
  predicted_temp_mean = prediction['predicted_value']
  temp_max = predicted_temp_mean + stats[:temp_range_half]
  temp_min = predicted_temp_mean - stats[:temp_range_half]
end
```

---

## ✅ これだけ！

### 効果
- ✅ 飽和問題が解決される
- ✅ 後方互換性も維持（ARIMAも動作）
- ✅ 最高・最低気温が独立したモデル予測になる

### Before
```
日較差: 8.0°C（固定・飽和）
```

### After
```
日較差: 6-15°C（変動・リアル）
```

---

## 🔍 確認方法

修正後、ブラウザで農場ページを開いて：
1. 温度チャートが表示される
2. エラーが出ない
3. ログに「🆕 [AGRR] Using multi-metric predictions」が出る（オプション）

---

**詳細**: `docs/RAILS_INTEGRATION_GUIDE.md` 参照

