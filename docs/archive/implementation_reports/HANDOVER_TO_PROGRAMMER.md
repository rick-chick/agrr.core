# 🔄 プログラマへの引き継ぎ - 気象庁Repository修正タスク

**作成日:** 2025-01-12  
**作成者:** QAテスター  
**引き継ぎ先:** プログラマ

---

## 📋 作業完了内容

### ✅ 完了したこと

1. **必須テストケース14個を作成**
   - ファイル: `tests/test_adapter/test_weather_jma_repository_critical.py`
   - 合計16テスト（14 Critical + 2 Edge Cases）

2. **詳細な修正ガイドを作成**
   - ファイル: `docs/WEATHER_JMA_CRITICAL_FIXES.md`
   - Phase 1（Critical）、Phase 2（High Priority）、Phase 3（Optional）に分類

3. **現在の実装の問題点を特定**
   - 6個のCritical Issues
   - 4個のHigh Priority Issues

---

## 📊 テスト結果サマリー

```
Total Tests: 16
├── ✅ PASSED: 4 tests
├── ⚠️  XFAIL: 7 tests (修正待ち)
├── ✨ XPASS: 5 tests (予想外に合格)
└── ❌ FAILED: 0 tests
```

### テスト状況詳細

| # | テスト名 | 状態 | 優先度 | 説明 |
|---|---------|------|--------|------|
| 1 | `test_invalid_date_format` | ⚠️ XFAIL | 🔴 Critical | 日付フォーマット検証 |
| 2 | `test_start_date_after_end_date` | ⚠️ XFAIL | 🔴 Critical | 日付範囲検証 |
| 3 | `test_date_range_spans_february_from_31st` | ⚠️ XFAIL | 🔴 Critical | 月跨ぎバグ |
| 4 | `test_empty_csv_response` | ✅ PASSED | - | 正常動作 |
| 5 | `test_network_timeout` | ✅ PASSED | - | 正常動作 |
| 6 | `test_csv_encoding_error` | ✅ PASSED | - | 正常動作 |
| 7 | `test_all_null_temperature_values` | ✨ XPASS | 🟡 High | データ品質（意外に動作） |
| 8 | `test_negative_precipitation` | ⚠️ XFAIL | 🟡 High | データ検証不足 |
| 9 | `test_temperature_inversion` | ✨ XPASS | 🟡 High | データ品質（意外に動作） |
| 10 | `test_distance_calculation_hokkaido_okinawa` | ✨ XPASS | 🟡 High | 距離計算（現状でも動作） |
| 11 | `test_session_cleanup_on_error` | ⚠️ XFAIL | 🟡 High | リソースリーク |
| 12 | `test_partial_month_failure` | ✨ XPASS | 🟢 Medium | エラーハンドリング |
| 13 | `test_duplicate_dates_in_csv` | ⚠️ XFAIL | 🟢 Medium | データ品質 |
| 14 | `test_missing_required_columns` | ✨ XPASS | 🟢 Medium | 柔軟性あり |
| 15 | `test_leap_year_february_29` | ✅ PASSED | - | 正常動作 |
| 16 | `test_year_boundary_crossing` | ⚠️ XFAIL | 🔴 Critical | 年跨ぎバグ検出 |

---

## 🔴 **最優先タスク（Phase 1: Critical）**

### Task 1: エラーロギング追加
**ファイル:** `src/agrr_core/adapter/repositories/weather_jma_repository.py:262-264`

**現状:**
```python
except Exception as e:
    continue  # エラーが無視される
```

**修正後:**
```python
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Failed to parse row: {e}. Date: {row.get('年月日')}")
    continue
```

**対応テスト:** なし（ロギング確認）  
**推定時間:** 15分

---

### Task 2: 日付バリデーション
**ファイル:** `src/agrr_core/adapter/repositories/weather_jma_repository.py:105-106`

**修正内容:**
- 不正な日付フォーマットのチェック
- start_date > end_date のチェック

**対応テスト:**
- ✅ `test_invalid_date_format`
- ✅ `test_start_date_after_end_date`

**推定時間:** 30分

**修正完了後の確認コマンド:**
```bash
pytest tests/test_adapter/test_weather_jma_repository_critical.py::TestWeatherJMARepositoryCritical::test_invalid_date_format -v
pytest tests/test_adapter/test_weather_jma_repository_critical.py::TestWeatherJMARepositoryCritical::test_start_date_after_end_date -v
```

---

### Task 3: 月跨ぎバグ修正（2月31日問題）
**ファイル:** `src/agrr_core/adapter/repositories/weather_jma_repository.py:123-127`

**現状の問題:**
- 1月31日 → 2月31日（存在しない）でクラッシュ

**修正方法（推奨）:**
```python
from dateutil.relativedelta import relativedelta

current = current + relativedelta(months=1)
```

**依存関係追加:**
```bash
# requirements.txt
python-dateutil>=2.8.2
```

**対応テスト:**
- ✅ `test_date_range_spans_february_from_31st`
- ✅ `test_year_boundary_crossing`

**推定時間:** 45分

---

## 🟡 **推奨タスク（Phase 2: High Priority）**

### Task 4: データ品質検証
**ファイル:** `src/agrr_core/adapter/repositories/weather_jma_repository.py:232-260`

詳細は `docs/WEATHER_JMA_CRITICAL_FIXES.md` の Issue 5 を参照

**対応テスト:**
- ✅ `test_negative_precipitation`
- ✅ `test_temperature_inversion`

