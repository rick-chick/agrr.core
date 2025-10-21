# インド天気データ取得 - CLI使用ガイド

## 概要

NOAA ISD（Integrated Surface Database）を使用して、インドの主要農業地域49地点から2000年以降の高解像度天気データをCLIで取得できます。

## 実装完了内容 ✅

### データソース: `--data-source noaa`

- **観測所数**: 49地点（インド主要農業地域）
- **カバレッジ**: パンジャブ、UP、マハーラーシュトラ、カルナータカ、タミル・ナードゥ等
- **期間**: 2000年頃〜現在
- **解像度**: 
  - 時間解像度: hourly（時間単位）→ daily統計に集計
  - 空間解像度: 実測値（観測所ベース）
- **データ品質**: 高品質（公式観測所の実測データ）

### NASA POWERとの比較

| 項目 | NOAA ISD (`--data-source noaa`) | NASA POWER (`--data-source nasa-power`) |
|------|----------------------------------|------------------------------------------|
| 空間解像度 | ⭐⭐⭐⭐⭐ 観測所（実測） | ⭐⭐ グリッド（0.5度、約50km） |
| データ品質 | ⭐⭐⭐⭐⭐ 高品質実測 | ⭐⭐⭐ 衛星+再解析 |
| 時間解像度 | ⭐⭐⭐⭐⭐ hourly | ⭐⭐⭐⭐ daily |
| 農業利用 | ✅ 推奨 | ❌ 解像度が粗い |

**結論**: 農業用途には`--data-source noaa`を使用してください。

## 基本的な使い方

### 1. デリーの2023年データ取得

```bash
agrr weather --location 28.5844,77.2031 \
  --start-date 2023-01-01 --end-date 2023-12-31 \
  --data-source noaa --json > delhi_2023.json
```

### 2. ルディヤーナ（パンジャブ小麦ベルト）の2022年データ

```bash
agrr weather --location 30.9000,75.8500 \
  --start-date 2022-01-01 --end-date 2022-12-31 \
  --data-source noaa --json > ludhiana_2022.json
```

### 3. ムンバイの最近30日間

```bash
agrr weather --location 19.0896,72.8681 \
  --days 30 --data-source noaa
```

### 4. バンガロールの2021年データ

```bash
agrr weather --location 12.9500,77.6681 \
  --start-date 2021-01-01 --end-date 2021-12-31 \
  --data-source noaa --json > bangalore_2021.json
```

## インド主要農業地域の座標

### 北部（小麦・米ベルト）

```bash
# パンジャブ州
Ludhiana:     30.9000,75.8500   # 農業の中心都市
Amritsar:     31.6300,74.8700   # 黄金寺院の街
Bathinda:     30.2000,74.9500   # 綿花地帯
Patiala:      30.3400,76.3900   # 歴史的都市

# ハリヤーナー州
Hisar:        29.1500,75.7200   # 農業研究の中心
Karnal:       29.6900,76.9900   # 米の街
Rohtak:       28.8900,76.6400   # 穀倉地帯

# ウッタル・プラデーシュ州（最大農業生産州）
Lucknow:      26.7600,80.8800   # 州都
Kanpur:       26.4400,80.3600   # 工業・農業都市
Varanasi:     25.4500,82.8600   # 東部の中心
Prayagraj:    25.4400,81.7300   # ガンジス平原
Agra:         27.1600,77.9600   # タージマハルの街
Gorakhpur:    26.7500,83.3600   # 東部農業地帯
```

### デリー首都圏

```bash
Delhi:        28.5844,77.2031   # 首都
```

### 西部（綿花・乾燥地農業）

```bash
# ラージャスターン州
Jaipur:       26.8200,75.8000   # ピンクシティ
Jodhpur:      26.3000,73.0200   # ブルーシティ
Udaipur:      24.6200,73.8900   # 湖の都市
Kota:         25.1600,75.8400   # 教育の街
Bikaner:      28.0100,73.3100   # 砂漠地帯

# グジャラート州
Ahmedabad:    23.0700,72.6300   # 最大都市
Surat:        21.1200,72.7500   # ダイヤモンド産業
Rajkot:       22.3100,70.8100   # 綿花地帯
Vadodara:     22.3400,73.2300   # 文化都市
```

### 西部（マハーラーシュトラ州 - 綿花・サトウキビ）

```bash
Mumbai:       19.0896,72.8681   # 州都・金融の中心
Pune:         18.5800,73.9200   # IT都市
Nagpur:       21.0900,79.0500   # オレンジの街
Nashik:       19.9700,73.8000   # ワインの産地
Aurangabad:   19.8800,75.3400   # 歴史的都市
```

### 中部（大豆・小麦）

```bash
# マディヤ・プラデーシュ州
Bhopal:       23.2800,77.3400   # 州都
Indore:       22.7200,75.8000   # 商業の中心
Jabalpur:     23.1800,79.9900   # 大理石の街
Gwalior:      26.2900,78.2300   # 要塞都市
```

### 南部（米・コーヒー）

```bash
# カルナータカ州
Bangalore:    12.9500,77.6681   # IT都市・州都
Mysore:       12.3100,76.6500   # 宮殿の街
Hubli:        15.3600,75.0800   # 商業都市

# テランガーナ州
Hyderabad:    17.4500,78.4675   # IT都市・州都
Warangal:     18.0000,79.5800   # 歴史的都市

# アーンドラ・プラデーシュ州
Vijayawada:   16.5200,80.6200   # 東部の中心
Visakhapatnam:17.7200,83.2200   # 港湾都市
Tirupati:     13.6300,79.5400   # 巡礼の街

# タミル・ナードゥ州
Chennai:      12.9900,80.1692   # 州都
Coimbatore:   11.0300,77.0400   # 繊維産業
Madurai:      9.8400,78.0900    # 寺院の街
Tiruchirappalli: 10.7700,78.7100 # 中部の中心
```

