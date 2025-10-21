# タイ天気データ取得ガイド（NOAA ISD）

## 概要

このガイドでは、NOAA ISD（Integrated Surface Database）を使用してタイの主要農業地域から気温データを取得する方法を説明します。

## 実装完了内容

### 1. 観測所マッピング（81地点）

`WeatherNOAAGateway`に、タイの主要農業地域から選定した81地点の観測所を追加しました：

#### **北部（Northern Region）- 21地点** - 米・果樹・茶の生産地
- **チェンマイ県（Chiang Mai）**: 3地点
  - Chiang Mai Intl, Mae Jo Agromet, Lamphun
- **チェンライ県（Chiang Rai）**: 2地点
  - Chiang Rai, Mae Fah Luang Chiang Rai Intl
- **ランパーン県（Lampang）**: 2地点
  - Lampang, Lampang Agromet
- **ナーン県（Nan）**: 2地点
  - Nan, Nan Agromet
- **その他北部**: パヤオ、プレー、メーホンソン、ターク、ピッサヌローク、ウッタラディット、スコータイ、ペッチャブーン、カムペーンペット等

#### **東北部（Northeastern Region / Isan）- 26地点** - 最大の米生産地域
- **ウドンターニー県（Udon Thani）**: 1地点
- **ノーンカーイ県（Nong Khai）**: 1地点
- **ルーイ県（Loei）**: 2地点
- **サコンナコーン県（Sakon Nakhon）**: 2地点
- **ナコーンパノム県（Nakhon Phanom）**: 2地点
- **コーンケン県（Khon Kaen）**: 2地点
- **ムクダーハーン県（Mukdahan）**: 1地点
- **ロイエット県（Roi Et）**: 2地点
- **チャイヤプーム県（Chaiyaphum）**: 1地点
- **ナコーンラーチャシーマー県（Korat）**: 3地点
- **ブリーラム県（Buriram）**: 2地点
- **スリン県（Surin）**: 2地点
- **ウボンラーチャターニー県（Ubon Ratchathani）**: 2地点
- **シーサケート県（Si Saket）**: 1地点
- **その他**: Kosumphisai, Nongbualamphu等

#### **中部（Central Region）- 24地点** - チャオプラヤー川流域・米の主要生産地
- **ナコーンサワン県（Nakhon Sawan）**: 2地点
- **チャイナート県（Chai Nat）**: 1地点
- **ロッブリー県（Lop Buri）**: 1地点
- **サラブリー県（Saraburi）**: 1地点
- **アユタヤ県（Ayutthaya）**: 1地点
- **スパンブリー県（Suphan Buri）**: 2地点
- **パトゥムターニー県（Pathum Thani）**: 1地点
- **バンコク首都圏**: 3地点
  - Bangkok Intl / Don Mueang Intl, Suvarnabhumi Inter Airport, Bangkok Metropolis
- **その他中部**: ラーチャブリー、カンチャナブリー、ペッチャブリー、プラチュワップキーリーカン、チャチューンサオ、チョンブリー、ラヨーン等

#### **南部（Southern Region）- 18地点** - ゴム・パーム油・果樹の生産地
- **チュムポーン県（Chumphon）**: 1地点
- **ラノーン県（Ranong）**: 1地点
- **スラートターニー県（Surat Thani）**: 2地点
- **ナコーンシータンマラート県**: 2地点
- **クラビー県（Krabi）**: 1地点
- **プーケット県（Phuket）**: 2地点
- **トラン県（Trang）**: 1地点
- **パッタルン県（Phatthalung）**: 1地点
- **ソンクラー県（Songkhla）**: 2地点
- **パッターニー県（Pattani）**: 1地点
- **ヤラー県（Yala）**: 1地点
- **ナラーティワート県（Narathiwat）**: 1地点
- **その他**: コサムイ、チャイアン等

### 2. データ取得範囲

- **期間**: 1940年代〜現在（観測所により異なる）
- **解像度**: 
  - 時間解像度: 時間単位（hourly）→日次統計に集計
  - 空間解像度: 観測所ベース（実測値）
- **データ項目**:
  - 気温（最高・最低・平均）
  - 降水量
  - 風速
  - ※日照時間はNOAA ISDには含まれない
