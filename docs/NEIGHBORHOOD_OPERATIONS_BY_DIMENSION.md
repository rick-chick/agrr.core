# 近傍操作の3次元分類：作物・期間・圃場

## 概要

最適化問題の決定変数は**3つの次元**を持ちます：

```
決定変数: x[field, crop, period]
├─ Field（圃場）: どの圃場で栽培するか
├─ Crop（作物）: 何の作物を栽培するか
└─ Period（期間）: いつ栽培するか（開始日・完了日）

+ Quantity（数量）: 何個栽培するか
```

それぞれの次元で独立した**近傍操作**が定義できます。

---

## 次元1: 作物の近傍（Crop Neighborhood）

### 定義
**同じ圃場・同じ期間**で、**作物だけを変更**する操作

```
固定: Field, Period
変更: Crop
```

---

### C1. Change Crop（作物変更）

**操作**:
```python
Before:
  Field A, 4/1-8/31: Rice 2000株 (500m²)

After:
  Field A, 4/1-8/31: Tomato 1666.67株 (500m²)
  # 同じ圃場、同じ期間、作物だけ変更
```

**面積調整**:
```python
# 同じ面積を維持
original_area = quantity_old × crop_old.area_per_unit
new_quantity = original_area / crop_new.area_per_unit
```

**ユースケース**:
- 市場価格の変動に対応
- より高収益な作物への変更
- 需要の変化に対応

**計算量**: O(n × C) （C=作物種類数）

---

### C2. Crop Swap（作物の入れ替え）

**操作**:
```python
Before:
  Field A, 4/1-8/31: Rice 2000株 (500m²)
  Field B, 4/1-8/31: Tomato 1000株 (300m²)

After:
  Field A, 4/1-8/31: Tomato 1666.67株 (500m²)
  Field B, 4/1-8/31: Rice 1200株 (300m²)
  # 2つの割り当ての作物を交換
```

**面積調整**:
```python
# 各圃場の元の面積を維持
new_quantity_a = area_a / crop_b.area_per_unit
new_quantity_b = area_b / crop_a.area_per_unit
```

**ユースケース**:
- 作物と圃場の相性を最適化
- 土壌条件に合わせた作物配置
- 連作障害の回避

**計算量**: O(n²)

---

### C3. Crop Insert（作物の追加）

**操作**:
```python
Before:
  Field A, 4/1-8/31: Rice 2000株 (500m², 500m²空き)

After:
  Field A, 4/1-8/31: Rice 2000株 (500m²)
          9/1-12/31: Tomato 1666.67株 (500m²)
  # 別の期間に別の作物を追加
```

**制約**:
```python
# 時間的重複なし
period_a.end < period_b.start

# 面積制約
area_a + area_b ≤ field.area
```

**ユースケース**:
- 作物多様性の向上
- 年間作付け回数の増加
- リスク分散

**計算量**: O(n × C × P) （P=期間候補数）

---

### C4. Crop Mix（作物の混植）

**操作**:
```python
Before:
  Field A, 4/1-8/31: Rice 2000株 (500m²)

After:
  Field A, 4/1-8/31: Rice 1000株 (250m²) + Wheat 1250株 (250m²)
  # 同じ期間に複数作物を混植
```

**面積調整**:
```python
# 総面積を分割
area_total = original_area
area_crop1 + area_crop2 + ... = area_total
```

**ユースケース**:
- コンパニオンプランティング
- リスク分散
- 土地の有効活用

**計算量**: O(n × 2^C)

**注意**: 複雑度が高いため、Phase 3以降の実装

---

## 次元2: 期間の近傍（Period Neighborhood）

### 定義
**同じ圃場・同じ作物**で、**期間（タイミング）だけを変更**する操作

```
固定: Field, Crop
変更: Period (start_date, end_date)
```

---

### P1. Shift（時期シフト）★ 最重要

**操作**:
```python
Before:
  Field A: Rice 2000株, 4/1-8/31 (153日)

After:
  Field A: Rice 2000株, 4/15-9/15 (154日)
  # 2週間後ろにシフト
```

**面積調整**: なし（数量・面積は維持）

