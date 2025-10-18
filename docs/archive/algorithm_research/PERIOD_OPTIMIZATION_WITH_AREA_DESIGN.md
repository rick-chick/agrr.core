# Period Optimization に面積を追加する設計

## 問題の整理

### 現在の問題

```python
# 現在の実装
period_result = GrowthPeriodOptimizeInteractor.execute(
    crop_id="rice",
    field=field,  # 圃場全体の情報のみ
    # ❌ 実際に使用する面積の情報がない
)

# その後、異なるQuantityで候補生成
for quantity_level in [1.0, 0.75, 0.5, 0.25]:
    quantity = field_capacity * quantity_level
    # ❌ しかし、Period最適化は一度しか実行していない
    # ❌ Quantity=50%では異なるPeriodが最適かもしれない
```

### なぜ面積が重要か

1. **固定コストモデル（現在）**
   - Period最適化はQuantityと独立（数学的に証明済み）
   - しかし、**収益計算には影響**する
   - Quantityが小さい場合、より長いPeriodでも採算が取れない可能性

2. **変動コストモデル（将来）**
   - コスト = 固定コスト + 変動コスト × 面積
   - Period最適化がQuantityに依存する
   - 同時最適化が必要

3. **収益上限制約（将来）**
   - 収益に上限がある場合
   - 面積を分割して並行栽培する方が有利
   - Period×Quantityの同時最適化が必須

---

## 解決方法の比較

### 方法1: RequestDTOにQuantityパラメータを追加（推奨）⭐⭐⭐

**設計**:
```python
@dataclass
class OptimalGrowthPeriodRequestDTO:
    crop_id: str
    variety: Optional[str]
    evaluation_period_start: datetime
    evaluation_period_end: datetime
    weather_data_file: str
    field: Field
    crop_requirement_file: Optional[str] = None
    
    # ✅ 新規追加
    quantity: Optional[float] = None  # 栽培個数（Noneの場合は圃場容量100%）
    area_used: Optional[float] = None  # 使用面積（m²、Noneの場合は圃場全体）
```

**実装例**:
```python
# GrowthPeriodOptimizeInteractor
class GrowthPeriodOptimizeInteractor:
    async def execute(self, request: OptimalGrowthPeriodRequestDTO):
        # 面積情報の取得
        if request.area_used is not None:
            area = request.area_used
        elif request.quantity is not None:
            # Crop情報から面積を計算
            crop = await self._get_crop_info(request.crop_id, request.variety)
            area = request.quantity * crop.area_per_unit
        else:
            # デフォルト: 圃場全体
            area = request.field.area
        
        # 候補評価時に面積を考慮
        candidates = await self._evaluate_candidates_efficient(
            request, daily_fixed_cost, area
        )
        
        # 最適候補の選択（収益も考慮）
        optimal_candidate = self.select_best(valid_candidates)
        ...
```

**MultiFieldCropAllocationGreedyInteractor での使用**:
```python
# 各Quantityレベルで個別にPeriod最適化
for quantity_level in config.quantity_levels:
    quantity = field_capacity * quantity_level
    area_used = quantity * crop.area_per_unit
    
    # ✅ Quantityを指定してPeriod最適化
    optimization_request = OptimalGrowthPeriodRequestDTO(
        crop_id=crop_spec.crop_id,
        variety=crop_spec.variety,
        evaluation_period_start=request.planning_period_start,
        evaluation_period_end=request.planning_period_end,
        weather_data_file=request.weather_data_file,
        field_id=field.field_id,
        crop_requirement_file=crop_spec.crop_requirement_file,
        quantity=quantity,  # ✅ 追加
        area_used=area_used,  # ✅ 追加
    )
    
    optimization_result = await self.growth_period_optimizer.execute(optimization_request)
    
    # 各Quantityに最適化されたPeriod候補を取得
    for candidate_period in optimization_result.candidates[:config.top_period_candidates]:
        candidates.append(AllocationCandidate(...))
```

**メリット**:
- ✅ **後方互換性**: quantity=Noneで従来の動作を維持
- ✅ **柔軟性**: 面積または個数のどちらでも指定可能
- ✅ **段階的実装**: 現在は参照のみ、将来的にコスト計算で使用
- ✅ **明示的**: 各Period最適化がどのQuantityを対象にしているか明確

