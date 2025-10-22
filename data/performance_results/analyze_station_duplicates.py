"""
観測所の重複・近接地点を分析

CSVから取得したデータを分析して、同じ地点や非常に近い地点を検出します。
"""

import csv
from collections import defaultdict
import math


def read_csv_data(filename):
    """CSVファイルを読み込む"""
    stations = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['ステータス'] == 'success':
                stations.append({
                    'region': row['地域'],
                    'name': row['観測所名'],
                    'avg_temp': float(row['平均気温']) if row['平均気温'] else None
                })
    return stations


def calculate_distance(lat1, lon1, lat2, lon2):
    """2点間の距離を計算（km）"""
    # 簡易的なユークリッド距離（緯度経度を度で計算）
    # 1度 ≈ 111km
    dlat = (lat2 - lat1) * 111
    dlon = (lon2 - lon1) * 111 * math.cos(math.radians((lat1 + lat2) / 2))
    return math.sqrt(dlat**2 + dlon**2)


def analyze_duplicates():
    """観測所の重複を分析"""
    from agrr_core.adapter.gateways.weather_noaa_gateway import THAILAND_LOCATION_MAPPING
    
    print("="*80)
    print("タイ観測所の重複・近接地点分析")
    print("="*80)
    print()
    
    # CSVデータを読み込み
    csv_data = read_csv_data('thailand_stations_test_result.csv')
    csv_dict = {station['name']: station for station in csv_data}
    
    print(f"総観測所数（マッピング）: {len(THAILAND_LOCATION_MAPPING)}地点")
    print(f"成功した観測所数（CSV）: {len(csv_data)}地点")
    print()
    
    # 1. 完全一致する座標を探す
    print("1. 完全一致する座標の検出")
    print("-"*80)
    
    coord_groups = defaultdict(list)
    for (lat, lon), (usaf, wban, name, actual_lat, actual_lon) in THAILAND_LOCATION_MAPPING.items():
        # 座標をキーにグループ化（小数点3桁で丸める）
        coord_key = (round(actual_lat, 3), round(actual_lon, 3))
        coord_groups[coord_key].append((name, actual_lat, actual_lon, usaf))
    
    duplicate_coords = {k: v for k, v in coord_groups.items() if len(v) > 1}
    
    if duplicate_coords:
        print(f"完全一致する座標: {len(duplicate_coords)}組")
        for coord, stations in duplicate_coords.items():
            print(f"\n座標: {coord}")
            for name, lat, lon, usaf in stations:
                status = "✅" if name in csv_dict else "❌"
                avg_temp = csv_dict[name]['avg_temp'] if name in csv_dict else "N/A"
                print(f"  {status} {name} (USAF: {usaf}) - {avg_temp}°C")
                print(f"     詳細座標: ({lat}, {lon})")
    else:
        print("完全一致する座標はありません")
    
    print()
    
    # 2. 非常に近い地点を探す（5km以内）
    print("2. 近接地点の検出（5km以内）")
    print("-"*80)
    
    stations_list = []
    for (lat, lon), (usaf, wban, name, actual_lat, actual_lon) in THAILAND_LOCATION_MAPPING.items():
        if name in csv_dict:
            stations_list.append({
                'name': name,
                'lat': actual_lat,
                'lon': actual_lon,
                'usaf': usaf,
                'avg_temp': csv_dict[name]['avg_temp'],
                'region': csv_dict[name]['region']
            })
    
    nearby_pairs = []
    for i, station1 in enumerate(stations_list):
        for station2 in stations_list[i+1:]:
            distance = calculate_distance(
                station1['lat'], station1['lon'],
                station2['lat'], station2['lon']
            )
            
            if distance < 5.0:  # 5km以内
                nearby_pairs.append({
                    'station1': station1,
                    'station2': station2,
                    'distance': distance
                })
    
    if nearby_pairs:
        print(f"近接地点: {len(nearby_pairs)}組")
        
        # 距離でソート
        nearby_pairs.sort(key=lambda x: x['distance'])
        
        for pair in nearby_pairs:
            s1 = pair['station1']
            s2 = pair['station2']
            dist = pair['distance']
            temp_diff = abs(s1['avg_temp'] - s2['avg_temp'])
            
            print(f"\n距離: {dist:.2f}km | 気温差: {temp_diff:.2f}°C")
            print(f"  1. {s1['name']} ({s1['region']})")
            print(f"     座標: ({s1['lat']}, {s1['lon']}) | USAF: {s1['usaf']}")
            print(f"     平均気温: {s1['avg_temp']:.1f}°C")
            print(f"  2. {s2['name']} ({s2['region']})")
            print(f"     座標: ({s2['lat']}, {s2['lon']}) | USAF: {s2['usaf']}")
            print(f"     平均気温: {s2['avg_temp']:.1f}°C")
            
            # 統合候補を提案
            if temp_diff < 1.0 and dist < 1.0:
                print(f"     ⚠️  統合候補: 気温差が小さく距離も近い")
    else:
        print("5km以内の近接地点はありません")
    
    print()
    
    # 3. 同じUSAFコードを持つ地点
    print("3. 同じUSAFコードの検出")
    print("-"*80)
    
    usaf_groups = defaultdict(list)
    for (lat, lon), (usaf, wban, name, actual_lat, actual_lon) in THAILAND_LOCATION_MAPPING.items():
        usaf_groups[usaf].append((name, actual_lat, actual_lon))
    
    duplicate_usaf = {k: v for k, v in usaf_groups.items() if len(v) > 1}
    
    if duplicate_usaf:
        print(f"同じUSAFコード: {len(duplicate_usaf)}組")
        for usaf, stations in duplicate_usaf.items():
            print(f"\nUSAF: {usaf}")
            for name, lat, lon in stations:
                status = "✅" if name in csv_dict else "❌"
                avg_temp = csv_dict[name]['avg_temp'] if name in csv_dict else "N/A"
                print(f"  {status} {name} - ({lat}, {lon}) - {avg_temp}°C")
    else:
        print("同じUSAFコードの地点はありません")
    
    print()
    
    # 4. 同じ都市名を持つ地点（Agrometなど）
    print("4. 同じ都市名を持つ地点の検出")
    print("-"*80)
    
    city_groups = defaultdict(list)
    for (lat, lon), (usaf, wban, name, actual_lat, actual_lon) in THAILAND_LOCATION_MAPPING.items():
        # 都市名を抽出（AgromまたはIntlなどを除く）
        city_name = name.replace(" Agromet", "").replace(" Intl", "").replace(" Airport", "")
        if " / " in city_name:
            city_name = city_name.split(" / ")[0].strip()
        
        city_groups[city_name].append({
            'full_name': name,
            'lat': actual_lat,
            'lon': actual_lon,
            'usaf': usaf,
            'in_csv': name in csv_dict,
            'avg_temp': csv_dict[name]['avg_temp'] if name in csv_dict else None
        })
    
    duplicate_cities = {k: v for k, v in city_groups.items() if len(v) > 1}
    
    if duplicate_cities:
        print(f"同じ都市に複数観測所: {len(duplicate_cities)}都市")
        for city, stations in sorted(duplicate_cities.items()):
            print(f"\n{city}: {len(stations)}地点")
            for station in stations:
                status = "✅" if station['in_csv'] else "❌"
                temp_str = f"{station['avg_temp']:.1f}°C" if station['avg_temp'] else "N/A"
                print(f"  {status} {station['full_name']}")
                print(f"     座標: ({station['lat']}, {station['lon']}) | USAF: {station['usaf']} | {temp_str}")
    else:
        print("同じ都市に複数観測所はありません")
    
    print()
    print("="*80)
    print("分析完了")
    print("="*80)


if __name__ == "__main__":
    analyze_duplicates()