**シフト候補**:
```python
shift_days = [-14, -7, -3, -1, +1, +3, +7, +14]
# または連続的な範囲
```

**ユースケース**:
- より有利な気象条件を利用
- 霜害リスクの回避
- 他の作物との時間的衝突回避
- 収穫時期の分散

**計算量**: O(n × S) （S=シフト候補数）

**効果**: 最も効果的（+5%以上の改善）

---

### P2. Extend/Shrink（期間の伸縮）

**操作**:
```python
Before:
  Field A: Rice 2000株, 4/1-8/31 (153日)

After:
  Field A: Rice 2000株, 4/1-9/15 (168日)
  # 完了日を延長（より多くのGDD蓄積）
```

**面積調整**: なし

**制約**:
```python
# 生育に必要な最小GDD
accumulated_gdd >= required_gdd

# 圃場の利用可能期間
period.end ≤ next_allocation.start
```

**ユースケース**:
- GDD蓄積の最適化
- 品質向上のための期間延長
- 早期収穫による期間短縮

**計算量**: O(n × E) （E=伸縮候補数）

---

### P3. Split Period（期間分割）

**操作**:
```python
Before:
  Field A: Rice 4000株, 4/1-8/31 (500m²全体)

After:
  Field A: Rice 2000株, 4/1-6/30 (250m²)
          Rice 2000株, 7/1-10/31 (250m²)
  # 同じ作物を異なる期間に分割
```

**面積調整**:
```python
# 総数量を分割
quantity_1 + quantity_2 = original_quantity

# 面積も分割
area_1 + area_2 = original_area
```

**ユースケース**:
- 収穫時期の分散
- リスク分散（気象変動）
- 労働力の平準化

**計算量**: O(n × P²)

---

### P4. Replace Period（期間置換）

**操作**:
```python
Before:
  Field A: Rice 2000株, 4/1-8/31

After:
  Field A: Rice 2000株, 5/1-9/30
  # 完全に異なる期間に置換
```

**面積調整**: なし（数量維持）

**ユースケース**:
- 大幅な時期変更
- 季節の最適化
- 既存実装のReplace操作に相当

**計算量**: O(n × P)

---

### P5. Period Swap（期間の入れ替え）

**操作**:
```python
Before:
  Field A: Rice 2000株, 4/1-8/31
  Field A: Tomato 1666株, 9/1-12/31

After:
  Field A: Tomato 1666株, 4/1-7/31
  Field A: Rice 2000株, 8/1-12/31
  # 同じ圃場内で栽培順序を入れ替え
```

**面積調整**: なし

**ユースケース**:
- 栽培順序の最適化
- 前作・後作の組み合わせ最適化
- 連作障害の回避

**計算量**: O(n²)

---

## 次元3: 圃場の近傍（Field Neighborhood）

### 定義
**同じ作物・同じ期間**で、**圃場だけを変更**する操作

```
固定: Crop, Period
変更: Field
```

---

### F1. Move to Different Field（圃場移動）

**操作**:
```python
Before:
  Field A (5000円/日): Rice 2000株, 4/1-8/31 (500m²)

After:
  Field B (4000円/日): Rice 2000株, 4/1-8/31 (500m²)
  # より低コストな圃場へ移動
```

**面積調整**:
```python
# 目標: 元の面積を維持
original_area = quantity × crop.area_per_unit

# 新しい圃場の空き容量をチェック
available_area = field_new.area - used_area_new

if available_area >= original_area:
    new_quantity = quantity  # そのまま移動
else:
    new_quantity = available_area / crop.area_per_unit  # 縮小
```

**ユースケース**:
- より低コストな圃場への移動
- より適した土壌条件の圃場へ移動
- 圃場間の負荷分散

**計算量**: O(n × F) （F=圃場数）

---

### F2. Field Swap（圃場の入れ替え）★ 実装済み

**操作**:
```python
Before:
  Field A (5000円/日): Rice 2000株, 4/1-8/31 (500m²)
  Field B (6000円/日): Tomato 1000株, 4/1-7/31 (300m²)

After:
  Field A (5000円/日): Tomato 1666.67株, 4/1-7/31 (500m²)
  Field B (6000円/日): Rice 1200株, 4/1-8/31 (300m²)
  # 2つの割り当ての圃場を交換
```

