# CLI→コンポーネント間データ移送フロー - 気象庁データ取得

**作成日:** 2025-01-12  
**対象:** 気象庁（JMA）データ取得のデータフロー

---

## 📊 概要図

```
[ユーザー入力]
     ↓
┌─────────────────────────────────────────┐
│ CLI Layer                                │
│ ・コマンドライン引数                      │
│ ・文字列データ                           │
└─────────────────────────────────────────┘
     ↓ parse arguments
┌─────────────────────────────────────────┐
│ Framework Layer (Container)              │
│ ・config辞書                             │
│ ・依存性解決とインスタンス生成            │
└─────────────────────────────────────────┘
     ↓ inject dependencies
┌─────────────────────────────────────────┐
│ Adapter Layer (Controller)               │
│ ・parsed_args → DTO変換                 │
│ ・WeatherDataRequestDTO                  │
└─────────────────────────────────────────┘
     ↓ call interactor
┌─────────────────────────────────────────┐
│ UseCase Layer (Interactor)               │
│ ・DTO → Entity変換                       │
│ ・Location, DateRange                    │
└─────────────────────────────────────────┘
     ↓ call gateway
┌─────────────────────────────────────────┐
│ Adapter Layer (Gateway)                  │
│ ・parameters → Repository呼び出し        │
└─────────────────────────────────────────┘
     ↓ call repository
┌─────────────────────────────────────────┐
│ Adapter Layer (Repository - JMA)         │
│ ・CSVダウンロード                        │
│ ・DataFrame → WeatherData Entity変換    │
└─────────────────────────────────────────┘
     ↓ return DTO
┌─────────────────────────────────────────┐
│ Framework Layer (CSV Downloader)         │
│ ・HTTP GET リクエスト                    │
│ ・CSV → DataFrame                        │
└─────────────────────────────────────────┘
     ↓ 逆方向のデータフロー
┌─────────────────────────────────────────┐
│ Adapter Layer (Presenter)                │
│ ・Entity → 表示用データ変換              │
│ ・Table形式またはJSON出力                │
└─────────────────────────────────────────┘
     ↓
[ユーザー出力]
```

---

## 🔄 詳細データフロー

### Step 1: CLIコマンド実行

**入力（ユーザー）:**
```bash
agrr weather \
  --location 35.6895,139.6917 \
  --days 7 \
  --data-source jma
```

**データ型:** `List[str]` (コマンドライン引数)

---

### Step 2: CLI引数パース（cli.py）

**場所:** `src/agrr_core/cli.py:150-165`

**処理:**
```python
# 引数から data-source を抽出
args = ['weather', '--location', '35.6895,139.6917', '--days', '7', '--data-source', 'jma']

# data-source を抽出
weather_data_source = 'jma'  # args から抽出

# config 辞書作成
config = {
    'open_meteo_base_url': 'https://archive-api.open-meteo.com/v1/archive',
    'weather_data_source': 'jma'  # ← ここがポイント
}
```

**データ型変化:**
```
List[str] → Dict[str, str]
['--data-source', 'jma'] → {'weather_data_source': 'jma'}
```

---

### Step 3: Container インスタンス化（Container）

**場所:** `src/agrr_core/framework/agrr_core_container.py:65-82`

**処理フロー:**
```python
container = WeatherCliContainer(config)

# 1. get_weather_gateway_impl() が呼ばれる
data_source = config.get('weather_data_source', 'openmeteo')  # 'jma'

# 2. data_source に応じてRepository選択
if data_source == 'jma':
    weather_api_repository = self.get_weather_jma_repository()
    # ↓
    # get_csv_downloader() → CsvDownloader インスタンス化
    # ↓
    # WeatherJMARepository(csv_downloader) インスタンス化
else:
    weather_api_repository = self.get_weather_api_repository()

# 3. Gateway インスタンス化
WeatherGatewayImpl(
    weather_file_repository=weather_file_repository,
    weather_api_repository=weather_api_repository  # ← JMARepository
)
```

