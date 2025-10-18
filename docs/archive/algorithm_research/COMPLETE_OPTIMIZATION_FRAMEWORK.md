# 完全な最適化フレームワーク：4次元の決定変数

## 最終的な問題定義

### 決定変数の完全な定義

```
x[Field, Crop, Period, Quantity]
   │      │      │        │
   │      │      │        └─ 作付け数量（何個？）
   │      │      └────────── 栽培期間（いつ？）
   │      └───────────────── 作物の種類（何を？）
   └──────────────────────── 圃場の選択（どこで？）
```

---

## 各次元の最適化戦略

### 次元1: Field（圃場） - どこで？

**最適化手法**: 近傍操作（Local Search）

**操作**:
- F1. Move（移動）- 別の圃場へ
- F2. Swap（交換）- 2つの圃場を交換（面積等価）
- F5. Remove（削除）

**品質**: 90-95%（近似解）  
**計算量**: O(n² × F)

---

### 次元2: Crop（作物） - 何を？

**最適化手法**: 近傍操作（Local Search）

**操作**:
- C1. Change Crop（変更）- 別の作物に
- C3. Crop Insert（追加）- 新しい作物を追加

**品質**: 90-95%（近似解）  
**計算量**: O(n × C)

---

### 次元3: Period（期間） - いつ？

**最適化手法**: ★DP（Dynamic Programming）

**既存実装**: `GrowthPeriodOptimizeInteractor`
```python
# Field + Crop が固定されれば、Period はDPで厳密最適化
optimal_period = GrowthPeriodOptimizeInteractor.execute(
    field=field,
    crop=crop,
    evaluation_period_start=start,
    evaluation_period_end=end,
)
```

**品質**: 100%（厳密最適解）  
**計算量**: O(M) （M=気象データ日数）

**重要**: 近傍操作は不要（DPで解決済み）

---

### 次元4: Quantity（数量） - いくつ？

**最適化手法**: 離散候補 + 近傍操作

**前提**: コストモデルによる
- **固定コストのみ**: Quantity最適化は不要（常に100%が最適）
- **変動コストあり**: Quantity最適化が重要

**操作**:
- Q1. Increase/Decrease（増減）- ±10%, ±20%
- Q2. Optimize（最適化）- LPで厳密解

**品質**: 90-95%（離散候補）～100%（LP）  
**計算量**: O(n × L) （L=Quantityレベル数）

---

## 統合された最適化アルゴリズム

### 全体の流れ

```
┌─────────────────────────────────────────────────┐
│ Phase 1: 候補生成                                │
├─────────────────────────────────────────────────┤
│ for each (Field, Crop):                         │
│   Period ← DP最適化（厳密解、100%）★            │
│   Quantity ← 複数レベル（100%, 75%, 50%, 25%）★ │
│                                                 │
│ 候補: F × C × P × Q                             │
│ 例: 10 × 5 × 3 × 4 = 600候補                    │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ Phase 2: Greedy 選択                             │
├─────────────────────────────────────────────────┤
│ 利益率順に選択（制約内で）                       │
│                                                 │
│ Field, Crop, Period, Quantity の組み合わせ      │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ Phase 3: Local Search                           │
├─────────────────────────────────────────────────┤
│ Field の近傍:  F1.Move, F2.Swap                 │
│ Crop の近傍:   C1.Change, C3.Insert             │
│ Quantity の近傍: Q1.Adjust ★                    │
│                                                 │
│ Period: 候補から選び直すのみ（DP結果を活用）    │
└─────────────────────────────────────────────────┘
```

---

## コストモデルの重要性

### Model A: 固定コストのみ（現在の実装）

```python
cost = growth_days × field.daily_fixed_cost

特徴:
  - Quantityに無関係
  - 常に100%使用が最適
  - Quantity最適化は不要
```

### Model B: 混合コスト（推奨）

```python
cost = fixed_cost + variable_cost
     = (growth_days × field.fixed_daily_cost) +
       (growth_days × area_used × field.variable_cost_per_area)

特徴:
  - Quantityに依存
  - 最適Quantityが存在
  - Quantity最適化が重要 ★
```

### 実際の農業コスト

```
固定コスト（30-50%）:
  - 管理者人件費
  - 保険料
  - 固定資産税

変動コスト（50-70%）:
  - 肥料代（面積比例）
  - 農薬代（面積比例）
  - 収穫作業費（数量比例）
  - 灌漑費用（面積比例）
```

**結論**: **混合モデルが現実的** → **Quantity最適化が重要**

---

## 実装の優先順位（修正版）

### Phase 1: 基本実装（現状）

```
決定変数:
  Field: 近傍操作 ✓
  Crop:  近傍操作 ✓
  Period: DP ✓
  Quantity: 固定（100%）⚠️

品質: 85-95%
```

