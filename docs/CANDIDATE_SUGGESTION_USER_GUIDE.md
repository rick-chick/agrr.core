# 候補リスト提示機能 ユーザーガイド

## 概要

候補リスト提示機能は、既存の最適化結果を基に、圃場ごとに利益最高の挿入可能な候補を提示する機能です。提示された候補は`adjust`コマンドで利用可能な状態になります。

## 機能の特徴

- **既存システムとの統合**: 既存の最適化処理とは独立した機能
- **利益最大化**: 圃場ごとに最も利益の高い候補を選択
- **adjust連携**: 提示結果を`adjust`コマンドで直接利用可能
- **柔軟な出力形式**: テーブル形式とJSON形式に対応

## 基本的な使用方法

### 1. 基本的な候補生成

```bash
agrr optimize candidates \
  --allocation current_allocation.json \
  --fields-file fields.json \
  --crops-file crops.json \
  --target-crop tomato \
  --planning-start 2024-04-01 --planning-end 2024-10-31 \
  --weather-file weather.json \
  --output candidates.txt
```

### 2. 相互作用ルール付きの候補生成

```bash
agrr optimize candidates \
  --allocation current_allocation.json \
  --fields-file fields.json \
  --crops-file crops.json \
  --target-crop tomato \
  --interaction-rules-file interaction_rules.json \
  --planning-start 2024-04-01 --planning-end 2024-10-31 \
  --weather-file weather.json \
  --output candidates.txt
```

### 3. JSON出力（adjust用）

```bash
agrr optimize candidates \
  --allocation current_allocation.json \
  --fields-file fields.json \
  --crops-file crops.json \
  --target-crop tomato \
  --planning-start 2024-04-01 --planning-end 2024-10-31 \
  --weather-file weather.json \
  --output candidates.json \
  --format json
```

## オプション詳細

### 必須オプション

- `--allocation, -a`: 既存の最適化結果ファイル（`optimize allocate`の出力）
- `--fields-file, -f`: 圃場設定ファイル
- `--crops-file, -c`: 作物設定ファイル
- `--target-crop, -t`: 対象作物ID
- `--planning-start, -s`: 計画期間開始日（YYYY-MM-DD形式）
- `--planning-end, -e`: 計画期間終了日（YYYY-MM-DD形式）
- `--weather-file, -w`: 気象データファイル
- `--output, -o`: 出力ファイルパス

### オプション

- `--interaction-rules-file, -i`: 相互作用ルールファイル（オプション）
- `--format, -fmt`: 出力形式（table/json、デフォルト: table）

## 入力ファイル形式

### 1. 既存の最適化結果ファイル（allocation.json）

```json
{
  "optimization_result": {
    "optimization_id": "opt_001",
    "field_schedules": [
      {
        "field_id": "field_1",
        "field_name": "Field 1",
        "allocations": [
          {
            "allocation_id": "alloc_001",
            "crop_id": "carrot",
            "crop_name": "Carrot",
            "area_used": 300.0,
            "start_date": "2024-05-01",
            "completion_date": "2024-07-15",
            "growth_days": 75,
            "total_cost": 75000,
            "expected_revenue": 120000,
            "profit": 45000
          }
        ]
      }
    ],
    "total_profit": 45000.0
  }
}
```

### 2. 圃場設定ファイル（fields.json）

```json
{
  "fields": [
    {
      "field_id": "field_1",
      "field_name": "Field 1",
      "area": 1000.0,
      "daily_fixed_cost": 1000.0
    },
    {
      "field_id": "field_2",
      "field_name": "Field 2",
      "area": 800.0,
      "daily_fixed_cost": 800.0
    }
  ]
}
```

### 3. 作物設定ファイル（crops.json）

```json
{
  "crops": [
    {
      "crop_id": "tomato",
      "name": "Tomato",
      "area_per_unit": 1.0,
      "variety": "default",
      "revenue_per_area": 1500.0,
      "max_revenue": 1000000.0,
      "groups": ["solanaceae"]
    },
    {
      "crop_id": "carrot",
      "name": "Carrot",
      "area_per_unit": 1.0,
      "variety": "default",
      "revenue_per_area": 1200.0,
      "max_revenue": 800000.0,
      "groups": ["umbelliferae"]
    }
  ]
}
```

### 4. 気象データファイル（weather.json）

```json
{
  "latitude": 35.6762,
  "longitude": 139.6503,
  "elevation": 40.0,
  "timezone": "Asia/Tokyo",
  "data": [
    {
      "time": "2024-04-01",
      "temperature_2m_max": 20.0,
      "temperature_2m_min": 10.0,
      "temperature_2m_mean": 15.0
    },
    {
      "time": "2024-04-02",
      "temperature_2m_max": 22.0,
      "temperature_2m_min": 12.0,
      "temperature_2m_mean": 17.0
    }
  ]
}
```

## 出力形式

### 1. テーブル形式（table）

