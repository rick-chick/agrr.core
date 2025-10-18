# 近傍操作の実装計画：3次元アプローチ

## 全体像

```
決定変数: x[Field, Crop, Period, Quantity]

         Crop（作物）
          ↑ 何を？
          │
          │ 4操作
          │
Field ────●──── Period
（圃場）   │    （期間）
どこで？   │    いつ？
          │
    5操作 │ 5操作
          ↓
      Quantity
      （数量）
      いくつ？
```

---

## 📊 全操作の一覧表

### 次元1: 期間の近傍（Period Neighborhood）

| ID | 操作名 | 説明 | 効果 | 難易度 | 優先度 | 状態 | 実装工数 |
|----|--------|------|------|--------|--------|------|----------|
| **P1** | **Shift** | 時期シフト（±1週, ±2週） | ⭐⭐⭐⭐⭐ | 低 | **1位** | 🆕 | 2-3日 |
| P2 | Extend/Shrink | 期間の伸縮 | ⭐⭐⭐☆☆ | 中 | 6位 | 🆕 | 3-4日 |
| P3 | Split Period | 期間を2つに分割 | ⭐⭐☆☆☆ | 中 | 10位 | 🆕 | 4-5日 |
| P4 | Replace Period | 期間の完全置換 | ⭐⭐☆☆☆ | 低 | 8位 | ⚠️ | 1日 |
| P5 | Period Swap | 同一圃場内で期間入れ替え | ⭐⭐☆☆☆ | 中 | 9位 | 🆕 | 3日 |

**期待改善**: +5-8%  
**推奨実装**: P1（必須）、P4改善（推奨）

---

### 次元2: 圃場の近傍（Field Neighborhood）

| ID | 操作名 | 説明 | 効果 | 難易度 | 優先度 | 状態 | 実装工数 |
|----|--------|------|------|--------|--------|------|----------|
| **F1** | **Move** | 別の圃場へ移動 | ⭐⭐⭐⭐☆ | 中 | **3位** | 🆕 | 3-4日 |
| **F2** | **Field Swap** | 2つの割り当ての圃場交換 | ⭐⭐⭐⭐⭐ | 中 | **2位** | ✅ | - |
| F3 | Field Split | 圃場を分割利用 | ⭐⭐⭐☆☆ | 中 | 7位 | 🆕 | 4-5日 |
| F4 | Expand | 隣接圃場に拡張 | ⭐⭐☆☆☆ | 高 | 11位 | 🆕 | 5-7日 |
| F5 | Remove | 圃場から削除 | ⭐⭐⭐☆☆ | 低 | 5位 | ✅ | - |

**期待改善**: +3-5%  
**推奨実装**: F1（推奨）、F2（実装済み）

---

### 次元3: 作物の近傍（Crop Neighborhood）

| ID | 操作名 | 説明 | 効果 | 難易度 | 優先度 | 状態 | 実装工数 |
|----|--------|------|------|--------|--------|------|----------|
| C1 | Change Crop | 作物を別の作物に変更 | ⭐⭐⭐⭐☆ | 高 | 4位 | 🆕 | 4-5日 |
| C2 | Crop Swap | 2つの割り当ての作物交換 | ⭐⭐⭐☆☆ | 高 | 7位 | 🆕 | 4-5日 |
| **C3** | **Crop Insert** | 別の作物を追加 | ⭐⭐⭐⭐☆ | 中 | **4位** | 🆕 | 3-4日 |
| C4 | Crop Mix | 複数作物の混植 | ⭐⭐☆☆☆ | 高 | 12位 | 🆕 | 7-10日 |

**期待改善**: +2-4%  
**推奨実装**: C3（推奨）、C1（推奨）

---

### 補助操作: 数量の近傍（Quantity Neighborhood）

| ID | 操作名 | 説明 | 効果 | 難易度 | 優先度 | 状態 | 実装工数 |
|----|--------|------|------|--------|--------|------|----------|
| Q1 | Increase Quantity | 数量を増やす | ⭐⭐⭐☆☆ | 低 | 8位 | 🆕 | 2日 |
| Q2 | Decrease Quantity | 数量を減らす | ⭐⭐☆☆☆ | 低 | 10位 | 🆕 | 2日 |
| Q3 | Optimize Quantity | 最適な数量を計算 | ⭐⭐⭐☆☆ | 中 | 9位 | 🆕 | 3-4日 |

