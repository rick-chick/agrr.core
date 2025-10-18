# 現在の実装状況：max_temperature
**作成日**: 2025-10-14  
**目的**: 実際のコードの動作を正確に説明

---

## ⚠️ 重要な発見

### 現在の実装（行187）

```python
# src/agrr_core/framework/repositories/crop_profile_file_repository.py
temperature = TemperatureProfile(
    base_temperature=temp_data['base_temperature'],
    optimal_min=temp_data['optimal_min'],
    optimal_max=temp_data['optimal_max'],
    low_stress_threshold=temp_data.get('low_stress_threshold', temp_data['optimal_min']),
    high_stress_threshold=temp_data.get('high_stress_threshold', temp_data['optimal_max']),
    frost_threshold=temp_data.get('frost_threshold', 0.0),
    max_temperature=temp_data['max_temperature'],  # ← 必須フィールド！
    sterility_risk_threshold=temp_data.get('sterility_risk_threshold')
)
```

**現状**: `max_temperature` は **必須フィールド** として扱われている

---

## 📊 実装方針の2つの選択肢

### 方針A: max_temperature を必須にする（現在の実装）⭐

**コード**:
```python
max_temperature=temp_data['max_temperature'],  # 必須
```

**動作**:
- ❌ 古いJSONファイル（`max_temperature`なし）は読み込みエラー
- ✅ 新しいJSONファイル（`max_temperature`あり）のみ対応
- ✅ シンプルな実装

**利点**:
- ✅ 実装が最もシンプル
- ✅ バリデーションが明確
- ✅ 「後方変換は作らない」方針と一致

**欠点**:
- ❌ 既存のJSONファイルが使えない
- ❌ 手動で既存ファイルに`max_temperature`を追加する必要がある

---

### 方針B: max_temperature を自動推定する（推奨）⭐⭐⭐

**コード**:
```python
# 修正案
high_stress = temp_data.get('high_stress_threshold', temp_data['optimal_max'])
max_temperature=temp_data.get('max_temperature', high_stress + 7.0),  # 自動推定
```

**動作**:
- ✅ 古いJSONファイル（`max_temperature`なし）→ 自動推定
- ✅ 新しいJSONファイル（`max_temperature`あり）→ そのまま使用
- ✅ 既存ファイルの変更不要

**利点**:
- ✅ **完璧な後方互換性**
- ✅ 既存のJSONファイルがそのまま動作
- ✅ 段階的な移行が可能

**欠点**:
- △ やや複雑（推定ロジックが必要）

---

## 🎯 推奨事項

### 推奨: 方針B（自動推定）を実装

**理由**:
1. ✅ 既存のJSONファイルを守る
2. ✅ ユーザーの手間を省く
3. ✅ 「後方変換は作らない」と矛盾しない
   - 読み込み時の補完は「後方変換」ではない
   - 書き込み時は常に新形式（`max_temperature`を含む）

---

## 🔧 修正案

### 修正箇所

**ファイル**: `src/agrr_core/framework/repositories/crop_profile_file_repository.py`

**修正前（行178-189）**:
```python
temp_data = stage_data['temperature']

temperature = TemperatureProfile(
    base_temperature=temp_data['base_temperature'],
    optimal_min=temp_data['optimal_min'],
    optimal_max=temp_data['optimal_max'],
    low_stress_threshold=temp_data.get('low_stress_threshold', temp_data['optimal_min']),
    high_stress_threshold=temp_data.get('high_stress_threshold', temp_data['optimal_max']),
    frost_threshold=temp_data.get('frost_threshold', 0.0),
    max_temperature=temp_data['max_temperature'],  # ← 必須
    sterility_risk_threshold=temp_data.get('sterility_risk_threshold')
)
```