---

### Phase 2: Quantity候補の追加（Week 2-3）

```
決定変数:
  Field: 近傍操作 ✓
  Crop:  近傍操作 ✓
  Period: DP ✓
  Quantity: 離散候補（100%, 75%, 50%, 25%）★NEW

実装内容:
  1. Fieldエンティティの拡張（コスト分離）
  2. 候補生成でQuantity変動
  3. コスト計算の修正

工数: 3-5日
品質: 88-96% (+3-5%)
```

---

### Phase 3: Quantity調整の近傍操作（Week 4）

```
決定変数:
  Field: 近傍操作 ✓
  Crop:  近傍操作 ✓
  Period: DP ✓
  Quantity: 離散候補 + 近傍調整 ★NEW

実装内容:
  4. Quantity Adjustment操作
  5. 局所探索への統合

工数: 2日
品質: 90-97% (+1-2%)
```

---

### Phase 4: 連続最適化（将来）

```
決定変数:
  Field: 近傍操作 ✓
  Crop:  近傍操作 ✓
  Period: DP ✓
  Quantity: LP（連続最適化）★NEW

実装: オプション（厳密解が必要な場合）
工数: 5-7日
品質: 92-98% (+2-3%)
```

---

## 実装例

### Quantityを可変にした候補生成

```python
async def _generate_candidates_with_variable_quantity(
    self,
    fields: List[Field],
    request: MultiFieldCropAllocationRequestDTO,
) -> List[AllocationCandidate]:
    """Generate candidates with variable quantity levels."""
    candidates = []
    
    # Quantityレベルの定義
    QUANTITY_LEVELS = [1.0, 0.75, 0.5, 0.25]
    
    for field in fields:
        for crop_spec in request.crop_requirements:
            max_quantity = field.area / crop.area_per_unit
            
            # 各Quantityレベルで候補を生成
            for level in QUANTITY_LEVELS:
                quantity = max_quantity * level
                area_used = quantity * crop.area_per_unit
                
                # Period はDPで最適化（既存実装）
                period_result = await self.growth_period_optimizer.execute(
                    OptimalGrowthPeriodRequestDTO(
                        field_id=field.field_id,
                        crop_id=crop_spec.crop_id,
                        # ...
                    )
                )
                
                # 上位3Period候補のみ
                for period in period_result.candidates[:3]:
                    # コスト計算（混合モデル）
                    fixed_cost = period.growth_days * field.fixed_daily_cost
                    variable_cost = period.growth_days * area_used * field.variable_cost_per_area
                    total_cost = fixed_cost + variable_cost
                    
                    # 収益計算（数量比例）
                    revenue = quantity * crop.revenue_per_area * crop.area_per_unit
                    profit = revenue - total_cost
                    
                    candidates.append(AllocationCandidate(
                        field=field,
                        crop=crop,
                        quantity=quantity,  # ★ 可変
                        # ...
                    ))
    
    return candidates

# 候補数: F × C × P × Q = 10 × 5 × 3 × 4 = 600候補
```

---

## 期待される効果

### 品質向上

```
現状（Quantity固定）:
  品質: 85-95%

+ Quantity候補（4レベル）:
  品質: 88-96% (+3-5%)

+ Quantity調整（近傍操作）:
  品質: 90-97% (+1-2%)

+ Quantity連続最適化（LP）:
  品質: 92-98% (+2-3%)
```

### 計算時間への影響

```
候補生成:
  現状: 2秒
  + Quantity変動: 8秒（4倍）

対策:
  - 候補フィルタリング
  - Quantityレベルを2つに削減（100%, 50%）
  
改善後: 4秒（2倍に抑制）
```

---

## まとめ

### 重要な洞察

**Quantity = 面積比率の実体**

```
Ratio（抽象）: 30%, 50%, 20%
    ↓ 具体化
Quantity（実体）: 1200株, 1666株, 1000株
    ↓ 制約
Area（物理）: 300m², 500m², 200m²
```

### 最適化の4次元

```
1. Field（圃場）:   近傍操作（Swap, Move）
2. Crop（作物）:    近傍操作（Change, Insert）
3. Period（期間）:  ★DP（厳密解）
4. Quantity（数量）: 離散候補 + 近傍操作 ★NEW
```

### 実装の推奨

```
Week 2-3: Quantity候補の追加
  → 離散レベル（100%, 50%の2レベル）
  → コストモデルの明確化
  
Week 4: Quantity調整の近傍操作
  → ±10%, ±20%の微調整
  
期待効果: +4-7%
実装工数: 5-7日
```

**Quantityの最適化により、さらなる品質向上が可能です！**