### 東部（米・ジュート）

```bash
# 西ベンガル州
Kolkata:      22.6544,88.4467   # 州都

# ビハール州
Patna:        25.6000,85.1000   # 州都

# オディシャ州
Bhubaneswar:  20.2500,85.8200   # 州都

# チャッティースガル州
Raipur:       21.1800,81.7300   # 州都

# ジャールカンド州
Ranchi:       23.3100,85.3200   # 州都
```

## 使用例（実践的）

### 例1: 小麦栽培シーズンのデータ（パンジャブ）

```bash
# 2022年11月〜2023年4月（小麦栽培期間）
agrr weather --location 30.9000,75.8500 \
  --start-date 2022-11-01 --end-date 2023-04-30 \
  --data-source noaa --json > punjab_wheat_season.json
```

### 例2: モンスーンシーズンのデータ（ケーララ）

```bash
# 2023年6月〜9月（モンスーン）
agrr weather --location 8.5241,76.9366 \
  --start-date 2023-06-01 --end-date 2023-09-30 \
  --data-source noaa --json > monsoon_2023.json
```

### 例3: 複数年の気候トレンド分析

```bash
# 2020-2023年のデリー
for year in 2020 2021 2022 2023; do
  agrr weather --location 28.5844,77.2031 \
    --start-date ${year}-01-01 --end-date ${year}-12-31 \
    --data-source noaa --json > delhi_${year}.json
done
```

### 例4: 複数地点の同時期データ取得

```bash
# 2023年の主要農業都市
for city in "Ludhiana:30.9000,75.8500" "Lucknow:26.7600,80.8800" "Mumbai:19.0896,72.8681"; do
  name=$(echo $city | cut -d: -f1)
  coords=$(echo $city | cut -d: -f2)
  agrr weather --location $coords \
    --start-date 2023-01-01 --end-date 2023-12-31 \
    --data-source noaa --json > ${name}_2023.json
done
```

## データ品質の確認

取得したデータの品質を確認：

```bash
# JSON形式で取得して確認
agrr weather --location 28.5844,77.2031 \
  --start-date 2023-01-01 --end-date 2023-01-31 \
  --data-source noaa --json | jq '
  {
    total_days: (.data | length),
    temp_range: {
      min: (.data | map(.temperature_2m_min) | min),
      max: (.data | map(.temperature_2m_max) | max)
    },
    precipitation: {
      total: (.data | map(.precipitation_sum) | add),
      days_with_rain: (.data | map(select(.precipitation_sum > 0)) | length)
    }
  }'
```

## 出力データ形式

```json
{
  "data": [
    {
      "time": "2023-01-01",
      "temperature_2m_max": 22.5,
      "temperature_2m_min": 10.2,
      "temperature_2m_mean": 16.3,
      "precipitation_sum": 0.0,
      "wind_speed_10m": 3.5
    }
  ],
  "total_count": 365,
  "location": {
    "latitude": 28.5844,
    "longitude": 77.2031,
    "elevation": null,
    "timezone": "America/New_York"
  },
  "data_source": "noaa"
}
```

**注意**: 
- `sunshine_duration`はNOAA ISDに含まれないため`null`
- 日照時間が必要な場合は別のデータソースを併用

## トラブルシューティング

### エラー: "No weather data found"

```bash
# 最も近い観測所が選択されますが、データがない期間もあります
# 期間を変更して再試行：
agrr weather --location 28.5844,77.2031 \
  --start-date 2022-01-01 --end-date 2022-12-31 \
  --data-source noaa
```

### エラー: ネットワーク接続

```bash
# DNSエラーの場合、ネットワーク接続を確認
ping www.ncei.noaa.gov

# プロキシ環境の場合、環境変数を設定
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
```

### 観測所が見つからない

指定した座標に最も近い観測所が自動選択されます。主要都市以外では、50km以上離れた観測所が選ばれる場合があります。

```bash
# デバッグ情報を確認（エラーメッセージに観測所名が表示される）
agrr weather --location 28.5844,77.2031 \
  --start-date 2023-01-01 --end-date 2023-01-07 \
  --data-source noaa 2>&1 | grep "Station:"
```

## ヘルプとドキュメント

```bash
# CLIヘルプ
agrr --help
agrr weather --help

# ドキュメント
cat docs/guides/INDIA_WEATHER_NOAA_GUIDE.md
cat docs/guides/INDIA_WEATHER_CLI_USAGE.md
```

## 制限事項

1. **観測所の制約**: 主要都市のみカバー（49地点）
2. **日照時間**: データに含まれない
3. **欠測**: 一部の期間でデータが欠けている可能性
4. **ネットワーク**: 実際のHTTPリクエストが必要（キャッシュなし）

## 次のステップ

1. 取得したデータで作物成長予測
2. 複数年データで気候トレンド分析
3. 異なる地域の比較分析

---

**実装日**: 2025-01-21  
**バージョン**: v1.0  
**データソース**: NOAA ISD (Integrated Surface Database)  
**観測所数**: 49地点（インド主要農業地域）