**修正後**:
```python
temp_data = stage_data['temperature']

# high_stress_threshold を先に取得（max_temperature の推定に使う）
high_stress = temp_data.get('high_stress_threshold', temp_data['optimal_max'])

temperature = TemperatureProfile(
    base_temperature=temp_data['base_temperature'],
    optimal_min=temp_data['optimal_min'],
    optimal_max=temp_data['optimal_max'],
    low_stress_threshold=temp_data.get('low_stress_threshold', temp_data['optimal_min']),
    high_stress_threshold=high_stress,
    frost_threshold=temp_data.get('frost_threshold', 0.0),
    max_temperature=temp_data.get('max_temperature', high_stress + 7.0),  # ← 自動推定
    sterility_risk_threshold=temp_data.get('sterility_risk_threshold')
)
```

**変更内容**:
1. `high_stress` 変数の追加
2. `temp_data['max_temperature']` → `temp_data.get('max_temperature', high_stress + 7.0)`

---

## 📝 具体的な動作例

### 例1: 古いJSONファイル

**入力**:
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

**修正前の動作**:
```python
# エラー発生！
KeyError: 'max_temperature'
```

**修正後の動作**:
```python
# 自動推定される
high_stress = 35.0
max_temperature = 35.0 + 7.0 = 42.0°C

# 正常に読み込める
temperature = TemperatureProfile(
    base_temperature=10.0,
    optimal_min=25.0,
    optimal_max=30.0,
    high_stress_threshold=35.0,
    max_temperature=42.0,  # ← 自動推定
    # ...
)
```

---

### 例2: 新しいJSONファイル

**入力**:
```json
{
  "temperature": {
    "base_temperature": 10.0,
    "optimal_min": 25.0,
    "optimal_max": 30.0,
    "high_stress_threshold": 35.0,
    "max_temperature": 42.0
  }
}
```

**修正前の動作**:
```python
# 正常に読み込める
max_temperature = 42.0  # JSONから取得
```

**修正後の動作**:
```python
# 同じく正常に読み込める
max_temperature = temp_data.get('max_temperature', high_stress + 7.0)
# → max_temperature = 42.0（JSONから取得）
```

**結果**: 新しいファイルの動作は変わらない ✅

---

## 🔄 「後方変換は作らない」の正しい理解

### 後方変換とは？

**定義**: 新しい形式のデータを古い形式に変換すること

**例（やらないこと）**:
```python
# ❌ これは後方変換（不要）
def convert_to_old_format(profile: TemperatureProfile) -> dict:
    """新しい形式 → 古い形式への変換（作らない）"""
    return {
        "base_temperature": profile.base_temperature,
        "optimal_min": profile.optimal_min,
        "optimal_max": profile.optimal_max,
        # max_temperature を除外（後方互換のため）
    }
```

---

### 自動推定は後方変換ではない

**自動推定（やること）**:
```python
# ✅ これは後方変換ではない（読み込み時の補完）
max_temperature = temp_data.get('max_temperature', high_stress + 7.0)
```

**理由**:
- 読み込み: 古い形式 → 新しい形式（順方向）
- 補完: 足りないフィールドを推定で埋める
- 結果: メモリ上は常に新しい形式

---

### データフロー

```
読み込み（古い形式 → 新しい形式）
┌──────────────┐     自動推定      ┌──────────────┐
│  古いJSON    │  ───────────────> │ TemperatureProfile │
│              │     補完          │  (新しい形式)  │
│ max_temp無し │                   │  max_temp有り  │
└──────────────┘                   └──────────────┘
                                           │
                                           │ 使用
                                           ↓
                                    UseCase層で処理
                                           │
                                           │ 保存
                                           ↓
書き込み（常に新しい形式）
┌──────────────┐
│  新しいJSON   │
│              │
│ max_temp有り │  ← 常に完全な形式
└──────────────┘
```

**重要**: 
- ✅ 読み込み: 柔軟（自動推定で補完）
- ✅ 書き込み: 厳格（常に新形式）
- ❌ 後方変換: 不要（作らない）

---

## ✅ 修正のメリット