**デメリット**:
- ⚠️ **計算量増加**: Quantityレベルごとに Period最適化を実行（4倍〜8倍）
- ⚠️ **API変更**: 既存の呼び出しコードへの影響（オプショナルなので最小限）

**実装工数**: 1-2日

---

### 方法2: 複数Quantityレベルを一括処理（効率重視）⭐⭐

**設計**:
```python
@dataclass
class OptimalGrowthPeriodRequestDTO:
    # ... 既存のフィールド ...
    
    # ✅ 新規追加：複数のQuantityレベルを一度に処理
    quantity_levels: Optional[List[float]] = None  # [0.25, 0.5, 0.75, 1.0]
```

**実装例**:
```python
class GrowthPeriodOptimizeInteractor:
    async def execute(self, request: OptimalGrowthPeriodRequestDTO):
        if request.quantity_levels:
            # 複数Quantityレベルで一括評価
            return await self._execute_multi_quantity(request)
        else:
            # 従来の単一Quantity処理
            return await self._execute_single_quantity(request)
    
    async def _execute_multi_quantity(self, request):
        """複数Quantityレベルを効率的に評価"""
        # 基本的なPeriod候補を生成（一度だけ）
        base_candidates = await self._evaluate_candidates_efficient(
            request, request.field.daily_fixed_cost
        )
        
        # 各Quantityレベルで収益を計算
        crop = await self._get_crop_info(...)
        results_by_quantity = {}
        
        for quantity_level in request.quantity_levels:
            quantity = (request.field.area / crop.area_per_unit) * quantity_level
            area_used = quantity * crop.area_per_unit
            
            # 各候補の収益を計算
            candidates_with_revenue = []
            for candidate in base_candidates:
                # 収益 = quantity × revenue_per_area × area_per_unit
                revenue = quantity * crop.revenue_per_area * crop.area_per_unit
                profit = revenue - candidate.total_cost
                
                candidates_with_revenue.append(
                    CandidateResultDTO(
                        start_date=candidate.start_date,
                        completion_date=candidate.completion_date,
                        growth_days=candidate.growth_days,
                        field=candidate.field,
                        quantity=quantity,
                        area_used=area_used,
                        expected_revenue=revenue,
                        profit=profit,
                    )
                )
            
            results_by_quantity[quantity_level] = candidates_with_revenue
        
        return MultiQuantityOptimalGrowthPeriodResponseDTO(
            results_by_quantity=results_by_quantity
        )
```

**メリット**:
- ✅ **効率的**: Period計算は一度だけ（スライディングウィンドウを再利用）
- ✅ **計算量削減**: 4倍〜8倍の高速化
- ✅ **一貫性**: すべてのQuantityで同じPeriod候補を使用

**デメリット**:
- ❌ **精度**: Quantityごとの最適Periodを見逃す可能性
- ❌ **複雑性**: レスポンスDTOが複雑になる
- ⚠️ **固定コスト前提**: 変動コストモデルでは使えない

**実装工数**: 2-3日

---

### 方法3: Lazy評価（キャッシュ活用）⭐⭐

**設計**:
```python
class GrowthPeriodOptimizeInteractor:
    def __init__(self, ...):
        self._period_cache = {}  # キャッシュ
    
    async def execute(self, request: OptimalGrowthPeriodRequestDTO):
        # キャッシュキーを生成
        cache_key = self._generate_cache_key(request)
        
        if cache_key in self._period_cache:
            # キャッシュヒット：Period候補を再利用
            base_candidates = self._period_cache[cache_key]
        else:
            # Period候補を計算してキャッシュ
            base_candidates = await self._evaluate_candidates_efficient(...)
            self._period_cache[cache_key] = base_candidates
        
        # Quantityを考慮して候補を再評価
        if request.quantity:
            candidates = self._recalculate_with_quantity(
                base_candidates, request.quantity, crop
            )
        else:
            candidates = base_candidates
        
        return response
```

**メリット**:
- ✅ **効率的**: 同じField×Cropの組み合わせでキャッシュを再利用
- ✅ **透過的**: 呼び出し側は意識不要
- ✅ **段階的**: まずキャッシュなしで実装、後で追加

