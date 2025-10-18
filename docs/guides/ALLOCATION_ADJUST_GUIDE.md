# Allocation Adjustment Guide

## 概要

`agrr optimize adjust`コマンドは、既存の作物配置に対して手動で調整（移動・削除）を指定し、制約を満たしながら利益を再最適化する機能です。

## 使用シーン

### 1. 圃場の障害対応
```bash
# 例: field_1が天候不良で使えなくなった場合
# field_1の作物をfield_2に移動
agrr optimize adjust \
  --current-allocation current_result.json \
  --moves moves_emergency.json \
  --weather-file weather.json \
  --planning-start 2024-04-01 \
  --planning-end 2024-10-31
```

### 2. 作物の追加配置
```bash
# 例: 新しい作物を追加したい場合
# 既存配置を基に、新作物の最適配置を計算
agrr optimize adjust \
  --current-allocation current_result.json \
  --moves add_cucumber.json \
  --crops-file crops_with_cucumber.json \
  --weather-file weather.json \
  --planning-start 2024-04-01 \
  --planning-end 2024-10-31
```

### 3. 手動調整の評価
```bash
# 例: 専門家の経験に基づく調整を評価
agrr optimize adjust \
  --current-allocation current_result.json \
  --moves expert_adjustments.json \
  --weather-file weather.json \
  --interaction-rules-file rules.json \
  --planning-start 2024-04-01 \
  --planning-end 2024-10-31 \
  --format json > adjusted_result.json
```

## 入力ファイル形式

### 1. 現在の配置ファイル (current_allocation.json)

`agrr optimize allocate`コマンドの出力をそのまま使用できます：

```json
{
  "optimization_result": {
    "optimization_id": "opt_20240401_123456",
    "field_schedules": [
      {
        "field": {
          "field_id": "field_1",
          "name": "北圃場",
          "area": 1000.0,
          "daily_fixed_cost": 5000.0,
          "fallow_period_days": 28
        },
        "allocations": [
          {
            "allocation_id": "alloc_tomato_001",
            "crop": {
              "crop_id": "tomato",
              "name": "Tomato",
              "variety": "Momotaro",
              "revenue_per_area": 50000.0,
              "max_revenue": 800000.0
            },
            "start_date": "2024-05-01T00:00:00",
            "completion_date": "2024-08-15T00:00:00",
            "growth_days": 106,
            "area_used": 15.0,
            "total_cost": 530000.0,
            "expected_revenue": 750000.0,
            "profit": 220000.0,
            "accumulated_gdd": 1200.0
          }
        ],
        "total_cost": 530000.0,
        "total_revenue": 750000.0,
        "total_profit": 220000.0
      }
    ],
    "total_cost": 530000.0,
    "total_revenue": 750000.0,
    "total_profit": 220000.0
  }
}
```

### 2. 移動指示ファイル (moves.json)

#### 移動 (move) の例
```json
{
  "moves": [
    {
      "allocation_id": "alloc_tomato_001",
      "action": "move",
      "to_field_id": "field_2",
      "to_start_date": "2024-05-15",
      "to_area": 12.0
    }
  ]
}
```

**フィールド説明:**
- `allocation_id` (必須): 移動する配置のID
- `action` (必須): "move" - 移動アクション
- `to_field_id` (必須): 移動先の圃場ID
- `to_start_date` (必須): 移動後の開始日 (YYYY-MM-DD形式)
- `to_area` (オプション): 移動後の面積 (省略時は元の面積を使用)

#### 削除 (remove) の例
```json
{
  "moves": [
    {
      "allocation_id": "alloc_cucumber_002",
      "action": "remove"
    }
  ]
}
```

**フィールド説明:**
- `allocation_id` (必須): 削除する配置のID
- `action` (必須): "remove" - 削除アクション

#### 複数の移動を組み合わせる例
```json
{
  "moves": [
    {
      "allocation_id": "alloc_tomato_001",
      "action": "move",
      "to_field_id": "field_2",
      "to_start_date": "2024-05-15",
      "to_area": 12.0
    },
    {
      "allocation_id": "alloc_cucumber_002",
      "action": "remove"
    },
    {
      "allocation_id": "alloc_rice_003",
      "action": "move",
      "to_field_id": "field_3",
      "to_start_date": "2024-06-01"
    }
  ]
}
```

## コマンドオプション

### 必須オプション