**インスタンス構造:**
```
Container
├── CsvDownloader
│   └── requests.Session
├── WeatherJMARepository
│   └── csv_service: CsvDownloader
├── WeatherGatewayImpl
│   └── weather_api_repository: WeatherJMARepository
├── WeatherCLIPresenter
└── WeatherCliFetchController
    ├── weather_gateway: WeatherGatewayImpl
    ├── cli_presenter: WeatherCLIPresenter
    └── weather_interactor: FetchWeatherDataInteractor
```

---

### Step 4: Controller - 引数パース（Controller）

**場所:** `src/agrr_core/adapter/controllers/weather_cli_controller.py:261-291`

**処理:**
```python
# argparse で解析
parsed_args = parser.parse_args(args)
# parsed_args.location = '35.6895,139.6917'
# parsed_args.days = 7
# parsed_args.data_source = 'jma'

# 座標をパース
latitude, longitude = self.parse_location(args.location)
# → (35.6895, 139.6917)

# 日付範囲を計算
start_date, end_date = self.calculate_date_range(args.days)
# → ('2024-10-05', '2024-10-11')

# DTO作成
request = WeatherDataRequestDTO(
    latitude=35.6895,
    longitude=139.6917,
    start_date='2024-10-05',
    end_date='2024-10-11'
)
```

**データ型変化:**
```
argparse.Namespace → WeatherDataRequestDTO

Namespace(
    location='35.6895,139.6917',
    days=7,
    data_source='jma'
)
    ↓
WeatherDataRequestDTO(
    latitude=35.6895,      # float
    longitude=139.6917,    # float
    start_date='2024-10-05',  # str
    end_date='2024-10-11'     # str
)
```

---

### Step 5: Interactor - DTO→Entity変換（UseCase）

**場所:** `src/agrr_core/usecase/interactors/weather_fetch_interactor.py:27-66`

**処理:**
```python
async def execute(self, request: WeatherDataRequestDTO) -> dict:
    # DTOからEntityを作成
    location = Location(
        latitude=request.latitude,    # 35.6895
        longitude=request.longitude    # 139.6917
    )
    
    date_range = DateRange(
        start_date=request.start_date,  # '2024-10-05'
        end_date=request.end_date       # '2024-10-11'
    )
    
    # Gateway呼び出し（プリミティブ型で渡す）
    weather_data_with_location = await self.weather_gateway.get_by_location_and_date_range(
        location.latitude,      # float: 35.6895
        longitude.longitude,    # float: 139.6917
        date_range.start_date,  # str: '2024-10-05'
        date_range.end_date     # str: '2024-10-11'
    )
```

**データ型変化:**
```
WeatherDataRequestDTO (DTO)
    ↓
Location (Entity) + DateRange (Entity)
    ↓
float, float, str, str (プリミティブ型)
```

**重要ポイント:**
- **DTOはデータ転送用**（層を跨ぐ）
- **Entityはビジネスロジック用**（バリデーション含む）
- **プリミティブ型でGatewayに渡す**（依存を最小化）

---

### Step 6: Gateway - Repository呼び出し（Adapter）

**場所:** `src/agrr_core/adapter/gateways/weather_gateway_impl.py:41-51`

**処理:**
```python
async def get_by_location_and_date_range(
    self,
    latitude: float,      # 35.6895
    longitude: float,     # 139.6917
    start_date: str,      # '2024-10-05'
    end_date: str         # '2024-10-11'
) -> WeatherDataWithLocationDTO:
    
    # Repositoryに直接転送（型はそのまま）
    return await self.weather_api_repository.get_by_location_and_date_range(
        latitude,    # 35.6895
        longitude,   # 139.6917
        start_date,  # '2024-10-05'
        end_date     # '2024-10-11'
    )
```

**データ型変化:**
```
変化なし（透過的な転送）
float, float, str, str → float, float, str, str
```

**重要ポイント:**
- **Gatewayは透過的**
- **型変換は行わない**
- **どのRepositoryかは関係ない**（インターフェース統一）

---

### Step 7: Repository - データ取得（Adapter - JMA）

**場所:** `src/agrr_core/adapter/repositories/weather_jma_repository.py:77-146`

