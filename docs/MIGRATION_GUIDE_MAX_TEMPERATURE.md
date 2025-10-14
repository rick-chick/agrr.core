# max_temperature パラメータ追加 - 移行ガイド

**対象バージョン**: v0.1.x → v0.2.0  
**更新日**: 2025-10-14  
**影響**: 🔴 **破壊的変更** - 既存のJSONファイルの更新が必要

---

## ⚠️ 破壊的変更の警告

このバージョンでは、作物プロファイルのJSONフォーマットに**必須パラメータ**が追加されました。

**`max_temperature`（最高限界温度・発育停止温度）が必須になります。**

---

## 🔍 影響を受けるユーザー

以下のいずれかに該当する場合、対応が必要です：

✅ **対応必要**:
- 既存の作物プロファイルJSONファイルを使用している
- `agrr progress`コマンドを使用している
- `agrr optimize period`コマンドを使用している

❌ **対応不要**:
- `agrr crop --query`でLLMから毎回生成している
- `agrr weather`のみ使用している
- `agrr forecast`のみ使用している

---

## 📋 移行手順

### ステップ1: 影響を受けるファイルの確認

既存の作物プロファイルJSONファイルを探します：

```bash
# プロジェクト内のJSONファイルを検索
find . -name "*.json" -type f | grep -E "(crop|profile)"
```

### ステップ2: 各JSONファイルに`max_temperature`を追加

#### 更新前（v0.1.x形式 - エラーになる）

```json
{
  "crop": {
    "crop_id": "rice",
    "name": "Rice",
    "variety": "Koshihikari"
  },
  "stage_requirements": [
    {
      "stage": {"name": "Vegetative", "order": 1},
      "temperature": {
        "base_temperature": 10.0,
        "optimal_min": 25.0,
        "optimal_max": 30.0,
        "low_stress_threshold": 17.0,
        "high_stress_threshold": 35.0,
        "frost_threshold": 5.0,
        "sterility_risk_threshold": 35.0
        // ❌ max_temperature がない
      },
      "sunshine": {...},
      "thermal": {...}
    }
  ]
}
```

#### 更新後（v0.2.0形式 - 正常動作）

```json
{
  "crop": {
    "crop_id": "rice",
    "name": "Rice",
    "variety": "Koshihikari"
  },
  "stage_requirements": [
    {
      "stage": {"name": "Vegetative", "order": 1},
      "temperature": {
        "base_temperature": 10.0,
        "optimal_min": 25.0,
        "optimal_max": 30.0,
        "low_stress_threshold": 17.0,
        "high_stress_threshold": 35.0,
        "frost_threshold": 5.0,
        "max_temperature": 42.0,          // ✅ 追加！
        "sterility_risk_threshold": 35.0
      },
      "sunshine": {...},
      "thermal": {...}
    }
  ]
}
```

### ステップ3: `max_temperature`の値の決定

作物分類に基づいて推奨値を設定してください：

| 作物分類 | 計算式 | 例 |
|---------|-------|-----|
| イネ・穀物（rice, maize, sorghum） | `high_stress_threshold + 7°C` | 35 + 7 = **42°C** |
| 小麦類（wheat, barley） | `high_stress_threshold + 5°C` | 30 + 5 = **35°C** |
| 野菜類（tomato, eggplant, pepper） | `high_stress_threshold + 3°C` | 32 + 3 = **35°C** |
| 豆類（soybean, pea） | `high_stress_threshold + 5°C` | 35 + 5 = **40°C** |
| 一般作物 | `high_stress_threshold + 6°C` | - |

**文献値がある場合は、文献値を優先してください。**

### ステップ4: 動作確認

更新したJSONファイルで動作確認：

```bash
# JSONファイルの構文チェック（オプション）
python3 -c "import json; json.load(open('rice_profile.json'))"

# 実際のコマンド実行
agrr progress --crop-file rice_profile.json --start-date 2024-05-01 --weather-file weather.json
```

---

## 🛠️ 自動更新スクリプト（Python）

多数のJSONファイルを一括更新するスクリプト例：

