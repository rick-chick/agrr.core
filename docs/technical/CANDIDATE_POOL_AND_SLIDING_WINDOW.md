# 候補プールとスライディングウィンドウの関係

## 概要

作物配置最適化における**候補プール**と**スライディングウィンドウアルゴリズム**の関係を説明します。

---

## 全体フロー

```
Phase 1: 候補生成（事前処理）
┌────────────────────────────────────────────────────────┐
│ GrowthPeriodOptimizeInteractor                         │
│   ├─ スライディングウィンドウアルゴリズム             │
│   └─ すべての有効な開始日を網羅的に評価              │
└───────────────────┬────────────────────────────────────┘
                    │
                    ▼
              候補プール生成
         (Field × Crop × StartDate)
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│ 候補プール（固定リスト）                               │
│                                                        │
│ Field A × Tomato:                                      │
│   - Start: 2024-05-01, End: 2024-08-08, GDD: 1000     │
│   - Start: 2024-05-02, End: 2024-08-09, GDD: 1000     │
│   - Start: 2024-05-03, End: 2024-08-10, GDD: 1000     │
│   ...                                                  │
│                                                        │
│ Field B × Tomato:                                      │
│   - Start: 2024-05-01, End: 2024-08-08, GDD: 1000     │
│   ...                                                  │
└───────────────────┬────────────────────────────────────┘
                    │
                    ▼
Phase 2: 最適化（メイン処理）
┌────────────────────────────────────────────────────────┐
│ MultiFieldCropAllocationGreedyInteractor               │
│   ├─ Greedy Allocation（候補プールから選択）          │
│   ├─ Local Search / ALNS                               │
│   │   └─ 候補プール内でのみ移動可能 ⚠️                │
│   └─ 最適解を出力                                      │
└────────────────────────────────────────────────────────┘
```

---

## 1. スライディングウィンドウアルゴリズム

### 役割
**あらゆる開始日から栽培開始した場合の終了日を効率的に計算**

### 実装場所
`src/agrr_core/usecase/interactors/growth_period_optimize_interactor.py`

### アルゴリズム

```python
def sliding_window_gdd_accumulation(
    crop_profile: CropProfile,
    weather_data: List[WeatherData],
    evaluation_start: datetime,
    evaluation_end: datetime
) -> List[CandidateResultDTO]:
    """スライディングウィンドウでGDD蓄積を計算.
    
    Time Complexity: O(M)
    - M = 天気データの日数
    - 各日付を最大2回スキャン（開始と終了）
    
    vs. Naive: O(N × M)
    - N = 候補開始日数
    - M = 天気データ日数
    
    Speedup: 最大200倍（N=200日の場合）
    """
    total_required_gdd = sum(stage.thermal.required_gdd for stage in stages)
    
    # 初期化
    start_date = evaluation_start
    accumulated_gdd = 0.0
    window_start_idx = 0
    window_end_idx = 0
    results = []
    
    # Step 1: 最初の候補の終了日を求める
    # evaluation_start から開始して、GDD >= required_gdd になるまで蓄積
    while window_end_idx < len(weather_data) and accumulated_gdd < total_required_gdd:
        daily_gdd = calculate_gdd(weather_data[window_end_idx].temp)
        accumulated_gdd += daily_gdd
        window_end_idx += 1
    
    if accumulated_gdd >= total_required_gdd:
        completion_date = weather_data[window_end_idx - 1].time
        results.append(CandidateResultDTO(
            start_date=start_date,
            completion_date=completion_date,
            growth_days=(completion_date - start_date).days,
            accumulated_gdd=accumulated_gdd
        ))
    
    # Step 2: スライドさせて次の候補を計算
    # 開始日を1日ずつ後ろにずらす
    while start_date < evaluation_end:
        # 古い開始日のGDDを削除
        old_gdd = calculate_gdd(weather_data[window_start_idx].temp)
        accumulated_gdd -= old_gdd
        window_start_idx += 1
        
        # 新しい開始日に移動
        start_date += timedelta(days=1)
        
        # 終了日を延長してGDDを補充
        while accumulated_gdd < total_required_gdd and window_end_idx < len(weather_data):
            daily_gdd = calculate_gdd(weather_data[window_end_idx].temp)
            accumulated_gdd += daily_gdd
            window_end_idx += 1
        
        # 候補を記録
        if accumulated_gdd >= total_required_gdd:
            completion_date = weather_data[window_end_idx - 1].time
            results.append(CandidateResultDTO(
                start_date=start_date,
                completion_date=completion_date,
                growth_days=(completion_date - start_date).days,
                accumulated_gdd=accumulated_gdd
            ))
    
    return results
```

