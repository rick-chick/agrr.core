# 複数圃場・複数作物の最適化設計書

## 概要

現在の最適化に以下の要素を追加する：
1. **作物をどのFieldに割り当てるか**（Field Allocation Problem）
2. **作物を何個作るか**（Quantity Optimization Problem）
3. **既存**: いつ栽培するか（Period Optimization Problem）

これにより、**複数の圃場で複数の作物を時系列で栽培する総合的な最適化**を実現する。

## 問題の定式化

### 最適化の目標

**総利益の最大化** = 総収益 - 総コスト

または

**総コストの最小化**（収益制約付き）

### 決定変数

#### 1. 離散変数（0-1整数計画問題）

- `x[f][c][s][t]` ∈ {0, 1}
  - f: Field ID（圃場）
  - c: Crop ID（作物）
  - s: Schedule ID（栽培スケジュール: 開始日と完了日のペア）
  - t: Time period（栽培期間）
  
  `x[f][c][s][t] = 1` のとき、圃場fで作物cをスケジュールsで栽培する

#### 2. 連続変数

- `quantity[f][c][s]`: 圃場fで作物cをスケジュールsで栽培する個数（実数）

### 制約条件

#### 1. 圃場の面積制約

各圃場fの面積 `A_f` に対して：

```
Σ(c, s) quantity[f][c][s] × area_per_unit[c] × x[f][c][s] ≤ A_f
```

各圃場で栽培する作物の総面積が圃場面積を超えない。

#### 2. 圃場の時間的排他制約（Non-overlapping Constraint）

各圃場fにおいて、時刻tで同時に栽培できる作物は1つまで：

```
Σ(c, s) x[f][c][s] × overlap(s, t) ≤ 1  for all f, t
```

ここで、`overlap(s, t) = 1` if スケジュールsが時刻tを含む、0 otherwise

#### 3. 作物の栽培可能期間制約

作物cのスケジュールsが気象条件などで栽培可能か：

```
x[f][c][s] = 1 ⇒ is_feasible[c][s] = 1
```

#### 4. 最小生産量制約（オプション）

作物cの最小生産量要件：

```
Σ(f, s) quantity[f][c][s] × x[f][c][s] ≥ min_quantity[c]
```

#### 5. 非負制約

```
quantity[f][c][s] ≥ 0
```

### 目的関数

#### パターンA: 利益最大化

```
Maximize: Σ(f, c, s) [
  quantity[f][c][s] × x[f][c][s] × (
    revenue_per_unit[c] - 
    (growth_days[s] × daily_cost[f] / quantity[f][c][s])
  )
]
```

#### パターンB: コスト最小化（生産量制約付き）

```
Minimize: Σ(f, c, s) [
  quantity[f][c][s] × x[f][c][s] × growth_days[s] × daily_cost[f]
]

Subject to:
  Σ(f, s) quantity[f][c][s] × x[f][c][s] ≥ target_quantity[c]  for all c
```

## データモデル設計

### 1. 新しいエンティティ

#### `CropAllocation` Entity

```python
@dataclass(frozen=True)
class CropAllocation:
    """作物割り当て情報"""
    allocation_id: str
    field: Field
    crop: Crop
    quantity: float  # 栽培個数
    start_date: datetime
    completion_date: datetime
    growth_days: int
    total_cost: float
    expected_revenue: Optional[float] = None
    area_used: float = 0.0  # 使用面積（m²）
```

#### `FieldSchedule` Entity

```python
@dataclass(frozen=True)
class FieldSchedule:
    """圃場の栽培スケジュール"""
    field: Field
    allocations: List[CropAllocation]
    total_area_used: float
    total_cost: float
    total_revenue: float
    profit: float
    utilization_rate: float  # 圃場利用率（%）
```

#### `MultiFieldOptimizationResult` Entity

```python
@dataclass(frozen=True)
class MultiFieldOptimizationResult:
    """複数圃場の最適化結果"""
    optimization_id: str
    field_schedules: List[FieldSchedule]
    total_cost: float
    total_revenue: float
    total_profit: float
    crop_quantities: Dict[str, float]  # {crop_id: total_quantity}
    optimization_time: float  # 計算時間（秒）
```

### 2. DTO設計

#### Request DTO

