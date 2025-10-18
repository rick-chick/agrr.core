# max_temperature 実装方針の確定
**作成日**: 2025-10-14  
**決定**: max_temperatureは必須フィールド

---

## ✅ 確定した方針

### max_temperature は**必須フィールド**

**実装（現状のまま維持）**:
```python
# src/agrr_core/framework/repositories/crop_profile_file_repository.py
temp_data = stage_data['temperature']

temperature = TemperatureProfile(
    base_temperature=temp_data['base_temperature'],
    optimal_min=temp_data['optimal_min'],
    optimal_max=temp_data['optimal_max'],
    low_stress_threshold=temp_data.get('low_stress_threshold', temp_data['optimal_min']),
    high_stress_threshold=temp_data.get('high_stress_threshold', temp_data['optimal_max']),
    frost_threshold=temp_data.get('frost_threshold', 0.0),
    max_temperature=temp_data['max_temperature'],  # ✅ 必須フィールド（エラーを出す）
    sterility_risk_threshold=temp_data.get('sterility_risk_threshold')
)
```

---

## 🎯 設計思想

### 1. **明示的なエラー** ⭐

**方針**: `max_temperature`がない場合は**エラーを出す**

```python
# JSONに max_temperature がない場合
max_temperature=temp_data['max_temperature']
# → KeyError: 'max_temperature'  ← これが正しい動作
```

**理由**:
- ✅ データの不完全性を明確に示す
- ✅ ユーザーに明示的な対応を求める
- ✅ 暗黙の推定による予期しない動作を防ぐ

---

### 2. **自動推定は行わない** ⭐

**行わないこと**:
```python
# ❌ これはやらない
max_temperature=temp_data.get('max_temperature', high_stress + 7.0)
```

**理由**:
- 自動推定は誤差を含む（±2°C）
- ユーザーが気づかないうちに不正確な値を使う可能性
- データの品質を保証できない

---

### 3. **ユーザーの責任** ⭐

**期待される動作**:
1. 古いJSONファイルを読み込もうとする
2. エラーが発生: `KeyError: 'max_temperature'`
3. ユーザーがJSONに`max_temperature`を追加
4. 再度実行して成功

**メリット**:
- ✅ データの完全性が保証される
- ✅ ユーザーが意識的に値を設定する
- ✅ 予期しない動作がない

---

## 📊 動作の比較

### 現在の実装（確定）

```
古いJSONファイル（max_temperature なし）
    ↓
読み込み試行
    ↓
❌ KeyError: 'max_temperature'
    ↓
ユーザーがファイルを更新
    ↓
✅ 正常に動作
```

**特徴**:
- ✅ 明示的なエラー
- ✅ データの完全性保証
- ✅ 予測可能な動作

---

### 自動推定案（採用しない）

```
古いJSONファイル（max_temperature なし）
    ↓
読み込み試行
    ↓
自動推定（high_stress + 7.0）
    ↓
✅ 動作するが値が不正確
```

**問題点**:
- ❌ ユーザーが気づかない
- ❌ 誤差を含む値を使用
- ❌ 後で問題が発覚する可能性

---

## 🔍 具体例

### ケース1: 古いJSONファイル

**ファイル**: `rice_koshihikari.json`
```json
{
  "temperature": {
    "base_temperature": 10.0,
    "optimal_min": 25.0,
    "optimal_max": 30.0,
    "high_stress_threshold": 35.0
  }
}
```

**実行**:
```bash
$ agrr progress --crop-file rice_koshihikari.json --start-date 2024-05-01 ...
```

**結果**:
```
Error: KeyError: 'max_temperature'
File 'rice_koshihikari.json' is missing required field 'max_temperature'

Please add 'max_temperature' to your crop profile file.
Example:
  "temperature": {
    "base_temperature": 10.0,
    "optimal_min": 25.0,
    "optimal_max": 30.0,
    "high_stress_threshold": 35.0,
    "max_temperature": 42.0  ← Add this
  }
```

**ユーザーの対応**:
1. ファイルを開く
2. `max_temperature`を追加（推奨値: `high_stress + 7`）
3. 保存
4. 再実行

---

### ケース2: LLMによる新規作成

**コマンド**:
```bash
$ agrr crop --query "トマト Aiko" > tomato_aiko.json
```

**生成されるJSON**:
```json
{
  "temperature": {
    "base_temperature": 10.0,
    "optimal_min": 20.0,
    "optimal_max": 25.0,
    "high_stress_threshold": 32.0,
    "max_temperature": 35.0  ← LLMが自動生成
  }
}
```

**結果**: 常に完全な形式で生成される ✅

---

## 📝 エラーメッセージの改善（推奨）

### 現在のエラー

```python
KeyError: 'max_temperature'
```

### 改善案

```python
# src/agrr_core/framework/repositories/crop_profile_file_repository.py

try:
    max_temperature = temp_data['max_temperature']
except KeyError:
    raise ValueError(
        f"Missing required field 'max_temperature' in temperature profile.\n"
        f"Please add 'max_temperature' to your crop profile file.\n"
        f"Recommended value: {temp_data.get('high_stress_threshold', temp_data['optimal_max'])} + 7.0"
    )

temperature = TemperatureProfile(
    # ...
    max_temperature=max_temperature,
    # ...
)
```

**メリット**:
- ✅ より親切なエラーメッセージ
- ✅ 推奨値を提示
- ✅ ユーザーが対応しやすい

---

## 🎯 実装の完了状態

### 現在の実装（完璧）✅

**ファイル**: `src/agrr_core/framework/repositories/crop_profile_file_repository.py`

```python
# 行187
max_temperature=temp_data['max_temperature'],  # ✅ 必須フィールド
```

**状態**: **完璧に実装されている**

**必要な変更**: なし

---

## 📊 まとめ

### 確定事項

| 項目 | 決定 |
|------|------|
| **max_temperature** | 必須フィールド |
| **古いファイル** | エラーを出す |
| **自動推定** | 行わない |
| **ユーザー対応** | 手動で追加 |
| **現在の実装** | 正しい ✅ |

### 理由

1. ✅ **データの完全性**: 不完全なデータを許容しない
2. ✅ **明示性**: エラーで問題を明確に示す
3. ✅ **予測可能性**: 暗黙の推定を行わない
4. ✅ **品質保証**: ユーザーが意識的に値を設定

### 今後の対応

**実装**: 完了 ✅  
**変更**: 不要  
**オプション**: エラーメッセージの改善（推奨）

---

## 🚀 ユーザーガイド

### 既存ファイルの更新方法

**Step 1**: エラーを確認
```bash
$ agrr progress --crop-file rice.json ...
Error: KeyError: 'max_temperature'
```

**Step 2**: ファイルを更新
```json
{
  "temperature": {
    "base_temperature": 10.0,
    "optimal_min": 25.0,
    "optimal_max": 30.0,
    "high_stress_threshold": 35.0,
    "max_temperature": 42.0  ← 追加（推奨: high_stress + 7）
  }
}
```

**Step 3**: 再実行
```bash
$ agrr progress --crop-file rice.json ...
✓ Success
```

### 推奨値の計算

```
max_temperature = high_stress_threshold + 7.0

例:
- high_stress_threshold: 35.0°C
- max_temperature: 42.0°C (= 35.0 + 7.0)
```

---

## ✅ 結論

**現在の実装は正しい**: `max_temperature`を必須フィールドとして扱う

**自動推定は不要**: エラーを出してユーザーに対応を求める

**方針は明確**: データの完全性と明示性を優先

**実装は完了**: これ以上の変更は不要

---

**最終決定**: 現在の実装（必須フィールド）を維持する ✅

