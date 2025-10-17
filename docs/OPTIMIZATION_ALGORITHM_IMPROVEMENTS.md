# 最適化アルゴリズム改善提案

## 現状分析

### 現在のアルゴリズム（Greedy + Local Search）

```python
# Phase 1: 候補生成
candidates = DP_weighted_interval_scheduling(fields, crops)  # O(n log n)

# Phase 2: Greedy Allocation
allocations = greedy_by_profit_rate(candidates)  # O(n log n)

# Phase 3: Local Search (Hill Climbing)
allocations = local_search(allocations, max_iterations=100)  # O(k·n²)
```

**特徴**:
- ✅ 計算時間: 10-30秒（実用的）
- ✅ 解の品質: 85-95%（良好）
- ✅ 実装済み・安定動作
- ⚠️ 局所最適に陥る可能性
- ⚠️ 貪欲フェーズで最初の選択を誤ると回復困難

---

## 改善アルゴリズムの提案

### 🥇 推奨1: Adaptive Large Neighborhood Search (ALNS)

**概要**: 局所探索を大幅に強化し、動的に探索戦略を切り替える

#### アルゴリズム

```python
def alns_optimization(initial_solution, candidates, fields, crops, config):
    """ALNS: 適応的大規模近傍探索
    
    特徴:
    - 複数の破壊・修復オペレータ
    - 動的な重み調整（成功率に基づく）
    - Simulated Annealing的な受理基準
    """
    current = initial_solution
    best = current
    
    # オペレータの種類と初期重み
    destroy_ops = {
        'random_removal': 1.0,           # ランダムに削除
        'worst_removal': 1.0,            # 低利益率を削除
        'related_removal': 1.0,          # 関連する割当を削除
        'field_removal': 1.0,            # 圃場単位で削除
        'crop_removal': 1.0,             # 作物単位で削除
        'time_slice_removal': 1.0,       # 時期単位で削除
    }
    
    repair_ops = {
        'greedy_insert': 1.0,            # 貪欲に挿入
        'regret_insert': 1.0,            # Regret基準で挿入
        'dp_insert': 1.0,                # DP最適化して挿入
        'random_insert': 0.5,            # ランダムに挿入
    }
    
    # Simulated Annealing パラメータ
    temp = 10000.0
    cooling_rate = 0.99
    
    for iteration in range(config.max_iterations):
        # 1. 破壊オペレータを選択（重みに基づいてルーレット選択）
        destroy_op = weighted_random_choice(destroy_ops)
        
        # 2. 修復オペレータを選択
        repair_op = weighted_random_choice(repair_ops)
        
        # 3. 破壊: 解の一部を削除
        partial_solution, removed = destroy_op(current)
        
        # 4. 修復: 削除された部分を再挿入
        new_solution = repair_op(partial_solution, removed, candidates)
        
        # 5. 受理判定（Simulated Annealing）
        delta = profit(new_solution) - profit(current)
        if delta > 0 or random() < exp(delta / temp):
            current = new_solution
            
            # 最良解の更新
            if profit(current) > profit(best):
                best = current
                
            # 重みの更新（成功報酬）
            update_weight(destroy_op, reward=10)
            update_weight(repair_op, reward=10)
        else:
            # 重みの更新（小さな報酬）
            update_weight(destroy_op, reward=1)
            update_weight(repair_op, reward=1)
        
        # 温度の低下
        temp *= cooling_rate
    
    return best
```

#### 破壊オペレータの例