**期待改善**: +1-2%

---

## 優先度順の実装計画

### 総合ランキング（効果 × 実装容易性）

| 順位 | 次元 | 操作 | 効果 | 難易度 | 工数 | 累積品質 | 状態 |
|------|------|------|------|--------|------|---------|------|
| **1** | **Period** | **P1. Shift** | ⭐⭐⭐⭐⭐ | 低 | 2-3日 | **90-93%** | 🆕 |
| 2 | Field | F2. Field Swap | ⭐⭐⭐⭐⭐ | 中 | - | - | ✅ |
| **3** | **Field** | **F1. Move** | ⭐⭐⭐⭐☆ | 中 | 3-4日 | **92-94%** | 🆕 |
| **4** | **Crop** | **C3. Crop Insert** | ⭐⭐⭐⭐☆ | 中 | 3-4日 | **93-95%** | 🆕 |
| 4 | Crop | C1. Change Crop | ⭐⭐⭐⭐☆ | 高 | 4-5日 | 93-96% | 🆕 |
| 5 | Field | F5. Remove | ⭐⭐⭐☆☆ | 低 | - | - | ✅ |
| 6 | Period | P2. Extend/Shrink | ⭐⭐⭐☆☆ | 中 | 3-4日 | 94-96% | 🆕 |
| 7 | Field | F3. Field Split | ⭐⭐⭐☆☆ | 中 | 4-5日 | 94-97% | 🆕 |
| 7 | Crop | C2. Crop Swap | ⭐⭐⭐☆☆ | 高 | 4-5日 | 94-97% | 🆕 |
| 8 | Period | P4. Replace | ⭐⭐☆☆☆ | 低 | 1日 | - | ⚠️ |
| 9 | Period | P5. Period Swap | ⭐⭐☆☆☆ | 中 | 3日 | 95-97% | 🆕 |
| 10 | Quantity | Q1-Q3 | ⭐⭐☆☆☆ | 低-中 | 2-4日 | 95-97% | 🆕 |

---

## 詳細実装計画

### Phase 1: 期間の最適化（Week 1）🔥

**目標**: 期間次元での最適化を完成させる

#### Day 1-2: P1. Shift実装

```python
def _shift_operation(
    allocation: CropAllocation,
    shift_days: int,
    candidates: List[AllocationCandidate]
) -> Optional[CropAllocation]:
    """
    時期をshift_days日シフトする
    
    固定: Field, Crop, Quantity
    変更: Period (start_date, completion_date)
    """
    new_start = allocation.start_date + timedelta(days=shift_days)
    
    # 同じ圃場・同じ作物で最も近い候補を探す
    best_candidate = find_closest_candidate(
        candidates,
        field=allocation.field,
        crop=allocation.crop,
        target_date=new_start,
        tolerance=7  # 7日以内
    )
    
    if best_candidate is None:
        return None
    
    # 数量・面積は維持、コストのみ再計算
    new_cost = best_candidate.growth_days * allocation.field.daily_fixed_cost
    
    return create_allocation_with_new_period(allocation, best_candidate, new_cost)
```

**テストケース**:
- ✓ 基本的なシフト（±7日、±14日）
- ✓ シフト後の実行可能性チェック
- ✓ コストの再計算
- ✓ 時間的衝突の回避

#### Day 3: P4. Replace改善

```python
# 候補数を3→10に増加
for candidate in similar_candidates[:10]:  # 3→10
    neighbor = solution.copy()
    neighbor[i] = self._candidate_to_allocation(candidate)
    neighbors.append(neighbor)
```

#### Day 4: テストと品質評価

**期待結果**: 品質 85-90% → 90-93%

---

### Phase 2: 圃場の最適化（Week 2）

**目標**: 圃場次元での最適化を完成させる