**面積調整**:
```python
# 各割り当ての元の面積を維持
new_quantity_a = area_a / crop_a.area_per_unit
new_quantity_b = area_b / crop_b.area_per_unit
```

**ユースケース**:
- コスト構造の最適化
- 作物と圃場の相性最適化
- 圃場利用の効率化

**計算量**: O(n²)

**状態**: ✅ 実装済み（面積等価版）

---

### F3. Field Split（圃場の分割利用）

**操作**:
```python
Before:
  Field A (1000m²): Rice 4000株 (1000m²全体使用)

After:
  Field A (1000m²): Rice 2000株 (500m²)
                   Tomato 1666株 (500m²)
  # 同じ圃場を複数の割り当てで分割利用
```

**面積調整**:
```python
# 圃場を分割
area_1 + area_2 + ... ≤ field.area

# 各割り当ての数量
quantity_1 = area_1 / crop_1.area_per_unit
quantity_2 = area_2 / crop_2.area_per_unit
```

**ユースケース**:
- 圃場の有効活用
- 作物多様性の向上
- リスク分散

**計算量**: O(n × F × C)

---

### F4. Expand to Adjacent Field（隣接圃場への拡張）

**操作**:
```python
Before:
  Field A (1000m²): Rice 4000株 (1000m²全部使用)
  Field B (1000m²): [空き]

After:
  Field A+B (2000m²): Rice 8000株 (2000m²使用)
  # 隣接する圃場に拡張
```

**面積調整**:
```python
# 複数圃場の合計面積
total_area = field_a.area + field_b.area
max_quantity = total_area / crop.area_per_unit
```

**ユースケース**:
- 大規模栽培への対応
- 連続した圃場での効率的栽培
- 機械化対応

**計算量**: O(n × F²)

**注意**: 圃場の隣接関係のデータが必要

---

### F5. Field Remove（圃場からの削除）

**操作**:
```python
Before:
  Field A: Rice 2000株, 4/1-8/31

After:
  Field A: [empty]
  # この割り当てを完全に削除
```

**面積調整**: 削除により面積が空く

**ユースケース**:
- 不採算な割り当ての除去
- 制約違反の解消
- 他の割り当てのためのスペース確保

**計算量**: O(n)

**状態**: ✅ 実装済み（Remove操作）

---

## 複合操作（Multi-Dimensional）

### M1. Field + Crop Swap（圃場と作物の同時交換）

**操作**:
```
x[Field A, Rice, Period 1] ⟷ x[Field B, Tomato, Period 2]

変更: Field + Crop
固定: なし
```

**例**:
```python
Before:
  Field A: Rice, 4/1-8/31
  Field B: Tomato, 9/1-12/31

After:
  Field A: Tomato, 9/1-12/31
  Field B: Rice, 4/1-8/31
```

---

### M2. Crop + Period Change（作物と期間の同時変更）

**操作**:
```
x[Field A, Rice, Period 1] → x[Field A, Tomato, Period 2]

固定: Field
変更: Crop + Period
```

**例**:
```python
Before:
  Field A: Rice, 4/1-8/31

After:
  Field A: Tomato, 5/1-9/30
```

---

### M3. Field + Period Change（圃場と期間の同時変更）

**操作**:
```
x[Field A, Rice, Period 1] → x[Field B, Rice, Period 2]

固定: Crop
変更: Field + Period
```

**例**:
```python
Before:
  Field A: Rice, 4/1-8/31

After:
  Field B: Rice, 5/1-9/30
```

---

### M4. Full Change（全次元の変更）

**操作**:
```
x[Field A, Rice, Period 1] → x[Field B, Tomato, Period 2]

変更: Field + Crop + Period
```

**注意**: 制約が緩すぎて効率的な探索が困難

---

## 次元別の操作サマリー

### 作物の近傍（Crop Neighborhood）

| 操作 | 説明 | 優先度 | 状態 |
|------|------|--------|------|
| **C1. Change Crop** | 作物変更 | ⭐⭐⭐⭐☆ | 🆕 |
| **C2. Crop Swap** | 作物入れ替え | ⭐⭐⭐☆☆ | 🆕 |
| **C3. Crop Insert** | 作物追加 | ⭐⭐⭐⭐☆ | 🆕 |
| **C4. Crop Mix** | 作物混植 | ⭐⭐☆☆☆ | Phase 3 |

