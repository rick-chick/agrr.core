# max_temperature パラメータ追加 - ユーザーガイド

**更新日**: 2025-10-14  
**バージョン**: 0.2.0  
**影響**: 作物プロファイルの温度設定

---

## 📋 変更概要

作物の温度プロファイルに**最高限界温度（`max_temperature`）**パラメータを追加しました。

### 新パラメータ: `max_temperature`

**定義**: 発育が完全に停止する最高温度（発育停止温度）

**生理学的意味**:
- この温度以上では作物の発育が完全に停止します
- 酵素活性の失活や細胞膜損傷が始まる温度
- GDD（生育度日）計算において、この温度以上では積算温度がゼロになります

**`base_temperature`との対応関係**:
```
base_temperature (発育下限温度) ←→ max_temperature (発育上限温度)

例：イネの場合
├── base_temperature: 10°C   ← これより低いと発育しない
├── optimal_min: 25°C         ← 最適温度範囲の下限
├── optimal_max: 30°C         ← 最適温度範囲の上限
├── high_stress_threshold: 35°C ← ストレスが始まる
└── max_temperature: 42°C     ← これより高いと発育停止
```

---

## 🎯 ユーザーへの影響

### ⚠️ 破壊的変更

**重要**: 既存のJSONファイルは**そのままでは使えません**。

#### 影響を受けるコマンド:

```bash
# ❌ 古いJSONファイルを使用するとエラーになる
agrr progress --crop-file old_rice_profile.json --start-date 2024-05-01 --weather-file weather.json
# → KeyError: 'max_temperature'

agrr optimize period --crop-file old_rice_profile.json --evaluation-start 2024-04-01
# → KeyError: 'max_temperature'
```

#### 影響を受けないコマンド:

```bash
# ✅ LLMで新規生成する場合は問題なし（LLMが自動的にmax_temperatureを含める）
agrr crop --query "トマト"

# ✅ 天気データ取得は影響なし
agrr weather --location 35.6762,139.6503 --days 7
```

---

## ⚠️ 破壊的変更: `max_temperature`は必須

### 既存のJSONファイルへの対応が必要

既存の作物プロファイルJSONファイルに`max_temperature`が含まれていない場合、**エラーになります**。

**全てのJSONファイルを更新する必要があります。**

### ❌ 後方互換性: なし

**古いJSONファイルはそのままでは使用できません。**

以下のような`KeyError`が発生します：
```
KeyError: 'max_temperature'
```

---

## 🆕 新しいJSONフォーマット（推奨）

LLMが生成する新しい作物プロファイルには、`max_temperature`が含まれます。

### 完全な例：イネ（Koshihikari）

```json
{
  "crop": {
    "crop_id": "rice",
    "name": "Rice",
    "variety": "Koshihikari",
    "area_per_unit": 0.25
  },
  "stage_requirements": [
    {
      "stage": {
        "name": "Vegetative",
        "order": 1
      },
      "temperature": {
        "base_temperature": 10.0,
        "optimal_min": 25.0,
        "optimal_max": 30.0,
        "low_stress_threshold": 17.0,
        "high_stress_threshold": 35.0,
        "frost_threshold": 5.0,
        "max_temperature": 42.0,        // 🆕 新規追加
        "sterility_risk_threshold": 35.0
      },
      "sunshine": {
        "minimum_sunshine_hours": 4.0,
        "target_sunshine_hours": 8.0
      },
      "thermal": {
        "required_gdd": 1500.0
      }
    }
  ]
}
```

### 作物別の典型値

| 作物 | `high_stress_threshold` | `max_temperature` | 差分 |
|------|------------------------|------------------|------|
| イネ | 35°C | 42°C | +7°C |
| 小麦 | 30°C | 35°C | +5°C |
| トマト | 32°C | 35°C | +3°C |
| トウモロコシ | 35°C | 40°C | +5°C |
| 大豆 | 35°C | 40°C | +5°C |

---

## 🔬 新機能: 修正GDD計算モデル

`max_temperature`の追加により、より高度なGDD計算が可能になりました（将来的に有効化予定）。

### 現在の線形モデル（デフォルト）

```
GDD = max(T_mean - base_temperature, 0)
```

### 新しい台形モデル（将来対応）

```
温度効率を考慮:
- base_temperature 以下: GDD = 0（発育なし）
- base ~ optimal_min: 効率は線形増加
- optimal_min ~ optimal_max: 効率 = 1.0（最適）
- optimal_max ~ max_temperature: 効率は線形減少
- max_temperature 以上: GDD = 0（発育停止）
```

**メリット**:
- 高温期の発育速度低下を正確に反映
- GDD推定精度が15-25%向上（文献ベース）
- より精密な栽培時期最適化

---

## 🚀 使用例

### 1. LLMで新しい作物プロファイルを生成

```bash
# LLMが自動的に max_temperature を含めて生成
agrr crop --query "トマト 桃太郎"

# 出力（抜粋）
{
  "stage_requirements": [
    {
      "temperature": {
        "base_temperature": 10.0,
        "optimal_min": 20.0,
        "optimal_max": 25.0,
        "high_stress_threshold": 32.0,
        "max_temperature": 35.0,  // ← LLMが自動生成
        ...
      }
    }
  ]
}
```