#### Step 7-1: 地点マッピング

**処理:**
```python
# 緯度経度から気象庁観測地点を特定
prec_no, block_no, location_name = self._find_nearest_location(35.6895, 139.6917)
# → (44, 47662, "東京")
```

**データ型変化:**
```
float, float → int, int, str
(35.6895, 139.6917) → (44, 47662, "東京")
```

#### Step 7-2: URL生成

**処理:**
```python
# 日付範囲から月リストを生成
start = datetime.strptime('2024-10-05', '%Y-%m-%d')  # 2024-10-05
end = datetime.strptime('2024-10-11', '%Y-%m-%d')    # 2024-10-11

# 月初に揃える
current = start.replace(day=1)   # 2024-10-01
end_month = end.replace(day=1)   # 2024-10-01

# URL生成（1ヶ月分のみ）
url = self._build_url(44, 47662, 2024, 10)
# → "https://www.data.jma.go.jp/obd/stats/etrn/view/daily_s1.php?prec_no=44&block_no=47662&year=2024&month=10&day=&view="
```

**データ型変化:**
```
str → datetime → int, int
'2024-10-05' → datetime(2024, 10, 5) → (2024, 10)
```

---

### Step 8: CSV Downloader - データ取得（Framework）

**場所:** `src/agrr_core/framework/repositories/csv_downloader.py:25-53`

**処理:**
```python
# CSV ダウンロード
url = "https://www.data.jma.go.jp/obd/stats/etrn/view/daily_s1.php?..."
encoding = 'shift_jis'

# HTTP GET リクエスト
response = self.session.get(url, timeout=30)
# → bytes (Shift-JIS エンコード)

# デコード
csv_text = response.content.decode('shift_jis')
# → str (CSV テキスト)

# pandas でパース
df = pd.read_csv(StringIO(csv_text))
# → DataFrame
```

**データ型変化:**
```
str (URL) 
    ↓ HTTP GET
bytes (CSV binary, Shift-JIS)
    ↓ decode
str (CSV text)
    ↓ pd.read_csv
pd.DataFrame
```

**DataFrame例:**
```
     年月日  最高気温(℃)  最低気温(℃)  ...
0  2024-10-05     22.5       15.3   ...
1  2024-10-06     23.1       16.2   ...
2  2024-10-07     21.8       14.9   ...
...
```

---

### Step 9: Repository - CSV→Entity変換（Adapter - JMA）

**場所:** `src/agrr_core/adapter/repositories/weather_jma_repository.py:193-297`

**処理フロー:**
```python
def _parse_jma_csv(df: pd.DataFrame, start_date: str, end_date: str):
    weather_data_list = []
    
    for _, row in df.iterrows():
        # 1. 日付抽出
        date_str = row.get('年月日')  # '2024-10-05'
        record_date = datetime.strptime(date_str, '%Y-%m-%d')
        
        # 2. 数値データ抽出
        temp_max = self._safe_float(row.get('最高気温(℃)'))  # 22.5
        temp_min = self._safe_float(row.get('最低気温(℃)'))  # 15.3
        temp_mean = self._safe_float(row.get('平均気温(℃)')) # 18.9
        precipitation = self._safe_float(row.get('降水量の合計(mm)'))  # 2.5
        sunshine_hours = self._safe_float(row.get('日照時間(時間)'))   # 5.2
        wind_speed = self._safe_float(row.get('最大風速(m/s)'))       # 3.5
        
        # 3. 単位変換
        sunshine_duration = sunshine_hours * 3600  # 5.2時間 → 18720秒
        
        # 4. Entity作成
        weather_data = WeatherData(
            time=record_date,                    # datetime
            temperature_2m_max=temp_max,         # float: 22.5
            temperature_2m_min=temp_min,         # float: 15.3
            temperature_2m_mean=temp_mean,       # float: 18.9
            precipitation_sum=precipitation,     # float: 2.5
            sunshine_duration=sunshine_duration, # float: 18720.0
            wind_speed_10m=wind_speed,          # float: 3.5
            weather_code=None                    # None（JMAにはない）
        )
        
        # 5. データ品質検証
        if self._validate_weather_data(weather_data, date_str):
            weather_data_list.append(weather_data)
        else:
            skipped_count += 1  # 不正データはスキップ
    
    return weather_data_list
```