#### Day 5-7: F1. Move実装

```python
def _move_operation(
    allocation: CropAllocation,
    target_field: Field,
    used_area_in_target: float,
) -> Optional[CropAllocation]:
    """
    別の圃場に移動
    
    固定: Crop, Period
    変更: Field
    調整: Quantity（空き容量に応じて）
    """
    available_area = target_field.area - used_area_in_target
    original_area = allocation.quantity * allocation.crop.area_per_unit
    
    # 空き容量に収まるように調整
    area_to_use = min(original_area, available_area)
    new_quantity = area_to_use / allocation.crop.area_per_unit
    
    # コスト再計算
    new_cost = allocation.growth_days * target_field.daily_fixed_cost
    
    return create_allocation_in_new_field(allocation, target_field, new_quantity, new_cost)
```

#### Day 8-9: テストと品質評価

**期待結果**: 品質 90-93% → 92-95%

---

### Phase 3: 作物の最適化（Week 3）

**目標**: 作物次元での最適化を完成させる

#### Day 10-12: C3. Crop Insert実装

```python
def _crop_insert_operation(
    solution: List[CropAllocation],
    candidates: List[AllocationCandidate],
) -> List[List[CropAllocation]]:
    """
    新しい作物を追加
    
    固定: Field（空き容量の範囲内）
    変更: Crop, Period
    """
    neighbors = []
    
    # 各圃場の空き容量と空き時間を計算
    field_availability = calculate_availability(solution)
    
    # 未使用の候補から追加可能なものを探す
    for candidate in unused_candidates:
        if fits_in_field(candidate, field_availability):
            neighbor = solution + [candidate_to_allocation(candidate)]
            neighbors.append(neighbor)
    
    return neighbors
```

#### Day 13-15: C1. Change Crop実装

```python
def _change_crop_operation(
    allocation: CropAllocation,
    new_crop: Crop,
    candidates: List[AllocationCandidate],
) -> Optional[CropAllocation]:
    """
    作物を変更
    
    固定: Field, Period（できるだけ近い期間）
    変更: Crop
    調整: Quantity（面積等価）
    """
    # 同じ面積を維持
    original_area = allocation.quantity * allocation.crop.area_per_unit
    new_quantity = original_area / new_crop.area_per_unit
    
    # 同じ圃場・近い時期の候補を探す
    similar_candidate = find_similar_candidate(
        candidates,
        field=allocation.field,
        crop=new_crop,
        target_date=allocation.start_date,
    )
    
    return create_allocation_with_new_crop(allocation, new_crop, new_quantity, similar_candidate)
```

#### Day 16-17: テストと統合

**期待結果**: 品質 92-95% → 94-96%

---

## 操作の詳細比較表

### 次元1: 期間（Period）

| 操作 | 固定 | 変更 | 面積調整 | 数量調整 | コスト再計算 | 例 |
|------|------|------|---------|---------|------------|-----|
| **P1. Shift** | Field, Crop, Qty | Period | なし | なし | ✓ | 4/1→4/15 |
| P2. Extend | Field, Crop | Period | なし | なし | ✓ | 153日→168日 |
| P3. Split | Field, Crop | Period | ✓ 分割 | ✓ 分割 | ✓ | 1期→2期 |
| P4. Replace | Field, Crop | Period | なし | なし | ✓ | 4/1→5/1 |
| P5. Period Swap | Field | Period | なし | なし | ✓ | 前期⟷後期 |

### 次元2: 圃場（Field）

| 操作 | 固定 | 変更 | 面積調整 | 数量調整 | コスト再計算 | 例 |
|------|------|------|---------|---------|------------|-----|
| **F1. Move** | Crop, Period | Field | ✓ 空き容量 | ✓ 可能 | ✓ | A→B |
| **F2. Field Swap** | Crop, Period | Field | ✓ 等価 | ✓ 必須 | ✓ | A⟷B |
| F3. Field Split | Period | Field, Crop | ✓ 分割 | ✓ 分割 | - | 1圃場→2区画 |
| F4. Expand | Crop, Period | Field | ✓ 拡大 | ✓ 増加 | ✓ | A→A+B |
| F5. Remove | - | - | - | - | - | 削除 |