```python
def random_removal(solution, removal_rate=0.3):
    """ランダムに30%の割当を削除"""
    n_remove = int(len(solution) * removal_rate)
    removed = random.sample(solution, n_remove)
    remaining = [a for a in solution if a not in removed]
    return remaining, removed

def worst_removal(solution, removal_rate=0.3):
    """利益率の低い30%を削除"""
    n_remove = int(len(solution) * removal_rate)
    sorted_by_profit_rate = sorted(solution, key=lambda a: a.profit_rate)
    removed = sorted_by_profit_rate[:n_remove]
    remaining = sorted_by_profit_rate[n_remove:]
    return remaining, removed

def related_removal(solution, removal_rate=0.3):
    """時間的・空間的に関連する割当をまとめて削除"""
    # ランダムに1つ選択
    seed = random.choice(solution)
    
    # 関連度を計算（同じ圃場、近い時期、同じ作物）
    related = []
    for alloc in solution:
        relatedness = calculate_relatedness(seed, alloc)
        related.append((alloc, relatedness))
    
    # 関連度の高い順に削除
    related.sort(key=lambda x: x[1], reverse=True)
    n_remove = int(len(solution) * removal_rate)
    removed = [a for a, _ in related[:n_remove]]
    remaining = [a for a, _ in related[n_remove:]]
    return remaining, removed

def field_removal(solution):
    """ランダムに1圃場の割当を全削除"""
    fields_in_solution = list(set(a.field.field_id for a in solution))
    target_field = random.choice(fields_in_solution)
    
    removed = [a for a in solution if a.field.field_id == target_field]
    remaining = [a for a in solution if a.field.field_id != target_field]
    return remaining, removed

def time_slice_removal(solution):
    """特定の時期の割当を全削除"""
    # 時期を分割（例: 3ヶ月単位）
    all_dates = [a.start_date for a in solution]
    median_date = sorted(all_dates)[len(all_dates) // 2]
    
    # 中央付近の割当を削除
    removed = [a for a in solution if abs((a.start_date - median_date).days) < 90]
    remaining = [a for a in solution if a not in removed]
    return remaining, removed
```

#### 修復オペレータの例

```python
def greedy_insert(partial_solution, removed, candidates):
    """貪欲に再挿入"""
    current = partial_solution.copy()
    
    # 削除された候補を利益率順にソート
    sorted_removed = sorted(removed, key=lambda a: a.profit_rate, reverse=True)
    
    for alloc in sorted_removed:
        if is_feasible(current + [alloc]):
            current.append(alloc)
    
    return current

def regret_insert(partial_solution, removed, candidates):
    """Regret基準で再挿入
    
    Regret: その割当を今入れなかった場合の後悔の大きさ
    = 1位の利益 - 2位の利益
    """
    current = partial_solution.copy()
    
    while removed:
        # 各候補のRegretを計算
        regrets = []
        for alloc in removed:
            if is_feasible(current + [alloc]):
                # この割当を入れた場合の利益
                profit_with = total_profit(current + [alloc])
                
                # 次善の選択肢を入れた場合の利益
                alternatives = [a for a in removed if a != alloc and is_feasible(current + [a])]
                if alternatives:
                    best_alt = max(alternatives, key=lambda a: a.profit)
                    profit_with_alt = total_profit(current + [best_alt])
                else:
                    profit_with_alt = total_profit(current)
                
                # Regret = 機会損失
                regret = profit_with - profit_with_alt
                regrets.append((alloc, regret))
        
        if not regrets:
            break
        
        # 最大Regretを持つ割当を優先挿入
        best_alloc, _ = max(regrets, key=lambda x: x[1])
        current.append(best_alloc)
        removed.remove(best_alloc)
    
    return current

def dp_insert(partial_solution, removed, candidates):
    """DPで各圃場を最適化しながら再挿入"""
    current = partial_solution.copy()
    
    # 圃場ごとにグループ化
    removed_by_field = {}
    for alloc in removed:
        field_id = alloc.field.field_id
        if field_id not in removed_by_field:
            removed_by_field[field_id] = []
        removed_by_field[field_id].append(alloc)
    
    # 各圃場でWeighted Interval Schedulingを解く
    for field_id, field_removed in removed_by_field.items():
        # 既存の割当
        existing = [a for a in current if a.field.field_id == field_id]
        
        # DPで最適化
        all_candidates = existing + field_removed
        optimal = weighted_interval_scheduling_dp(all_candidates)
        
        # 更新
        current = [a for a in current if a.field.field_id != field_id]
        current.extend(optimal)
    
    return current
```

#### 重みの動的調整

