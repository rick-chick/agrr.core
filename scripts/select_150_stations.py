#!/usr/bin/env python3
"""
Select 150 optimal weather stations from NOAA ISD database.

Selection criteria:
1. Geographic coverage (all 50 states)
2. Agricultural importance (major crop production areas)
3. Climate diversity (different climate zones)
4. Data quality (long-term continuous data)
"""

import json
from collections import defaultdict
from datetime import datetime


# 州別の優先地点数（農業重要度と面積で調整）
STATE_PRIORITIES = {
    # 超大型州（10-15地点）
    'AK': 10,  # Alaska - 広大だが農業少
    'TX': 15,  # Texas - 巨大で農業重要
    'CA': 15,  # California - 農業超重要
    
    # 大型農業州（5-8地点）
    'IA': 8,   # Iowa - Corn Belt核心
    'IL': 8,   # Illinois - Corn Belt
    'NE': 7,   # Nebraska - Corn/Wheat
    'KS': 7,   # Kansas - Wheat Belt
    'MN': 7,   # Minnesota - Corn/Soybean
    'IN': 6,   # Indiana - Corn Belt
    'ND': 6,   # North Dakota - Wheat
    'SD': 5,   # South Dakota - Corn/Wheat
    'MO': 5,   # Missouri - 農業重要
    'WI': 5,   # Wisconsin - Dairy/Corn
    'OH': 5,   # Ohio - Corn/Soybean
    
    # 中型農業州（3-4地点）
    'MT': 4,   # Montana - Wheat
    'OK': 4,   # Oklahoma - Wheat/Cotton
    'MI': 4,   # Michigan - 多様な農業
    'GA': 4,   # Georgia - Cotton/Peanuts
    'NC': 4,   # North Carolina - Tobacco/Hogs
    'AR': 3,   # Arkansas - Rice/Poultry
    'MS': 3,   # Mississippi - Cotton
    'AL': 3,   # Alabama - Cotton
    'CO': 3,   # Colorado - Wheat/Cattle
    'WA': 3,   # Washington - Wheat/Apples
    'OR': 3,   # Oregon - Wheat/Berries
    'ID': 3,   # Idaho - Potatoes/Wheat
    'FL': 3,   # Florida - Citrus/Vegetables
    'LA': 3,   # Louisiana - Rice/Sugarcane
    'NY': 3,   # New York - Dairy/Vegetables
    'PA': 3,   # Pennsylvania - Dairy/Corn
    'VA': 3,   # Virginia - Tobacco/Peanuts
    'KY': 3,   # Kentucky - Tobacco/Corn
    'TN': 3,   # Tennessee - Cotton/Soybeans
    'SC': 3,   # South Carolina - Cotton
    
    # 小型州（2地点）
    'WY': 2,
    'AZ': 2,
    'NM': 2,
    'NV': 2,
    'UT': 2,
    'ME': 2,
    'WV': 2,
    
    # 極小州（1地点）
    'MA': 1,
    'CT': 1,
    'RI': 1,
    'VT': 1,
    'NH': 1,
    'NJ': 1,
    'DE': 1,
    'MD': 1,
    'HI': 1,
}


def calculate_station_score(station, state_stations):
    """
    Calculate priority score for a station.
    Higher score = higher priority.
    """
    score = 0
    
    # 1. ICAOコード（空港）がある = +100（データ品質高い）
    if station.get('icao'):
        score += 100
    
    # 2. データ期間の長さ
    try:
        begin = station.get('begin', '')
        if begin and len(begin) == 8:
            begin_year = int(begin[:4])
            data_length = 2024 - begin_year
            score += min(data_length, 50)  # 最大50点
    except:
        pass
    
    # 3. 観測所名に"AIRPORT"/"MUNICIPAL"が含まれる = +30
    name = station.get('name', '').upper()
    if 'AIRPORT' in name or 'MUNICIPAL' in name or 'REGIONAL' in name:
        score += 30
    
    # 4. WBAN番号がある = +20（古くからの観測所）
    if station.get('wban') != '99999':
        score += 20
    
    # 5. 標高が適切（-100m〜3000m）= +10
    try:
        elev = station.get('elev', '')
        if elev:
            elev_val = float(elev.replace('+', '').replace('-', ''))
            if -100 <= elev_val <= 3000:
                score += 10
    except:
        pass
    
    return score