### 次元3: 作物（Crop）

| 操作 | 固定 | 変更 | 面積調整 | 数量調整 | コスト再計算 | 例 |
|------|------|------|---------|---------|------------|-----|
| C1. Change Crop | Field, Period | Crop | ✓ 等価 | ✓ 必須 | ✓ | Rice→Tomato |
| C2. Crop Swap | Period | Crop, Field | ✓ 等価 | ✓ 必須 | ✓ | A:Rice⟷B:Tomato |
| **C3. Crop Insert** | Field（空き） | Crop, Period | ✓ 制約内 | ✓ 制約内 | ✓ | +Tomato |
| C4. Crop Mix | Field, Period | Crop | ✓ 分割 | ✓ 分割 | - | Rice+Wheat |

---

## 実装の段階的ロードマップ

### Week 1: Period最適化（最優先）

**実装**:
- ✅ P1. Shift（2-3日）
- ✅ P4. Replace改善（1日）

**テスト**:
- 小規模データ（3圃場×2作物）
- 中規模データ（10圃場×5作物）

**目標品質**: 90-93%

---

### Week 2: Field最適化

**実装**:
- ✅ F1. Move（3-4日）

**テスト**:
- 圃場数を増やしたテスト
- コスト差のある圃場でのテスト

**目標品質**: 92-95%

---

### Week 3: Crop最適化

**実装**:
- ✅ C3. Crop Insert（3-4日）
- ✅ C1. Change Crop（オプション、4-5日）

**テスト**:
- 作物数を増やしたテスト
- 収益性が異なる作物でのテスト

**目標品質**: 94-96%

---

### Week 4: 統合とチューニング

**実装**:
- 複合操作の実験
- パラメータチューニング
- パフォーマンス最適化

**目標品質**: 95-97%

---

## 面積調整の統一ルール

### ルール1: 面積等価の原則

```python
# 次元を変更する際は、面積を適切に調整
new_quantity = target_area / new_crop.area_per_unit
```

### ルール2: 容量制約

```python
# 圃場の容量を超えない
allocated_area ≤ field.area
```

### ルール3: 数量の非負性

```python
# 数量は常に正
quantity > 0
```

---

## 次元ごとの効果と実装コスト

```
              効果    実装コスト
Period    ■■■■■      ▓▓░░░
Field     ■■■■░      ▓▓▓░░
Crop      ■■■░░      ▓▓▓▓░
Quantity  ■■░░░      ▓░░░░

凡例:
■ = 高い効果
▓ = 高い実装コスト
```

### 費用対効果（ROI）

```
1. Period: 効果大、コスト小 → ROI: 最高 ★★★★★
2. Field:  効果中、コスト中 → ROI: 高 ★★★★☆
3. Crop:   効果中、コスト大 → ROI: 中 ★★★☆☆
4. Quantity: 効果小、コスト小 → ROI: 中 ★★★☆☆
```

---

## まとめ

### 3次元の体系的分類

決定変数の各次元に対応した近傍操作を体系的に整理しました：

1. **期間の近傍（5操作）**: 最も効果的（+5-8%）
2. **圃場の近傍（5操作）**: 次に効果的（+3-5%）
3. **作物の近傍（4操作）**: 補完的（+2-4%）

### 推奨実装順序

```
Week 1: P1.Shift（最優先、期間次元）
Week 2: F1.Move（圃場次元）
Week 3: C3.Crop Insert（作物次元）
```

### 期待される品質向上

```
現状:   85-90% ████████████████░░░░
  ↓ Week 1 (+P1.Shift)
Phase 1: 90-93% ███████████████████░
  ↓ Week 2 (+F1.Move)
Phase 2: 92-95% ████████████████████░
  ↓ Week 3 (+C3.Insert)
Phase 3: 94-96% █████████████████████
```

この3次元アプローチにより、各次元で独立して最適化を進め、段階的に解の品質を向上させることができます。

**次のアクション**: P1. Shift操作の実装から開始することを強く推奨します！