```
候補リスト提示結果
==================

圃場ID: field_1
候補タイプ: INSERT
作物: tomato
開始日: 2024-06-01
面積: 500.0 m²
予想利益: 150,000円

圃場ID: field_2
候補タイプ: MOVE
移動元配分: alloc_001
移動先開始日: 2024-07-01
面積: 300.0 m²
予想利益: 120,000円
```

### 2. JSON形式（json）

```json
{
  "candidates": [
    {
      "field_id": "field_1",
      "candidate_type": "INSERT",
      "crop_id": "tomato",
      "start_date": "2024-06-01",
      "area": 500.0,
      "expected_profit": 150000,
      "move_instruction": {
        "action": "add",
        "crop_id": "tomato",
        "to_field_id": "field_1",
        "to_start_date": "2024-06-01",
        "to_area": 500.0
      }
    },
    {
      "field_id": "field_2",
      "candidate_type": "MOVE",
      "allocation_id": "alloc_001",
      "start_date": "2024-07-01",
      "area": 300.0,
      "expected_profit": 120000,
      "move_instruction": {
        "allocation_id": "alloc_001",
        "action": "move",
        "to_field_id": "field_2",
        "to_start_date": "2024-07-01",
        "to_area": 300.0
      }
    }
  ]
}
```

## adjustコマンドとの連携

### 1. 候補生成

```bash
# 候補をJSON形式で生成
agrr optimize candidates \
  --allocation current_allocation.json \
  --fields-file fields.json \
  --crops-file crops.json \
  --target-crop tomato \
  --planning-start 2024-04-01 --planning-end 2024-10-31 \
  --weather-file weather.json \
  --output candidates.json \
  --format json
```

### 2. adjustコマンドで適用

```bash
# 生成された候補をadjustコマンドで適用
agrr optimize adjust \
  --allocation current_allocation.json \
  --fields-file fields.json \
  --crops-file crops.json \
  --moves-file candidates.json \
  --planning-start 2024-04-01 --planning-end 2024-10-31 \
  --weather-file weather.json \
  --output adjusted_allocation.json
```

## 候補の種類

### 1. 新規挿入候補（INSERT）

- 対象作物を各圃場の空き期間に挿入
- 最適な開始日と面積を計算
- 制約条件（休閑期間、相互作用ルール、圃場容量）を遵守

### 2. 移動候補（MOVE）

- 既存の配分を他の圃場に移動
- 移動先の最適な開始日と面積を計算
- 移動による利益の変化を考慮

## 制約条件

### 1. 休閑期間

- 既存の配分との間隔を確保
- 作物の連作障害を考慮

### 2. 相互作用ルール

- 作物間の相互作用を考慮
- 相性の良い/悪い作物の組み合わせを制御

### 3. 圃場容量

- 圃場の面積制限を遵守
- 既存の配分との重複を回避

## トラブルシューティング

### 1. よくあるエラー

#### エラー: "Target crop not found"
- **原因**: 指定した作物IDがcrops.jsonに存在しない
- **解決方法**: crops.jsonファイルを確認し、正しい作物IDを指定

#### エラー: "Failed to load current optimization result"
- **原因**: allocation.jsonファイルが存在しないか、形式が正しくない
- **解決方法**: `optimize allocate`コマンドでallocation.jsonを生成

#### エラー: "Invalid date format"
- **原因**: 日付の形式が正しくない
- **解決方法**: YYYY-MM-DD形式で日付を指定（例: 2024-04-01）

### 2. パフォーマンスの問題

#### 実行時間が長い場合
- 計画期間を短くする
- 圃場数や作物数を減らす
- 相互作用ルールファイルを簡素化

#### メモリ使用量が多い場合
- 気象データの期間を短くする
- 圃場の面積を小さくする

## ベストプラクティス

### 1. データ準備

- 最新の気象データを使用
- 正確な圃場情報を入力
- 適切な作物プロファイルを設定

### 2. 計画期間の設定

- 栽培に適した期間を設定
- 気象データの期間と一致させる
- 十分な余裕を持たせる

### 3. 候補の評価

- 生成された候補を慎重に評価
- 実際の栽培条件と照らし合わせる
- 必要に応じて手動で調整

## 関連コマンド

- `agrr optimize period` - 最適な栽培期間の計算
- `agrr optimize allocate` - 複数圃場での作物配分最適化
- `agrr optimize adjust` - 既存配分の調整
- `agrr weather` - 気象データの取得
- `agrr crop` - 作物プロファイルの生成

## サポート

問題が発生した場合は、以下の情報を含めて報告してください：

1. 使用したコマンド
2. 入力ファイルの形式
3. エラーメッセージ
4. 実行環境（OS、Pythonバージョン等）

詳細な情報は、[要件定義書](CANDIDATE_SUGGESTION_FEATURE.md)と[テスト設計書](CANDIDATE_SUGGESTION_TEST_DESIGN.md)を参照してください。