```python
class AdaptiveWeights:
    """オペレータの重みを動的に調整"""
    
    def __init__(self, operators):
        self.weights = {op: 1.0 for op in operators}
        self.success_counts = {op: 0 for op in operators}
        self.usage_counts = {op: 0 for op in operators}
        self.decay_rate = 0.99
    
    def select_operator(self):
        """重みに基づいてオペレータを選択（ルーレット選択）"""
        total = sum(self.weights.values())
        probabilities = {op: w / total for op, w in self.weights.items()}
        return weighted_random_choice(probabilities)
    
    def update(self, operator, reward):
        """成功報酬に基づいて重みを更新"""
        self.usage_counts[operator] += 1
        
        if reward > 5:  # 良い改善があった
            self.success_counts[operator] += 1
        
        # 重みの更新（成功率と最近の報酬を考慮）
        success_rate = self.success_counts[operator] / max(self.usage_counts[operator], 1)
        self.weights[operator] = 0.5 * self.weights[operator] * self.decay_rate + 0.5 * (success_rate + reward / 10)
    
    def reset_periodically(self, iteration):
        """定期的に重みをリセット（探索の多様性を保つ）"""
        if iteration % 100 == 0:
            for op in self.weights:
                self.weights[op] = max(0.1, self.weights[op] * 0.5 + 0.5)
```

#### 計算量

- **時間複雑度**: O(iterations × (destroy + repair))
  - 破壊: O(n)
  - 修復: O(removed × n)（greedy）、O(removed² × n)（regret）、O(removed × log removed)（DP）
  - 全体: O(iterations × n²)（現在のLocal Searchと同等）

- **期待品質**: 90-98%（現在の85-95%から改善）

#### メリット

- ✅ **大規模な近傍を探索**: 30%を一気に削除・再構築
- ✅ **動的な戦略選択**: 効果的なオペレータを自動学習
- ✅ **局所最適からの脱出**: Simulated Annealing的な受理基準
- ✅ **実装の段階的拡張**: 現在のコードに追加可能

#### デメリット

- ⚠️ **実装コスト**: 中程度（5-7日）
- ⚠️ **パラメータチューニング**: 温度、冷却率、報酬設定が必要

---

### 🥈 推奨2: Mixed Integer Linear Programming (MILP)

**概要**: 最適解を数学的に保証

#### 定式化

```python
from pulp import *

def milp_optimization(fields, crops, candidates, planning_period):
    """MILPによる厳密最適化
    
    特徴:
    - 最適解を保証
    - 複雑な制約を表現可能
    """
    
    # 問題定義
    prob = LpProblem("CropAllocation", LpMaximize)
    
    # 決定変数: x[i] ∈ {0, 1}（候補iを選ぶか）
    x = {}
    for i, candidate in enumerate(candidates):
        x[i] = LpVariable(f"x_{i}", cat='Binary')
    
    # 目的関数: 総利益の最大化
    prob += lpSum([
        x[i] * candidates[i].profit 
        for i in range(len(candidates))
    ])
    
    # 制約1: 時間的重複の禁止（各圃場で）
    for field in fields:
        field_candidates = [
            (i, c) for i, c in enumerate(candidates) 
            if c.field.field_id == field.field_id
        ]
        
        # 重複する候補ペアを列挙
        for i, c1 in field_candidates:
            for j, c2 in field_candidates:
                if i < j and time_overlaps(c1, c2):
                    # 両方選べない
                    prob += x[i] + x[j] <= 1
    
    # 制約2: max_revenue制約（作物ごと）
    crop_revenue_limits = {
        crop.crop_id: crop.max_revenue 
        for crop in crops 
        if crop.max_revenue is not None
    }
    
    for crop_id, max_revenue in crop_revenue_limits.items():
        crop_candidates = [
            (i, c) for i, c in enumerate(candidates)
            if c.crop.crop_id == crop_id
        ]
        
        # 総収益が上限を超えない
        prob += lpSum([
            x[i] * c.revenue 
            for i, c in crop_candidates
        ]) <= max_revenue
    
    # 制約3: 連続栽培ペナルティ（オプション）
    # （線形化が必要 - 複雑なため省略）
    
    # 求解
    prob.solve(PULP_CBC_CMD(timeLimit=300))  # 5分制限
    
    # 解の抽出
    solution = [
        candidates[i] 
        for i in range(len(candidates)) 
        if x[i].varValue == 1
    ]
    
    return solution
```

#### 計算量

- **時間複雂度**: 最悪 O(2^n)（指数時間）
  - ただし、実用的には数分で解ける（Branch and Bound）
  - CBC, Gurobi, CPLEXなどのソルバーが高速

- **期待品質**: 100%（最適解を保証）

#### メリット

- ✅ **最適解を保証**: 数学的に証明された最良解
- ✅ **複雑な制約に対応**: 線形制約なら何でも追加可能
- ✅ **商用ソルバーで高速**: Gurobi、CPLEXは非常に高速