- **タイムゾーン**: Asia/Bangkok（自動設定）

### 3. 主要作物カバレッジ

| 作物 | カバレッジ地域 | 観測所数 |
|------|---------------|---------|
| 米（Rice） | 北部、東北部、中部、南部 | 全域 (71地点) |
| ゴム（Rubber） | 南部 | 18地点 |
| パーム油（Palm Oil） | 南部 | 18地点 |
| キャッサバ（Cassava） | 東北部 | 26地点 |
| サトウキビ（Sugarcane） | 中部、東北部 | 50地点 |
| 果樹（Fruits） | 北部、南部、中部 | 63地点 |
| 茶（Tea） | 北部 | 21地点 |

## 使用方法

### 基本的な使い方

```python
from agrr_core.adapter.gateways.weather_noaa_gateway import WeatherNOAAGateway
from agrr_core.framework.services.clients.http_client import HttpClient

# HTTP クライアントを作成
http_client = HttpClient()

# Gateway を作成
gateway = WeatherNOAAGateway(http_client)

# バンコク（ドンムアン空港）の2024年1月のデータを取得
result = await gateway.get_by_location_and_date_range(
    latitude=13.9130,   # バンコク
    longitude=100.6070,
    start_date="2024-01-01",
    end_date="2024-01-31"
)

# 結果を確認
print(f"Location: {result.location.latitude}, {result.location.longitude}")
print(f"Timezone: {result.location.timezone}")
print(f"Data points: {len(result.weather_data_list)}")

for weather_data in result.weather_data_list:
    print(f"{weather_data.time}: {weather_data.temperature_2m_mean}°C")
```

### 主要農業地域の座標

```python
# 北部（米・果樹）
CHIANG_MAI = (18.767, 98.963)
CHIANG_RAI = (19.885, 99.827)
LAMPANG = (18.271, 99.504)

# 東北部イサーン（最大の米生産地域）
UDON_THANI = (17.386, 102.788)
KHON_KAEN = (16.467, 102.784)
UBON_RATCHATHANI = (15.251, 104.870)
NAKHON_RATCHASIMA = (14.935, 102.079)  # コラート

# 中部（チャオプラヤー川流域・米）
NAKHON_SAWAN = (15.673, 100.137)
AYUTTHAYA = (14.517, 100.717)
SUPHAN_BURI = (14.467, 100.133)
BANGKOK = (13.913, 100.607)

# 南部（ゴム・パーム油）
SURAT_THANI = (9.133, 99.136)
PHUKET = (8.113, 98.317)
HAT_YAI = (6.933, 100.393)
```

### CLI使用例

```bash
# チェンマイの2024年データを取得
python -m agrr_core.cli weather \
  --location 18.767,98.963 \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --source noaa

# イサーン地方（コーンケン）のデータを取得
python -m agrr_core.cli weather \
  --location 16.467,102.784 \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --source noaa \
  --json > khon_kaen_2024.json
```

## データの特徴

### 長所

1. **高品質**: 公式観測所からの実測データ
2. **長期間**: 1940年代から現在まで利用可能（観測所による）
3. **時間解像度**: 時間単位のデータで日次統計を計算
4. **広範囲**: タイ全土81地点をカバー
5. **無料**: NOAAの公開データ
6. **信頼性**: グローバル標準の品質管理
7. **自動タイムゾーン**: Asia/Bangkokタイムゾーンを自動設定

### 短所

1. **日照時間**: データに含まれない
2. **欠測**: 一部の期間でデータが欠けている可能性
3. **ネットワーク**: 実際のHTTPリクエストが必要
4. **空間解像度**: 主要都市・空港のみ（農村部の観測所は限定的）

## データ品質チェック

### 温度範囲の妥当性

タイの気候帯別の典型的な温度範囲：

- **北部（チェンマイ、チェンライ）**: 10°C 〜 42°C（冬季は涼しい）
- **東北部イサーン（ウドンターニー、コーンケン）**: 15°C 〜 40°C（乾季と雨季の差が大きい）
- **中部（バンコク、アユタヤ）**: 20°C 〜 38°C（年間通して温暖）
- **南部（プーケット、スラートターニー）**: 22°C 〜 36°C（熱帯性、高温多湿）

### データの欠測対応