**デメリット**:
- ⚠️ **メモリ使用量**: キャッシュの管理が必要
- ⚠️ **複雑性**: キャッシュの無効化ロジック
- ⚠️ **並列処理**: スレッドセーフな実装が必要

**実装工数**: 3-4日

---

### 方法4: 2段階最適化（現実的な妥協案）⭐⭐⭐

**設計**:
```python
# Stage 1: 粗い最適化（代表的なQuantityレベルのみ）
representative_levels = [0.25, 0.5, 1.0]  # 3つだけ

for quantity_level in representative_levels:
    optimization_request = OptimalGrowthPeriodRequestDTO(
        ...,
        quantity=field_capacity * quantity_level,
    )
    result = await growth_period_optimizer.execute(optimization_request)
    # トップ3候補を保存
    candidates.extend(result.candidates[:3])

# Stage 2: 詳細な評価（必要に応じて）
if config.enable_detailed_optimization:
    # より細かいQuantityレベルで評価
    for quantity_level in [0.1, 0.2, ..., 0.9]:
        ...
```

**メリット**:
- ✅ **バランス**: 精度と速度のバランスが良い
- ✅ **設定可能**: 粗い最適化 or 詳細な最適化を選択
- ✅ **実用的**: ほとんどのケースで十分な精度

**デメリット**:
- ⚠️ **設定依存**: 最適なQuantityレベルの選択が必要
- ⚠️ **見逃しリスク**: 中間のQuantityで最適解を見逃す可能性

**実装工数**: 1-2日

---

## 推奨アプローチ

### 短期（Phase 1）: 方法1 + 方法4 ⭐⭐⭐

**実装順序**:

1. **Week 1**: RequestDTOにquantity/area_usedを追加（方法1）
   - 後方互換性を維持
   - 現在は参照のみ（コスト計算には未使用）
   - テストを追加

2. **Week 2**: 2段階最適化の実装（方法4）
   - 代表的なQuantityレベル（3-5個）で Period最適化
   - OptimizationConfig に設定を追加
   ```python
   @dataclass
   class OptimizationConfig:
       # 既存のフィールド...
       
       # ✅ 新規追加
       quantity_optimization_mode: str = "representative"  # "single", "representative", "full"
       representative_quantity_levels: List[float] = field(
           default_factory=lambda: [0.25, 0.5, 1.0]
       )
   ```

3. **Week 3**: 統合とテスト
   - MultiFieldCropAllocationGreedyInteractor での統合
   - パフォーマンステスト
   - ドキュメント更新

**期待される効果**:
- ✅ 精度向上: Quantityに応じた最適Period選択
- ✅ 計算量: 3倍程度の増加（許容範囲）
- ✅ 後方互換性: 既存のコードは動作を継続

---

### 長期（Phase 2）: 方法3を追加

変動コストモデルや収益上限制約を導入する際に、キャッシュ機構を追加：
- Period候補の再利用
- 計算量の大幅削減
- より細かいQuantityレベルでの最適化

---

## 実装例（推奨アプローチ）

### Step 1: RequestDTOの拡張

```python
# src/agrr_core/usecase/dto/growth_period_optimize_request_dto.py

@dataclass
class OptimalGrowthPeriodRequestDTO:
    """Request DTO for optimal growth period calculation use case."""

    crop_id: str
    variety: Optional[str]
    evaluation_period_start: datetime
    evaluation_period_end: datetime
    weather_data_file: str
    field: Field
    crop_requirement_file: Optional[str] = None
    
    # ✅ Phase 1: Quantityパラメータを追加
    quantity: Optional[float] = None  # 栽培個数（Noneの場合は圃場容量100%）
    area_used: Optional[float] = None  # 使用面積（m²）
    
    def __post_init__(self):
        """Validate input parameters."""
        if self.evaluation_period_start > self.evaluation_period_end:
            raise ValueError(...)
        
        # ✅ 新規バリデーション
        if self.quantity is not None and self.quantity < 0:
            raise ValueError("quantity must be non-negative")
        if self.area_used is not None and self.area_used < 0:
            raise ValueError("area_used must be non-negative")
        if self.area_used is not None and self.area_used > self.field.area:
            raise ValueError(
                f"area_used ({self.area_used} m²) exceeds field area ({self.field.area} m²)"
            )
```

