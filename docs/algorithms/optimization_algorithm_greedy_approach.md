# 貪欲法による複数圃場・複数作物の割り当てアルゴリズム

## アルゴリズムの概要

実装の第一段階として、**貪欲法（Greedy Algorithm）** + **局所探索（Local Search）** による最適化を提案します。

### 利点
- 実装がシンプル
- 計算時間が予測可能（多項式時間）
- 実用的に良好な解が得られる
- 段階的に改善可能

### 欠点
- 最適解の保証なし（近似解）
- 局所最適に陥る可能性

## アルゴリズムの全体像

```
1. 候補生成フェーズ
   ↓
2. 初期解生成フェーズ（貪欲法）
   ↓
3. 解の改善フェーズ（局所探索）
   ↓
4. 結果の出力
```

## フェーズ1: 候補生成

### 目的
各作物について、各圃場で栽培可能なスケジュール候補を列挙

### 手順

```python
def generate_candidates(
    fields: List[Field],
    crops: List[Crop],
    planning_period_start: datetime,
    planning_period_end: datetime,
    weather_data: List[WeatherData]
) -> List[AllocationCandidate]:
    """
    候補生成
    
    Returns:
        List of AllocationCandidate = [
            (field, crop, start_date, completion_date, cost, revenue, profit)
        ]
    """
    candidates = []
    
    for field in fields:
        for crop in crops:
            # 既存のGrowthPeriodOptimizeInteractorを利用
            optimization_result = optimize_growth_period(
                crop=crop,
                field=field,
                evaluation_period_start=planning_period_start,
                evaluation_period_end=planning_period_end,
                weather_data=weather_data
            )
            
            # 各候補日程について
            for candidate in optimization_result.candidates:
                if candidate.is_feasible:
                    # 数量を計算（圃場面積 ÷ 作物の単位面積）
                    max_quantity = field.area / crop.area_per_unit
                    
                    # 候補として登録
                    candidates.append(AllocationCandidate(
                        field=field,
                        crop=crop,
                        start_date=candidate.start_date,
                        completion_date=candidate.completion_date,
                        quantity=max_quantity,
                        cost=candidate.total_cost,
                        revenue=max_quantity * crop.revenue_per_area * crop.area_per_unit,
                        profit=revenue - cost,
                        profit_rate=profit / cost if cost > 0 else 0
                    ))
    
    return candidates
```

### 出力例

```
Candidate 1: Field_001 × Rice (4/1-8/31), Qty=2000, Cost=600k, Revenue=1000k, Profit=400k, Rate=67%
Candidate 2: Field_001 × Tomato (4/1-7/31), Qty=1500, Cost=450k, Revenue=900k, Profit=450k, Rate=100%
Candidate 3: Field_001 × Rice (4/15-9/15), Qty=2000, Cost=620k, Revenue=1000k, Profit=380k, Rate=61%
...
Candidate N: Field_010 × Lettuce (11/1-12/31), Qty=500, Cost=100k, Revenue=150k, Profit=50k, Rate=50%
```

## フェーズ2: 初期解生成（貪欲法）

### 戦略A: 利益率優先（推奨）

```python
def greedy_profit_rate(
    candidates: List[AllocationCandidate],
    crop_targets: Dict[str, float]  # {crop_id: target_quantity}
) -> List[Allocation]:
    """
    利益率が高い順に割り当て
    """
    # 利益率でソート（降順）
    sorted_candidates = sorted(candidates, key=lambda c: c.profit_rate, reverse=True)
    
    allocations = []
    field_schedules = {field.field_id: [] for field in fields}  # 圃場ごとの占有スケジュール
    crop_quantities = {crop_id: 0.0 for crop_id in crop_targets.keys()}  # 作物ごとの達成量
    
    for candidate in sorted_candidates:
        # 制約チェック1: 時間的な重複がないか
        if has_time_overlap(field_schedules[candidate.field.field_id], candidate):
            continue
        
        # 制約チェック2: 作物の目標達成済みか
        if crop_quantities[candidate.crop.crop_id] >= crop_targets[candidate.crop.crop_id]:
            continue
        
        # 制約チェック3: 圃場の面積制約
        if not fits_in_field(candidate):
            continue
        
        # 割り当て実行
        allocations.append(candidate)
        field_schedules[candidate.field.field_id].append(candidate)
        crop_quantities[candidate.crop.crop_id] += candidate.quantity
    
    return allocations
```