```python
import pandas as pd
from datetime import datetime, timedelta

# 欠測データの確認
def check_missing_data(result, start_date, end_date):
    """Check for missing dates in weather data."""
    missing_dates = []
    expected_dates = pd.date_range(start_date, end_date, freq='D')
    
    actual_dates = {wd.time.date() for wd in result.weather_data_list}
    
    for date in expected_dates:
        if date.date() not in actual_dates:
            missing_dates.append(date)
    
    if missing_dates:
        print(f"Missing data for {len(missing_dates)} days")
        print(f"First missing: {missing_dates[0]}")
        print(f"Last missing: {missing_dates[-1]}")
        # 補間や代替データソースの検討
    
    return missing_dates
```

## 季節別データ取得の推奨

### 稲作サイクルに合わせたデータ取得

```python
# タイの稲作サイクル
# 雨季作（メインクロップ）: 5月〜11月
# 乾季作（セカンドクロップ）: 11月〜4月

# 雨季作データ
rainy_season_data = await gateway.get_by_location_and_date_range(
    latitude=16.467,  # コーンケン（イサーン最大の米生産地）
    longitude=102.784,
    start_date="2024-05-01",
    end_date="2024-11-30"
)

# 乾季作データ
dry_season_data = await gateway.get_by_location_and_date_range(
    latitude=14.517,  # アユタヤ（中部の米生産地）
    longitude=100.717,
    start_date="2023-11-01",
    end_date="2024-04-30"
)
```

## 他のデータソースとの比較

### NOAA ISD vs NASA POWER

| 項目 | NOAA ISD | NASA POWER |
|------|----------|------------|
| 空間解像度 | 観測所（高） | 0.5度グリッド（中） |
| 時間解像度 | 時間単位 | 日単位 |
| データ期間 | 1940年代〜 | 1984年〜 |
| 日照時間 | ✗ | ✓ |
| カバレッジ | 主要都市・空港（81地点） | 全球均一 |
| データ品質 | 実測値（高） | 衛星+地上融合（中） |
| タイ農業地域カバー | ★★★★★ | ★★★★☆ |

### NOAA ISD vs タイ気象局（TMD）

| 項目 | NOAA ISD | TMD（タイ気象局） |
|------|----------|---------------------|
| 観測所数 | 81地点 | 数百地点（推定） |
| データアクセス | API/HTTP（容易） | スクレイピング必要 |
| 品質管理 | グローバル標準 | タイ国内標準 |
| 信頼性 | 高 | 高 |
| 国際互換性 | 高 | 低 |

## テスト

### ユニットテスト

```bash
pytest tests/test_adapter/test_weather_noaa_gateway.py -v
```

### E2Eテスト（実際のデータ取得）

```bash
# すべてのE2Eテストを実行
pytest tests/test_e2e/test_noaa_thailand.py -v -m e2e

# 特定の地域のみテスト
pytest tests/test_e2e/test_noaa_thailand.py::TestNOAAThailandE2E::test_bangkok_weather_2023 -v -m e2e

# 全地域カバレッジテスト
pytest tests/test_e2e/test_noaa_thailand.py::TestNOAAThailandRegionalCoverage -v -m e2e
```

**注意**: E2Eテストは実際のHTTPリクエストを行うため、ネットワーク接続が必要で、実行に時間がかかります。

## トラブルシューティング

### データが取得できない場合

1. **観測所の確認**: 指定した座標に最も近い観測所を確認
   ```python
   # 最寄りの観測所を確認
   from agrr_core.adapter.gateways.weather_noaa_gateway import THAILAND_LOCATION_MAPPING
   
   target_lat, target_lon = 18.767, 98.963
   min_distance = float('inf')
   nearest = None
   
   for (lat, lon), (usaf, wban, name, st_lat, st_lon) in THAILAND_LOCATION_MAPPING.items():
       distance = ((target_lat - lat) ** 2 + (target_lon - lon) ** 2) ** 0.5
       if distance < min_distance:
           min_distance = distance
           nearest = (name, st_lat, st_lon, usaf)
   
   print(f"Nearest station: {nearest[0]}")
   print(f"Location: ({nearest[1]}, {nearest[2]})")
   print(f"USAF: {nearest[3]}")
   ```