### Step 2: Interactorの拡張

```python
# src/agrr_core/usecase/interactors/growth_period_optimize_interactor.py

class GrowthPeriodOptimizeInteractor(BaseOptimizer[CandidateResultDTO], ...):
    async def execute(self, request: OptimalGrowthPeriodRequestDTO):
        # 面積情報の取得（Phase 1では参照のみ）
        effective_area = await self._get_effective_area(request)
        
        # 既存のロジック
        daily_fixed_cost = request.field.daily_fixed_cost
        candidates = await self._evaluate_candidates_efficient(
            request, daily_fixed_cost, effective_area  # ✅ 渡すが現在は未使用
        )
        
        # ... 以降は既存のロジック
    
    async def _get_effective_area(self, request: OptimalGrowthPeriodRequestDTO) -> float:
        """Get effective cultivation area.
        
        Priority:
        1. area_used (if specified)
        2. quantity * crop.area_per_unit (if quantity specified)
        3. field.area (default: 100% of field)
        """
        if request.area_used is not None:
            return request.area_used
        
        if request.quantity is not None:
            # Crop情報を取得
            crop_requirement = await self._get_crop_requirements(
                request.crop_id, request.variety
            )
            return request.quantity * crop_requirement.crop.area_per_unit
        
        # デフォルト: 圃場全体
        return request.field.area
```

### Step 3: MultiFieldCropAllocationGreedyInteractorの更新

```python
# src/agrr_core/usecase/interactors/multi_field_crop_allocation_greedy_interactor.py

class MultiFieldCropAllocationGreedyInteractor(BaseOptimizer[AllocationCandidate]):
    async def _generate_candidates_for_field_crop(
        self,
        field: Field,
        crop_spec: CropRequirementSpec,
        request: MultiFieldCropAllocationRequestDTO,
        config: OptimizationConfig,
    ) -> List[AllocationCandidate]:
        """Generate candidates for a single field×crop combination."""
        
        # Crop情報を取得
        crop_requirement = await self.crop_requirement_gateway.craft(...)
        crop = crop_requirement.crop
        field_capacity = field.area / crop.area_per_unit
        
        candidates = []
        
        # ✅ 各Quantityレベルで個別にPeriod最適化
        for quantity_level in config.quantity_levels:
            quantity = field_capacity * quantity_level
            area_used = quantity * crop.area_per_unit
            
            # ✅ Quantityを指定してPeriod最適化
            optimization_request = OptimalGrowthPeriodRequestDTO(
                crop_id=crop_spec.crop_id,
                variety=crop_spec.variety,
                evaluation_period_start=request.planning_period_start,
                evaluation_period_end=request.planning_period_end,
                weather_data_file=request.weather_data_file,
                field_id=field.field_id,
                crop_requirement_file=crop_spec.crop_requirement_file,
                quantity=quantity,  # ✅ 追加
                area_used=area_used,  # ✅ 追加
            )
            
            optimization_result = await self.growth_period_optimizer.execute(
                optimization_request
            )
            
            # トップN候補を使用
            for candidate_period in optimization_result.candidates[:config.top_period_candidates]:
                if candidate_period.completion_date is None:
                    continue
                
                candidate = AllocationCandidate(
                    field=field,
                    crop=crop,
                    start_date=candidate_period.start_date,
                    completion_date=candidate_period.completion_date,
                    growth_days=candidate_period.growth_days,
                    accumulated_gdd=0.0,
                    quantity=quantity,
                    area_used=area_used,
                )
                
                # Quality filtering
                if config.enable_candidate_filtering:
                    if candidate.profit_rate < config.min_profit_rate_threshold:
                        continue
                    # ... その他のフィルタ
                
                candidates.append(candidate)
        
        return candidates
```

### Step 4: OptimizationConfigの拡張

