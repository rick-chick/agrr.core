"""Weather NOAA gateway implementation for US weather data.

This gateway directly implements WeatherGateway interface for NOAA ISD data access.
Data source: NOAA Integrated Surface Database (ISD)
https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database
"""

import logging
from typing import Dict, Tuple, List, Optional
from datetime import datetime, date, timedelta
import re

from agrr_core.entity import WeatherData, Location
from agrr_core.entity.exceptions.weather_api_error import WeatherAPIError
from agrr_core.entity.exceptions.weather_data_not_found_error import WeatherDataNotFoundError
from agrr_core.adapter.interfaces.clients.http_client_interface import HttpClientInterface
from agrr_core.usecase.dto.weather_data_with_location_dto import WeatherDataWithLocationDTO
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway

# NOAA ISD 観測地点マッピング（緯度経度 → (USAF, WBAN, name)）
# アメリカ主要都市の観測所を定義
US_LOCATION_MAPPING: Dict[Tuple[float, float], Tuple[str, str, str, float, float]] = {
    # (latitude, longitude): (usaf, wban, name, actual_lat, actual_lon)
    
    # 東海岸
    (40.7128, -74.0060): ("725030", "14732", "LaGuardia Airport, NY", 40.7769, -73.8739),  # New York
    (42.3601, -71.0589): ("725090", "14739", "Boston Logan Airport, MA", 42.3606, -71.0096),  # Boston
    (38.9072, -77.0369): ("724050", "13743", "Washington Dulles Airport, DC", 38.9531, -77.4565),  # Washington DC
    (25.7617, -80.1918): ("722020", "12839", "Miami Airport, FL", 25.7932, -80.2906),  # Miami
    (33.7490, -84.3880): ("722190", "13874", "Atlanta Airport, GA", 33.6367, -84.4281),  # Atlanta
    
    # 中西部
    (41.8781, -87.6298): ("725300", "94846", "Chicago O'Hare Airport, IL", 41.9950, -87.9336),  # Chicago
    (39.7392, -104.9903): ("724699", "03017", "Denver Airport, CO", 39.8561, -104.6737),  # Denver
    (29.7604, -95.3698): ("722430", "12960", "Houston Bush Airport, TX", 29.9844, -95.3414),  # Houston
    (32.7767, -96.7970): ("722590", "03927", "Dallas Fort Worth Airport, TX", 32.8998, -97.0403),  # Dallas
    
    # 西海岸
    (34.0522, -118.2437): ("722950", "23174", "Los Angeles Airport, CA", 33.9381, -118.3889),  # Los Angeles
    (37.7749, -122.4194): ("724940", "23234", "San Francisco Airport, CA", 37.6213, -122.3790),  # San Francisco
    (47.6062, -122.3321): ("727930", "24233", "Seattle Tacoma Airport, WA", 47.4502, -122.3088),  # Seattle
    (45.5152, -122.6784): ("726980", "24229", "Portland Airport, OR", 45.5887, -122.5975),  # Portland
    (32.7157, -117.1611): ("722900", "23188", "San Diego Airport, CA", 32.7336, -117.1830),  # San Diego
    
    # その他主要都市
    (36.1699, -115.1398): ("723860", "23169", "Las Vegas Airport, NV", 36.0801, -115.1522),  # Las Vegas
    (33.4484, -112.0740): ("722780", "23183", "Phoenix Airport, AZ", 33.4342, -112.0116),  # Phoenix
    (30.2672, -97.7431): ("722540", "13904", "Austin Airport, TX", 30.1945, -97.6699),  # Austin
}