### 戦略B: 総利益優先

```python
def greedy_total_profit(
    candidates: List[AllocationCandidate],
    crop_targets: Dict[str, float]
) -> List[Allocation]:
    """
    総利益が高い順に割り当て
    """
    sorted_candidates = sorted(candidates, key=lambda c: c.profit, reverse=True)
    
    # （以下、戦略Aと同様）
```

### 戦略C: 制約充足優先

```python
def greedy_constraint_first(
    candidates: List[AllocationCandidate],
    crop_targets: Dict[str, float]
) -> List[Allocation]:
    """
    まず制約（目標生産量）を満たし、その後利益最大化
    """
    allocations = []
    crop_quantities = {crop_id: 0.0 for crop_id in crop_targets.keys()}
    
    # Phase 1: 制約を満たす
    for crop_id, target in crop_targets.items():
        crop_candidates = [c for c in candidates if c.crop.crop_id == crop_id]
        crop_candidates.sort(key=lambda c: c.profit_rate, reverse=True)
        
        for candidate in crop_candidates:
            if crop_quantities[crop_id] >= target:
                break
            
            if can_allocate(candidate, allocations):
                allocations.append(candidate)
                crop_quantities[crop_id] += candidate.quantity
    
    # Phase 2: 余剰で利益最大化
    remaining_candidates = [c for c in candidates if c not in allocations]
    remaining_candidates.sort(key=lambda c: c.profit, reverse=True)
    
    for candidate in remaining_candidates:
        if can_allocate(candidate, allocations):
            allocations.append(candidate)
    
    return allocations
```

## フェーズ3: 解の改善（局所探索）

### 近傍操作の定義

#### 操作1: Swap（入れ替え）

```python
def swap_operation(allocations: List[Allocation], i: int, j: int) -> List[Allocation]:
    """
    2つの割り当てを入れ替える
    
    Before:
      Field_A: [Allocation_i]
      Field_B: [Allocation_j]
    
    After:
      Field_A: [Allocation_j]
      Field_B: [Allocation_i]
    """
    if can_swap(allocations[i], allocations[j]):
        new_allocations = allocations.copy()
        new_allocations[i], new_allocations[j] = new_allocations[j], new_allocations[i]
        return new_allocations
    return None
```

#### 操作2: Shift（時期変更）

```python
def shift_operation(allocation: Allocation, days: int) -> Allocation:
    """
    栽培開始日を前後にシフト
    
    Before: 4/1-8/31
    After:  4/15-9/15 (14日後にシフト)
    """
    new_start = allocation.start_date + timedelta(days=days)
    # 新しい完了日を再計算（GDD計算）
    new_completion = calculate_completion_date(
        crop=allocation.crop,
        start_date=new_start,
        weather_data=weather_data
    )
    
    return Allocation(
        field=allocation.field,
        crop=allocation.crop,
        start_date=new_start,
        completion_date=new_completion,
        # ... (コストと収益を再計算)
    )
```

#### 操作3: Replace（作物変更）

```python
def replace_operation(allocation: Allocation, new_crop: Crop) -> Allocation:
    """
    同じ圃場・同じ時期で作物を変更
    """
    return Allocation(
        field=allocation.field,
        crop=new_crop,
        start_date=allocation.start_date,
        # ... (新作物での最適化を実行)
    )
```

#### 操作4: Split（分割）

```python
def split_operation(allocation: Allocation, ratio: float) -> Tuple[Allocation, Allocation]:
    """
    1つの割り当てを2つに分割（数量を分ける）
    
    Before: Field_A (1000m²) × Rice 2000株
    After:  
      Field_A (500m²) × Rice 1000株
      Field_A (500m²) × Tomato 1000株 (別の期間)
    """
    quantity1 = allocation.quantity * ratio
    quantity2 = allocation.quantity * (1 - ratio)
    
    # 時間的に分割（前半と後半）
    alloc1 = Allocation(
        field=allocation.field,
        crop=allocation.crop,
        start_date=allocation.start_date,
        completion_date=allocation.completion_date,
        quantity=quantity1,
        # ...
    )
    
    alloc2 = Allocation(
        field=allocation.field,
        crop=allocation.crop,  # または別の作物
        start_date=allocation.completion_date + timedelta(days=1),
        # ...
        quantity=quantity2
    )
    
    return (alloc1, alloc2)
```