2. **期間の確認**: 2000年以前や最新データは存在しない可能性
3. **ネットワーク**: NOAAサーバーへの接続を確認
4. **レート制限**: 大量リクエスト時は間隔を空ける

### エラーメッセージ

```python
# WeatherDataNotFoundError: データが見つからない
# → 期間を変更するか、別の観測所を試す

# WeatherAPIError: APIエラー
# → ネットワーク接続やNOAAサーバーの状態を確認
```

### ファイル名形式の注意

NOAA ISDのファイル名は `{USAF}{WBAN}.csv` 形式（ハイフンなし）です。
例: `48456099999.csv` (Bangkok Don Mueang)

## 今後の拡張

1. **観測所の追加**: さらに地方都市の観測所を追加
2. **データ補間**: 欠測データの補間アルゴリズム実装
3. **キャッシュ**: 取得済みデータのローカルキャッシュ
4. **バッチ取得**: 複数地点・複数年のバッチ取得機能
5. **農業指標**: GDD（Growing Degree Days）の自動計算

## 参考資料

- [NOAA ISD公式サイト](https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database)
- [NOAA ISDデータフォーマット](https://www.ncei.noaa.gov/data/global-hourly/doc/)
- [タイ農業統計](http://www.oae.go.th/)
- [タイ気象局（TMD）](https://www.tmd.go.th/)

## 実装ファイル

- Gateway: `src/agrr_core/adapter/gateways/weather_noaa_gateway.py`
- マッピング: `THAILAND_LOCATION_MAPPING`（81地点）
- テスト: `tests/test_e2e/test_noaa_thailand.py`
- ドキュメント: `docs/guides/THAILAND_WEATHER_NOAA_GUIDE.md`

## サンプルコード

### 複数地点の一括取得

```python
import asyncio
from agrr_core.adapter.gateways.weather_noaa_gateway import WeatherNOAAGateway
from agrr_core.framework.services.clients.http_client import HttpClient

async def fetch_multiple_locations():
    """Fetch weather data from multiple locations."""
    http_client = HttpClient()
    gateway = WeatherNOAAGateway(http_client)
    
    # タイ主要農業地域の座標
    locations = {
        "Chiang Mai": (18.767, 98.963),
        "Khon Kaen": (16.467, 102.784),
        "Bangkok": (13.913, 100.607),
        "Surat Thani": (9.133, 99.136),
    }
    
    start_date = "2024-01-01"
    end_date = "2024-01-31"
    
    results = {}
    
    for name, (lat, lon) in locations.items():
        print(f"Fetching data for {name}...")
        try:
            result = await gateway.get_by_location_and_date_range(
                latitude=lat,
                longitude=lon,
                start_date=start_date,
                end_date=end_date
            )
            results[name] = result
            print(f"  → {len(result.weather_data_list)} records")
        except Exception as e:
            print(f"  → Error: {e}")
    
    return results

# 実行
if __name__ == "__main__":
    results = asyncio.run(fetch_multiple_locations())
```

### 月別平均気温の計算

```python
from collections import defaultdict

def calculate_monthly_average(weather_data_list):
    """Calculate monthly average temperature."""
    monthly_temps = defaultdict(list)
    
    for wd in weather_data_list:
        if wd.temperature_2m_mean is not None:
            month_key = (wd.time.year, wd.time.month)
            monthly_temps[month_key].append(wd.temperature_2m_mean)
    
    monthly_averages = {}
    for (year, month), temps in monthly_temps.items():
        avg_temp = sum(temps) / len(temps)
        monthly_averages[f"{year}-{month:02d}"] = avg_temp
    
    return monthly_averages

# 使用例
result = await gateway.get_by_location_and_date_range(
    latitude=16.467,  # Khon Kaen
    longitude=102.784,
    start_date="2024-01-01",
    end_date="2024-12-31"
)

monthly_avg = calculate_monthly_average(result.weather_data_list)
for month, temp in sorted(monthly_avg.items()):
    print(f"{month}: {temp:.1f}°C")
```

## まとめ

NOAA ISDを使用したタイの気温データ取得システムは、タイ全土の主要農業地域81地点から高品質な気象データを取得できます。稲作を中心とした農業計画・研究に必要な長期的・高解像度のデータを提供します。