# インド主要農業地域の観測所マッピング（50地点）
# 選定基準：主要農業州（パンジャブ、UP、マハーラーシュトラ等）の代表都市と主要作物生産地域
INDIA_LOCATION_MAPPING: Dict[Tuple[float, float], Tuple[str, str, str, float, float]] = {
    # (latitude, longitude): (usaf, wban, name, actual_lat, actual_lon)
    
    # パンジャブ州（Punjab）- 小麦・米の主要生産地
    (30.9000, 75.8500): ("421650", "99999", "Ludhiana", 30.9000, 75.8500),
    (31.6300, 74.8700): ("420710", "99999", "Amritsar/Raja Sansi Airport", 31.7097, 74.7972),
    (30.2000, 74.9500): ("421890", "99999", "Bathinda", 30.2708, 74.7556),
    (30.3400, 76.3900): ("421970", "99999", "Patiala", 30.3398, 76.3869),
    
    # ハリヤーナー州（Haryana）- 小麦・米
    (29.1500, 75.7200): ("422630", "99999", "Hisar", 29.1792, 75.7547),
    (29.6900, 76.9900): ("422340", "99999", "Karnal", 29.6857, 76.9905),
    (28.8900, 76.6400): ("422470", "99999", "Rohtak", 28.8955, 76.6066),
    
    # ウッタル・プラデーシュ州（Uttar Pradesh）- 最大農業生産州
    (26.7600, 80.8800): ("423690", "99999", "Lucknow/Amausi Airport", 26.7606, 80.8893),
    (26.4400, 80.3600): ("423390", "99999", "Kanpur/Chakeri Airport", 26.4041, 80.4100),
    (25.4500, 82.8600): ("424920", "99999", "Varanasi/Babatpur Airport", 25.4524, 82.8594),
    (25.4400, 81.7300): ("424850", "99999", "Prayagraj/Bamrauli Airport", 25.4395, 81.7339),
    (27.1600, 77.9600): ("421970", "99999", "Agra/Kheria Airport", 27.1558, 77.9608),
    (26.7500, 83.3600): ("423620", "99999", "Gorakhpur Airport", 26.7397, 83.4497),
    
    # デリー首都圏（NCR）
    (28.5844, 77.2031): ("421820", "99999", "Delhi/Safdarjung Airport", 28.5844, 77.2031),
    
    # ラージャスターン州（Rajasthan）- 綿花・小麦・乾燥地農業
    (26.8200, 75.8000): ("424920", "99999", "Jaipur/Sanganer Airport", 26.8242, 75.8122),
    (26.3000, 73.0200): ("423910", "99999", "Jodhpur Airport", 26.2515, 73.0489),
    (24.6200, 73.8900): ("425050", "99999", "Udaipur/Dabok Airport", 24.6177, 73.8961),
    (25.1600, 75.8400): ("424780", "99999", "Kota Airport", 25.1602, 75.8456),
    (28.0100, 73.3100): ("422410", "99999", "Bikaner Airport", 28.0706, 73.2072),
    
    # グジャラート州（Gujarat）- 綿花・落花生
    (23.0700, 72.6300): ("426470", "99999", "Ahmedabad Airport", 23.0772, 72.6347),
    (21.1200, 72.7500): ("429710", "99999", "Surat Airport", 21.1140, 72.7419),
    (22.3100, 70.8100): ("426700", "99999", "Rajkot Airport", 22.3092, 70.7795),
    (22.3400, 73.2300): ("426850", "99999", "Vadodara Airport", 22.3362, 73.2263),
    
    # マハーラーシュトラ州（Maharashtra）- 綿花・サトウキビ
    (19.0896, 72.8681): ("430030", "99999", "Mumbai/Santacruz Airport", 19.0896, 72.8681),
    (18.5800, 73.9200): ("430630", "99999", "Pune Airport", 18.5822, 73.9197),
    (21.0900, 79.0500): ("429710", "99999", "Nagpur/Sonegaon Airport", 21.0922, 79.0472),
    (19.9700, 73.8000): ("430350", "99999", "Nashik Airport", 19.9667, 73.8011),
    (19.8800, 75.3400): ("430470", "99999", "Aurangabad/Chikkalthana Airport", 19.8627, 75.3981),
    
    # マディヤ・プラデーシュ州（Madhya Pradesh）- 大豆・小麦
    (23.2800, 77.3400): ("426670", "99999", "Bhopal/Bairagarh Airport", 23.2875, 77.3374),
    (22.7200, 75.8000): ("426750", "99999", "Indore Airport", 22.7218, 75.8011),
    (23.1800, 79.9900): ("427090", "99999", "Jabalpur Airport", 23.1778, 79.9181),
    (26.2900, 78.2300): ("424150", "99999", "Gwalior Airport", 26.2933, 78.2278),
    
    # カルナータカ州（Karnataka）- 米・コーヒー
    (12.9500, 77.6681): ("432940", "99999", "Bangalore/HAL Airport", 12.9500, 77.6681),
    (12.3100, 76.6500): ("433150", "99999", "Mysore Airport", 12.2297, 76.6547),
    (15.3600, 75.0800): ("432200", "99999", "Hubli Airport", 15.3617, 75.0849),
    
    # テランガーナ州（Telangana）- 米・綿花
    (17.4500, 78.4675): ("431280", "99999", "Hyderabad/Shamshabad Airport", 17.2403, 78.4294),
    (18.0000, 79.5800): ("431160", "99999", "Warangal", 17.9189, 79.5926),
    
    # アーンドラ・プラデーシュ州（Andhra Pradesh）- 米・綿花
    (16.5200, 80.6200): ("431460", "99999", "Vijayawada/Gannavaram Airport", 16.5304, 80.7968),
    (17.7200, 83.2200): ("431500", "99999", "Visakhapatnam Airport", 17.7212, 83.2245),
    (13.6300, 79.5400): ("432450", "99999", "Tirupati Airport", 13.6325, 79.5433),
    
    # タミル・ナードゥ州（Tamil Nadu）- 米
    (12.9900, 80.1692): ("432780", "99999", "Chennai/Meenambakkam Airport", 12.9900, 80.1692),
    (11.0300, 77.0400): ("432950", "99999", "Coimbatore/Peelamedu Airport", 11.0300, 77.0434),
    (9.8400, 78.0900): ("433290", "99999", "Madurai Airport", 9.8347, 78.0934),
    (10.7700, 78.7100): ("433210", "99999", "Tiruchirappalli Airport", 10.7654, 78.7097),
    
    # 西ベンガル州（West Bengal）- 米・ジュート
    (22.6544, 88.4467): ("428090", "99999", "Kolkata/Dum Dum Airport", 22.6544, 88.4467),
    
    # ビハール州（Bihar）- 米・小麦
    (25.6000, 85.1000): ("424930", "99999", "Patna Airport", 25.5913, 85.0880),
    
    # オディシャ州（Odisha）- 米
    (20.2500, 85.8200): ("428740", "99999", "Bhubaneswar/Biju Patnaik Airport", 20.2444, 85.8178),
    
    # チャッティースガル州（Chhattisgarh）- 米
    (21.1800, 81.7300): ("429470", "99999", "Raipur Airport", 21.1804, 81.7388),
    
    # ジャールカンド州（Jharkhand）- 米
    (23.3100, 85.3200): ("427180", "99999", "Ranchi/Birsa Munda Airport", 23.3143, 85.3217),
}