### 局所探索アルゴリズム（Hill Climbing）

```python
def local_search(
    initial_solution: List[Allocation],
    max_iterations: int = 1000,
    no_improvement_limit: int = 100
) -> List[Allocation]:
    """
    山登り法による局所探索
    """
    current_solution = initial_solution
    current_profit = calculate_total_profit(current_solution)
    
    no_improvement_count = 0
    
    for iteration in range(max_iterations):
        # 近傍解を生成
        neighbors = generate_neighbors(current_solution)
        
        # 最良の近傍解を選択
        best_neighbor = None
        best_profit = current_profit
        
        for neighbor in neighbors:
            if is_feasible(neighbor):
                neighbor_profit = calculate_total_profit(neighbor)
                if neighbor_profit > best_profit:
                    best_neighbor = neighbor
                    best_profit = neighbor_profit
        
        # 改善があれば更新
        if best_neighbor is not None:
            current_solution = best_neighbor
            current_profit = best_profit
            no_improvement_count = 0
        else:
            no_improvement_count += 1
        
        # 改善が見つからなくなったら終了
        if no_improvement_count >= no_improvement_limit:
            break
    
    return current_solution


def generate_neighbors(solution: List[Allocation]) -> List[List[Allocation]]:
    """
    近傍解の生成
    """
    neighbors = []
    
    # Swap操作: すべてのペアを試す
    for i in range(len(solution)):
        for j in range(i + 1, len(solution)):
            neighbor = swap_operation(solution, i, j)
            if neighbor:
                neighbors.append(neighbor)
    
    # Shift操作: 各割り当てを前後にシフト
    for i, alloc in enumerate(solution):
        for shift_days in [-14, -7, 7, 14]:  # 1週間、2週間単位でシフト
            neighbor = solution.copy()
            neighbor[i] = shift_operation(alloc, shift_days)
            if is_feasible(neighbor):
                neighbors.append(neighbor)
    
    # Replace操作: 別の作物に変更
    for i, alloc in enumerate(solution):
        for crop in all_crops:
            if crop != alloc.crop:
                neighbor = solution.copy()
                neighbor[i] = replace_operation(alloc, crop)
                if is_feasible(neighbor):
                    neighbors.append(neighbor)
    
    return neighbors
```

### 局所探索の拡張: Simulated Annealing

```python
def simulated_annealing(
    initial_solution: List[Allocation],
    initial_temp: float = 1000.0,
    cooling_rate: float = 0.95,
    min_temp: float = 1.0
) -> List[Allocation]:
    """
    焼きなまし法（局所最適を脱出）
    """
    current_solution = initial_solution
    current_profit = calculate_total_profit(current_solution)
    best_solution = current_solution
    best_profit = current_profit
    
    temp = initial_temp
    
    while temp > min_temp:
        # ランダムに近傍解を選択
        neighbor = random.choice(generate_neighbors(current_solution))
        neighbor_profit = calculate_total_profit(neighbor)
        
        # 改善なら必ず採用、悪化でも確率的に採用
        delta = neighbor_profit - current_profit
        if delta > 0 or random.random() < math.exp(delta / temp):
            current_solution = neighbor
            current_profit = neighbor_profit
            
            # 最良解の更新
            if current_profit > best_profit:
                best_solution = current_solution
                best_profit = current_profit
        
        # 温度を下げる
        temp *= cooling_rate
    
    return best_solution
```

## フェーズ4: 数量最適化

### 離散的な数量調整

```python
def optimize_quantities(
    allocations: List[Allocation],
    fields: List[Field]
) -> List[Allocation]:
    """
    各割り当ての数量を最適化
    """
    optimized = []
    
    for allocation in allocations:
        field = allocation.field
        
        # 圃場の利用可能面積を計算
        used_area = sum(
            a.quantity * a.crop.area_per_unit 
            for a in optimized 
            if a.field.field_id == field.field_id
        )
        available_area = field.area - used_area
        
        # 最大数量を計算
        max_quantity = available_area / allocation.crop.area_per_unit
        
        # 利益を最大化する数量を選択
        best_quantity = allocation.quantity
        best_profit = allocation.profit
        
        # 10%, 20%, ..., 100% の数量を試す
        for ratio in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
            test_quantity = min(max_quantity, allocation.quantity * ratio)
            test_profit = calculate_profit(allocation, test_quantity)
            
            if test_profit > best_profit:
                best_quantity = test_quantity
                best_profit = test_profit
        
        optimized.append(Allocation(
            field=allocation.field,
            crop=allocation.crop,
            start_date=allocation.start_date,
            completion_date=allocation.completion_date,
            quantity=best_quantity,
            # ... (コスト・収益を再計算)
        ))
    
    return optimized
```

