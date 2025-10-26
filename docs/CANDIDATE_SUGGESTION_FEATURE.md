# 候補リスト提示機能 要件定義書

## 概要

既存の最適化処理に、候補リストを提示する機能を追加する。利益最高の挿入可能な候補を圃場ごとに一つ提示し、その結果は`adjust`コマンドで利用できる状態にする。

## 機能要件

### 基本機能
- 既存の最適化結果を基に、圃場ごとに利益最高の挿入可能な候補を提示
- 提示した結果は`adjust`コマンドで利用可能な状態にする
- 既存の最適化処理とは独立した機能として実装

### 候補の種類
1. **新しい作物の挿入候補**
   - 対象作物を各圃場の空き期間に挿入
   - 最適な開始日と面積を計算

2. **既存の作物の移動候補**
   - 既存の配分を他の圃場に移動
   - 移動先の最適な開始日と面積を計算

### 入力データ
- `fields.json` - 圃場設定ファイル
- `allocation.json` - 既存の最適化結果（`optimize allocate`の出力）
- `crops.json` - 作物設定ファイル
- `interaction_rules.json` - 相互作用ルールファイル（オプション）
- `target_crop` - 対象作物ID（パフォーマンスによっては複数）
- `weather.json` - 気象データファイル

### 出力形式
- 圃場ごとに1つの最利益候補を提示
- `adjust`コマンドで利用可能な形式（moves.json形式）

## 技術要件

### 制約条件
- 既存の制約に従う（休閑期間、相互作用ルール、圃場容量など）
- 既存の`ViolationCheckerService`を使用

### 利益計算
- 既存の`OptimizationMetrics`クラスを使用
- `revenue - cost`で計算

### 既存システムとの連携
- `GrowthPeriodOptimizeInteractor`でGDD計算
- `ViolationCheckerService`で制約チェック
- `OptimizationMetrics`で利益計算
- `MoveInstruction`エンティティを活用

## CLI仕様

### コマンド形式
```bash
agrr optimize candidates [OPTIONS]
```

**注意**: 既存の`optimize`コマンドのサブコマンドとして追加されます。
現在のサブコマンド: `period`, `allocate`, `adjust`
新しいサブコマンド: `candidates`

### オプション
- `--allocation, -a` - 既存の最適化結果ファイル（必須）
- `--fields-file, -f` - 圃場設定ファイル（必須）
- `--crops-file, -c` - 作物設定ファイル（必須）
- `--target-crop, -t` - 対象作物ID（必須）
- `--interaction-rules-file, -i` - 相互作用ルールファイル（オプション）
- `--planning-start, -s` - 計画期間開始日（必須）
- `--planning-end, -e` - 計画期間終了日（必須）
- `--weather-file, -w` - 気象データファイル（必須）
- `--output, -o` - 出力ファイルパス（必須）
- `--format, -fmt` - 出力形式（table/json、デフォルト: table）

**注意**: 既存のoptimizeコマンドと同様のオプション命名規則に従っています。
- `--fields-file` (allocateコマンドと同じ)
- `--crops-file` (allocateコマンドと同じ)
- `--planning-start/--planning-end` (allocateコマンドと同じ)
- `--weather-file` (allocateコマンドと同じ)

### 使用例
```bash
# 基本的な使用例（Table形式）
agrr optimize candidates \
  --allocation current_allocation.json \
  --fields-file fields.json \
  --crops-file crops.json \
  --target-crop tomato \
  --planning-start 2024-04-01 --planning-end 2024-10-31 \
  --weather-file weather.json \
  --output candidates.txt

# 相互作用ルール付き（Table形式）
agrr optimize candidates \
  --allocation current_allocation.json \
  --fields-file fields.json \
  --crops-file crops.json \
  --target-crop tomato \
  --interaction-rules-file interaction_rules.json \
  --planning-start 2024-04-01 --planning-end 2024-10-31 \
  --weather-file weather.json \
  --output candidates.txt

# JSON出力（adjust用）
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

**注意**: 既存のoptimizeコマンドと同様の使用例形式に従っています。
- バックスラッシュ（`\`）による行継続
- 同じオプション名と順序
- 同じファイル拡張子（`.json`）

## アーキテクチャ設計

### Clean Architecture準拠
既存のClean Architectureに従って実装：

```
src/agrr_core/
├── adapter/
│   ├── controllers/
│   │   └── candidate_suggestion_cli_controller.py
│   └── presenters/
│       └── candidate_suggestion_cli_presenter.py
├── usecase/
│   ├── interactors/
│   │   └── candidate_suggestion_interactor.py
│   ├── dto/
│   │   ├── candidate_suggestion_request_dto.py
│   │   └── candidate_suggestion_response_dto.py
│   └── gateways/
│       └── candidate_suggestion_gateway.py
└── entity/
    └── entities/
        └── candidate_suggestion_entity.py
```

### コンポーネント設計

#### Entity Layer
- `CandidateSuggestion` - 候補提案エンティティ
- `CandidateType` - 候補タイプ（INSERT/MOVE）

#### UseCase Layer
- `CandidateSuggestionInteractor` - 候補提案ユースケース
- `CandidateSuggestionRequestDTO` - リクエストDTO
- `CandidateSuggestionResponseDTO` - レスポンスDTO
- `CandidateSuggestionGateway` - ゲートウェイインターフェース

#### Adapter Layer
- `CandidateSuggestionCliController` - CLIコントローラー
- `CandidateSuggestionCliPresenter` - CLIプレゼンター
- `CandidateSuggestionFileGateway` - ファイルゲートウェイ実装

## 実装方針

### 1. 既存システムの再利用
- `GrowthPeriodOptimizeInteractor`でGDD計算
- `ViolationCheckerService`で制約チェック
- `OptimizationMetrics`で利益計算
- `MoveInstruction`エンティティを活用

### 2. パフォーマンス最適化
- 圃場ごとの候補生成を並列化
- GDD計算のキャッシュ活用
- 制約チェックの効率化

### 3. adjust連携
- 候補結果をmoves.json形式で出力
- 既存の`MoveInstruction`エンティティを活用

## 出力例

### Table形式
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

### JSON形式（adjust用）
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

## テスト要件

### 単体テスト
- `CandidateSuggestionInteractor`のテスト
- 利益計算ロジックのテスト
- 制約チェックのテスト

### 統合テスト
- CLIコマンドのテスト
- ファイル入出力のテスト
- adjust連携のテスト

### パフォーマンステスト
- 大量データでの実行時間テスト
- メモリ使用量テスト

## 非機能要件

### パフォーマンス
- 圃場数100、作物数50の規模で1分以内に完了
- メモリ使用量は既存の最適化処理と同等以下

### 可用性
- 既存の最適化処理に影響を与えない
- エラー時は適切なエラーメッセージを表示

### 保守性
- Clean Architectureに準拠
- 既存のテスト戦略に従う
- ドキュメント化を徹底

## 実装スケジュール

1. **要件定義完了** ✅
2. **アーキテクチャ設計** ✅
3. **CLI仕様整合性確認** ✅
4. **Entity/DTO実装**
5. **Interactor実装**
6. **Controller/Presenter実装**
7. **テスト実装**
8. **統合テスト**
9. **ドキュメント整備**

## 関連ドキュメント

- [Clean Architecture設計原則](ARCHITECTURE.md)
- [最適化処理概要](ALLOCATION_ADJUST_OPTIMIZATION.md)
- [テスト戦略](TEST_STRATEGY.md)
- [パフォーマンス要件](PERFORMANCE_REQUIREMENTS.md)