| オプション | 短縮形 | 説明 | 例 |
|-----------|--------|------|-----|
| `--current-allocation` | `-ca` | 現在の配置ファイル (JSON) | `current_result.json` |
| `--moves` | `-m` | 移動指示ファイル (JSON) | `moves.json` |
| `--weather-file` | `-w` | 気象データファイル (JSON/CSV) | `weather.json` |
| `--planning-start` | `-s` | 計画期間の開始日 (YYYY-MM-DD) | `2024-04-01` |
| `--planning-end` | `-e` | 計画期間の終了日 (YYYY-MM-DD) | `2024-10-31` |

### オプション

| オプション | 短縮形 | 説明 | デフォルト |
|-----------|--------|------|-----------|
| `--fields-file` | `-fs` | 圃場情報ファイル (JSONで上書き) | - |
| `--crops-file` | `-cs` | 作物情報ファイル (JSONで上書き) | - |
| `--interaction-rules-file` | `-irf` | 相互作用ルールファイル (JSON) | - |
| `--objective` | `-obj` | 最適化目的 (maximize_profit, minimize_cost) | `maximize_profit` |
| `--algorithm` | `-alg` | アルゴリズム (dp, greedy) | `dp` |
| `--format` | `-fmt` | 出力形式 (table, json) | `table` |
| `--max-time` | `-mt` | 最大計算時間 (秒) | - |
| `--enable-parallel` | - | 並列候補生成を有効化 | false |
| `--disable-local-search` | - | 局所探索を無効化 | false |
| `--no-filter-redundant` | - | 冗長候補のフィルタリングを無効化 | false |

## 出力形式

### Table形式 (デフォルト)

```
================================================================================
ALLOCATION ADJUSTMENT RESULT
================================================================================

✓ Successfully adjusted allocation with 2 moves applied, 0 moves rejected.

Optimization ID: opt_20240401_234567
Algorithm: adjust+dp
Computation Time: 12.34s
Is Optimal: No

Applied Moves                            Action    
--------------------------------------------------------------------------------
alloc_tomato_001                         move → field_2 (start: 2024-05-15)
alloc_cucumber_002                       remove

Financial Summary                 Amount              
--------------------------------------------------------------------------------
Total Cost                       ¥      2,450,000
Total Revenue                    ¥      3,200,000
Total Profit                     ¥        750,000
Profit Rate                            30.6%

Field Summary        Fields     Allocations    Avg Utilization     
--------------------------------------------------------------------------------
Total                      4              12              45.2%

Crop Diversity: 6 unique crops

FIELD SCHEDULES
================================================================================

Field: 北圃場 (field_1)
  Area: 1000.0m²
  Daily Fixed Cost: ¥5,000/day
  Fallow Period: 28 days
  Utilization: 52.3%
  Profit: ¥185,000

  Crop            Start Date   End Date     Days   Area     Profit      
  ---------------------------------------------------------------------------
  Rice            2024-05-01   2024-08-15    106   250.0    ¥   185,000

...
```

### JSON形式

```json
{
  "success": true,
  "message": "Successfully adjusted allocation with 2 moves applied, 0 moves rejected.",
  "applied_moves": [
    {
      "allocation_id": "alloc_tomato_001",
      "action": "move",
      "to_field_id": "field_2",
      "to_start_date": "2024-05-15T00:00:00",
      "to_area": 12.0
    },
    {
      "allocation_id": "alloc_cucumber_002",
      "action": "remove",
      "to_field_id": null,
      "to_start_date": null,
      "to_area": null
    }
  ],
  "rejected_moves": [],
  "optimization_result": {
    "optimization_id": "opt_20240401_234567",
    "algorithm_used": "adjust+dp",
    "optimization_time": 12.34,
    "is_optimal": false,
    "field_schedules": [...],
    "total_cost": 2450000.0,
    "total_revenue": 3200000.0,
    "total_profit": 750000.0,
    "crop_areas": {
      "rice": 500.0,
      "tomato": 240.0
    }
  }
}
```

## 制約と注意事項

### 適用される制約

1. **休閑期間 (Fallow Period)**
   - 各圃場の休閑期間は厳密に守られます
   - 移動先でも休閑期間が適用されます

2. **連作障害 (Interaction Rules)**
   - `--interaction-rules-file`を指定した場合、連作障害ルールが適用されます
   - 同じ科の作物を連続で栽培すると収益が減少する可能性があります

3. **圃場容量**
   - 移動先の圃場の面積を超える配置はできません
   - 同一期間に複数の作物が重複することはできません

4. **計画期間**
   - すべての配置は`--planning-start`から`--planning-end`の期間内に収まる必要があります

### 移動の適用プロセス

