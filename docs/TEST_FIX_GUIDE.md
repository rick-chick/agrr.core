# テスト修正ガイド

このドキュメントは、"Remove unused revenue/profit calculations" リファクタリングによって失敗したテストの修正方法を説明します。

## 目次

1. [AllocationCandidate インターフェース変更](#allocationcandidate-インターフェース変更)
2. [OptimizationConfig インターフェース変更](#optimizationconfig-インターフェース変更)
3. [修正例](#修正例)

---

## AllocationCandidate インターフェース変更

### 変更前のインターフェース

```python
@dataclass
class AllocationCandidate:
    field: Field
    crop: Crop
    start_date: datetime
    completion_date: datetime
    growth_days: int
    accumulated_gdd: float
    area_used: float
    previous_crop: Optional[Crop]  # ❌ 削除された
    interaction_impact: float = 1.0  # ❌ 削除された
    
    @property
    def revenue(self) -> float:
        """直接計算された収益 (不完全)"""
        base_revenue = self.area_used * self.crop.revenue_per_area
        if self.crop.max_revenue:
            base_revenue = min(base_revenue, self.crop.max_revenue)
        return base_revenue * self.interaction_impact
    
    @property
    def profit(self) -> float:
        """直接計算された利益 (不完全)"""
        return self.revenue - self.cost
```

### 変更後のインターフェース

```python
@dataclass
class AllocationCandidate:
    field: Field
    crop: Crop
    start_date: datetime
    completion_date: datetime
    growth_days: int
    accumulated_gdd: float
    area_used: float
    # previous_crop と interaction_impact は削除
    
    def get_metrics(
        self, 
        current_allocations: Optional[List[CropAllocation]] = None,
        field_schedules: Optional[Dict[str, List[CropAllocation]]] = None,
        interaction_rules: Optional[List] = None
    ) -> OptimizationMetrics:
        """完全な計算を含むメトリクスを取得"""
        return OptimizationMetrics.create_for_allocation(
            area_used=self.area_used,
            revenue_per_area=self.crop.revenue_per_area,
            max_revenue=self.crop.max_revenue,
            growth_days=self.growth_days,
            daily_fixed_cost=self.field.daily_fixed_cost,
            crop_id=self.crop.crop_id,
            crop=self.crop,
            field=self.field,
            start_date=self.start_date,
            current_allocations=current_allocations,  # 市場需要追跡
            field_schedules=field_schedules,  # 相互作用ルール
            interaction_rules=interaction_rules,  # 連作障害ルール
        )
    
    @property
    def revenue(self) -> Optional[float]:
        """ベースライン収益 (コンテキストなし - フィルタリング用のみ)"""
        return self.get_metrics().revenue
    
    @property
    def profit(self) -> float:
        """ベースライン利益 (コンテキストなし - フィルタリング用のみ)"""
        return self.get_metrics().profit
```

### 主な変更点

1. **削除されたパラメータ:**
   - `previous_crop: Optional[Crop]`
   - `interaction_impact: float`

2. **新しいメソッドシグネチャ:**
   - `get_metrics()` が3つのオプションパラメータを受け取る
   - `current_allocations`: 同じ作物の累積収益を追跡（市場需要制限用）
   - `field_schedules`: 各圃場の割り当て履歴（相互作用ルール用）
   - `interaction_rules`: 相互作用ルールのリスト（連作障害用）

3. **計算の統一:**
   - すべての計算は `OptimizationMetrics.create_for_allocation()` で実行
   - 以下の要素がすべて考慮される:
     - `soil_recovery_factor`: 休閑期間ボーナス
     - `interaction_impact`: 連作障害ペナルティ
     - `yield_factor`: 温度ストレス
     - `max_revenue`: 市場需要制限

---

## OptimizationConfig インターフェース変更

### 変更前のインターフェース

```python
@dataclass
class OptimizationConfig:
    # ... 他のパラメータ ...
    
    enable_alns: bool = False
    alns_iterations: int = 200
    alns_initial_temp: float = 1000.0  # ❌ 削除された
    alns_cooling_rate: float = 0.95  # ❌ 削除された
    alns_removal_rate: float = 0.3
```

### 変更後のインターフェース

```python
@dataclass
class OptimizationConfig:
    # ... 他のパラメータ ...
    
    enable_alns: bool = False
    alns_iterations: int = 200
    alns_removal_rate: float = 0.3
    # alns_initial_temp と alns_cooling_rate は削除
```

### 理由

ALNS (Adaptive Large Neighborhood Search) の実装で、焼きなまし法の温度パラメータが不要になったため。

---

## 修正例

### 例1: test_continuous_cultivation_impact.py

#### 修正前

```python
def test_candidate_with_continuous_cultivation_penalty(self):
    """連作障害ペナルティが収益を減らすことをテスト"""
    field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
    crop = Crop("eggplant", "Eggplant", 0.5, revenue_per_area=50000.0, groups=["Solanaceae"])
    previous_crop = Crop("tomato", "Tomato", 0.5, groups=["Solanaceae"])
    
    candidate = AllocationCandidate(
        field=field,
        crop=crop,
        start_date=datetime(2025, 9, 1),
        completion_date=datetime(2026, 1, 31),
        growth_days=150,
        accumulated_gdd=2000.0,
        area_used=500.0,
        previous_crop=previous_crop,  # ❌ 削除されたパラメータ
        interaction_impact=0.7  # ❌ 削除されたパラメータ - 30%ペナルティ
    )
    
    # 収益は: 500 * 50000 * 0.7 = 17,500,000 (30%減)
    assert candidate.revenue == 17500000.0
```

#### 修正後

```python
def test_candidate_with_continuous_cultivation_penalty(self):
    """連作障害ペナルティが収益を減らすことをテスト"""
    field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
    crop = Crop("eggplant", "Eggplant", 0.5, revenue_per_area=50000.0, groups=["Solanaceae"])
    previous_crop = Crop("tomato", "Tomato", 0.5, groups=["Solanaceae"])
    
    # 前作物の割り当てを作成
    previous_allocation = CropAllocation(
        field_id="f1",
        crop_id="tomato",
        start_date=datetime(2025, 4, 1),
        completion_date=datetime(2025, 8, 31),
        growth_days=150,
        area_used=500.0,
        accumulated_gdd=2000.0,
        expected_revenue=None,
        profit=None
    )
    
    # 相互作用ルールを定義 (連作障害: 30%ペナルティ)
    interaction_rule = InteractionRule(
        rule_type=RuleType.CONTINUOUS_CULTIVATION,
        crop_family_a="Solanaceae",
        crop_family_b="Solanaceae",
        impact_ratio=0.7,  # 30%減
        is_directional=False
    )
    
    candidate = AllocationCandidate(
        field=field,
        crop=crop,
        start_date=datetime(2025, 9, 1),
        completion_date=datetime(2026, 1, 31),
        growth_days=150,
        accumulated_gdd=2000.0,
        area_used=500.0,
    )
    
    # コンテキストを含めてメトリクスを取得
    metrics = candidate.get_metrics(
        current_allocations=[],  # 市場需要制限なし
        field_schedules={"f1": [previous_allocation]},  # 前作物の履歴
        interaction_rules=[interaction_rule]  # 連作障害ルール
    )
    
    # 収益は: 500 * 50000 * 0.7 = 17,500,000 (30%減)
    assert metrics.revenue == 17500000.0
    assert metrics.cost == 150 * 5000.0  # コストは変わらず: 750,000
    
    # 利益 = 収益 - コスト = 17,500,000 - 750,000 = 16,750,000
    expected_profit = 17500000.0 - 750000.0
    assert metrics.profit == pytest.approx(expected_profit, rel=0.001)
```

### 例2: test_alns_optimizer.py

#### 修正前

```python
@pytest.fixture
def config(self):
    """テスト用の設定を作成"""
    return OptimizationConfig(
        enable_alns=True,
        alns_iterations=10,
        alns_initial_temp=1000.0,  # ❌ 削除された
        alns_cooling_rate=0.95,  # ❌ 削除された
        alns_removal_rate=0.3,
    )
```

#### 修正後

```python
@pytest.fixture
def config(self):
    """テスト用の設定を作成"""
    return OptimizationConfig(
        enable_alns=True,
        alns_iterations=10,
        alns_removal_rate=0.3,
    )
```

### 例3: test_multi_field_crop_allocation_dp.py

#### 修正前

```python
def test_dp_allocation_max_revenue_constraint(self):
    """最大収益制約が適用されることをテスト"""
    field = Field("f1", "Field 1", 1000.0, 5000.0)
    crop = Crop("tomato", "Tomato", 0.5, revenue_per_area=50000.0, max_revenue=15000000.0)
    
    candidate = AllocationCandidate(
        field=field,
        crop=crop,
        start_date=datetime(2025, 4, 1),
        completion_date=datetime(2025, 8, 31),
        growth_days=150,
        accumulated_gdd=2000.0,
        area_used=500.0,
        previous_crop=None,  # ❌ 削除された
    )
    
    # 収益上限が適用される: min(500 * 50000, 15000000) = 15000000
    assert candidate.revenue == 15000000.0
```

#### 修正後

```python
def test_dp_allocation_max_revenue_constraint(self):
    """最大収益制約が適用されることをテスト"""
    field = Field("f1", "Field 1", 1000.0, 5000.0)
    crop = Crop("tomato", "Tomato", 0.5, revenue_per_area=50000.0, max_revenue=15000000.0)
    
    candidate = AllocationCandidate(
        field=field,
        crop=crop,
        start_date=datetime(2025, 4, 1),
        completion_date=datetime(2025, 8, 31),
        growth_days=150,
        accumulated_gdd=2000.0,
        area_used=500.0,
    )
    
    # メトリクスを取得 (市場需要制限なし)
    metrics = candidate.get_metrics(
        current_allocations=[],
        field_schedules={},
        interaction_rules=[]
    )
    
    # 収益上限が適用される: min(500 * 50000, 15000000) = 15000000
    assert metrics.revenue == 15000000.0
```

---

## テスト修正のチェックリスト

各テストを修正する際は、以下を確認してください:

- [ ] `AllocationCandidate` から `previous_crop` パラメータを削除
- [ ] `AllocationCandidate` から `interaction_impact` パラメータを削除
- [ ] 必要に応じて `CropAllocation` オブジェクトを作成し `field_schedules` に設定
- [ ] 必要に応じて `InteractionRule` オブジェクトを作成し `interaction_rules` に設定
- [ ] `candidate.revenue` の代わりに `candidate.get_metrics(...).revenue` を使用
- [ ] `candidate.profit` の代わりに `candidate.get_metrics(...).profit` を使用
- [ ] `OptimizationConfig` から `alns_initial_temp` パラメータを削除
- [ ] `OptimizationConfig` から `alns_cooling_rate` パラメータを削除
- [ ] テストが新しい設計の意図を正しく検証していることを確認

---

## OptimizationMetrics の新しい計算フロー

新しい設計では、`OptimizationMetrics.create_for_allocation()` が以下の順序で計算を実行します:

1. **基本収益の計算:**
   ```python
   base_revenue = area_used * revenue_per_area
   ```

2. **市場需要制限の適用:**
   ```python
   crop_cumulative_revenue = calculate_crop_cumulative_revenue(crop_id, current_allocations)
   remaining_revenue = max_revenue - crop_cumulative_revenue
   constrained_revenue = min(base_revenue, remaining_revenue)
   ```

3. **相互作用影響の計算:**
   ```python
   interaction_impact = calculate_interaction_impact(
       crop, field, start_date, field_schedules, interaction_rules
   )
   ```

4. **最終収益の計算:**
   ```python
   final_revenue = constrained_revenue * interaction_impact * soil_recovery_factor * yield_factor
   ```

5. **コストの計算:**
   ```python
   cost = growth_days * daily_fixed_cost
   ```

6. **利益の計算:**
   ```python
   profit = final_revenue - cost
   ```

この計算フローにより、すべての要素が正しい順序で適用されます。

---

## まとめ

このリファクタリングは、計算ロジックを一箇所に集約し、より正確で保守しやすいコードを実現しています。テストの修正は手間がかかりますが、新しい設計の利点を理解することで、より良いテストコードを書くことができます。

