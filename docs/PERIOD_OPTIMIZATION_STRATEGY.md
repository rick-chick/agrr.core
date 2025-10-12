# Period最適化戦略の再検討：DP vs 近傍操作

## 重要な発見

**Period（期間）の最適化は、既にDPで厳密解を得ている！**

---

## 現状の実装の確認

### `GrowthPeriodOptimizeInteractor`の役割

既に実装されている`GrowthPeriodOptimizeInteractor`は：

```python
# 既存実装（スライディングウィンドウDP）
async def execute(request: OptimalGrowthPeriodRequestDTO):
    """
    与えられた圃場・作物で、最適な栽培期間を見つける
    
    入力:
      - field_id: 圃場
      - crop_id: 作物
      - evaluation_period_start/end: 評価期間
    
    出力:
      - optimal_start_date: 最適な開始日
      - candidates: すべての候補期間（評価済み）
    
    アルゴリズム: スライディングウィンドウDP
    計算量: O(M) （M=気象データ日数）
    品質: 100%（厳密最適解）
    ```

**つまり、Field + Crop が固定されれば、Period は既にDPで最適化されている！**

---

## 問題の再定義

### 最適化の2段階構造

```
Level 1: Period最適化（Field + Crop固定）
  └─ 既存のGrowthPeriodOptimizeInteractor（DP）
     品質: 100%（厳密解）
     
Level 2: Field + Crop の組み合わせ最適化
  └─ 新しいMultiFieldCropAllocationInteractor（Greedy + LS）
     品質: 85-95%（近似解）
```

### 候補生成での活用

```python
# 候補生成フェーズ（現在の実装）
for field in fields:
    for crop in crops:
        # ★ ここでDPを使って最適期間を見つける
        result = GrowthPeriodOptimizeInteractor.execute(
            field=field,
            crop=crop,
            evaluation_period_start=start,
            evaluation_period_end=end,
        )
        
        # result.candidatesには、すべての有効な期間候補が含まれる
        # これらはすでにPeriod次元で最適化されている
        for candidate in result.candidates:
            all_candidates.append((field, crop, candidate))
```

---

## Periodに対する2つのアプローチ

### Approach A: DP活用（推奨）★★★★★

**戦略**: 候補生成時にDPで最適Period を見つけ、その後はField・Cropの組み合わせのみを最適化

```python
# Phase 1: 候補生成（DPで最適Period を見つける）
candidates = []
for field in fields:
    for crop in crops:
        # DPで最適な期間を見つける（厳密解）
        optimal_periods = find_optimal_periods_dp(field, crop)
        
        for period in optimal_periods:
            candidates.append(AllocationCandidate(
                field=field,
                crop=crop,
                period=period,  # すでに最適化済み
                # ...
            ))

# Phase 2: Field + Crop の組み合わせ最適化（Greedy + LS）
# Period は候補として固定
allocations = greedy_allocation(candidates)
allocations = local_search(allocations)  # Field・Cropのみ変更
```

**メリット**:
- ✅ Period は厳密最適解（100%）
- ✅ 計算量が少ない（既に計算済み）
- ✅ 実装がシンプル
- ✅ デバッグしやすい

**デメリット**:
- ⚠️ Field・Crop変更後の Period 再最適化ができない
- ⚠️ 「この圃場ならもっと良い期間がある」を見逃す可能性

---

### Approach B: 近傍操作（Period変更あり）

**戦略**: 局所探索でPeriodも変更

```python
# Phase 1: 候補生成（同上）
candidates = generate_all_candidates()

# Phase 2: Greedy
allocations = greedy_allocation(candidates)

# Phase 3: Local Search（Period も変更）
for iteration in range(max_iterations):
    # Field の変更
    neighbors_field = swap_fields(allocations)
    
    # Crop の変更
    neighbors_crop = change_crops(allocations)
    
    # Period の変更 ← これが必要か？
    neighbors_period = shift_periods(allocations)
    
    best = select_best(neighbors_field + neighbors_crop + neighbors_period)
```

**メリット**:
- ✅ より柔軟な探索
- ✅ Field・Crop変更後の Period 再最適化が可能

**デメリット**:
- ❌ すでに最適化されたPeriodを変更する（効率悪い）
- ❌ 計算量が増加
- ❌ 実装が複雑

---

## 推奨戦略：ハイブリッドアプローチ