1. **移動指示の検証**: 各移動指示の妥当性をチェック
2. **配置の削除/移動**: 指定された配置を削除または移動
3. **再最適化**: 残りの配置と新しい候補を使って全体を再最適化
4. **制約チェック**: 休閑期間、連作障害などの制約を確認
5. **結果の出力**: 調整後の最適配置を出力

### 移動が拒否される場合

以下の場合、移動は拒否されます：

- 指定された`allocation_id`が存在しない
- 移動先の圃場が存在しない
- 移動先の圃場の容量不足
- 休閑期間の制約違反
- 開始日が計画期間外

拒否された移動は`rejected_moves`として出力され、理由が表示されます。

## 実践例

### 例1: 圃場障害時の緊急対応

**シナリオ**: field_1が突然使用不可になったため、全ての作物をfield_2に移動

**moves.json**:
```json
{
  "moves": [
    {
      "allocation_id": "alloc_tomato_001",
      "action": "move",
      "to_field_id": "field_2",
      "to_start_date": "2024-05-15"
    },
    {
      "allocation_id": "alloc_cucumber_002",
      "action": "move",
      "to_field_id": "field_2",
      "to_start_date": "2024-07-01"
    }
  ]
}
```

**コマンド**:
```bash
agrr optimize adjust \
  --current-allocation current.json \
  --moves moves.json \
  --weather-file weather.json \
  --planning-start 2024-04-01 \
  --planning-end 2024-10-31 \
  --format json > emergency_result.json
```

### 例2: 収益性の低い作物の削除と再最適化

**シナリオ**: 収益性の低い2つの作物を削除し、残りで最適化

**moves.json**:
```json
{
  "moves": [
    {
      "allocation_id": "alloc_low_profit_001",
      "action": "remove"
    },
    {
      "allocation_id": "alloc_low_profit_002",
      "action": "remove"
    }
  ]
}
```

**コマンド**:
```bash
agrr optimize adjust \
  --current-allocation current.json \
  --moves moves.json \
  --weather-file weather.json \
  --planning-start 2024-04-01 \
  --planning-end 2024-10-31 \
  --algorithm dp
```

### 例3: 専門家の知見に基づく複雑な調整

**シナリオ**: 専門家の推奨に基づき、複数の作物を移動・削除

**moves.json**:
```json
{
  "moves": [
    {
      "allocation_id": "alloc_tomato_001",
      "action": "move",
      "to_field_id": "field_3",
      "to_start_date": "2024-06-01",
      "to_area": 18.0
    },
    {
      "allocation_id": "alloc_cucumber_002",
      "action": "remove"
    },
    {
      "allocation_id": "alloc_rice_003",
      "action": "move",
      "to_field_id": "field_1",
      "to_start_date": "2024-05-10"
    }
  ]
}
```

**コマンド**:
```bash
agrr optimize adjust \
  --current-allocation current.json \
  --moves moves.json \
  --weather-file weather.json \
  --interaction-rules-file rules.json \
  --planning-start 2024-04-01 \
  --planning-end 2024-10-31 \
  --enable-parallel \
  --format json > expert_adjusted.json
```

## トラブルシューティング

### Q: 移動がすべて拒否される

**A**: 以下を確認してください：
- `allocation_id`が正しいか (現在の配置ファイルから確認)
- 移動先の圃場IDが存在するか
- 開始日が計画期間内か
- 圃場の容量が十分か

### Q: 再最適化後の利益が元より低い

**A**: これは期待される動作です。手動で配置を削除/移動した場合、元の最適解から離れるため、利益が低下する可能性があります。`rejected_moves`を確認し、どの移動が適用されたかを確認してください。

### Q: 計算時間が長い

**A**: 以下のオプションを試してください：
- `--algorithm greedy`: DPより高速なgreedyアルゴリズムを使用
- `--enable-parallel`: 並列処理を有効化
- `--disable-local-search`: 局所探索を無効化 (精度は低下)
- `--max-time 30`: 最大計算時間を設定 (秒)

## 関連コマンド

- `agrr optimize allocate`: 最初の配置最適化
- `agrr optimize period`: 単一作物の最適栽培期間計算
- `agrr weather`: 気象データ取得
- `agrr crop`: 作物プロファイル生成

## 参考資料

- [ARCHITECTURE.md](../ARCHITECTURE.md): プロジェクトアーキテクチャ
- [allocation_adjust_interactor.py](../src/agrr_core/usecase/interactors/allocation_adjust_interactor.py): ビジネスロジック実装
- [test_data/](../test_data/): サンプルデータ

