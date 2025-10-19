# xfailed/xpassed テスト分析

## 現状サマリー

- **XFAIL（失敗を期待、実際に失敗）**: 4件 ✅ 正当
- **XPASS（失敗を期待、実際に成功）**: 3件 ⚠️ 要対応

## 1. XFAIL - 失敗を期待し、実際に失敗（正当）

### 1.1 `test_session_cleanup_on_error`
**理由**: `Resource leak - session not cleaned up on error`

**正当性**: ✅ **正当**
- リソースリークの問題を文書化
- 実装が完了するまでxfailマークは適切
- セッションクリーンアップの実装待ち

**対応**: 将来実装予定（優先度: 中）

### 1.2 `test_partial_month_failure`
**理由**: `Error handling for partial failures not clear`

**正当性**: ✅ **正当**
- エラーハンドリングの仕様が未定義
- 部分的な成功をどう扱うかの設計が必要
- テストが仕様を文書化している

**対応**: 仕様決定後に実装（優先度: 低）

### 1.3 `test_duplicate_dates_in_csv`
**理由**: `Duplicate date handling not implemented`

**正当性**: ✅ **正当**
- JMAデータに重複がある可能性
- 処理方法の実装が必要（最初/最後/平均を取る、エラーを出すなど）

**対応**: データ品質向上のため実装推奨（優先度: 中）

### 1.4 `test_missing_required_columns`
**理由**: `Column validation not implemented`

**正当性**: ✅ **正当**
- 不完全なデータのハンドリング未実装
- 本番環境でのデータ品質保証に重要

**対応**: 実装推奨（優先度: 高）

---

## 2. XPASS - 失敗を期待したが成功（要対応）

### 2.1 `test_all_null_temperature_values`
**理由**: `Data quality validation not implemented yet`

**現状**: ⚠️ **テストが成功している**

**分析**:
- xfailマークがあるが、実際にはテストが成功
- データ品質検証が実装済みの可能性
- または、テストが正しく実装されていない可能性

**推奨対応**:
```python
# Option 1: 機能が実装済みなら xfail を削除
async def test_all_null_temperature_values(self, repository, mock_html_fetcher):
    # テスト実装

# Option 2: テストが不正確なら修正
@pytest.mark.xfail(reason="Data quality validation not implemented yet", strict=True)
async def test_all_null_temperature_values(self, repository, mock_html_fetcher):
    # strict=True で意図しない成功を検出
```

### 2.2 `test_distance_calculation_hokkaido_okinawa`
**理由**: `Euclidean distance used instead of Haversine`

**現状**: ⚠️ **テストが成功している**

**分析**:
- Haversine距離が実装済みの可能性
- または、テストの許容範囲が広すぎる可能性

**推奨対応**: 実装を確認し、xfailマークを削除

### 2.3 `test_year_boundary_crossing`
**理由**: `Year boundary crossing issue - January data not returned`

**現状**: ⚠️ **テストが成功している**

**分析**:
- 年境界の問題が修正済み
- テストは成功しているのでxfailマークは不要

**推奨対応**: xfailマークを削除

---

## 3. xfailed/xpassedの正当性評価

### 正当なxfail（保持すべき）: 4件
1. ✅ `test_session_cleanup_on_error` - 未実装機能を文書化
2. ✅ `test_partial_month_failure` - 仕様未定義を文書化
3. ✅ `test_duplicate_dates_in_csv` - 未実装機能を文書化
4. ✅ `test_missing_required_columns` - 未実装機能を文書化

### 不正なxfail（削除すべき）: 3件
1. ⚠️ `test_all_null_temperature_values` - 実装済み、xfailマーク削除すべき
2. ⚠️ `test_distance_calculation_hokkaido_okinawa` - 実装済み、xfailマーク削除すべき
3. ⚠️ `test_year_boundary_crossing` - 実装済み、xfailマーク削除すべき

---

## 4. 推奨アクション

### すぐに対応すべき（XPASSの解消）
1. 実装状況を確認
2. 実装済みならxfailマークを削除
3. 未実装なら`strict=True`を追加してテストを厳密化

### 将来対応すべき（XFAILの解消）
1. `test_missing_required_columns` - 優先度: 高
2. `test_duplicate_dates_in_csv` - 優先度: 中
3. `test_session_cleanup_on_error` - 優先度: 中
4. `test_partial_month_failure` - 優先度: 低（仕様決定待ち）

---

## 5. xfail使用のベストプラクティス

### ✅ 正当な使用
```python
@pytest.mark.xfail(reason="Known issue #123 - fix planned for v2.0")
def test_future_feature():
    # 実装予定の機能をテスト
    pass
```

### ❌ 不適切な使用
```python
@pytest.mark.xfail(reason="Broken test - ignoring for now")
def test_something():
    # 壊れたテストを無視するのは不適切
    pass
```

### 推奨: strict=True の使用
```python
@pytest.mark.xfail(reason="Feature not implemented", strict=True)
def test_future_feature():
    # strict=True で意図しない成功（XPASS）を検出
    pass
```

---

## まとめ

**正当性評価:**
- ✅ 現在のXFAIL（4件）は全て正当
- ⚠️ 現在のXPASS（3件）は要対応（実装済みなのにマークが残っている）

**次のステップ:**
1. XPASSテストのxfailマークを削除
2. 残りのXFAILテストの実装を計画