## 実装のポイント

### 1. 制約チェックの効率化

```python
class AllocationManager:
    """割り当て管理クラス（効率的な制約チェック）"""
    
    def __init__(self, fields: List[Field]):
        # 圃場ごとのインターバルツリー（時間的重複の高速チェック）
        self.field_intervals = {
            field.field_id: IntervalTree() 
            for field in fields
        }
        
        # 圃場ごとの使用面積
        self.field_area_used = {
            field.field_id: 0.0 
            for field in fields
        }
    
    def can_add(self, allocation: Allocation) -> bool:
        """割り当て可能かチェック（O(log n)）"""
        # 時間的重複チェック
        overlaps = self.field_intervals[allocation.field.field_id].overlap(
            allocation.start_date, allocation.completion_date
        )
        if overlaps:
            return False
        
        # 面積制約チェック
        new_area = self.field_area_used[allocation.field.field_id] + \
                   allocation.quantity * allocation.crop.area_per_unit
        if new_area > allocation.field.area:
            return False
        
        return True
    
    def add(self, allocation: Allocation):
        """割り当てを追加"""
        self.field_intervals[allocation.field.field_id].add(
            allocation.start_date, allocation.completion_date, allocation
        )
        self.field_area_used[allocation.field.field_id] += \
            allocation.quantity * allocation.crop.area_per_unit
```

### 2. 評価関数の設計

```python
def evaluate_solution(allocations: List[Allocation]) -> Dict[str, float]:
    """
    解の総合評価
    
    Returns:
        {
            'total_profit': 総利益,
            'total_revenue': 総収益,
            'total_cost': 総コスト,
            'field_utilization': 圃場利用率（平均）,
            'crop_diversity': 作物多様性（種類数）,
            'risk_score': リスクスコア（低いほど良い）
        }
    """
    total_profit = sum(a.profit for a in allocations)
    total_revenue = sum(a.revenue for a in allocations)
    total_cost = sum(a.cost for a in allocations)
    
    # 圃場利用率
    field_utilizations = []
    for field in fields:
        used_area = sum(
            a.quantity * a.crop.area_per_unit 
            for a in allocations 
            if a.field.field_id == field.field_id
        )
        field_utilizations.append(used_area / field.area)
    avg_utilization = sum(field_utilizations) / len(field_utilizations)
    
    # 作物多様性
    crop_types = len(set(a.crop.crop_id for a in allocations))
    
    # リスクスコア（単一作物への依存度）
    crop_revenues = {}
    for allocation in allocations:
        crop_revenues[allocation.crop.crop_id] = \
            crop_revenues.get(allocation.crop.crop_id, 0) + allocation.revenue
    max_crop_ratio = max(crop_revenues.values()) / total_revenue if total_revenue > 0 else 0
    risk_score = max_crop_ratio  # 0-1の範囲、1に近いほど高リスク
    
    return {
        'total_profit': total_profit,
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'field_utilization': avg_utilization,
        'crop_diversity': crop_types,
        'risk_score': risk_score
    }
```

## 計算量の分析

- **候補生成**: O(F × C × S) 
  - F: 圃場数、C: 作物種類、S: スケジュール候補数
- **貪欲法**: O(N log N) 
  - N: 候補数 = F × C × S
- **局所探索**: O(iterations × N²)
  - iterations: 反復回数（通常100-1000）
- **全体**: O(F × C × S + iterations × (F × C × S)²)

### 実用的な見積もり

- 圃場10個、作物5種類、各30候補 → N = 1,500
- 貪欲法: 約0.1秒
- 局所探索（100回）: 約10秒
- **合計: 約10秒**

## まとめ

この貪欲法ベースのアプローチは：
- ✅ 実装が簡単
- ✅ 計算時間が予測可能
- ✅ 実用的に十分な品質の解
- ✅ 段階的な改善が可能

次のステップで、より高度なアルゴリズム（DP、MILP）への拡張も可能です。