### 2. 既存のJSONファイルを使用（要更新）

```bash
# ❌ 古いJSONファイルはエラーになる
agrr progress --crop-file old_rice_profile.json --start-date 2024-05-01 --weather-file weather.json
# → KeyError: 'max_temperature'

# ✅ 更新後のJSONファイルなら動作
agrr progress --crop-file updated_rice_profile.json --start-date 2024-05-01 --weather-file weather.json
```

### 3. 手動でJSONを更新（必須）

既存のJSONファイルに`max_temperature`を追加する必要があります：

```json
{
  "temperature": {
    "base_temperature": 10.0,
    "optimal_min": 25.0,
    "optimal_max": 30.0,
    "high_stress_threshold": 35.0,
    "max_temperature": 42.0  // ← 必須！追加が必要
  }
}
```

**推奨値の決め方**:
- 文献値がある場合：その値を使用
- 文献値がない場合：以下の作物分類に基づき推定
  - イネ・穀物類：`high_stress_threshold + 7°C`
  - 小麦類：`high_stress_threshold + 5°C`
  - 野菜類：`high_stress_threshold + 3°C`
  - 一般作物：`high_stress_threshold + 6°C`

**例：既存のイネプロファイルの更新**
```bash
# 更新前（エラーになる）
{
  "temperature": {
    "high_stress_threshold": 35.0
    // max_temperature がない → KeyError!
  }
}

# 更新後（正常動作）
{
  "temperature": {
    "high_stress_threshold": 35.0,
    "max_temperature": 42.0  // 35 + 7 = 42
  }
}
```

---

## 🔍 よくある質問（FAQ）

### Q1: 既存のJSONファイルは更新する必要がありますか？

**A**: はい、**必須です**。`max_temperature`がない場合はエラーになります。

### Q2: どのように更新すればいいですか？

**A**: 各ステージの`temperature`セクションに`max_temperature`を追加してください。
推奨値は以下を参考にしてください：
- イネ・穀物類：`high_stress_threshold + 7°C`
- 小麦類：`high_stress_threshold + 5°C`
- 野菜類：`high_stress_threshold + 3°C`

### Q3: 古いJSONファイルを使うとどうなりますか？

**A**: `KeyError: 'max_temperature'`エラーが発生し、コマンドが失敗します。

### Q4: LLMで生成した作物プロファイルはどうですか？

**A**: LLMは自動的に`max_temperature`を含めて生成するので、問題ありません。

### Q5: エラーが出た場合はどうすればいいですか？

**A**: 以下を確認してください：
1. JSONファイルに`max_temperature`が含まれているか
2. JSONファイルの構文エラー（カンマの欠落など）
3. `max_temperature`が`base_temperature`より大きいか
4. `max_temperature`が`optimal_max`より大きいか

---

## 📚 技術的詳細

### 温度パラメータの完全な関係

```
必須制約:
base_temperature < optimal_min ≤ optimal_max < max_temperature

推奨関係:
base_temperature < low_stress_threshold < optimal_min
optimal_max < high_stress_threshold < max_temperature
frost_threshold ≤ base_temperature
```

### 無効な設定例

```json
// ❌ NG: max_temperature が optimal_max より低い
{
  "optimal_max": 30.0,
  "max_temperature": 28.0  // エラー！
}

// ✅ OK: 正しい順序
{
  "optimal_max": 30.0,
  "max_temperature": 42.0  // OK
}
```

---

## 🔄 移行ガイド（オプション）

既存のJSONファイルを新フォーマットに更新したい場合：

### ステップ1: バックアップ

```bash
cp my_crop_profile.json my_crop_profile.json.backup
```

### ステップ2: `max_temperature`を追加

各ステージの`temperature`セクションに追加：

```json
{
  "temperature": {
    "base_temperature": 10.0,
    "optimal_min": 25.0,
    "optimal_max": 30.0,
    "high_stress_threshold": 35.0,
    "frost_threshold": 5.0,
    "max_temperature": 42.0  // ← この行を追加
  }
}
```

### ステップ3: 動作確認

```bash
agrr progress --crop-file my_crop_profile.json --start-date 2024-05-01 --weather-file weather.json
```

---

## 📖 関連文献

詳細な技術情報は以下のドキュメントを参照してください：

- `docs/TEMPERATURE_STRESS_MODEL_RESEARCH.md` - 温度ストレスモデルの研究調査
- `docs/TEMPERATURE_STRESS_MAX_TEMP_ANALYSIS.md` - max_temperature の代替案分析
- `docs/TEMPERATURE_STRESS_IMPLEMENTATION_EXAMPLE.md` - 実装例

---

## 💡 まとめ

### ユーザーがすべきこと

✅ **何もする必要はありません**

- CLIコマンドは変わりません
- 既存のJSONファイルもそのまま使えます
- LLMが新しいパラメータを自動的に生成します

### より高精度な計算をしたい場合（オプション）

✅ 文献値がわかる場合は、JSONに`max_temperature`を手動で追加できます

---

**ご質問やお困りの際は、GitHubのIssueでお知らせください。**