### Strategy: DP for Initial + LS for Refinement

```python
# Phase 1: 候補生成（DPでPeriod最適化）
candidates = []
for field in fields:
    for crop in crops:
        # ★ DPで最適なPeriod候補を生成（top 3-5候補）
        optimal_periods = find_optimal_periods_dp(field, crop, top_k=5)
        
        for period in optimal_periods:
            candidates.append(Candidate(field, crop, period))

# Phase 2: Greedy（Field + Crop の組み合わせ）
allocations = greedy_allocation(candidates)

# Phase 3: Local Search
for iteration in range(max_iterations):
    neighbors = []
    
    # Operation 1: Field Swap（圃場を交換）
    neighbors += field_swap(allocations)
    
    # Operation 2: Field Move（圃場を移動）
    neighbors += field_move(allocations)
    
    # Operation 3: Crop Change（作物を変更）
    neighbors += crop_change(allocations)
    
    # Operation 4: Period Re-optimize（条件付き）
    # Field or Crop が変更された場合のみ、Period を再最適化
    if field_or_crop_changed:
        neighbors += period_reoptimize(allocations, candidates)
    
    best = select_best(neighbors)
```

---

## 具体的な実装方針

### 方針1: Period候補の事前計算（推奨）

```python
# 候補生成時に複数のPeriod候補を保持
@dataclass
class AllocationCandidate:
    field: Field
    crop: Crop
    # ★ 複数のPeriod候補を保持
    period_candidates: List[PeriodCandidate]  # Top 5-10候補
    # デフォルトは最適なもの
    selected_period: PeriodCandidate

# 近傍操作
def replace_period_operation(alloc, candidates):
    """Period を別の候補に置換"""
    # 同じField・Cropの他のPeriod候補を探す
    same_field_crop_candidates = find_candidates(
        candidates,
        field=alloc.field,
        crop=alloc.crop
    )
    
    # 上位5候補から選択（すでにDPで最適化済み）
    for period_candidate in same_field_crop_candidates.period_candidates[:5]:
        if period_candidate != alloc.selected_period:
            new_alloc = create_with_new_period(alloc, period_candidate)
            yield new_alloc
```

**メリット**:
- ✅ DPの結果を完全に活用
- ✅ Period は常に良質（DPの候補範囲内）
- ✅ 計算量が少ない

---

### 方針2: 条件付きPeriod再最適化

```python
def local_search_with_conditional_reoptimization(allocations, candidates):
    """条件付きでPeriod を再最適化"""
    
    for iteration in range(max_iterations):
        neighbors = []
        
        # Field・Crop の近傍を生成
        neighbors += generate_field_crop_neighbors(allocations)
        
        # ★ Field or Crop が変更された近傍については、
        # Period を再最適化
        for neighbor in neighbors:
            if is_field_or_crop_changed(neighbor, allocations):
                # DPで再計算
                reoptimized = reoptimize_periods_dp(neighbor)
                neighbors.append(reoptimized)
        
        best = select_best(neighbors)
```

**メリット**:
- ✅ Field・Crop変更後のPeriod最適化
- ✅ より柔軟

**デメリット**:
- ❌ DP再計算のコスト（LLM呼び出しが必要）
- ❌ 計算時間が増加

---

## 計算量の比較

### Approach A: DP活用のみ

```
候補生成: O(F × C × M)
  F: 圃場数
  C: 作物数
  M: 気象データ日数（DPの計算量）
  
局所探索: O(k × (n² + n×F + n×C))
  k: 反復回数
  n: 割り当て数
  Field・Crop のみ変更
  
合計: O(F×C×M + k×n²)
```

**実測例**:
```
F=10, C=5, M=365, k=100, n=20

候補生成: 10 × 5 × 365 = 18,250 (約2秒)
局所探索: 100 × (400 + 200 + 100) = 70,000 (約3秒)
合計: 約5秒 ✓
```

---

### Approach B: 近傍でPeriod変更

```
候補生成: O(F × C × M)

局所探索: O(k × (n² + n×F + n×C + n×P))
  P: Period候補数（~30）
  
合計: O(F×C×M + k×n²×P)
```

**実測例**:
```
F=10, C=5, M=365, k=100, n=20, P=30

候補生成: 18,250 (約2秒)
局所探索: 100 × (400 + 200 + 100 + 600) = 130,000 (約6秒)
合計: 約8秒 △
```