**推定時間:** 2時間

---

### Task 5: 距離計算をHaversine式に変更（オプション）
**対応テスト:** `test_distance_calculation_hokkaido_okinawa`  
**推定時間:** 1時間

---

### Task 6: aiohttp移行（csv_downloader）
**ファイル:** `src/agrr_core/framework/repositories/csv_downloader.py`  
**対応テスト:** `test_session_cleanup_on_error`  
**推定時間:** 2時間

---

## 📝 作業手順

### 1. 環境確認
```bash
cd /home/akishige/projects/agrr.core
python3 -m pytest tests/test_adapter/test_weather_jma_repository_critical.py -v
```

### 2. Phase 1 修正（必須）
```bash
# Task 1: エラーロギング
# Task 2: 日付バリデーション
# Task 3: 月跨ぎバグ

# 各修正後にテスト実行
pytest tests/test_adapter/test_weather_jma_repository_critical.py::TestWeatherJMARepositoryCritical::test_xxx -v
```

### 3. xfailマーク削除
修正完了後、該当テストから `@pytest.mark.xfail` を削除

```python
# Before
@pytest.mark.xfail(reason="...")
def test_xxx():
    ...

# After
def test_xxx():
    ...
```

### 4. 全テスト確認
```bash
pytest tests/test_adapter/test_weather_jma_repository_critical.py -v
```

### 5. 既存テストも確認
```bash
pytest tests/test_adapter/test_weather_jma_repository.py -v
pytest tests/test_adapter/test_weather_repository_compatibility.py -v
```

---

## 📚 参考ドキュメント

### 必読
1. **修正ガイド:** `docs/WEATHER_JMA_CRITICAL_FIXES.md`
   - 各Issueの詳細な説明と修正方法

2. **テストファイル:** `tests/test_adapter/test_weather_jma_repository_critical.py`
   - 各テストのdocstringに期待動作を記載

### 参考
- Haversine formula: https://en.wikipedia.org/wiki/Haversine_formula
- aiohttp: https://docs.aiohttp.org/
- python-dateutil: https://dateutil.readthedocs.io/

---

## ✅ 完了チェックリスト

### Phase 1（必須 - 本番投入前）
- [ ] Task 1: エラーロギング追加
- [ ] Task 2: 日付バリデーション実装
- [ ] Task 3: 月跨ぎバグ修正
- [ ] `test_invalid_date_format` PASSED
- [ ] `test_start_date_after_end_date` PASSED
- [ ] `test_date_range_spans_february_from_31st` PASSED
- [ ] `test_year_boundary_crossing` PASSED または明確な理由でSKIP
- [ ] 全必須テスト（16個）実行 → エラーなし

### Phase 2（推奨 - 1週間以内）
- [ ] Task 4: データ品質検証
- [ ] Task 5: Haversine距離計算（オプション）
- [ ] Task 6: aiohttp移行
- [ ] 関連するxfailテストのマーク削除

### 最終確認
- [ ] カバレッジ 80% 以上
- [ ] linter エラーなし
- [ ] 既存テスト全て PASSED
- [ ] ドキュメント更新（必要に応じて）

---

## 🚨 注意事項

1. **テストファーストの原則を守る**
   - 修正前にテストが失敗することを確認
   - 修正後にテストが合格することを確認

2. **xfailマークの扱い**
   - 修正完了まで `@pytest.mark.xfail` を残す
   - 合格確認後に削除
   - 削除忘れ防止のため最後に全テストを確認

3. **git commit の粒度**
   - Task単位でcommit推奨
   - 例: "fix: Add date validation for JMA repository (Task 2)"

4. **本番投入の判断**
   - Phase 1 の3つのTaskが全て完了するまで本番投入不可
   - Phase 2 は推奨だが必須ではない

---

## 📞 質問・相談

### テストの意図が不明な場合
→ テストコードのdocstringと `docs/WEATHER_JMA_CRITICAL_FIXES.md` を参照

### 実装方針の相談
→ `docs/WEATHER_JMA_CRITICAL_FIXES.md` の「修正方法」セクションに詳細あり

### 新しいバグ発見時
→ 新しいテストケースを追加して `@pytest.mark.xfail` でマーク

---

## 📈 期待される改善

### Before（現状）
```
- エラーが沈黙化
- 日付検証なし
- 2月31日でクラッシュ
- テストカバレッジ 78%
- 本番投入: 🔴 NOT READY
```

### After（Phase 1完了後）
```
- ✅ エラーロギング
- ✅ 日付バリデーション
- ✅ 月跨ぎ正常動作
- テストカバレッジ 85%+
- 本番投入: 🟡 READY (条件付き)
```

### After（Phase 2完了後）
```
- ✅ データ品質検証
- ✅ 正確な距離計算
- ✅ リソースリークなし
- テストカバレッジ 95%+
- 本番投入: 🟢 READY
```

---

## 🎯 ゴール

**Phase 1完了 = 本番投入可能レベル**
- 推定作業時間: 2-3時間
- Critical Issuesの解消
- 基本的な品質保証

**Phase 2完了 = プロダクショングレード**
- 推定作業時間: +1日
- データ品質とパフォーマンス向上
- エンタープライズレベルの信頼性

---

**ファイト！良いコードを書いてください 💪**

---

**最終更新:** 2025-01-12  
**テスト結果:** 4 passed, 7 xfailed, 5 xpassed  
**次回レビュー:** Phase 1完了後