**データ型変化:**
```
pd.DataFrame
    ↓ iterrows()
pd.Series (1行分)
    ↓ get() + _safe_float()
Optional[float] (各フィールド)
    ↓ 単位変換
float (秒単位)
    ↓ WeatherData()
WeatherData Entity
    ↓ _validate_weather_data()
List[WeatherData] (検証済み)
```

**重要な変換:**
```
気象庁CSV → WeatherData Entity
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
年月日            → time (datetime)
最高気温(℃)      → temperature_2m_max (float)
最低気温(℃)      → temperature_2m_min (float)
平均気温(℃)      → temperature_2m_mean (float)
降水量の合計(mm)  → precipitation_sum (float)
日照時間(時間)    → sunshine_duration (float) ×3600
最大風速(m/s)     → wind_speed_10m (float)
(なし)           → weather_code (None)
```

---

### Step 10: Repository - DTO作成（Adapter - JMA）

**場所:** `src/agrr_core/adapter/repositories/weather_jma_repository.py:152-161`

**処理:**
```python
# Location DTO作成
location = Location(
    latitude=35.6895,       # リクエスト値
    longitude=139.6917,     # リクエスト値
    elevation=None,         # JMAにはない
    timezone="Asia/Tokyo"   # 固定値
)

# WeatherDataWithLocationDTO作成
return WeatherDataWithLocationDTO(
    weather_data_list=[
        WeatherData(...),  # 2024-10-05
        WeatherData(...),  # 2024-10-06
        WeatherData(...),  # 2024-10-07
        ...
    ],
    location=location
)
```

**データ型変化:**
```
List[WeatherData] + metadata
    ↓
WeatherDataWithLocationDTO(
    weather_data_list: List[WeatherData],
    location: Location
)
```

---

### Step 11: Gateway - 透過的転送（Adapter）

**場所:** `src/agrr_core/adapter/gateways/weather_gateway_impl.py:41-51`

**処理:**
```python
# Repository から受け取ったDTOをそのまま返す
weather_data_with_location = await self.weather_api_repository.get_by_location_and_date_range(...)
return weather_data_with_location  # そのまま返す
```

**データ型変化:**
```
変化なし（透過的）
WeatherDataWithLocationDTO → WeatherDataWithLocationDTO
```

---

### Step 12: Interactor - Entity→ResponseDTO変換（UseCase）

**場所:** `src/agrr_core/usecase/interactors/weather_fetch_interactor.py:67-100`

**処理:**
```python
# Gatewayから受け取ったDTO
weather_data_with_location = WeatherDataWithLocationDTO(...)

# 1. weather_data_list を取り出し
weather_data_list = weather_data_with_location.weather_data_list
# → [WeatherData(...), WeatherData(...), ...]

# 2. 各WeatherDataをDTOに変換
response_data = []
for weather_data in weather_data_list:
    weather_dto = WeatherDataResponseDTO(
        time=weather_data.time.isoformat(),           # datetime → str
        temperature_2m_max=weather_data.temperature_2m_max,
        temperature_2m_min=weather_data.temperature_2m_min,
        temperature_2m_mean=weather_data.temperature_2m_mean,
        precipitation_sum=weather_data.precipitation_sum,
        sunshine_duration=weather_data.sunshine_duration,
        sunshine_hours=weather_data.sunshine_hours,   # プロパティ（秒→時間）
        wind_speed_10m=weather_data.wind_speed_10m,
        weather_code=weather_data.weather_code
    )
    response_data.append(weather_dto)

# 3. LocationをDTOに変換
location_dto = LocationResponseDTO(
    latitude=api_location.latitude,
    longitude=api_location.longitude,
    elevation=api_location.elevation,
    timezone=api_location.timezone
)

# 4. 最終的なResponseDTO作成
response = WeatherDataListResponseDTO(
    data=response_data,
    total_count=len(response_data),
    location=location_dto
)

# 5. Presenterに渡す
return self.weather_presenter_output_port.format_success(response)
```

