# アメリカの気象データ取得ガイド

## すぐに使える方法：Open-Meteo API（推奨）✅

### 特徴

- ✅ **完全無料** - 登録不要、API制限なし
- ✅ **すぐに使える** - 既に実装・動作確認済み
- ✅ **世界中対応** - アメリカを含む全世界の座標
- ✅ **高品質** - ERA5再解析データベース使用

### 使用方法

#### 1. 基本的な使用

```bash
# ニューヨーク（過去7日間）
agrr weather --location 40.7128,-74.0060 --days 7

# ロサンゼルス（過去30日間）
agrr weather --location 34.0522,-118.2437 --days 30

# シカゴ（JSON形式で出力）
agrr weather --location 41.8781,-87.6298 --days 7 --json
```

#### 2. 特定期間のデータ取得

```bash
# 2024年1月のデータ
agrr weather --location 40.7128,-74.0060 --start-date 2024-01-01 --end-date 2024-01-31

# 2024年全体のデータ（JSON保存）
agrr weather --location 40.7128,-74.0060 --start-date 2024-01-01 --end-date 2024-12-31 --json > ny_2024.json
```

#### 3. 複数都市のデータ取得（スクリプト例）

```bash
#!/bin/bash
# fetch_us_cities.sh

# アメリカ主要都市の座標
declare -A cities=(
    ["new_york"]="40.7128,-74.0060"
    ["los_angeles"]="34.0522,-118.2437"
    ["chicago"]="41.8781,-87.6298"
    ["houston"]="29.7604,-95.3698"
    ["phoenix"]="33.4484,-112.0740"
    ["philadelphia"]="39.9526,-75.1652"
    ["san_antonio"]="29.4241,-98.4936"
    ["san_diego"]="32.7157,-117.1611"
    ["dallas"]="32.7767,-96.7970"
    ["san_jose"]="37.3382,-121.8863"
)

# 各都市のデータを取得
for city in "${!cities[@]}"; do
    echo "Fetching data for $city..."
    agrr weather --location ${cities[$city]} --days 30 --json > "${city}_weather.json"
done
```

## アメリカ主要都市の座標一覧

### 東海岸

| 都市 | 緯度 | 経度 | コマンド例 |
|------|------|------|------------|
| New York, NY | 40.7128 | -74.0060 | `agrr weather --location 40.7128,-74.0060 --days 7` |
| Boston, MA | 42.3601 | -71.0589 | `agrr weather --location 42.3601,-71.0589 --days 7` |
| Philadelphia, PA | 39.9526 | -75.1652 | `agrr weather --location 39.9526,-75.1652 --days 7` |
| Washington, DC | 38.9072 | -77.0369 | `agrr weather --location 38.9072,-77.0369 --days 7` |
| Miami, FL | 25.7617 | -80.1918 | `agrr weather --location 25.7617,-80.1918 --days 7` |
| Atlanta, GA | 33.7490 | -84.3880 | `agrr weather --location 33.7490,-84.3880 --days 7` |

### 中西部

| 都市 | 緯度 | 経度 | コマンド例 |
|------|------|------|------------|
| Chicago, IL | 41.8781 | -87.6298 | `agrr weather --location 41.8781,-87.6298 --days 7` |
| Detroit, MI | 42.3314 | -83.0458 | `agrr weather --location 42.3314,-83.0458 --days 7` |
| Minneapolis, MN | 44.9778 | -93.2650 | `agrr weather --location 44.9778,-93.2650 --days 7` |
| St. Louis, MO | 38.6270 | -90.1994 | `agrr weather --location 38.6270,-90.1994 --days 7` |

### 南部

| 都市 | 緯度 | 経度 | コマンド例 |
|------|------|------|------------|
| Houston, TX | 29.7604 | -95.3698 | `agrr weather --location 29.7604,-95.3698 --days 7` |
| Dallas, TX | 32.7767 | -96.7970 | `agrr weather --location 32.7767,-96.7970 --days 7` |
| San Antonio, TX | 29.4241 | -98.4936 | `agrr weather --location 29.4241,-98.4936 --days 7` |
| Austin, TX | 30.2672 | -97.7431 | `agrr weather --location 30.2672,-97.7431 --days 7` |
| New Orleans, LA | 29.9511 | -90.0715 | `agrr weather --location 29.9511,-90.0715 --days 7` |

### 西海岸

| 都市 | 緯度 | 経度 | コマンド例 |
|------|------|------|------------|
| Los Angeles, CA | 34.0522 | -118.2437 | `agrr weather --location 34.0522,-118.2437 --days 7` |
| San Francisco, CA | 37.7749 | -122.4194 | `agrr weather --location 37.7749,-122.4194 --days 7` |
| San Diego, CA | 32.7157 | -117.1611 | `agrr weather --location 32.7157,-117.1611 --days 7` |
| San Jose, CA | 37.3382 | -121.8863 | `agrr weather --location 37.3382,-121.8863 --days 7` |
| Seattle, WA | 47.6062 | -122.3321 | `agrr weather --location 47.6062,-122.3321 --days 7` |
| Portland, OR | 45.5152 | -122.6784 | `agrr weather --location 45.5152,-122.6784 --days 7` |