### 可視化

```
天気データ: [Day1, Day2, Day3, Day4, Day5, Day6, Day7, Day8, ...]
             ↓     ↓     ↓     ↓     ↓     ↓     ↓     ↓
             10°   12°   15°   20°   18°   16°   14°   12°  (平均気温)
             
Required GDD: 50 (仮定)
Base Temperature: 10°C

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

候補1: Start = Day1
Window: [Day1, Day2, Day3, Day4, Day5, Day6]
        └─────────────────────────────────┘
GDD:     0 +  2  +  5  + 10 +  8  +  6  = 31 ❌ 不足
        
さらに延長:
Window: [Day1, Day2, Day3, Day4, Day5, Day6, Day7, Day8]
        └───────────────────────────────────────────────┘
GDD:     0 +  2  +  5  + 10 +  8  +  6  +  4  +  2  = 37 ❌ 不足

（実際はもっと長い）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

候補2: Start = Day2（1日スライド）
        ┌─────────────────────────────────┐
Window: [Day2, Day3, Day4, Day5, Day6, Day7, ...]
GDD: (37 - 0) + ... = 再計算せずに増分更新 ⚡️

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

候補3: Start = Day3（さらに1日スライド）
              ┌─────────────────────────────┐
Window:       [Day3, Day4, Day5, Day6, Day7, ...]
GDD: (前回 - Day2のGDD) + ... = 増分更新 ⚡️

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

これを繰り返す → すべての開始日の候補を効率的に生成
```

### 特徴

| 項目 | スライディングウィンドウ | Naive実装 |
|------|--------------------------|-----------|
| **計算量** | O(M) | O(N × M) |
| **実例** | 1秒（M=365日） | 200秒（N=200, M=365） |
| **利点** | 圧倒的に高速 | 実装が単純 |
| **欠点** | 実装がやや複雑 | 実用不可能なほど遅い |

---

## 2. 候補プールの生成

### 生成プロセス

```python
# MultiFieldCropAllocationGreedyInteractor._generate_candidates_for_field_crop()

async def generate_all_candidates(
    fields: List[Field],
    crops: List[Crop],
    planning_period_start: datetime,
    planning_period_end: datetime,
    config: OptimizationConfig
) -> List[AllocationCandidate]:
    """すべてのField × Cropの組み合わせで候補生成."""
    
    all_candidates = []
    
    # Field × Crop のすべての組み合わせ
    for field in fields:
        for crop in crops:
            # スライディングウィンドウで期間候補を生成
            optimization_result = await growth_period_optimizer.execute(
                OptimalGrowthPeriodRequestDTO(
                    crop_id=crop.crop_id,
                    evaluation_period_start=planning_period_start,
                    evaluation_period_end=planning_period_end,
                    field=field
                )
            )
            
            # 上位N個の期間候補を選択
            top_period_candidates = optimization_result.candidates[:config.top_period_candidates]
            
            # Area × Period の組み合わせ
            for area_level in config.area_levels:  # [0.25, 0.5, 0.75, 1.0]
                area_used = field.area * area_level
                
                for period_candidate in top_period_candidates:
                    # 候補プールに追加
                    candidate = AllocationCandidate(
                        field=field,
                        crop=crop,
                        start_date=period_candidate.start_date,
                        completion_date=period_candidate.completion_date,
                        growth_days=period_candidate.growth_days,
                        accumulated_gdd=period_candidate.accumulated_gdd,
                        area_used=area_used
                    )
                    all_candidates.append(candidate)
    
    return all_candidates
```

