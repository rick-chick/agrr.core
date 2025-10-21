# インド天気データ取得ガイド（NOAA ISD）

## 概要

このガイドでは、NOAA ISD（Integrated Surface Database）を使用してインドの主要農業地域から2000年以降の天気データを取得する方法を説明します。

## 実装完了内容

### 1. 観測所マッピング（49地点）

`WeatherNOAAGateway`に、インドの主要農業地域から選定した49地点の観測所を追加しました：

- **パンジャブ州（Punjab）**: 4地点 - 小麦・米の主要生産地
  - Ludhiana, Amritsar, Bathinda, Patiala

- **ハリヤーナー州（Haryana）**: 3地点 - 小麦・米
  - Hisar, Karnal, Rohtak

- **ウッタル・プラデーシュ州（Uttar Pradesh）**: 6地点 - 最大農業生産州
  - Lucknow, Kanpur, Varanasi, Prayagraj, Agra, Gorakhpur

- **デリー首都圏（NCR）**: 1地点
  - Delhi/Safdarjung Airport

- **ラージャスターン州（Rajasthan）**: 5地点 - 綿花・小麦・乾燥地農業
  - Jaipur, Jodhpur, Udaipur, Kota, Bikaner

- **グジャラート州（Gujarat）**: 4地点 - 綿花・落花生
  - Ahmedabad, Surat, Rajkot, Vadodara

- **マハーラーシュトラ州（Maharashtra）**: 5地点 - 綿花・サトウキビ
  - Mumbai, Pune, Nagpur, Nashik, Aurangabad

- **マディヤ・プラデーシュ州（Madhya Pradesh）**: 4地点 - 大豆・小麦
  - Bhopal, Indore, Jabalpur, Gwalior

- **カルナータカ州（Karnataka）**: 3地点 - 米・コーヒー
  - Bangalore, Mysore, Hubli

- **テランガーナ州（Telangana）**: 2地点 - 米・綿花
  - Hyderabad, Warangal

- **アーンドラ・プラデーシュ州（Andhra Pradesh）**: 3地点 - 米・綿花
  - Vijayawada, Visakhapatnam, Tirupati

- **タミル・ナードゥ州（Tamil Nadu）**: 4地点 - 米
  - Chennai, Coimbatore, Madurai, Tiruchirappalli

- **西ベンガル州（West Bengal）**: 1地点 - 米・ジュート
  - Kolkata

- **ビハール州（Bihar）**: 1地点 - 米・小麦
  - Patna

- **オディシャ州（Odisha）**: 1地点 - 米
  - Bhubaneswar

- **チャッティースガル州（Chhattisgarh）**: 1地点 - 米
  - Raipur

- **ジャールカンド州（Jharkhand）**: 1地点 - 米
  - Ranchi

### 2. データ取得範囲

- **期間**: 2000年頃〜現在（観測所により異なる）
- **解像度**: 
  - 時間解像度: 時間単位（hourly）
  - 空間解像度: 観測所ベース（実測値）
- **データ項目**:
  - 気温（最高・最低・平均）
  - 降水量
  - 風速
  - ※日照時間はNOAA ISDには含まれない

## 使用方法

### 基本的な使い方

```python
from agrr_core.adapter.gateways.weather_noaa_gateway import WeatherNOAAGateway
from agrr_core.framework.services.clients.http_client import HttpClient

# HTTP クライアントを作成
http_client = HttpClient()

# Gateway を作成
gateway = WeatherNOAAGateway(http_client)

# デリーの2023年1月のデータを取得
result = await gateway.get_by_location_and_date_range(
    latitude=28.5844,   # デリー
    longitude=77.2031,
    start_date="2023-01-01",
    end_date="2023-01-31"
)

# 結果を確認
print(f"Location: {result.location.latitude}, {result.location.longitude}")
print(f"Data points: {len(result.weather_data_list)}")

for weather_data in result.weather_data_list:
    print(f"{weather_data.time}: {weather_data.temperature_2m_mean}°C")
```

### 主要農業地域の座標

```python
# パンジャブ州（小麦ベルト）
LUDHIANA = (30.9000, 75.8500)

# ウッタル・プラデーシュ州
LUCKNOW = (26.7600, 80.8800)
KANPUR = (26.4400, 80.3600)

# マハーラーシュトラ州（綿花生産）
MUMBAI = (19.0896, 72.8681)
PUNE = (18.5800, 73.9200)

# カルナータカ州
BANGALORE = (12.9500, 77.6681)

# タミル・ナードゥ州
CHENNAI = (12.9900, 80.1692)
```