### その他主要都市

| 都市 | 緯度 | 経度 | コマンド例 |
|------|------|------|------------|
| Phoenix, AZ | 33.4484 | -112.0740 | `agrr weather --location 33.4484,-112.0740 --days 7` |
| Las Vegas, NV | 36.1699 | -115.1398 | `agrr weather --location 36.1699,-115.1398 --days 7` |
| Denver, CO | 39.7392 | -104.9903 | `agrr weather --location 39.7392,-104.9903 --days 7` |
| Salt Lake City, UT | 40.7608 | -111.8910 | `agrr weather --location 40.7608,-111.8910 --days 7` |

## 出力フォーマット

### テーブル形式（デフォルト）

```bash
$ agrr weather --location 40.7128,-74.0060 --days 3

================================================================================
WEATHER FORECAST
================================================================================

Location: 40.7128°N, 74.0060°W | Elevation: 7m | Timezone: America/New_York

Date         Max Temp   Min Temp   Avg Temp   Precip   Sunshine  
----------------------------------------------------------------------
2024-10-15   18.5°C     12.2°C     15.4°C     2.1mm    6.5h      
2024-10-16   20.1°C     13.8°C     17.0°C     0.0mm    8.2h      
2024-10-17   19.3°C     14.1°C     16.7°C     5.3mm    4.1h      
```

### JSON形式

```bash
$ agrr weather --location 40.7128,-74.0060 --days 3 --json

{
  "success": true,
  "data": {
    "data": [
      {
        "time": "2024-10-15",
        "temperature_2m_max": 18.5,
        "temperature_2m_min": 12.2,
        "temperature_2m_mean": 15.4,
        "precipitation_sum": 2.1,
        "sunshine_duration": 23400.0,
        "sunshine_hours": 6.5
      }
    ],
    "total_count": 3,
    "location": {
      "latitude": 40.7128,
      "longitude": -74.0060,
      "elevation": 7.0,
      "timezone": "America/New_York"
    }
  }
}
```

## 農業応用例

### 1. 成長度日（GDD）計算

```bash
# ニューヨークの過去90日間のデータを取得
agrr weather --location 40.7128,-74.0060 --days 90 --json > ny_weather.json

# 作物プロファイルを作成
agrr crop --query "corn Field Corn" > corn_profile.json

# 成長進捗を計算
agrr progress --crop-file corn_profile.json --start-date 2024-05-01 --weather-file ny_weather.json
```

### 2. 最適な栽培期間の計算

```bash
# カリフォルニアのトマト栽培
agrr weather --location 34.0522,-118.2437 --start-date 2024-01-01 --end-date 2024-12-31 --json > la_weather.json
agrr crop --query "tomato Beefsteak" > tomato_profile.json

# 最適な栽培開始日を計算
agrr optimize period \
  --crop-file tomato_profile.json \
  --evaluation-start 2024-04-01 \
  --evaluation-end 2024-09-30 \
  --weather-file la_weather.json \
  --field-file field.json
```

### 3. 気象予測

```bash
# 過去のデータで機械学習モデルを訓練
agrr weather --location 40.7128,-74.0060 --days 365 --json > historical.json

# 将来30日間の気象を予測
agrr predict --input historical.json --output forecast.json --days 30 --model lightgbm
```

## トラブルシューティング

### エラー: "No weather data found"

**原因：** 日付範囲が遠すぎる過去または未来

**解決策：**
- Open-Meteoは2年前から現在までのデータを提供
- 最新のデータは通常、前日まで

```bash
# ❌ 失敗例
agrr weather --location 40.7128,-74.0060 --start-date 2020-01-01 --end-date 2020-12-31

# ✅ 成功例  
agrr weather --location 40.7128,-74.0060 --days 365  # 過去365日
```

### 座標の確認方法

Google Mapsで座標を取得：
1. Google Mapsで場所を右クリック
2. 座標をクリックしてコピー
3. 緯度,経度の形式で使用

## まとめ

### ✅ 今すぐ使える

```bash
# アメリカの任意の場所の気象データを取得
agrr weather --location <緯度>,<経度> --days <日数>
```

### 📚 サンプルコード

完全なサンプルは以下を参照：
- `examples/us_weather_example.sh` - 複数都市のデータ取得
- `examples/gdd_calculation.sh` - 成長度日計算
- `docs/NOAA_IMPLEMENTATION_SUMMARY.md` - NOAA実装の詳細

### 💡 Tips

1. **大量データの取得**：`--json` を使用してファイルに保存
2. **定期実行**：cronで毎日実行して最新データを取得
3. **キャッシュ**：取得済みデータは再利用可能