### 候補プールのサイズ

```
候補数 = Fields × Crops × PeriodCandidates × AreaLevels

例:
- Fields = 3圃場
- Crops = 6作物
- PeriodCandidates = 10個（上位10個の開始日）
- AreaLevels = 4個 [25%, 50%, 75%, 100%]

候補数 = 3 × 6 × 10 × 4 = 720候補
```

### 候補プールの例

```json
[
  {
    "field": {"field_id": "field_A", "name": "東圃場", "area": 10000},
    "crop": {"crop_id": "tomato", "name": "トマト"},
    "start_date": "2024-05-01",
    "completion_date": "2024-08-08",
    "growth_days": 100,
    "accumulated_gdd": 1000.0,
    "area_used": 2500.0  // 25%
  },
  {
    "field": {"field_id": "field_A", "name": "東圃場", "area": 10000},
    "crop": {"crop_id": "tomato", "name": "トマト"},
    "start_date": "2024-05-01",
    "completion_date": "2024-08-08",
    "growth_days": 100,
    "accumulated_gdd": 1000.0,
    "area_used": 5000.0  // 50%
  },
  {
    "field": {"field_id": "field_A", "name": "東圃場", "area": 10000},
    "crop": {"crop_id": "tomato", "name": "トマト"},
    "start_date": "2024-05-02",  // 1日後
    "completion_date": "2024-08-09",
    "growth_days": 100,
    "accumulated_gdd": 1000.0,
    "area_used": 2500.0
  },
  // ... 717候補 ...
]
```

---

## 3. 候補プールの制約

### 問題: 候補プールは固定リスト

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
候補プール（固定）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Field A × Tomato:
  ✅ 2024-05-01 開始
  ✅ 2024-05-02 開始
  ✅ 2024-05-03 開始
  ...
  ✅ 2024-05-10 開始（上位10個まで）
  
  ❌ 2024-05-11 開始（候補プールにない！）
  ❌ 2024-05-15 開始（候補プールにない！）
  ❌ 2024-06-01 開始（候補プールにない！）

Field B × Tomato:
  ✅ 2024-05-01 開始
  ✅ 2024-05-02 開始
  ...

Field A × Lettuce:
  ✅ 2024-04-01 開始
  ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 近傍操作の制約

```python
# FieldMoveOperation: 圃場Aから圃場Bに移動

現在の割当:
  Field A, Tomato, 2024-05-01 開始

移動先候補を検索:
  candidates から検索:
    Field B × Tomato × 2024-05-01 ← ✅ 見つかった！
    
しかし...

  Field B × Tomato × 2024-06-01 ← ❌ 候補プールにない
                                     → 移動できない
```

### 具体例: Local Search の制約

```
初期解（Greedy）:
┌────────────────────────────────────────┐
│ Field A: Tomato (2024-05-01~08-08)     │
│ Field B: Lettuce (2024-06-01~08-31)    │
└────────────────────────────────────────┘

Local Search が試したい移動:
  Field A の Tomato を Field B に移動
    → Field B × Tomato × 2024-05-01 を探す
    → ✅ 候補プールにある → 移動可能
  
  Field A の Tomato を 2024-06-01 に遅らせる
    → Field A × Tomato × 2024-06-01 を探す
    → ❌ 候補プールにない（上位10個に入ってない）
    → 移動不可 ⚠️

問題:
  候補プールの top_period_candidates=10 なので
  11番目以降の開始日は試せない！
```

---

## 4. 解決策: 動的GDD計算

### Before（現状）

```
近傍操作
  ↓
候補プールから検索
  ├─ 見つかった → ✅ 使用
  └─ 見つからない → ❌ 諦める（移動不可）
```

### After（改善案）

```
近傍操作
  ↓
候補プールから検索
  ├─ 見つかった → ✅ 使用（高速パス）
  └─ 見つからない
       ↓
     動的GDD計算（スライディングウィンドウを再実行）
       ├─ 計算成功 → ✅ 新規候補を生成
       └─ 計算失敗 → ❌ 諦める
```

### 実装例