**データ型変化:**
```
WeatherDataWithLocationDTO (内部DTO)
    ↓ Entity抽出
List[WeatherData] (Entity)
    ↓ DTO変換
List[WeatherDataResponseDTO] (出力DTO)
    ↓
WeatherDataListResponseDTO (最終Response)
    ↓ Presenter
dict (JSON or Table)
```

**重要な変換:**
```
Entity → Response DTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
time (datetime)          → time (str ISO形式)
sunshine_duration (秒)   → sunshine_hours (時間) プロパティで自動変換
```

---

### Step 13: Presenter - 表示形式変換（Adapter）

**場所:** `src/agrr_core/adapter/presenters/weather_cli_presenter.py`

**処理:**
```python
def format_success(self, response: WeatherDataListResponseDTO) -> dict:
    if json_format:
        # JSON形式
        return {
            "data": [
                {
                    "time": "2024-10-05",
                    "temperature_2m_max": 22.5,
                    "temperature_2m_min": 15.3,
                    "temperature_2m_mean": 18.9,
                    "precipitation_sum": 2.5,
                    "sunshine_duration": 18720.0,
                    "sunshine_hours": 5.2,
                    "wind_speed_10m": 3.5,
                    "weather_code": null
                },
                ...
            ],
            "total_count": 7,
            "location": {...}
        }
    else:
        # Table形式
        # テーブル表示用に整形
```

**データ型変化:**
```
WeatherDataListResponseDTO
    ↓
dict (JSON) または str (Table)
```

---

## 📋 データ型の変遷まとめ

### 下り（リクエスト）

```
1. CLI Input
   └── str: '--location 35.6895,139.6917 --days 7 --data-source jma'

2. Config (cli.py)
   └── Dict[str, Any]: {'weather_data_source': 'jma'}

3. Container (Container)
   └── Repository instance selection

4. argparse.Namespace (Controller)
   └── Namespace(location='35.6895,139.6917', days=7, data_source='jma')

5. WeatherDataRequestDTO (Controller→Interactor)
   └── WeatherDataRequestDTO(latitude=35.6895, longitude=139.6917, ...)

6. Location + DateRange Entity (Interactor)
   └── Location(35.6895, 139.6917)
   └── DateRange('2024-10-05', '2024-10-11')

7. Primitive types (Interactor→Gateway)
   └── float, float, str, str

8. Primitive types (Gateway→Repository)
   └── 35.6895, 139.6917, '2024-10-05', '2024-10-11'

9. Station mapping (Repository)
   └── (44, 47662, "東京")

10. URL (Repository→CSV Downloader)
    └── "https://www.data.jma.go.jp/obd/stats/etrn/view/daily_s1.php?..."

11. HTTP Request (CSV Downloader)
    └── bytes (CSV binary, Shift-JIS)
```

### 上り（レスポンス）

```
11. HTTP Response
    └── bytes (CSV binary)

10. DataFrame (CSV Downloader→Repository)
    └── pd.DataFrame (列: 年月日, 最高気温, ...)

9. WeatherData Entity (Repository)
    └── WeatherData(time=datetime(...), temperature_2m_max=22.5, ...)

8. List[WeatherData] (Repository - validation後)
    └── [WeatherData(...), WeatherData(...), ...]

7. WeatherDataWithLocationDTO (Repository→Gateway)
    └── WeatherDataWithLocationDTO(weather_data_list=[...], location=Location(...))

6. WeatherDataWithLocationDTO (Gateway→Interactor)
    └── 透過的転送

5. WeatherDataResponseDTO (Interactor)
    └── WeatherDataResponseDTO(time='2024-10-05', ...)

4. WeatherDataListResponseDTO (Interactor)
    └── WeatherDataListResponseDTO(data=[...], total_count=7, location=...)

3. dict (Interactor→Presenter)
    └── Presenterが整形

2. JSON or Table (Presenter)
    └── dict (JSON) or str (Table)

1. CLI Output
    └── stdout (ユーザーに表示)
```

---

