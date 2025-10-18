# CLIユーザー向け：休閑期間機能ガイド

## 休閑期間とは？

**休閑期間（Fallow Period）**は、作物を収穫した後、次の作物を植えるまでに必要な土壌の回復期間です。

### なぜ必要？
- 🌱 土壌の栄養分を回復させる
- 🦠 病害虫のサイクルを断ち切る
- 🌾 連作障害を防ぐ

---

## 使い方

### Step 1: ヘルプの確認

```bash
agrr optimize allocate --help
```

ヘルプの "Fallow Period" セクションを確認：
```
Fallow Period:
  - The fallow period is the required rest period for soil recovery between crops
  - Specified in days (integer, >= 0)
  - Default: 28 days if not specified
  - Set to 0 for continuous cultivation (no rest period)
  - Each field can have a different fallow period
  - Example: If crop A finishes on June 30 with 28-day fallow, 
             crop B cannot start before July 28
```

### Step 2: フィールド設定ファイルの作成

#### 例1: デフォルト値を使用（推奨）

`my_fields.json`:
```json
{
  "fields": [
    {
      "field_id": "field_01",
      "name": "北圃場",
      "area": 1000.0,
      "daily_fixed_cost": 5000.0
    }
  ]
}
```
※ `fallow_period_days` を省略すると**自動的に28日**が設定されます

#### 例2: カスタム休閑期間を設定

`my_fields.json`:
```json
{
  "fields": [
    {
      "field_id": "organic_field",
      "name": "有機栽培圃場",
      "area": 1000.0,
      "daily_fixed_cost": 5000.0,
      "fallow_period_days": 45
    },
    {
      "field_id": "intensive_field",
      "name": "集約栽培圃場",
      "area": 800.0,
      "daily_fixed_cost": 4000.0,
      "fallow_period_days": 14
    }
  ]
}
```

#### 例3: 連続栽培（休閑期間なし）

```json
{
  "fields": [
    {
      "field_id": "greenhouse",
      "name": "温室栽培",
      "area": 500.0,
      "daily_fixed_cost": 8000.0,
      "fallow_period_days": 0
    }
  ]
}
```

### Step 3: 最適化の実行

```bash
agrr optimize allocate \
  --fields-file my_fields.json \
  --crops-file crops.json \
  --planning-start 2024-04-01 \
  --planning-end 2024-10-31 \
  --weather-file weather.json
```

---

## サンプルデータで試す

### サンプル1: 異なる休閑期間（7〜28日）

```bash
agrr optimize allocate \
  --fields-file test_data/allocation_fields_with_fallow.json \
  --crops-file test_data/allocation_crops_1760447748.json \
  --planning-start 2023-04-01 \
  --planning-end 2023-10-31 \
  --weather-file test_data/weather_2023_full.json
```

**結果**:
- 総割り当て: 8回
- 総利益: ¥53,905
- 休閑期間が守られている

### サンプル2: 休閑期間なし

```bash
agrr optimize allocate \
  --fields-file test_data/allocation_fields_no_fallow.json \
  --crops-file test_data/allocation_crops_1760447748.json \
  --planning-start 2023-04-01 \
  --planning-end 2023-10-31 \
  --weather-file test_data/weather_2023_full.json
```

**結果**:
- 総割り当て: 9回（+1回）
- 総利益: ¥58,260（+¥4,355）
- 連続栽培が可能

---

## 推奨設定

### 栽培タイプ別

| 栽培タイプ | 推奨休閑期間 | 理由 |
|----------|------------|------|
| **有機栽培** | 45-60日 | 土壌の健康を最優先 |
| **一般栽培** | 28日 | バランス型（デフォルト） |
| **集約栽培** | 14-21日 | 生産性を重視 |
| **温室栽培** | 0-7日 | 環境制御が可能 |
| **連続栽培** | 0日 | 最大生産性（リスクあり） |

### 作物による調整

| 前作物 → 後作物 | 推奨休閑期間 |
|---------------|------------|
| ナス → トマト（同科） | 60日以上 |
| ナス → ニンジン | 28日 |
| ニンジン → ほうれん草 | 14日 |

---

## トラブルシューティング

### エラー: 重複エラー

```
ValueError: Allocations ... overlap (considering 60-day fallow period)
```

**原因**: 休閑期間が長すぎて、計画期間内に複数回栽培できない

**解決方法**:
1. 休閑期間を短くする（例: 60日 → 28日）
2. 計画期間を延長する
3. より短い栽培期間の作物を選ぶ

### より多く栽培したい場合

**現在**: 28日の休閑期間で8回の割り当て
**希望**: もっと多く栽培したい

**方法**:
1. `fallow_period_days` を短くする（例: 14日）
2. または `0` にする（連続栽培）

```json
{
  "field_id": "field_01",
  "fallow_period_days": 14
}
```

### 土壌を大切にしたい場合

**現在**: デフォルト28日
**希望**: より長い休閑期間

**方法**:
`fallow_period_days` を増やす（例: 45日）

```json
{
  "field_id": "organic_field",
  "fallow_period_days": 45
}
```

---

## 実行結果の見方

### 出力例

```
Field: ナス - 圃場1 (field_1)
  Area: 13.0 m² | Utilization: 200.0%
  
  Crop         Start Date   End Date       Days
  ------------------------------------------------
  ほうれん草      2023-05-12   2023-06-28       48
  ほうれん草      2023-09-09   2023-10-31       53
```

**確認ポイント**:
- 6/28 終了 → 9/9 開始 = **73日間隔**
- 設定した休閑期間（28日）以上が確保されている ✅

---

## よくある質問

### Q1: デフォルト値は何日？
**A**: 28日です。`fallow_period_days` を省略すると自動的に28日になります。

### Q2: 0日に設定できますか？
**A**: はい。`"fallow_period_days": 0` で連続栽培が可能です。

### Q3: 圃場ごとに異なる値を設定できますか？
**A**: はい。各圃場で個別に設定できます。

### Q4: 負の値は設定できますか？
**A**: いいえ。0以上の整数のみ設定可能です。

### Q5: 休閑期間を考慮しないで実行できますか？
**A**: はい。全ての圃場で `"fallow_period_days": 0` を設定してください。

---

## まとめ

### 基本的な使い方

1. **ヘルプを確認**: `agrr optimize allocate --help`
2. **設定ファイルを作成**: `fallow_period_days` を追加（省略可）
3. **最適化を実行**: 通常通りコマンドを実行

### 効果

✅ 土壌の健康を保つ  
✅ 連作障害を防ぐ  
✅ より現実的なスケジューリング  
✅ 圃場ごとに柔軟に設定可能  

---

**休閑期間機能を使って、持続可能な農業計画を立てましょう！** 🌾✨