```python
@dataclass
class MultiFieldCropAllocationRequestDTO:
    """複数圃場・複数作物の割り当て最適化リクエスト"""
    
    # 圃場情報
    field_ids: List[str]  # 対象圃場のリスト
    
    # 作物情報
    crop_requirements: List[Dict[str, Any]]  # 作物ごとの要件
    # Example: [
    #   {
    #     "crop_id": "rice",
    #     "variety": "Koshihikari",
    #     "min_quantity": 1000.0,  # 最小生産量
    #     "target_quantity": 2000.0,  # 目標生産量
    #     "max_quantity": 3000.0,  # 最大生産量
    #   }
    # ]
    
    # 時間範囲
    planning_period_start: datetime
    planning_period_end: datetime
    
    # 気象データ
    weather_data_file: str
    
    # 最適化パラメータ
    optimization_objective: str  # "maximize_profit", "minimize_cost"
    consider_revenue: bool = True
    max_computation_time: Optional[float] = None  # 最大計算時間（秒）
```

#### Response DTO

```python
@dataclass
class MultiFieldCropAllocationResponseDTO:
    """複数圃場・複数作物の割り当て最適化レスポンス"""
    
    optimization_result: MultiFieldOptimizationResult
    field_schedules: List[FieldSchedule]
    
    # サマリー情報
    total_fields_used: int
    total_cultivations: int  # 総栽培回数
    average_field_utilization: float  # 平均圃場利用率
    
    # 実行統計
    computation_time: float
    algorithm_used: str
    is_optimal: bool  # 最適解か（厳密解 vs 近似解）
```

## アルゴリズム設計

### アプローチ1: 動的計画法（小規模問題）

**適用条件**:
- 圃場数: 1-5個
- 作物種類: 1-3種類
- 計画期間: 1年以内

**アルゴリズム**:
1. 各作物・各圃場の候補スケジュールを生成（既存の最適化を利用）
2. 3次元DPテーブル: `dp[field_idx][time][crop_count]`
3. 圃場ごとに順次、非重複スケジュールを選択
4. 面積制約・数量制約を満たす組み合わせを探索

**計算量**: O(F × T × C × S²)
- F: 圃場数、T: 時間ステップ数、C: 作物種類、S: スケジュール候補数

### アプローチ2: 貪欲法 + 局所探索（中規模問題）

**適用条件**:
- 圃場数: 5-20個
- 作物種類: 3-10種類
- 計画期間: 1年

**アルゴリズム**:
1. **初期解の生成（貪欲法）**:
   - 利益率（revenue/cost）が高い順に作物をソート
   - 空いている圃場に順次割り当て
   - 面積・時間制約を満たす限り割り当て続ける

2. **局所探索による改善**:
   - Swap操作: 2つの割り当てを入れ替え
   - Insert操作: 割り当てを別の圃場・時期に移動
   - Delete操作: 不採算な割り当てを削除
   - 改善が見つからなくなるまで繰り返し

**計算量**: O(iterations × allocations²)

### アプローチ3: 整数計画法（大規模問題）

**適用条件**:
- 圃場数: 20個以上
- 作物種類: 10種類以上
- 厳密解が必要な場合

**アルゴリズム**:
1. 問題を混合整数計画問題（MILP）として定式化
2. 既存のソルバーを使用:
   - Python: `pulp`, `scipy.optimize`, `python-mip`
   - 商用: Gurobi, CPLEX

**変数**:
- バイナリ変数: x[f][c][s] ∈ {0, 1}
- 連続変数: quantity[f][c][s] ≥ 0

**制約**:
- 線形制約: 面積制約、数量制約
- 特殊制約: 非重複制約（Big-M法で線形化）

**計算量**: 指数時間（最悪ケース）、実用的には多項式時間で解ける場合が多い

## 実装の段階的アプローチ

### フェーズ1: 基本機能（推奨: 貪欲法）

1. **単一圃場・複数作物の最適化**
   - 既存のスケジューリングDPを拡張
   - 作物間の組み合わせ最適化

2. **複数圃場・単一作物の最適化**
   - 圃場間の負荷分散
   - コスト最小化

### フェーズ2: 統合最適化（推奨: 貪欲法 + 局所探索）

1. **複数圃場・複数作物の統合**
   - 2段階最適化: 
     - Stage 1: 各圃場で独立に最適化
     - Stage 2: 圃場間の割り当て調整

2. **数量最適化の追加**
   - 離散的な数量（1個、2個...）から開始
   - 徐々に連続変数へ拡張

### フェーズ3: 高度な最適化（推奨: MILP）

1. **厳密解の計算**
   - 整数計画ソルバーの統合
   - 分枝限定法の適用