## 🔍 重要なデータ変換ポイント

### 1. CLI引数 → Config

**変換場所:** `cli.py:150-164`

```python
# Before
args: ['--data-source', 'jma']

# After
config: {'weather_data_source': 'jma'}
```

**目的:** CLI引数をContainer設定に変換

---

### 2. Config → Repository選択

**変換場所:** `agrr_core_container.py:71-75`

```python
# Config読み取り
data_source = config.get('weather_data_source', 'openmeteo')

# Repository選択
if data_source == 'jma':
    repository = WeatherJMARepository(csv_downloader)
else:
    repository = WeatherAPIOpenMeteoRepository(http_client)
```

**目的:** 設定に基づいて適切なRepositoryをインスタンス化

---

### 3. 座標文字列 → float

**変換場所:** `weather_cli_controller.py:265`

```python
# Before
args.location = '35.6895,139.6917'

# After
latitude, longitude = self.parse_location(args.location)
# → (35.6895, 139.6917)
```

**目的:** 文字列からfloatに型変換

---

### 4. 相対日数 → 絶対日付

**変換場所:** `weather_cli_controller.py:278`

```python
# Before
args.days = 7

# After
start_date, end_date = self.calculate_date_range(7)
# → ('2024-10-05', '2024-10-11')
```

**目的:** 相対的な日数から具体的な日付範囲を計算

---

### 5. 緯度経度 → 観測地点

**変換場所:** `weather_jma_repository.py:46-75`

```python
# Before
latitude=35.6895, longitude=139.6917

# After
prec_no, block_no, location_name = self._find_nearest_location(...)
# → (44, 47662, "東京")
```

**目的:** 気象庁の観測地点IDを特定

---

### 6. CSV（日本語列名） → Entity（英語フィールド）

**変換場所:** `weather_jma_repository.py:232-276`

```python
# Before (CSV列名)
'年月日': '2024-10-05'
'最高気温(℃)': 22.5
'降水量の合計(mm)': 2.5
'日照時間(時間)': 5.2

# After (Entity フィールド)
WeatherData(
    time=datetime(2024, 10, 5),
    temperature_2m_max=22.5,
    precipitation_sum=2.5,
    sunshine_duration=18720.0  # 時間→秒
)
```

**目的:** 日本語→英語、単位変換、型変換

---

### 7. Entity → ResponseDTO

**変換場所:** `weather_fetch_interactor.py:80-95`

```python
# Before (Entity)
WeatherData(
    time=datetime(2024, 10, 5),
    temperature_2m_max=22.5
)

# After (ResponseDTO)
WeatherDataResponseDTO(
    time='2024-10-05',  # datetime → ISO string
    temperature_2m_max=22.5
)
```

**目的:** 内部Entityから出力DTOに変換

---

## 🎯 各層の責任

### CLI Layer
```
責任: ユーザー入力の受け取り
入力: コマンドライン引数（文字列）
出力: 引数リスト
```

### Framework Layer (Container)
```
責任: 依存性解決とインスタンス化
入力: config辞書
出力: 依存性注入済みのコンポーネント
重要: data_source に基づいてRepository選択
```

### Adapter Layer (Controller)
```
責任: CLI引数 → DTO変換
入力: argparse.Namespace
出力: WeatherDataRequestDTO
変換:
  - 座標文字列 → float
  - 相対日数 → 絶対日付
```

### UseCase Layer (Interactor)
```
責任: ビジネスロジック実行
入力: WeatherDataRequestDTO
出力: WeatherDataListResponseDTO
変換:
  - DTO → Entity (バリデーション)
  - Entity → ResponseDTO
```

### Adapter Layer (Gateway)
```
責任: Repository呼び出しの抽象化
入力: プリミティブ型 (float, str)
出力: WeatherDataWithLocationDTO
変換: なし（透過的転送）
```

### Adapter Layer (Repository - JMA)
```
責任: 外部データソースからのデータ取得
入力: プリミティブ型 (float, str)
出力: WeatherDataWithLocationDTO
変換:
  - 緯度経度 → 観測地点ID
  - CSV → DataFrame
  - DataFrame → WeatherData Entity
  - 日本語列名 → 英語フィールド
  - 時間 → 秒（×3600）
  - データ品質検証
```