## データの特徴

### 長所

1. **高品質**: 公式観測所からの実測データ
2. **長期間**: 2000年頃から現在まで利用可能
3. **時間解像度**: 時間単位のデータで日次統計を計算可能
4. **無料**: NOAAの公開データ
5. **信頼性**: グローバル標準の品質管理

### 短所

1. **カバレッジ**: 主要都市のみ（農村部は限定的）
2. **日照時間**: データに含まれない
3. **欠測**: 一部の期間でデータが欠けている可能性
4. **ネットワーク**: 実際のHTTPリクエストが必要

## テスト

### ユニットテスト

```bash
pytest tests/test_adapter/test_weather_noaa_gateway.py -v
```

### E2Eテスト（実際のデータ取得）

```bash
# すべてのE2Eテストを実行
pytest tests/test_e2e/test_noaa_india.py -v -m e2e

# 特定の地域のみテスト
pytest tests/test_e2e/test_noaa_india.py::TestNOAAIndiaE2E::test_delhi_weather_2023 -v
```

**注意**: E2Eテストは実際のHTTPリクエストを行うため、ネットワーク接続が必要で、実行に時間がかかります。

## データ品質チェック

### 温度範囲の妥当性

インドの気候帯別の典型的な温度範囲：

- **北部（デリー、パンジャブ）**: -5°C 〜 45°C
- **西部（ラージャスターン、グジャラート）**: 0°C 〜 50°C（乾燥地）
- **南部（カルナータカ、タミル・ナードゥ）**: 10°C 〜 40°C（温暖）
- **東部（西ベンガル、オディシャ）**: 10°C 〜 45°C（湿潤）
- **沿岸部（ムンバイ、チェンナイ）**: 15°C 〜 35°C（海洋性）

### データの欠測対応

```python
# 欠測データの確認
missing_dates = []
expected_dates = pd.date_range(start_date, end_date, freq='D')

for date in expected_dates:
    if date not in [w.time.date() for w in result.weather_data_list]:
        missing_dates.append(date)

if missing_dates:
    print(f"Missing data for {len(missing_dates)} days")
    # 補間や代替データソースの検討
```

## 他のデータソースとの比較

### NOAA ISD vs NASA POWER

| 項目 | NOAA ISD | NASA POWER |
|------|----------|------------|
| 空間解像度 | 観測所（高） | 0.5度グリッド（中） |
| 時間解像度 | 時間単位 | 日単位 |
| データ期間 | 1950年代〜 | 1981年〜 |
| 日照時間 | ✗ | ✓ |
| カバレッジ | 主要都市 | 全球均一 |

### NOAA ISD vs IMD

| 項目 | NOAA ISD | IMD（インド気象局） |
|------|----------|---------------------|
| 観測所数 | 49地点 | 数百地点 |
| データアクセス | API/HTTP | スクレイピング必要 |
| 品質管理 | グローバル標準 | インド国内標準 |
| 信頼性 | 高 | 高 |

## トラブルシューティング

### データが取得できない場合

1. **観測所の確認**: 指定した座標に最も近い観測所を確認
2. **期間の確認**: 2000年以前のデータは存在しない可能性
3. **ネットワーク**: NOAAサーバーへの接続を確認
4. **レート制限**: 大量リクエスト時は間隔を空ける

### エラーメッセージ

```python
# WeatherDataNotFoundError: データが見つからない
# → 期間を変更するか、別の観測所を試す

# WeatherAPIError: APIエラー
# → ネットワーク接続やNOAAサーバーの状態を確認
```

## 今後の拡張

1. **観測所の追加**: さらに地方都市の観測所を追加
2. **データ補間**: 欠測データの補間アルゴリズム実装
3. **キャッシュ**: 取得済みデータのローカルキャッシュ
4. **バッチ取得**: 複数地点・複数年のバッチ取得機能

## 参考資料

- [NOAA ISD公式サイト](https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database)
- [NOAA ISDデータフォーマット](https://www.ncei.noaa.gov/data/global-hourly/doc/)
- [インド農業統計](https://agricoop.nic.in/)

## 実装ファイル

- Gateway: `src/agrr_core/adapter/gateways/weather_noaa_gateway.py`
- テスト: `tests/test_adapter/test_weather_noaa_gateway.py`
- E2Eテスト: `tests/test_e2e/test_noaa_india.py`
- ドキュメント: `docs/guides/INDIA_WEATHER_NOAA_GUIDE.md`

