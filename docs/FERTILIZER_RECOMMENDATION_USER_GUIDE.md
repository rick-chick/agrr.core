# 肥料推奨機能 ユーザーガイド

## 概要
肥料推奨機能は、作物に最適なN-P-K（窒素・リン・カリウム）肥料の施肥計画を提供します。LLM（大規模言語モデル）を使用して学術的な農業指導書から情報を取得し、構造化された推奨事項を出力します。

## クイックスタート

### 1. 作物プロファイルの生成
```bash
# トマトの作物プロファイルを生成
agrr crop --query "tomato" > tomato_profile.json

# 米の作物プロファイルを生成
agrr crop --query "rice" > rice_profile.json
```

### 2. 肥料推奨の取得
```bash
# JSON形式で推奨事項を取得
agrr fertilize recommend --crop-file tomato_profile.json --json

# ファイルに保存
agrr fertilize recommend --crop-file tomato_profile.json --output tomato_fertilizer.json
```

## コマンド詳細

### 基本構文
```bash
agrr fertilize recommend --crop-file <作物プロファイルファイル> [オプション]
```

### オプション
- `--crop-file`, `-c`: **必須** - `agrr crop`で生成した作物プロファイルJSONファイルのパス
- `--json`, `-j`: JSON形式で出力（テキスト形式の説明を省略）
- `--output`, `-o`: 出力をファイルに保存（指定しない場合は標準出力）

### 使用例

#### 基本的な使用
```bash
# トマトの肥料推奨を取得
agrr crop --query "tomato" > tomato.json
agrr fertilize recommend --crop-file tomato.json
```

#### JSON出力
```bash
# JSON形式で出力（プログラム処理用）
agrr fertilize recommend --crop-file tomato.json --json
```

#### ファイル保存
```bash
# 推奨事項をファイルに保存
agrr fertilize recommend --crop-file tomato.json --output tomato_fertilizer.json
```

#### 組み合わせ
```bash
# JSON形式でファイルに保存
agrr fertilize recommend --crop-file tomato.json --json --output tomato_fertilizer.json
```

## 出力形式

### JSON出力例
```json
{
  "crop": {
    "crop_id": "tomato",
    "name": "Tomato"
  },
  "totals": {
    "N": 18.0,
    "P": 5.2,
    "K": 12.4
  },
  "applications": [
    {
      "type": "basal",
      "count": 1,
      "schedule_hint": "pre-plant",
      "nutrients": {
        "N": 6.0,
        "P": 2.0,
        "K": 3.0
      }
    },
    {
      "type": "topdress",
      "count": 2,
      "schedule_hint": "early fruit set; mid fruiting",
      "nutrients": {
        "N": 12.0,
        "P": 3.2,
        "K": 9.4
      },
      "per_application": {
        "N": 6.0,
        "P": 1.6,
        "K": 4.7
      }
    }
  ],
  "sources": [
    "https://example.org/tomato-fertilizer",
    "JAガイド 2021 p.12-18"
  ],
  "confidence": 0.7,
  "notes": "Adjust based on soil test results"
}
```

### 出力項目の説明

| 項目 | 説明 | 単位 |
|------|------|------|
| `crop` | 作物情報（ID、名前） | - |
| `totals` | 総施肥量（N、P、K） | g/m² |
| `applications` | 施肥計画の配列 | - |
| `applications[].type` | 施肥タイプ（basal=元肥、topdress=追肥） | - |
| `applications[].count` | 施肥回数 | 回 |
| `applications[].schedule_hint` | 施肥時期のヒント | - |
| `applications[].nutrients` | 該当タイプの総施肥量 | g/m² |
| `applications[].per_application` | 1回あたりの施肥量（追肥のみ） | g/m² |
| `sources` | 情報源（URL、文献等） | - |
| `confidence` | 推奨の信頼度（0-1） | - |
| `notes` | 追加の注意事項 | - |

## 対応作物

現在、以下の作物に対応しています：
- トマト（tomato）
- 米（rice）
- キュウリ（cucumber）
- ナス（eggplant）
- ニンジン（carrot）
- ほうれん草（spinach）

## 単位について

- **面積単位**: すべての施肥量は **g/m²**（平方メートルあたりグラム）で表示
- **栄養素**: N（窒素）、P（リン）、K（カリウム）の元素量
- **変換**: 従来のP2O5、K2O表記から元素量に自動変換

## トラブルシューティング

### よくあるエラー

#### 1. ファイルが見つからない
```bash
❌ Error: Crop profile file not found: tomato.json
```
**解決方法**: `agrr crop`コマンドで作物プロファイルを先に生成してください。

#### 2. 無効なJSON形式
```bash
❌ Error: Invalid JSON format in crop profile
```
**解決方法**: 作物プロファイルファイルが正しいJSON形式か確認してください。

#### 3. 作物が認識されない
```bash
❌ Error: Crop not recognized: unknown_crop
```
**解決方法**: 対応作物の名前を使用してください（例：tomato、rice）。

### デバッグ用オプション

#### テスト用モックデータの使用
```bash
# 開発・テスト用の固定データを使用
agrr fertilize recommend --crop-file tomato.json --mock-fertilizer --json
```

## 実用例

### 1. トマト栽培の施肥計画
```bash
# 1. 作物プロファイル生成
agrr crop --query "tomato" > tomato_profile.json

# 2. 肥料推奨取得
agrr fertilize recommend --crop-file tomato_profile.json --json > tomato_fertilizer.json

# 3. 結果確認
cat tomato_fertilizer.json
```

### 2. 複数作物の比較
```bash
# 複数の作物の施肥計画を比較
for crop in tomato rice cucumber; do
  agrr crop --query "$crop" > "${crop}_profile.json"
  agrr fertilize recommend --crop-file "${crop}_profile.json" --json > "${crop}_fertilizer.json"
done
```

### 3. 農業計画への統合
```bash
# 施肥計画を農業管理システムに統合
agrr fertilize recommend --crop-file tomato.json --json | jq '.totals' > tomato_nutrients.json
```

## 注意事項

1. **土壌テスト**: 推奨事項は一般的なガイドラインです。実際の施肥前に土壌テストを実施してください。

2. **地域性**: 推奨事項は主に日本の農業指導に基づいています。他の地域では調整が必要な場合があります。

3. **気象条件**: 天候や栽培条件により、施肥時期や量を調整してください。

4. **段階的適用**: 一度に全量を施肥せず、推奨される回数に分けて施肥してください。

## サポート

### ヘルプの表示
```bash
# 肥料コマンドのヘルプ
agrr fertilize --help

# 推奨サブコマンドのヘルプ
agrr fertilize recommend --help
```

### 関連ドキュメント
- [肥料推奨機能 設計書](../architecture/FERTILIZER_RECOMMENDATION_DESIGN.md)
- [API仕様書](../api/fertilizer_recommendation_api_reference.md)
- [LLM戦略](../guides/FERTILIZER_RECOMMENDATION_LLM_STRATEGY.md)

---

**最終更新**: 2025年1月  
**バージョン**: 1.0