def select_stations_for_state(state, stations, target_count):
    """Select best stations for a state."""
    # スコアを計算
    scored_stations = []
    for station in stations:
        score = calculate_station_score(station, stations)
        scored_stations.append((score, station))
    
    # スコア順にソート
    scored_stations.sort(reverse=True, key=lambda x: x[0])
    
    # 地理的分散を考慮して選択
    selected = []
    for score, station in scored_stations:
        if len(selected) >= target_count:
            break
        
        # 既に選択済みの観測所と距離をチェック（簡易版）
        too_close = False
        for sel_station in selected:
            lat_diff = abs(station['lat'] - sel_station['lat'])
            lon_diff = abs(station['lon'] - sel_station['lon'])
            
            # 大きな州では最低1度、小さな州では0.5度の間隔
            min_distance = 1.0 if target_count > 3 else 0.5
            
            if lat_diff < min_distance and lon_diff < min_distance:
                too_close = True
                break
        
        if not too_close:
            selected.append(station)
    
    return selected


def main():
    # NOAA観測所データを読み込み
    with open('noaa_us_stations.json', 'r') as f:
        data = json.load(f)
    
    all_stations = data['stations']
    
    # 州別にグループ化
    by_state = defaultdict(list)
    for station in all_stations:
        by_state[station['state']].append(station)
    
    print("=== Selecting 150 Weather Stations ===\n")
    
    # 各州の地点を選択
    selected_stations = {}
    total_selected = 0
    
    for state in sorted(STATE_PRIORITIES.keys()):
        target_count = STATE_PRIORITIES[state]
        
        if state not in by_state:
            print(f"⚠️  {state}: No stations available")
            continue
        
        available = len(by_state[state])
        actual_count = min(target_count, available)
        
        state_stations = select_stations_for_state(
            state, 
            by_state[state], 
            actual_count
        )
        
        selected_stations[state] = state_stations
        total_selected += len(state_stations)
        
        print(f"{state}: {len(state_stations):2d}/{target_count:2d} stations (available: {available:3d})")
    
    print(f"\n📊 Total selected: {total_selected} stations")
    print(f"🎯 Target: 150 stations")
    print(f"{'✅' if total_selected >= 150 else '⚠️'} Coverage: {total_selected/150*100:.1f}%")
    
    # Python辞書形式で出力（コードに直接使用可能）
    print("\n" + "="*80)
    print("LOCATION_MAPPING_150 = {")
    print("    # (latitude, longitude): (usaf, wban, name, actual_lat, actual_lon)")
    
    for state in sorted(selected_stations.keys()):
        print(f"\n    # {state} - {len(selected_stations[state])} stations")
        for station in selected_stations[state]:
            lat = station['lat']
            lon = station['lon']
            usaf = station['usaf']
            wban = station['wban']
            name = station['name']
            
            # 座標を0.01度単位に丸める（検索用）
            search_lat = round(lat, 2)
            search_lon = round(lon, 2)
            
            print(f'    ({search_lat}, {search_lon}): ("{usaf}", "{wban}", "{name}, {state}", {lat:.4f}, {lon:.4f}),')
    
    print("}")
    print("="*80)
    
    # JSONファイルとしても保存
    output = {
        'total_stations': total_selected,
        'states': {state: len(stations) for state, stations in selected_stations.items()},
        'stations': selected_stations
    }
    
    with open('selected_150_stations.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Saved to selected_150_stations.json")
    
    # 州別サマリー
    print(f"\n=== Coverage Summary ===")
    print(f"States covered: {len(selected_stations)}/50")
    print(f"Total stations: {total_selected}")
    print(f"Average per state: {total_selected/len(selected_stations):.1f}")
    
    # 地点数別の州数
    counts = defaultdict(int)
    for state, stations in selected_stations.items():
        counts[len(stations)] += 1
    
    print(f"\n=== Distribution ===")
    for count in sorted(counts.keys(), reverse=True):
        print(f"{count:2d} stations: {counts[count]:2d} states")


if __name__ == '__main__':
    main()