#### デメリット

- ⚠️ **非線形制約は扱えない**: 連続栽培ペナルティの線形化が必要
- ⚠️ **大規模問題で遅い**: 候補数1000以上で計算時間増大
- ⚠️ **外部ライブラリ必要**: PuLP（無料）またはGurobi（有料）

---

### 🥉 推奨3: Hybrid: Greedy + ALNS + MILP

**概要**: 複数のアルゴリズムを段階的に適用

#### アルゴリズム

```python
def hybrid_optimization(fields, crops, candidates, config):
    """ハイブリッド最適化
    
    Phase 1: Greedy（高速な初期解）
    Phase 2: ALNS（品質改善）
    Phase 3: MILP（小規模な部分問題を厳密最適化）
    """
    
    # Phase 1: Greedy（現在の実装）
    initial_solution = greedy_allocation(candidates)
    print(f"Greedy: Profit = {total_profit(initial_solution)}")
    
    # Phase 2: ALNS（大規模近傍探索）
    alns_solution = alns_optimization(
        initial_solution, 
        candidates, 
        fields, 
        crops, 
        iterations=200
    )
    print(f"ALNS: Profit = {total_profit(alns_solution)}")
    
    # Phase 3: MILP Refinement（部分問題を厳密最適化）
    # 各圃場を個別にMILPで最適化
    final_solution = []
    for field in fields:
        # この圃場の候補のみ抽出
        field_candidates = [
            c for c in candidates 
            if c.field.field_id == field.field_id
        ]
        
        # MILPで厳密最適化（小規模なので高速）
        optimal_for_field = milp_optimization_single_field(
            field, 
            field_candidates,
            time_limit=30
        )
        
        final_solution.extend(optimal_for_field)
    
    # 圃場間の調整（max_revenue制約）
    final_solution = enforce_global_constraints(final_solution, crops)
    
    print(f"Hybrid: Profit = {total_profit(final_solution)}")
    return final_solution
```

#### 計算量

- **Phase 1**: O(n log n) - 数秒
- **Phase 2**: O(iterations × n²) - 数十秒
- **Phase 3**: O(F × 2^(n/F)) - 数秒（圃場ごとに小規模）

**全体**: 1-2分（実用的）

#### メリット

- ✅ **最高品質**: 95-100%
- ✅ **実用的な計算時間**: 1-2分
- ✅ **段階的な実装**: Phase 1→2→3の順に追加可能

---

## その他の候補アルゴリズム

### 4. Genetic Algorithm (GA)

```python
def genetic_algorithm(candidates, fields, crops, config):
    """遺伝的アルゴリズム
    
    特徴:
    - 多様な解を並列探索
    - 交叉・突然変異で解を生成
    """
    population_size = 50
    generations = 100
    
    # 初期個体群（ランダム + Greedy）
    population = initialize_population(candidates, population_size)
    
    for generation in range(generations):
        # 評価
        fitness = [total_profit(individual) for individual in population]
        
        # 選択（トーナメント選択）
        parents = tournament_selection(population, fitness, n_parents=20)
        
        # 交叉（2つの解を組み合わせ）
        offspring = []
        for i in range(0, len(parents), 2):
            child1, child2 = crossover(parents[i], parents[i+1])
            offspring.extend([child1, child2])
        
        # 突然変異
        for individual in offspring:
            if random() < 0.1:  # 10%の確率
                mutate(individual, candidates)
        
        # 次世代（エリート保存 + 子世代）
        population = elitism(population, fitness, n_elite=10) + offspring
    
    # 最良個体を返す
    best = max(population, key=lambda ind: total_profit(ind))
    return best
```

**メリット**: 多様な解を探索、局所最適に陥りにくい  
**デメリット**: 収束が遅い、パラメータ調整が難しい  
**推奨度**: ⭐⭐⭐☆☆

---

### 5. Column Generation