```python
#!/usr/bin/env python3
"""Add max_temperature to existing crop profile JSON files."""

import json
import sys
from pathlib import Path

def update_json_file(file_path: Path, crop_type: str = "general"):
    """Update a single JSON file with max_temperature."""
    
    # Offset values by crop type
    offsets = {
        "rice": 7.0,
        "wheat": 5.0,
        "vegetable": 3.0,
        "soybean": 5.0,
        "general": 6.0,
    }
    offset = offsets.get(crop_type, 6.0)
    
    # Load JSON
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Update each stage
    modified = False
    for stage_req in data.get("stage_requirements", []):
        temp = stage_req.get("temperature", {})
        if "max_temperature" not in temp:
            high_stress = temp.get("high_stress_threshold", 32.0)
            temp["max_temperature"] = high_stress + offset
            modified = True
            print(f"  Added max_temperature={temp['max_temperature']} (high_stress={high_stress} + {offset})")
    
    # Save if modified
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Updated: {file_path}")
        return True
    else:
        print(f"⏭️  Skipped (already has max_temperature): {file_path}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 update_max_temperature.py <json_file> [crop_type]")
        print("Crop types: rice, wheat, vegetable, soybean, general")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    crop_type = sys.argv[2] if len(sys.argv) > 2 else "general"
    
    print(f"Processing: {file_path}")
    update_json_file(file_path, crop_type)
```

**使い方**:
```bash
# 単一ファイルを更新
python3 update_max_temperature.py rice_profile.json rice

# 複数ファイルを一括更新
for file in *.json; do
    python3 update_max_temperature.py "$file" rice
done
```

---

## 🚨 エラーと対処法

### エラー1: `KeyError: 'max_temperature'`

**原因**: JSONファイルに`max_temperature`が含まれていない

**対処法**: 上記の移行手順に従ってJSONファイルを更新

```bash
# エラー内容例
KeyError: 'max_temperature'
  File "crop_profile_file_repository.py", line 187
    max_temperature=temp_data['max_temperature'],
```

### エラー2: `JSONDecodeError`

**原因**: JSONの構文エラー（カンマの追加忘れなど）

**対処法**: JSON構文をチェック

```bash
# 構文チェック
python3 -c "import json; json.load(open('rice_profile.json'))"
```

よくあるミス：
```json
// ❌ NG: カンマが欠落
{
  "frost_threshold": 5.0
  "max_temperature": 42.0  // カンマがない
}

// ✅ OK: 正しい構文
{
  "frost_threshold": 5.0,
  "max_temperature": 42.0  // カンマを追加
}
```

### エラー3: 制約違反

**原因**: `max_temperature`が不正な値

**対処法**: 温度パラメータの制約を確認

```
必須制約:
base_temperature < optimal_min ≤ optimal_max < max_temperature
```

**例**:
```json
// ❌ NG: max_temperature が optimal_max より低い
{
  "optimal_max": 30.0,
  "max_temperature": 28.0  // エラー！
}

// ✅ OK
{
  "optimal_max": 30.0,
  "max_temperature": 42.0  // OK
}
```

---

## 📊 移行チェックリスト

作業を確実に進めるためのチェックリスト：

```
□ 既存の作物プロファイルJSONファイルを特定
□ 各JSONファイルに max_temperature を追加
  □ 作物分類を確認
  □ 推奨値を計算（high_stress + オフセット）
  □ 文献値がある場合は優先
□ JSON構文チェック
□ 温度制約の確認（base < optimal < max）
□ 動作確認（agrr progress コマンド実行）
□ バックアップの保存
```

---

## 💡 移行のベストプラクティス

### 1. バックアップを取る

```bash
# 更新前にバックアップ
cp rice_profile.json rice_profile.json.backup
```

### 2. 段階的に更新

```bash
# 1つずつ更新して動作確認
vim rice_profile.json  # max_temperature を追加
agrr progress --crop-file rice_profile.json --start-date 2024-05-01 --weather-file weather.json

# 成功したら次のファイルへ
```

### 3. LLMで再生成（推奨）

古いJSONファイルを更新する代わりに、LLMで最新版を生成：

```bash
# 新しいプロファイルを生成（max_temperature を含む）
agrr crop --query "イネ コシヒカリ" > rice_koshihikari_v2.json

# 新しいファイルを使用
agrr progress --crop-file rice_koshihikari_v2.json --start-date 2024-05-01 --weather-file weather.json
```

---

## 📞 サポート

移行でお困りの場合は、以下をお知らせください：

1. エラーメッセージの全文
2. 使用している作物プロファイルJSONファイル
3. 実行したコマンド

GitHubのIssueまたはサポートチャンネルで対応いたします。

---

## 🎯 まとめ

### 必要な作業

1. ✅ **既存のJSONファイルに`max_temperature`を追加**
2. ✅ **作物分類に基づいて値を設定**
3. ✅ **動作確認**

### メリット

- より正確なGDD計算
- 高温期の発育速度低下を反映
- 将来的な温度ストレスモデルの基盤

### サポート

- 移行スクリプト提供
- エラー時の詳細メッセージ
- 文献ベースの推奨値

---

**重要**: この変更により、より科学的に正確な栽培計画が可能になります。お手数ですが、ご協力をお願いいたします。