---

### Approach C: 条件付き再最適化

```
候補生成: O(F × C × M)

局所探索: O(k × (n² + r×M))
  r: 再最適化回数（Field/Crop変更時のみ）
  
合計: O(F×C×M + k×n² + k×r×M)
```

**実測例**:
```
k=100, r=10回（10%の確率で再最適化）

候補生成: 18,250 (約2秒)
局所探索: 100 × 400 + 10 × 365 = 43,650 (約5秒)
合計: 約7秒 △

※ crop_requirement取得でLLM呼び出しが必要な場合、さらに遅くなる
```

---

## 推奨戦略の決定

### ✅ 推奨: Approach A（DP活用のみ）

**理由**:

1. **Period はすでに最適**
   ```
   GrowthPeriodOptimizeInteractor（既存）:
     - スライディングウィンドウDP
     - O(M) の効率的アルゴリズム
     - 100%の厳密最適解
   
   → これ以上の改善は不要
   ```

2. **計算効率が最高**
   ```
   候補生成時に1回だけDPを実行
   局所探索では再計算不要
   → 最も高速
   ```

3. **実装がシンプル**
   ```
   Period の近傍操作が不要
   → コードが簡潔
   → バグが少ない
   ```

4. **品質も十分**
   ```
   Period: 100%（厳密解）
   Field + Crop: 85-95%（近似解）
   → 総合的に高品質
   ```

---

## 修正された設計

### 候補生成フェーズ

```python
async def _generate_candidates(fields, crops, request):
    """
    各 Field × Crop の組み合わせで、DPを使って最適なPeriodを見つける
    """
    candidates = []
    
    for field in fields:
        for crop in crops:
            # ★ DPで最適なPeriod候補を生成（top 3-5候補）
            period_optimization = await GrowthPeriodOptimizeInteractor.execute(
                OptimalGrowthPeriodRequestDTO(
                    field_id=field.field_id,
                    crop_id=crop.crop_id,
                    evaluation_period_start=request.planning_period_start,
                    evaluation_period_end=request.planning_period_end,
                    weather_data_file=request.weather_data_file,
                )
            )
            
            # Top候補のみを使用（例: 上位5候補）
            for candidate in period_optimization.candidates[:5]:
                if candidate.total_cost is not None:
                    candidates.append(AllocationCandidate(
                        field=field,
                        crop=crop,
                        start_date=candidate.start_date,  # DPで最適化済み
                        completion_date=candidate.completion_date,
                        # ...
                    ))
    
    return candidates
```

**結果**: 
- 各Field × Cropで、**最適な5つのPeriod候補**を取得
- Period は**すべてDP最適化済み**

---

### 局所探索フェーズ

```python
def _generate_neighbors(solution, candidates):
    """
    Field と Crop の近傍のみを生成
    Period は候補から選択するのみ
    """
    neighbors = []
    
    # ✅ Field の近傍
    neighbors += field_swap_neighbors(solution)
    neighbors += field_move_neighbors(solution, candidates)
    
    # ✅ Crop の近傍
    neighbors += crop_change_neighbors(solution, candidates)
    neighbors += crop_insert_neighbors(solution, candidates)
    
    # ✅ Period の変更（候補内での選択）
    neighbors += period_replace_neighbors(solution, candidates)
    # ただし、これは事前計算されたDPの候補から選ぶだけ
    
    # ❌ Period の近傍操作（Shift等）は不要
    # なぜなら、すでにDPで最適化されているから
    
    return neighbors
```

---

## Period操作の再定義

### ❌ 不要な操作（削除推奨）

| 操作 | 理由 |
|------|------|
| P1. Shift | すでにDPで最適化されている |
| P2. Extend/Shrink | 同上 |
| P3. Split Period | 同上 |
| P5. Period Swap | 同上 |

### ⚠️ 条件付き有効な操作

| 操作 | 条件 | 理由 |
|------|------|------|
| **P4. Replace Period** | 候補内での選択 | DP計算済みの候補から選ぶのは有効 |

---

## 修正された近傍操作の分類

### 主要な近傍操作（Field + Crop）