### 期間の近傍（Period Neighborhood）

| 操作 | 説明 | 優先度 | 状態 |
|------|------|--------|------|
| **P1. Shift** | 時期シフト | ⭐⭐⭐⭐⭐ | 🆕 最重要 |
| **P2. Extend/Shrink** | 期間伸縮 | ⭐⭐⭐☆☆ | 🆕 |
| **P3. Split Period** | 期間分割 | ⭐⭐☆☆☆ | Phase 3 |
| **P4. Replace Period** | 期間置換 | ⭐⭐☆☆☆ | ⚠️ 実装済み |
| **P5. Period Swap** | 期間入れ替え | ⭐⭐☆☆☆ | 🆕 |

### 圃場の近傍（Field Neighborhood）

| 操作 | 説明 | 優先度 | 状態 |
|------|------|--------|------|
| **F1. Move** | 圃場移動 | ⭐⭐⭐⭐☆ | 🆕 |
| **F2. Field Swap** | 圃場入れ替え | ⭐⭐⭐⭐⭐ | ✅ 実装済み |
| **F3. Field Split** | 圃場分割利用 | ⭐⭐⭐☆☆ | 🆕 |
| **F4. Expand** | 隣接圃場拡張 | ⭐⭐☆☆☆ | Phase 3 |
| **F5. Remove** | 削除 | ⭐⭐⭐⭐☆ | ✅ 実装済み |

---

## 実装の優先順位

### Phase 1: 各次元の最重要操作（1週間）

```
期間: P1. Shift ⭐⭐⭐⭐⭐ （最優先！）
圃場: F2. Field Swap ✅ （実装済み）
圃場: F5. Remove ✅ （実装済み）
期間: P4. Replace Period ⚠️ （改善が必要）
```

**期待品質**: 85-90% → **90-93%**

---

### Phase 2: 各次元の補完操作（2週間）

```
圃場: F1. Move（圃場移動）
作物: C1. Change Crop（作物変更）
作物: C3. Crop Insert（作物追加）
```

**期待品質**: 90-93% → **92-96%**

---

### Phase 3: 高度な操作（3週間以降）

```
作物: C2. Crop Swap
期間: P2. Extend/Shrink
圃場: F3. Field Split
複合: M1-M4
```

**期待品質**: 92-96% → **95-98%**

---

## 次元ごとの効果分析

### 期間の近傍（Period）: 効果最大

**理由**:
- 気象条件に直接影響
- GDD蓄積の最適化
- 時間的衝突の解消
- 既存の候補データを活用可能

**期待改善**: +5-7%

---

### 圃場の近傍（Field）: 効果中

**理由**:
- コスト構造の最適化
- 圃場の適性活用
- 負荷分散

**期待改善**: +3-5%

---

### 作物の近傍（Crop）: 効果中～小

**理由**:
- 市場対応
- 収益性の向上
- リスク分散

**期待改善**: +2-4%

---

## まとめ

### 3次元の体系的分類

```
決定変数 x[Field, Crop, Period, Quantity]
         │      │      │        │
         │      │      │        └─ 連続変数（調整）
         │      │      └────────── 期間の近傍（5操作）
         │      └───────────────── 作物の近傍（4操作）
         └──────────────────────── 圃場の近傍（5操作）

合計: 14操作 + 複合操作
```

### 実装の優先順位

1. **期間の近傍**: P1. Shift（最優先、+5-7%改善）
2. **圃場の近傍**: F1. Move、F2. Swap（+3-5%改善）
3. **作物の近傍**: C1. Change Crop、C3. Insert（+2-4%改善）

### 期待される品質向上

```
現状: 85-90%
  ↓ Phase 1（期間最適化）
90-93% (+3-5%)
  ↓ Phase 2（圃場+作物最適化）
92-96% (+2-3%)
  ↓ Phase 3（高度な操作）
95-98% (+1-3%)
```

この3次元分類により、各操作の役割と効果が明確になり、体系的な実装が可能になります。