2. **不確実性の考慮**
   - ロバスト最適化
   - 確率的制約

## 使用例

### ユースケース1: 小規模農家（圃場3つ、作物2種類）

```python
# 入力
request = MultiFieldCropAllocationRequestDTO(
    field_ids=["field_001", "field_002", "field_003"],
    crop_requirements=[
        {
            "crop_id": "rice",
            "variety": "Koshihikari",
            "target_quantity": 5000.0,  # kg
        },
        {
            "crop_id": "tomato",
            "variety": "Momotaro",
            "target_quantity": 3000.0,  # kg
        }
    ],
    planning_period_start=datetime(2025, 4, 1),
    planning_period_end=datetime(2026, 3, 31),
    weather_data_file="weather_2025.json",
    optimization_objective="maximize_profit"
)

# 出力例
# Field 001: 
#   - Rice (4/1-8/31): 2000kg, Cost: 600,000円, Revenue: 1,000,000円
#   - Tomato (9/1-12/31): 1500kg, Cost: 400,000円, Revenue: 900,000円
# Field 002:
#   - Rice (4/15-9/15): 2000kg, Cost: 610,000円, Revenue: 1,000,000円
#   - Tomato (9/20-1/20): 1500kg, Cost: 420,000円, Revenue: 900,000円
# Field 003:
#   - Rice (5/1-9/30): 1000kg, Cost: 550,000円, Revenue: 500,000円
# 
# Total: Revenue: 4,300,000円, Cost: 2,580,000円, Profit: 1,720,000円
```

### ユースケース2: 中規模農家（圃場10個、作物5種類）

```python
request = MultiFieldCropAllocationRequestDTO(
    field_ids=[f"field_{i:03d}" for i in range(1, 11)],
    crop_requirements=[
        {"crop_id": "rice", "variety": "Koshihikari", "target_quantity": 20000.0},
        {"crop_id": "wheat", "variety": "Haruyokoi", "target_quantity": 15000.0},
        {"crop_id": "tomato", "variety": "Momotaro", "target_quantity": 8000.0},
        {"crop_id": "cucumber", "variety": "Sagami", "target_quantity": 5000.0},
        {"crop_id": "lettuce", "variety": "Great Lakes", "target_quantity": 3000.0},
    ],
    planning_period_start=datetime(2025, 4, 1),
    planning_period_end=datetime(2026, 3, 31),
    weather_data_file="weather_2025.json",
    optimization_objective="maximize_profit",
    max_computation_time=300.0  # 5分以内
)
```

## 技術的課題と解決策

### 課題1: 計算時間の爆発

**問題**: 圃場×作物×時期の組み合わせが指数的に増加

**解決策**:
1. 候補の事前フィルタリング（不採算な組み合わせを除外）
2. 時間の粗い粒度化（日単位→週単位→月単位）
3. 段階的最適化（粗い解→細かい解）

### 課題2: 面積制約の扱い

**問題**: 連続変数と離散変数の混合

**解決策**:
1. 初期段階では離散化（1株、10株、100株単位）
2. 整数計画法の利用
3. 連続緩和 + 丸め

### 課題3: 不確実性（気象、市場価格）

**問題**: 将来の気象や価格が不確実

**解決策**:
1. 複数シナリオでの最適化
2. 期待値最適化
3. リスク指標（VaR, CVaR）の組み込み

## 実装優先順位

1. **Phase 1** (2週間):
   - `CropAllocation`, `FieldSchedule` エンティティの実装
   - 単一圃場・複数作物の貪欲法による最適化
   - 基本的なテストケース

2. **Phase 2** (2週間):
   - 複数圃場への拡張
   - 局所探索による改善
   - CLIインターフェース

3. **Phase 3** (3週間):
   - 数量最適化の追加
   - より高度なアルゴリズム（DP or MILP）
   - パフォーマンス最適化

## 参考文献

- **Weighted Interval Scheduling**: 既に実装済み
- **Job Shop Scheduling Problem**: 類似問題
- **Bin Packing Problem**: 圃場への割り当て問題として見れる
- **Mixed Integer Linear Programming**: 厳密解の計算

## まとめ

この設計では、既存の時系列最適化に加えて：
1. **空間的な最適化**（どの圃場に）
2. **量的な最適化**（何個作るか）

を統合することで、農業経営全体の最適化を実現します。

段階的に実装することで、早期に価値を提供しながら、徐々に高度な最適化へ進化できます。