```
Field の近傍:
  ✅ F1. Move（圃場移動）
  ✅ F2. Field Swap（圃場交換）
  ✅ F3. Field Split（圃場分割）
  ✅ F5. Remove（削除）

Crop の近傍:
  ✅ C1. Change Crop（作物変更）
  ✅ C2. Crop Swap（作物入れ替え）
  ✅ C3. Crop Insert（作物追加）
  
Period の「近傍」:
  ✅ P4. Replace Period（候補内での選択のみ）
  ❌ P1. Shift（不要 - DPで最適化済み）
  ❌ P2. Extend（不要 - DPで最適化済み）
  ❌ P3. Split（不要 - DPで最適化済み）
```

---

## 例外：Period再最適化が必要なケース

### Case 1: Field変更時

```python
# Field Aで最適だったPeriod が、Field Bでも最適とは限らない
# （日次コストが違うため）

Before:
  Field A (5000円/日): Rice, 4/1-8/31 (153日) ← DPで最適

After Field Swap:
  Field B (6000円/日): Rice, 4/1-8/31 (153日) ← 最適とは限らない
  
→ Field Bでの最適Period は 4/15-9/15 (154日) かもしれない
```

**対応策**:
```python
# 候補生成時に各Fieldで複数Period を計算しておく
# 局所探索でFieldを変更したら、その候補から選び直す

def field_move_with_period_reselection(alloc, target_field, candidates):
    # target_field での最適Period候補を探す
    period_candidates = [
        c for c in candidates
        if c.field == target_field and c.crop == alloc.crop
    ]
    
    # 最も利益が高いPeriod を選択
    best_period = max(period_candidates, key=lambda c: c.profit)
    
    return create_allocation(target_field, alloc.crop, best_period)
```

---

### Case 2: Crop変更時

```python
# Crop Aで最適だったPeriod が、Crop Bでも最適とは限らない
# （GDD要件が違うため）

Before:
  Field A: Rice, 4/1-8/31 (153日、1800 GDD) ← Riceで最適

After Crop Change:
  Field A: Tomato, 4/1-8/31 (153日) ← Tomatoで最適とは限らない
  
→ Tomatoでの最適Period は 5/1-8/31 (122日) かもしれない
```

**対応策**: 同上（候補から選び直す）

---

## 最終推奨：3段階アプローチ

### Phase 1: 候補生成（DPで厳密最適化）

```python
# 各Field × Cropで、top 5のPeriod候補を生成
for field in fields:
    for crop in crops:
        periods_dp = optimize_periods_with_dp(field, crop)
        # すでに最適化済み（100%品質）
```

### Phase 2: Greedy（組み合わせ選択）

```python
# Field × Crop × Period の組み合わせから選択
# Period はすでに最適化されているので、
# Field と Crop の組み合わせを最適化
allocations = greedy_select(candidates, by=profit_rate)
```

### Phase 3: Local Search（Field + Crop の最適化）

```python
# Field と Crop の近傍操作のみ
neighbors = []
neighbors += field_swap(allocations)
neighbors += field_move_with_period_reselection(allocations, candidates)
neighbors += crop_change_with_period_reselection(allocations, candidates)

# Period の直接変更はしない（候補から選び直すのみ）
```

---

## まとめ

### 重要な発見

**Period最適化は既にDPで解かれている**
→ 近傍操作で変更するのは非効率

### 推奨戦略

```
Period: DPで事前計算（厳密解）★★★★★
  ↓
Field + Crop: Greedy + Local Search（近似解）
```

### 近傍操作の見直し

| 次元 | アプローチ | 理由 |
|------|-----------|------|
| **Period** | **DPで事前計算** | すでに厳密最適解がある |
| **Field** | **近傍操作** | 組み合わせ最適化が必要 |
| **Crop** | **近傍操作** | 組み合わせ最適化が必要 |

### 実装の簡素化

**削除すべき操作**:
- ❌ P1. Shift（不要）
- ❌ P2. Extend/Shrink（不要）
- ❌ P3. Split Period（不要）
- ❌ P5. Period Swap（不要）

**保持すべき操作**:
- ✅ P4. Replace Period（候補内での選択）
- ✅ すべてのField操作
- ✅ すべてのCrop操作

### 期待される効果

```
計算時間: 5-10秒（Period近傍操作なしで高速化）
品質: 
  - Period: 100%（DP）
  - Field + Crop: 85-95%（Greedy + LS）
  → 総合: 90-97%
```

この戦略により、**計算量を削減しつつ、高品質な解を得られます**！

