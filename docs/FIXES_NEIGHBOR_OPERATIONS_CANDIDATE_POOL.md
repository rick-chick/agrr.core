# 近傍操作の候補プール検索への修正

## 方針
- 候補プール検索のみを使用（GDD再計算なし）
- 開始日が完全一致しない場合は最も近い候補を使用（許容誤差: 最大7日）
- Period Shift操作も実装（シフト後の開始日が候補プールになければスキップ）
- シフト量は外から設定可能（デフォルト: 7日）

---

## 修正が必要な箇所

### 1. BaseNeighborOperation - 共通ヘルパーメソッド追加
**ファイル**: `src/agrr_core/usecase/services/neighbor_operations/base_neighbor_operation.py`

**追加内容**:
- `_find_candidate_by_field_crop_date(candidates, field_id, crop_id, start_date, max_date_diff_days=7)` メソッド
  - 候補プールから(field_id, crop_id, start_date)で検索
  - 完全一致が見つからない場合は最も近い開始日の候補を返す
  - 最大7日以内の差の候補のみ許容、見つからなければNoneを返す

**理由**: 各操作で重複する候補検索ロジックを統一し、保守性を向上

---

### 2. FieldSwapOperation - 候補プール検索への修正
**ファイル**: `src/agrr_core/usecase/services/neighbor_operations/field_swap_operation.py`

**修正箇所**:
- `_swap_allocations_with_area_adjustment()` メソッド (77-159行)
  - 現在: 開始日・完了日・growth_daysをそのまま保持 (136-139, 150-153行)
  - 修正: 候補プールから`(alloc_b.field, alloc_a.crop, alloc_a.start_date)`の組み合わせで検索
  - 同様に`(alloc_a.field, alloc_b.crop, alloc_b.start_date)`も検索
  - 見つからない場合はNoneを返してスキップ

**影響**: 
- フィールド交換時に正確なGDD計算済みの期間情報を使用
- 期間の重なり判定が正確になる

---

### 3. PeriodShiftOperation - 新規実装
**ファイル**: `src/agrr_core/usecase/services/neighbor_operations/period_shift_operation.py` (新規作成)

**実装内容**:
- 開始日を±shift_days（デフォルト7日）シフト
- シフト後の開始日に対して候補プールから検索
- 見つからない場合はスキップ
- configから`period_shift_days`を取得（デフォルト7日）

**シフト方向**:
- +shift_days, -shift_days の両方向を試す

---

### 4. OptimizationConfig - シフト量設定の追加
**ファイル**: `src/agrr_core/usecase/dto/optimization_config.py`

**追加内容**:
- `period_shift_days: int = 7` フィールドを追加
  - Period Shift操作で使用するシフト日数
  - 外から設定可能

**操作の重み**に追加:
- `'period_shift': 0.1` を`operation_weights`に追加（デフォルト）

---

### 5. NeighborGeneratorService - PeriodShiftOperationの追加
**ファイル**: `src/agrr_core/usecase/services/neighbor_generator_service.py`

**修正箇所**:
- `_create_default_operations()` メソッド (53-64行)
  - `PeriodShiftOperation()`を追加
- import文に`PeriodShiftOperation`を追加

---

### 6. FieldMoveOperation - 開始日の近さを考慮した検索改善（オプション）
**ファイル**: `src/agrr_core/usecase/services/neighbor_operations/field_move_operation.py`

**現状**: 既に候補プール検索を使用しているが、開始日が異なる候補を選択している (68-77行)

**改善案**:
- 元の開始日に最も近い候補を優先的に選択
- 完全一致が見つからない場合も許容誤差（7日）内なら使用

**優先度**: 低（現状の実装でも動作はしているが、より正確な期間選択のため）

---

### 7. CropChangeOperation - 許容誤差の追加
**ファイル**: `src/agrr_core/usecase/services/neighbor_operations/crop_change_operation.py`

**現状**: 最も近い開始日の候補を選択しているが、**開始日の差に上限がない** (59-63行)
```python
# 現在の実装
best_candidate = min(
    similar_candidates,
    key=lambda c: abs((c.start_date - alloc.start_date).days)
)
```

**問題点**:
- 100日以上離れた候補でも選択されてしまう可能性がある
- 方針では「7日以内の許容誤差」としているので、これに準拠すべき

**修正内容**:
- 7日以内の差の候補のみを対象とする
- または共通ヘルパーメソッド`_find_candidate_by_field_crop_date()`を使用する（推奨）
- 見つからない場合はスキップ

**影響**: 
- 作物変更時に、より近い期間の候補のみを使用することで、期間の整合性が向上

---

## 実装順序（推奨）

1. **BaseNeighborOperation** - 共通ヘルパーを先に実装
2. **OptimizationConfig** - シフト量設定を追加
3. **FieldSwapOperation** - 最も重要な修正
4. **PeriodShiftOperation** - 新規実装
5. **NeighborGeneratorService** - PeriodShiftOperationを登録
6. **FieldMoveOperation** - 改善（オプション）

---

## テストが必要な箇所

### FieldSwapOperation
- フィールド交換時に候補プールに存在する開始日の場合
- フィールド交換時に候補プールに存在しない開始日（7日以内の差）の場合
- フィールド交換時に候補プールに存在しない開始日（7日以上差）の場合（スキップされることを確認）

### PeriodShiftOperation
- シフト後の開始日が候補プールに存在する場合
- シフト後の開始日が候補プールに存在しない場合（スキップされることを確認）
- +7日、-7日の両方向が正しく動作すること

### 共通ヘルパー
- 完全一致の候補が見つかる場合
- 7日以内の差の候補が見つかる場合
- 7日以上の差しかない場合（Noneが返されること）

---

## 注意事項

1. **パフォーマンス**: 候補プールの検索はO(n)だが、候補数が多い場合はインデックス化を検討
2. **一貫性**: 同じField×Crop×開始日の組み合わせは常に同じ結果になることを確認
3. **エッジケース**: 計画期間の境界付近でのシフト操作が正しく動作することを確認