# タイ主要農業地域の観測所マッピング（81地点）
# 選定基準：主要農作物生産地域（米、ゴム、パーム油、キャッサバ、サトウキビ等）、地理的バランス
THAILAND_LOCATION_MAPPING: Dict[Tuple[float, float], Tuple[str, str, str, float, float]] = {
    # (latitude, longitude): (usaf, wban, name, actual_lat, actual_lon)
    
    # 北部（Northern Region）- 米・果樹・茶
    (18.7670, 98.9630): ("483270", "99999", "Chiang Mai Intl", 18.767, 98.963),
    (18.5670, 99.0330): ("483290", "99999", "Lamphun", 18.567, 99.033),
    (19.8850, 99.8270): ("483030", "99999", "Chiang Rai", 19.885, 99.827),
    (19.9520, 99.8830): ("483031", "99999", "Mae Fah Luang Chiang Rai Intl", 19.952, 99.883),
    (18.2710, 99.5040): ("483280", "99999", "Lampang", 18.271, 99.504),
    (18.3170, 99.2830): ("483340", "99999", "Lampang Agromet", 18.317, 99.283),
    (18.8080, 100.7830): ("483310", "99999", "Nan", 18.808, 100.783),
    (18.8670, 100.7500): ("483330", "99999", "Nan Agromet", 18.867, 100.750),
    (18.1320, 100.1650): ("483300", "99999", "Phrae", 18.132, 100.165),
    (19.1930, 99.9000): ("483100", "99999", "Phayao", 19.193, 99.900),
    (19.3010, 97.9760): ("483000", "99999", "Mae Hong Son", 19.301, 97.976),
    (18.1670, 97.9330): ("483250", "99999", "Mae Sariang", 18.167, 97.933),
    (16.8960, 99.2530): ("483760", "99999", "Tak", 16.896, 99.253),
    (16.7000, 98.5450): ("483750", "99999", "Mae Sot", 16.700, 98.545),
    (16.7830, 100.2790): ("483780", "99999", "Phitsanulok", 16.783, 100.279),
    (17.6170, 100.1000): ("483510", "99999", "Uttaradit", 17.617, 100.100),
    (17.1000, 99.8000): ("483720", "99999", "Sukhothai", 17.100, 99.800),
    (16.6760, 101.1950): ("483790", "99999", "Phetchabun", 16.676, 101.195),
    (16.4830, 99.5330): ("483800", "99999", "Kamphaeng Phet", 16.483, 99.533),
    (19.4170, 100.8830): ("483070", "99999", "Tung Chang", 19.417, 100.883),
    
    # 東北部（Northeastern Region / Isan）- 最大の米生産地域
    (17.3860, 102.7880): ("483540", "99999", "Udon Thani", 17.386, 102.788),
    (17.8670, 102.7500): ("483520", "99999", "Nong Khai", 17.867, 102.750),
    (17.4390, 101.7220): ("483530", "99999", "Loei", 17.439, 101.722),
    (17.4000, 101.7330): ("483500", "99999", "Loei Agromet", 17.400, 101.733),
    (17.1950, 104.1190): ("483565", "99999", "Sakon Nakhon", 17.195, 104.119),
    (17.1170, 104.0500): ("483550", "99999", "Sakon Nakhon Agromet", 17.117, 104.050),
    (17.3840, 104.6430): ("483033", "99999", "Nakhon Phanom", 17.384, 104.643),
    (17.4330, 104.7830): ("483580", "99999", "Nakhon Phanom Agromet", 17.433, 104.783),
    (16.4670, 102.7840): ("483810", "99999", "Khon Kaen", 16.467, 102.784),
    (16.3330, 102.8170): ("483840", "99999", "Tha Phra Agromet", 16.333, 102.817),
    (16.5330, 104.7170): ("483830", "99999", "Mukdahan", 16.533, 104.717),
    (16.1170, 103.7740): ("483034", "99999", "Roi Et", 16.117, 103.774),
    (16.0670, 103.6170): ("484040", "99999", "Roi Et Agromet", 16.067, 103.617),
    (15.8000, 102.0330): ("484030", "99999", "Chaiyaphum", 15.800, 102.033),
    (14.9350, 102.0790): ("484310", "99999", "Khorat", 14.935, 102.079),
    (14.9490, 102.3130): ("484315", "99999", "Nakhon Ratchasima", 14.949, 102.313),
    (14.6330, 101.3170): ("484350", "99999", "Pakchong Agromet", 14.633, 101.317),
    (15.2300, 103.2530): ("484075", "99999", "Buri Ram", 15.230, 103.253),
    (14.6310, 102.7210): ("484360", "99999", "Nangrong", 14.631, 102.721),
    (14.8830, 103.5000): ("484320", "99999", "Surin", 14.883, 103.500),
    (14.8830, 103.4500): ("484330", "99999", "Surin Agromet", 14.883, 103.450),
    (15.2510, 104.8700): ("484070", "99999", "Ubon Ratchathani", 15.251, 104.870),
    (15.2330, 105.0330): ("484080", "99999", "Ubon Ratchathani Agromet", 15.233, 105.033),
    (15.0850, 104.3310): ("484090", "99999", "Si Saket Agromet", 15.085, 104.331),
    (16.2500, 103.0670): ("483820", "99999", "Kosumphisai", 16.250, 103.067),
    (17.2170, 102.4170): ("483600", "99999", "Nongbualamphu", 17.217, 102.417),
    
    # 中部（Central Region）- チャオプラヤー川流域・米の主要生産地
    (15.6730, 100.1370): ("484000", "99999", "Nakhon Sawan", 15.673, 100.137),
    (15.3500, 100.5000): ("484010", "99999", "Takfa Agromet", 15.350, 100.500),
    (15.1500, 100.1830): ("484020", "99999", "Chainat Agromet", 15.150, 100.183),
    (14.8000, 100.6170): ("484260", "99999", "Lop Buri", 14.800, 100.617),
    (14.5170, 100.7170): ("484150", "99999", "Ayutthaya", 14.517, 100.717),
    (14.4670, 100.1330): ("484250", "99999", "Suphan Buri", 14.467, 100.133),
    (14.3000, 99.8670): ("484270", "99999", "U Thong Agromet", 14.300, 99.867),
    (14.1000, 100.6170): ("484190", "99999", "Pathumthani", 14.100, 100.617),
    (13.9130, 100.6070): ("484560", "99999", "Bangkok Intl / Don Mueang Intl", 13.913, 100.607),
    (13.6830, 100.7670): ("484290", "99999", "Suvarnabhumi Inter Airport", 13.683, 100.767),
    (13.7330, 100.5670): ("484550", "99999", "Bangkok Metropolis", 13.733, 100.567),
    (13.5170, 100.7500): ("484200", "99999", "Samutprakan Agromet", 13.517, 100.750),
    (13.4830, 99.7830): ("484640", "99999", "Ratcha Buri", 13.483, 99.783),
    (14.0170, 99.5330): ("484500", "99999", "Kanchana Buri", 14.017, 99.533),
    (12.9990, 100.0670): ("484650", "99999", "Phetchaburi", 12.999, 100.067),
    (12.6360, 99.9520): ("484750", "99999", "Hua Hin", 12.636, 99.952),
    (11.7880, 99.8050): ("485000", "99999", "Prachuap", 11.788, 99.805),
    (13.5670, 101.4540): ("484580", "99999", "Chachoengsao Agromet", 13.567, 101.454),
    (12.6830, 100.9830): ("484770", "99999", "Sattahip", 12.683, 100.983),
    (12.6330, 101.3500): ("484780", "99999", "Rayong", 12.633, 101.350),
    (16.3330, 100.3670): ("483860", "99999", "Pichit Agromet", 16.333, 100.367),
    (13.9830, 101.7000): ("484390", "99999", "Kabinburi", 13.983, 101.700),
    (13.7830, 102.0330): ("484400", "99999", "Srakaew", 13.783, 102.033),
    
    # 南部（Southern Region）- ゴム・パーム油・果樹
    (10.7110, 99.3620): ("485170", "99999", "Chumphon", 10.711, 99.362),
    (9.7780, 98.5850): ("485320", "99999", "Ranong", 9.778, 98.585),
    (9.1330, 99.1360): ("485510", "99999", "Surat Thani", 9.133, 99.136),
    (9.1000, 99.6330): ("485550", "99999", "Surat Thani Agromet", 9.100, 99.633),
    (8.5400, 99.9450): ("485575", "99999", "Nakhon Si Thammarat", 8.540, 99.945),
    (8.3590, 100.0590): ("485540", "99999", "Nakhonsi Thammarat Agromet", 8.359, 100.059),
    (8.0990, 98.9860): ("485576", "99999", "Krabi", 8.099, 98.986),
    (8.1130, 98.3170): ("485650", "99999", "Phuket Intl", 8.113, 98.317),
    (7.8830, 98.4000): ("485640", "99999", "Phuket", 7.883, 98.400),
    (7.5090, 99.6170): ("485670", "99999", "Trang", 7.509, 99.617),
    (7.5830, 100.1670): ("485600", "99999", "Phatthalung Agromet", 7.583, 100.167),
    (7.1870, 100.6080): ("485680", "99999", "Songkhla", 7.187, 100.608),
    (6.9330, 100.3930): ("485690", "99999", "Hat Yai Intl", 6.933, 100.393),
    (6.7850, 101.1540): ("485800", "99999", "Pattani", 6.785, 101.154),
    (6.5170, 101.2830): ("485810", "99999", "Yala Agromet", 6.517, 101.283),
    (6.5200, 101.7430): ("485830", "99999", "Narathiwat", 6.520, 101.743),
    (9.5480, 100.0620): ("485577", "99999", "Samui", 9.548, 100.062),
    (8.4710, 99.9560): ("485520", "99999", "Cha Ian", 8.471, 99.956),
}