```python
# src/agrr_core/usecase/dto/optimization_config.py

@dataclass
class OptimizationConfig:
    # 既存のフィールド...
    
    # ✅ Quantity最適化モード
    quantity_optimization_mode: str = "representative"  # "single", "representative", "full"
    
    # ✅ 代表的なQuantityレベル（"representative"モード用）
    representative_quantity_levels: List[float] = field(
        default_factory=lambda: [0.25, 0.5, 1.0]
    )
    
    @property
    def quantity_levels(self) -> List[float]:
        """Get quantity levels based on optimization mode."""
        if self.quantity_optimization_mode == "single":
            return [1.0]  # 圃場全体のみ
        elif self.quantity_optimization_mode == "representative":
            return self.representative_quantity_levels
        elif self.quantity_optimization_mode == "full":
            return [i * 0.1 for i in range(1, 11)]  # 0.1, 0.2, ..., 1.0
        else:
            raise ValueError(f"Unknown quantity_optimization_mode: {self.quantity_optimization_mode}")
```

---

## テスト戦略

### Unit Tests

```python
# tests/test_usecase/test_growth_period_optimize_with_quantity.py

class TestGrowthPeriodOptimizeWithQuantity:
    """Test Period Optimization with quantity parameter."""
    
    @pytest.mark.asyncio
    async def test_with_quantity_parameter(self):
        """Test that quantity parameter is accepted and stored."""
        request = OptimalGrowthPeriodRequestDTO(
            crop_id="rice",
            variety="Koshihikari",
            evaluation_period_start=datetime(2025, 4, 1),
            evaluation_period_end=datetime(2025, 12, 31),
            weather_data_file="weather.json",
            field=field,
            quantity=2000.0,  # ✅ 指定
        )
        
        response = await interactor.execute(request)
        
        # 動作確認（Phase 1では結果は変わらないが、エラーにならない）
        assert response.optimal_start_date is not None
    
    @pytest.mark.asyncio
    async def test_quantity_validation(self):
        """Test quantity validation."""
        with pytest.raises(ValueError, match="quantity must be non-negative"):
            request = OptimalGrowthPeriodRequestDTO(
                ...,
                quantity=-100.0,  # ❌ 負の値
            )
    
    @pytest.mark.asyncio
    async def test_area_used_validation(self):
        """Test area_used validation."""
        with pytest.raises(ValueError, match="exceeds field area"):
            request = OptimalGrowthPeriodRequestDTO(
                ...,
                field=Field("f1", "Field1", area=1000.0, ...),
                area_used=1500.0,  # ❌ 圃場面積を超える
            )
```

### Integration Tests

```python
# tests/test_usecase/test_multi_field_with_quantity_optimization.py

class TestMultiFieldWithQuantityOptimization:
    """Test multi-field allocation with quantity-aware period optimization."""
    
    @pytest.mark.asyncio
    async def test_different_periods_for_different_quantities(self):
        """Test that different quantities may result in different optimal periods."""
        # この
テストはPhase 2（変動コストモデル導入後）で有効になる
        pass
    
    @pytest.mark.asyncio
    async def test_representative_quantity_levels(self):
        """Test optimization with representative quantity levels."""
        config = OptimizationConfig(
            quantity_optimization_mode="representative",
            representative_quantity_levels=[0.25, 0.5, 1.0],
        )
        
        request = MultiFieldCropAllocationRequestDTO(...)
        
        response = await interactor.execute(request, config=config)
        
        # 各Quantityレベルで候補が生成されていることを確認
        quantities_used = {alloc.quantity for alloc in response.optimization_result.all_allocations}
        assert len(quantities_used) >= 3  # 少なくとも3つのQuantityレベル
```

---

## まとめ

### 推奨: 方法1（RequestDTO拡張）+ 方法4（2段階最適化）

**Phase 1（2-3週間）**:
1. ✅ RequestDTOに `quantity` と `area_used` を追加
2. ✅ 2段階最適化（代表的なQuantityレベルのみ）
3. ✅ 後方互換性を維持
4. ✅ 段階的に実装

**期待される効果**:
- 精度向上: Quantityに応じた最適Period選択
- 計算量: 3倍程度の増加（10秒 → 30秒、許容範囲）
- 柔軟性: 将来の拡張に対応

**Phase 2（将来）**:
- キャッシュ機構の追加
- 変動コストモデルへの対応
- より細かいQuantity最適化

この設計により、Period OptimizationがQuantity情報を考慮し、より正確な最適化が可能になります！