```python
def column_generation(fields, crops, weather_data, planning_period):
    """列生成法（大規模問題向け）
    
    特徴:
    - 候補を動的に生成
    - 大規模問題に対応
    """
    # Master Problem: 圃場への割当パターンを選択
    master = LpProblem("Master", LpMaximize)
    
    # 各圃場のパターン変数
    patterns = {}  # {field_id: [pattern1, pattern2, ...]}
    
    while True:
        # Master Problemを解く
        master.solve()
        dual_values = get_dual_values(master)
        
        # Pricing Problem: 新しい有望なパターンを探す
        new_patterns = []
        for field in fields:
            pattern = solve_pricing_problem(field, crops, dual_values)
            if pattern.reduced_cost > 0:
                new_patterns.append(pattern)
        
        # 新しいパターンがなければ終了
        if not new_patterns:
            break
        
        # 新しいパターンをMasterに追加
        for pattern in new_patterns:
            add_pattern_to_master(master, pattern)
    
    return extract_solution(master)
```

**メリット**: 超大規模問題に対応（候補数10万以上）  
**デメリット**: 実装が非常に複雑  
**推奨度**: ⭐⭐☆☆☆（現時点では不要）

---

### 6. Constraint Programming (CP)

```python
from ortools.sat.python import cp_model

def cp_optimization(fields, crops, candidates):
    """制約プログラミング
    
    特徴:
    - 柔軟な制約表現
    - 非線形制約も対応
    """
    model = cp_model.CpModel()
    
    # 決定変数: x[i] ∈ {0, 1}
    x = {}
    for i, candidate in enumerate(candidates):
        x[i] = model.NewBoolVar(f'x_{i}')
    
    # 制約: 時間的重複の禁止
    for field in fields:
        field_candidates = get_field_candidates(candidates, field)
        
        # Interval変数（開始時刻、終了時刻）
        intervals = []
        for i, c in field_candidates:
            start = c.start_date.timestamp()
            end = c.completion_date.timestamp()
            duration = end - start
            
            interval = model.NewOptionalIntervalVar(
                start, duration, end, x[i], f'interval_{i}'
            )
            intervals.append(interval)
        
        # No Overlap制約
        model.AddNoOverlap(intervals)
    
    # 目的関数
    model.Maximize(sum(x[i] * candidates[i].profit for i in range(len(candidates))))
    
    # 求解
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 300
    status = solver.Solve(model)
    
    # 解の抽出
    solution = [candidates[i] for i in range(len(candidates)) if solver.Value(x[i]) == 1]
    return solution
```

**メリット**: 柔軟な制約、非線形も対応  
**デメリット**: ソルバー依存（OR-Tools）  
**推奨度**: ⭐⭐⭐⭐☆（MILP代替として有力）

---

## アルゴリズム比較表

| アルゴリズム | 品質 | 計算時間 | 実装難易度 | 推奨度 |
|------------|------|---------|-----------|--------|
| **現状（Greedy + LS）** | 85-95% | 10-30秒 | ★☆☆☆☆ | ⭐⭐⭐⭐☆ |
| **ALNS** | 90-98% | 30-60秒 | ★★★☆☆ | ⭐⭐⭐⭐⭐ |
| **MILP** | 100% | 1-10分 | ★★★★☆ | ⭐⭐⭐⭐☆ |
| **Hybrid (Greedy + ALNS + MILP)** | 95-100% | 1-2分 | ★★★★☆ | ⭐⭐⭐⭐⭐ |
| **Genetic Algorithm** | 88-95% | 1-5分 | ★★★☆☆ | ⭐⭐⭐☆☆ |
| **Column Generation** | 100% | 数秒-数分 | ★★★★★ | ⭐⭐☆☆☆ |
| **Constraint Programming** | 100% | 1-10分 | ★★★★☆ | ⭐⭐⭐⭐☆ |

---

## 実装ロードマップ

### Phase 1: ALNS実装（推奨）⭐⭐⭐⭐⭐

**期間**: 1-2週間  
**効果**: 品質 85-95% → 90-98%

**実装ステップ**:

```python
# Week 1: 基本フレームワーク
1. Destroy operators: random, worst, related
2. Repair operators: greedy, regret
3. Simulated Annealing受理基準
4. 基本的な重み調整

# Week 2: 拡張と最適化
5. 追加のDestroy: field_removal, time_slice_removal
6. 追加のRepair: dp_insert
7. Adaptive weights（動的重み調整）
8. パラメータチューニング
```

**コード例**:

```python
# src/agrr_core/usecase/services/alns_optimizer_service.py
class ALNSOptimizer:
    """Adaptive Large Neighborhood Search optimizer"""
    
    def __init__(self, config: OptimizationConfig):
        self.config = config
        self.destroy_ops = self._init_destroy_operators()
        self.repair_ops = self._init_repair_operators()
        self.weights = AdaptiveWeights(
            list(self.destroy_ops.keys()) + list(self.repair_ops.keys())
        )
    
    def optimize(
        self, 
        initial_solution: List[CropAllocation],
        candidates: List[AllocationCandidate],
        fields: List[Field],
        crops: List[Crop]
    ) -> List[CropAllocation]:
        """ALNS optimization main loop"""
        # ... (上記のアルゴリズム実装)
```

---

### Phase 2: MILP実装（オプション）⭐⭐⭐⭐☆

**期間**: 1-2週間  
**効果**: 厳密最適解を保証（小-中規模問題）

**実装ステップ**:

```python
# Week 1: 基本実装
1. PuLP統合
2. 基本制約（時間重複、max_revenue）
3. 目的関数（利益最大化）

# Week 2: 拡張
4. 連続栽培ペナルティの線形化
5. 大規模問題への対応（分解法）
6. 商用ソルバー統合（Gurobi - オプション）
```

---

### Phase 3: Hybrid実装（最終形態）⭐⭐⭐⭐⭐

**期間**: 1週間  
**効果**: 品質95-100%、計算時間1-2分

**実装ステップ**:

```python
def hybrid_optimize(fields, crops, candidates, config):
    """Hybrid: Greedy → ALNS → MILP"""
    
    # Phase 1: Greedy（既存）
    solution = greedy_allocation(candidates)
    
    # Phase 2: ALNS（大域的改善）
    if config.enable_alns:
        solution = alns_optimize(solution, candidates, fields, crops)
    
    # Phase 3: MILP Refinement（局所的な厳密最適化）
    if config.enable_milp_refinement:
        solution = milp_refine_per_field(solution, fields, candidates)
    
    return solution
```

---

## 推奨実装順序

### 短期（1-2週間）: ALNS導入

**優先度**: 🔥🔥🔥🔥🔥

**理由**:
- ✅ 品質改善が大きい（+5-10%）
- ✅ 既存コードへの統合が容易
- ✅ 計算時間は許容範囲

**実装**:
```bash
# 新規ファイル
src/agrr_core/usecase/services/alns_optimizer_service.py
src/agrr_core/usecase/services/destroy_operators.py
src/agrr_core/usecase/services/repair_operators.py

# 既存ファイルの修正
src/agrr_core/usecase/interactors/multi_field_crop_allocation_greedy_interactor.py
  → ALNSOptimizerを統合

# テスト
tests/test_unit/test_alns_optimizer.py
```

---

### 中期（1ヶ月後）: MILP統合

**優先度**: 🔥🔥🔥🔥☆

**理由**:
- ✅ 最適解を保証（小-中規模問題）
- ✅ 商用利用で信頼性が重要な場合に有効

**実装**:
```bash
# 新規ファイル
src/agrr_core/usecase/services/milp_optimizer_service.py

# 依存関係
requirements.txt に追加:
  pulp>=2.7
  # ortools>=9.6  # 代替案
```

---

### 長期（3ヶ月後）: Hybrid完成

**優先度**: 🔥🔥🔥🔥🔥

**理由**:
- ✅ 最高品質（95-100%）
- ✅ 実用的な計算時間
- ✅ 段階的に切り替え可能

---

## まとめ

### 🎯 最優先: ALNS実装

**現在のアルゴリズムは「なんちゃって貪欲」ではなく、かなり洗練されています。**

しかし、さらなる改善として**ALNS（Adaptive Large Neighborhood Search）**を推奨します：

1. **品質**: 85-95% → 90-98%（+5-10%改善）
2. **計算時間**: 30-60秒（許容範囲）
3. **実装難易度**: 中程度（1-2週間）
4. **効果**: 大きい

### 🥈 次点: MILP

厳密な最適解が必要な場合、MILPを検討：

1. **品質**: 100%（最適解保証）
2. **計算時間**: 1-10分（問題規模に依存）
3. **実装難易度**: 高い（1-2週間）
4. **効果**: 保証付き品質

### 🏆 最終形態: Hybrid

両方の利点を組み合わせ：

1. **品質**: 95-100%
2. **計算時間**: 1-2分
3. **実装難易度**: 高い（3-4週間）
4. **効果**: 最高

---

**今すぐ始めるなら**: ALNSを実装しましょう！🚀