# 統合マッピング（US + India + Thailand）
LOCATION_MAPPING: Dict[Tuple[float, float], Tuple[str, str, str, float, float]] = {
    **US_LOCATION_MAPPING,
    **INDIA_LOCATION_MAPPING,
    **THAILAND_LOCATION_MAPPING,
}

class WeatherNOAAGateway(WeatherGateway):
    """Gateway for fetching weather data from NOAA ISD.
    
    Directly implements WeatherGateway interface without intermediate layers.
    Uses NOAA Integrated Surface Database via HTTP access.
    """
    
    # NOAA ISD データアクセスURL
    BASE_URL = "https://www.ncei.noaa.gov/data/global-hourly/access"
    
    def __init__(self, http_client: HttpClientInterface):
        """Initialize NOAA weather gateway.
        
        Args:
            http_client: HTTP client for data access
        """
        self.http_client = http_client
        self.logger = logging.getLogger(__name__)
    
    def get(self) -> List[WeatherData]:
        """Get weather data from configured source.
        
        Note: This method is not used for NOAA weather data.
        Use get_by_location_and_date_range() instead.
        
        Raises:
            NotImplementedError: NOAA requires location and date range parameters
        """
        raise NotImplementedError(
            "NOAA weather source requires location and date range. "
            "Use get_by_location_and_date_range() instead."
        )
    
    def create(self, weather_data: List[WeatherData], destination: str) -> None:
        """Create weather data at destination.
        
        Raises:
            NotImplementedError: Weather data creation not supported for NOAA source
        """
        raise NotImplementedError(
            "Weather data creation not supported for NOAA source"
        )
    
    def get_forecast(
        self,
        latitude: float,
        longitude: float
    ) -> WeatherDataWithLocationDTO:
        """Get weather forecast.
        
        Raises:
            NotImplementedError: NOAA ISD does not provide forecast data
        """
        raise NotImplementedError(
            "NOAA ISD does not provide forecast data. Use Open-Meteo API instead."
        )
    
    def _find_nearest_location(self, latitude: float, longitude: float) -> Tuple[str, str, str, float, float]:
        """Find the nearest NOAA observation station.
        
        Args:
            latitude: Target latitude
            longitude: Target longitude
            
        Returns:
            Tuple of (usaf, wban, location_name, station_lat, station_lon)
            
        Raises:
            WeatherAPIError: If no suitable location found
        """
        min_distance = float('inf')
        nearest = None
        
        for (lat, lon), (usaf, wban, name, st_lat, st_lon) in LOCATION_MAPPING.items():
            # 簡易的な距離計算（緯度経度の差の二乗和）
            distance = ((latitude - lat) ** 2 + (longitude - lon) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                nearest = (usaf, wban, name, st_lat, st_lon)
        
        if nearest is None:
            raise WeatherAPIError(
                f"No NOAA observation station found for location ({latitude}, {longitude})"
            )
        
        return nearest
    
    def get_by_location_and_date_range(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str
    ) -> WeatherDataWithLocationDTO:
        """Get weather data from NOAA ISD.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            WeatherDataWithLocationDTO containing weather data and location
            
        Raises:
            WeatherAPIError: If data retrieval fails
            WeatherDataNotFoundError: If no data found
        """
        try:
            # Find nearest observation station
            usaf, wban, location_name, station_lat, station_lon = self._find_nearest_location(latitude, longitude)
            
            self.logger.info(
                f"Using NOAA station: {location_name} (USAF: {usaf}, WBAN: {wban}) "
                f"at ({station_lat}, {station_lon})"
            )
            
            # Parse and validate date range
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError as e:
                raise WeatherAPIError(
                    f"Invalid date format. Expected YYYY-MM-DD, "
                    f"got start_date='{start_date}', end_date='{end_date}': {e}"
                )
            
            # Validate date order
            if start > end:
                raise WeatherAPIError(
                    f"start_date ({start_date}) must be before or equal to "
                    f"end_date ({end_date})"
                )
            
            # Collect data for each year in the range
            all_weather_data = []
            failed_years = []
            
            current_year = start.year
            end_year = end.year
            
            while current_year <= end_year:
                try:
                    # Build filename for this year
                    # Format: {USAF}{WBAN}.csv (no hyphens, no year in filename)
                    filename = f"{usaf}{wban}.csv"
                    url = f"{self.BASE_URL}/{current_year}/{filename}"
                    
                    self.logger.info(f"Fetching NOAA data from: {url}")
                    
                    # Fetch CSV data (as text)
                    response_text = self._fetch_csv_text(url)
                    
                    # Parse CSV data
                    year_data = self._parse_noaa_csv(response_text, start_date, end_date)
                    all_weather_data.extend(year_data)
                    
                except Exception as e:
                    # Log failure but continue with other years
                    failed_years.append(current_year)
                    self.logger.warning(
                        f"Failed to fetch data for {current_year}: {e}. "
                        f"Continuing with available data."
                    )
                
                current_year += 1
            
            # If we got no data at all, raise error
            if not all_weather_data:
                raise WeatherDataNotFoundError(
                    f"No weather data found for location ({latitude}, {longitude}) "
                    f"from {start_date} to {end_date}. "
                    f"Station: {location_name}. "
                    f"Failed years: {failed_years if failed_years else 'None'}"
                )
            
            # Log partial success if any years failed
            if failed_years:
                self.logger.warning(
                    f"Partial data returned. Missing data for {len(failed_years)} year(s): {failed_years}"
                )
            
            # Group by day and calculate daily statistics
            daily_weather_data = self._aggregate_to_daily(all_weather_data)
            
            # Create location with appropriate timezone
            # Determine timezone based on longitude (simplified)
            if 6 <= station_lat <= 20 and 97 <= station_lon <= 106:
                # Thailand region
                tz = "Asia/Bangkok"
            elif 6 <= station_lat <= 36 and 68 <= station_lon <= 98:
                # India region
                tz = "Asia/Kolkata"
            else:
                # US region (default)
                tz = "America/New_York"
            
            location = Location(
                latitude=station_lat,
                longitude=station_lon,
                elevation=None,  # ISD doesn't always provide elevation
                timezone=tz
            )
            
            return WeatherDataWithLocationDTO(
                weather_data_list=daily_weather_data,
                location=location
            )
            
        except WeatherAPIError:
            raise
        except Exception as e:
            raise WeatherAPIError(f"Failed to fetch NOAA data: {e}")
    
    def _fetch_csv_text(self, url: str) -> str:
        """Fetch CSV text from URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            CSV text content
            
        Raises:
            WeatherAPIError: If fetch fails
        """
        import requests
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            raise WeatherAPIError(f"Failed to fetch NOAA data from {url}: {e}")
    
    def _parse_noaa_csv(
        self,
        csv_text: str,
        start_date: str,
        end_date: str
    ) -> List[WeatherData]:
        """Parse NOAA ISD CSV data.
        
        Args:
            csv_text: CSV text content
            start_date: Filter start date (YYYY-MM-DD)
            end_date: Filter end date (YYYY-MM-DD)
            
        Returns:
            List of WeatherData entities (hourly)
        """
        import csv
        from io import StringIO
        
        weather_data_list = []
        
        # Parse date range for filtering
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        reader = csv.DictReader(StringIO(csv_text))
        
        for row in reader:
            try:
                # Parse date/time
                date_str = row.get('DATE', '')
                if not date_str:
                    continue
                
                # DATE format: 2024-01-15T12:00:00
                record_time = datetime.fromisoformat(date_str.replace('Z', '+00:00')).replace(tzinfo=None)
                
                # Filter by date range
                if record_time.date() < start_dt.date() or record_time.date() > end_dt.date():
                    continue
                
                # Extract temperature (TMP column: "+15.5,1" format)
                temp = self._parse_noaa_value(row.get('TMP', ''))
                
                # Extract precipitation (AA1 column for precipitation)
                precip = self._parse_noaa_value(row.get('AA1', ''), scale=10.0)  # Convert mm/10 to mm
                
                # Extract wind speed (WND column)
                wind_speed = self._parse_noaa_value(row.get('WND', ''))
                
                # Create WeatherData entity (hourly)
                weather_data = WeatherData(
                    time=record_time,
                    temperature_2m_max=temp,  # 時間データなので仮でmaxに入れる
                    temperature_2m_min=temp,  # 時間データなので仮でminに入れる
                    temperature_2m_mean=temp,
                    precipitation_sum=precip,
                    sunshine_duration=None,  # NOAA ISDには含まれない
                    wind_speed_10m=wind_speed,
                    weather_code=None,
                )
                
                weather_data_list.append(weather_data)
                
            except Exception as e:
                self.logger.warning(f"Failed to parse row: {e}")
                continue
        
        return weather_data_list
    
    def _parse_noaa_value(self, value_str: str, scale: float = 10.0) -> Optional[float]:
        """Parse NOAA value format.
        
        NOAA format: "+15.5,1" where first part is value*10, second is quality
        
        Args:
            value_str: Value string from NOAA CSV
            scale: Scale divisor (default 10.0)
            
        Returns:
            Parsed float value or None
        """
        if not value_str or value_str == '':
            return None
        
        try:
            # Split by comma
            parts = value_str.split(',')
            if len(parts) < 1:
                return None
            
            # Extract numeric part
            value_part = parts[0].strip()
            
            # Handle missing data indicators
            if value_part in ['+9999', '9999', '+999999', '999999']:
                return None
            
            # Convert to float and scale
            value = float(value_part) / scale
            
            return value
            
        except (ValueError, IndexError):
            return None
    
    def _aggregate_to_daily(self, hourly_data: List[WeatherData]) -> List[WeatherData]:
        """Aggregate hourly data to daily statistics.
        
        Args:
            hourly_data: List of hourly WeatherData
            
        Returns:
            List of daily WeatherData with min/max/mean
        """
        from collections import defaultdict
        
        # Group by date
        daily_groups = defaultdict(list)
        for data in hourly_data:
            date_key = data.time.date()
            daily_groups[date_key].append(data)
        
        daily_weather_data = []
        
        for date_key in sorted(daily_groups.keys()):
            day_records = daily_groups[date_key]
            
            # Calculate statistics
            temps = [r.temperature_2m_mean for r in day_records if r.temperature_2m_mean is not None]
            precips = [r.precipitation_sum for r in day_records if r.precipitation_sum is not None]
            winds = [r.wind_speed_10m for r in day_records if r.wind_speed_10m is not None]
            
            # Create daily weather data
            daily_data = WeatherData(
                time=datetime.combine(date_key, datetime.min.time()),
                temperature_2m_max=max(temps) if temps else None,
                temperature_2m_min=min(temps) if temps else None,
                temperature_2m_mean=sum(temps) / len(temps) if temps else None,
                precipitation_sum=sum(precips) if precips else None,
                sunshine_duration=None,
                wind_speed_10m=max(winds) if winds else None,
                weather_code=None,
            )
            
            daily_weather_data.append(daily_data)
        
        return daily_weather_data