### Framework Layer (CSV Downloader)
```
責任: HTTPリクエストとCSVパース
入力: URL (str)
出力: DataFrame
変換:
  - HTTP Response (bytes) → str (Shift-JIS decode)
  - CSV text → DataFrame
```

### Adapter Layer (Presenter)
```
責任: 出力形式の整形
入力: WeatherDataListResponseDTO
出力: dict (JSON) or str (Table)
変換:
  - DTO → ユーザー表示形式
```

---

## 📊 データ変換の流れ（気象庁特有）

### 気象庁固有の変換

```
┌──────────────────────────────────────────┐
│ 気象庁CSV（日本語、独自フォーマット）      │
├──────────────────────────────────────────┤
│ 年月日: '2024-10-05'                      │
│ 最高気温(℃): 22.5                        │
│ 日照時間(時間): 5.2                       │
│ エンコーディング: Shift-JIS               │
└──────────────────────────────────────────┘
              ↓ CsvDownloader
┌──────────────────────────────────────────┐
│ pandas DataFrame                          │
├──────────────────────────────────────────┤
│ 列名: 日本語のまま                        │
│ データ型: object, float64                 │
└──────────────────────────────────────────┘
              ↓ WeatherJMARepository._parse_jma_csv
┌──────────────────────────────────────────┐
│ WeatherData Entity (共通フォーマット)     │
├──────────────────────────────────────────┤
│ time: datetime(2024, 10, 5)              │
│ temperature_2m_max: 22.5                  │
│ sunshine_duration: 18720.0 (秒)           │
│ weather_code: None                        │
└──────────────────────────────────────────┘
              ↓ データ品質検証
┌──────────────────────────────────────────┐
│ 検証済み WeatherData Entity               │
├──────────────────────────────────────────┤
│ ✅ 温度範囲OK                             │
│ ✅ 温度逆転なし                           │
│ ✅ 降水量非負                             │
│ ✅ 日照時間範囲内                         │
└──────────────────────────────────────────┘
              ↓ WeatherDataWithLocationDTO
┌──────────────────────────────────────────┐
│ 内部転送用DTO                             │
│ (OpenMeteoと同じ構造)                     │
└──────────────────────────────────────────┘
```

---

## 🔄 OpenMeteo vs JMA データフロー比較

### OpenMeteo

```
CLI → Container → Gateway → OpenMeteoRepository
                                      ↓
                              HttpClient (JSON API)
                                      ↓
                              JSON Response
                                      ↓
                              WeatherData Entity
```

### 気象庁（JMA）

```
CLI → Container → Gateway → JMARepository
                                      ↓
                              CsvDownloader
                                      ↓
                              CSV (Shift-JIS)
                                      ↓
                              DataFrame
                                      ↓
                              列名マッピング
                                      ↓
                              単位変換（時間→秒）
                                      ↓
                              データ品質検証 ⭐NEW
                                      ↓
                              WeatherData Entity
```

**差異:**
- JMAは**CSV処理**が追加
- JMAは**列名マッピング**が必要
- JMAは**データ品質検証**を実施
- JMAは**Shift-JISデコード**が必要

**共通点:**
- 最終的には同じ **WeatherData Entity**
- 同じ **WeatherDataWithLocationDTO**
- UseCase層以上は**完全に同じ**

---

## 🎯 まとめ

### データフローの特徴

1. **クリーンアーキテクチャの遵守**
   - 各層が適切な責任を持つ
   - 依存の方向が一方向
   - インターフェースによる抽象化

2. **データ変換の明確化**
   - 各層で適切なデータ型
   - 文字列→DTO→Entity→DTO→表示

3. **気象庁固有処理の分離**
   - Repository層で完結
   - UseCase層以上は変更なし

4. **品質保証**
   - 各段階でバリデーション
   - データ品質検証
   - エラーハンドリング

---

**作成日:** 2025-01-12  
**ドキュメント:** CLIデータフロー完全ガイド