```python
# CropMovementService.get_or_calculate_allocation()

def get_or_calculate_allocation(
    target_field: Field,
    crop: Crop,
    start_date: datetime,  # ← 任意の開始日
    candidates: List[AllocationCandidate],
    crop_profile: CropProfile,
    weather_data: List[WeatherData]
) -> Optional[AllocationCandidate]:
    
    # 1. 高速パス: 候補プールから検索
    existing = find_candidate_for_movement(
        target_field, crop, start_date, candidates
    )
    if existing:
        return existing  # ✅ 候補プールにあった
    
    # 2. 低速パス: 動的GDD計算（スライディングウィンドウ）
    result = calculate_completion_date(
        crop_profile, start_date, weather_data
    )
    if result is None:
        return None  # ❌ 完了できない
    
    # 3. 新規候補を生成
    return AllocationCandidate(
        field=target_field,
        crop=crop,
        start_date=start_date,
        completion_date=result.completion_date,
        growth_days=result.growth_days,
        accumulated_gdd=result.accumulated_gdd,
        area_used=area_used
    )
```

---

## 5. パフォーマンス比較

### 候補生成（事前処理）

| 方式 | 計算量 | 実行時間（例） |
|------|--------|---------------|
| **スライディングウィンドウ** | O(M) | 0.1秒/作物 |
| Naive（全開始日を独立計算） | O(N × M) | 20秒/作物 |

- M = 天気データ日数（365日）
- N = 開始日候補数（200日）

### 近傍操作（最適化中）

| 操作 | 高速パス | 低速パス |
|------|----------|----------|
| **候補プール検索** | O(n) | - |
| **動的GDD計算** | - | O(m) |
| **典型値** | <1ms | <10ms |

- n = 候補プール数（720個）
- m = 天気データ日数（365日）

### ALNS 200イテレーションでの影響

```
Before（候補プールのみ）:
  候補プール検索: 200回 × 1ms = 0.2秒
  合計: 0.2秒

After（動的GDD計算あり）:
  候補プール検索: 160回 × 1ms = 0.16秒（80%ヒット）
  動的GDD計算: 40回 × 10ms = 0.4秒（20%ミス）
  合計: 0.56秒

追加コスト: +0.36秒（許容範囲）
```

---

## 6. まとめ

### 関係性

```
┌────────────────────────────────────────────────────────┐
│ スライディングウィンドウアルゴリズム                   │
│   - 役割: あらゆる開始日の終了日を効率計算             │
│   - 計算量: O(M) ← 圧倒的に高速                        │
│   - 実行タイミング: 候補生成時（Phase 1）             │
└───────────────────┬────────────────────────────────────┘
                    │ 出力
                    ▼
┌────────────────────────────────────────────────────────┐
│ 候補プール                                             │
│   - 性質: 固定リスト                                   │
│   - サイズ: Fields × Crops × Periods × Areas          │
│   - 制約: top_period_candidates に制限                │
└───────────────────┬────────────────────────────────────┘
                    │ 利用
                    ▼
┌────────────────────────────────────────────────────────┐
│ 最適化（Greedy / DP / ALNS）                           │
│   - 問題: 候補プールにない組み合わせは試せない         │
│   - 解決策: 動的GDD計算（スライディングウィンドウ再実行）│
└────────────────────────────────────────────────────────┘
```

### キーポイント

1. **スライディングウィンドウ** = 候補生成アルゴリズム（事前処理）
2. **候補プール** = スライディングウィンドウの出力（固定リスト）
3. **制約** = 候補プールの上位N個に限定される
4. **解決策** = 動的にスライディングウィンドウを再実行（CropMovementService）

### 効果

| 項目 | Before | After |
|------|--------|-------|
| 探索空間 | 候補プールのみ | 候補プール + 任意の開始日 |
| 制約 | top_period_candidates=10 | 制約なし |
| ALNS品質 | 90-98% | 92-99%（予想） |
| 追加コスト | 0秒 | +0.36秒（200イテレーション） |

---

**バージョン**: 1.0  
**作成日**: 2025-01-20  
**ステータス**: 説明資料