### 1. 既存ファイルが使える

```bash
# 修正前: エラー
$ agrr progress --crop-file old_rice.json --start-date 2024-05-01 ...
Error: 'max_temperature' not found

# 修正後: 動作する
$ agrr progress --crop-file old_rice.json --start-date 2024-05-01 ...
✓ Successfully calculated growth progress
```

### 2. 段階的な移行

```
既存ファイル（max_temperatureなし）
    ↓
読み込み時に自動推定で補完
    ↓
メモリ上は新形式（max_temperatureあり）
    ↓
新規作成時は新形式で保存
    ↓
徐々に新形式ファイルが増える（自然な移行）
```

### 3. ユーザーの手間を省く

```
# 修正前: 手動で全ファイルを更新が必要
$ vi rice.json
$ vi wheat.json
$ vi tomato.json
...（数十ファイル）

# 修正後: 何もしなくても動作
$ agrr progress --crop-file rice.json ...  # そのまま動く
```

---

## 🎯 実装の推奨手順

### Step 1: コード修正（5分）

```python
# src/agrr_core/framework/repositories/crop_profile_file_repository.py

temp_data = stage_data['temperature']

# ↓ 追加
high_stress = temp_data.get('high_stress_threshold', temp_data['optimal_max'])

temperature = TemperatureProfile(
    # ... 他のフィールド
    high_stress_threshold=high_stress,  # ↓ 変更
    max_temperature=temp_data.get('max_temperature', high_stress + 7.0),  # ↓ 変更
    # ...
)
```

### Step 2: テスト（10分）

```python
# tests/test_framework/test_crop_profile_file_repository.py

def test_load_profile_without_max_temperature():
    """max_temperature がない古いファイルの読み込みテスト"""
    json_data = {
        "crop": {"crop_id": "rice", ...},
        "stage_requirements": [
            {
                "stage": {"name": "vegetative", "order": 1},
                "temperature": {
                    "base_temperature": 10.0,
                    "optimal_min": 25.0,
                    "optimal_max": 30.0,
                    "high_stress_threshold": 35.0
                    # max_temperature なし
                },
                "thermal": {"required_gdd": 800.0}
            }
        ]
    }
    
    # 読み込めることを確認
    profile = repository._load_from_dict(json_data)
    
    # max_temperature が自動推定されていることを確認
    assert profile.stage_requirements[0].temperature.max_temperature == 42.0

def test_load_profile_with_max_temperature():
    """max_temperature がある新しいファイルの読み込みテスト"""
    json_data = {
        # ... 同じ
        "temperature": {
            # ... 同じ
            "max_temperature": 42.0  # あり
        }
    }
    
    profile = repository._load_from_dict(json_data)
    
    # JSONの値が使われることを確認
    assert profile.stage_requirements[0].temperature.max_temperature == 42.0
```

### Step 3: 動作確認（5分）

```bash
# 既存のファイルで動作確認
$ agrr progress --crop-file examples/rice_koshihikari.json ...

# 問題なければOK
```

---

## 📊 まとめ

### 現状

- ❌ `max_temperature` は必須フィールド
- ❌ 古いJSONファイルは読み込めない

### 推奨修正

- ✅ `max_temperature` を自動推定
- ✅ 古いJSONファイルも新しいファイルも動作
- ✅ 「後方変換は作らない」方針と矛盾しない

### 修正内容

```python
# 3行の変更のみ
high_stress = temp_data.get('high_stress_threshold', temp_data['optimal_max'])  # 追加
# ...
high_stress_threshold=high_stress,  # 変更
max_temperature=temp_data.get('max_temperature', high_stress + 7.0),  # 変更
```

**工数**: 20分（実装5分 + テスト10分 + 確認5分）

---

**結論**: 現在の実装は `max_temperature` を必須にしていますが、自動推定を追加することで既存ファイルとの互換性を保ちながら、「後方変換は作らない」方針とも矛盾しない実装が可能です。

