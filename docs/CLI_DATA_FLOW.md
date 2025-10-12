# CLI データフロー図

## 概要

このドキュメントでは、AGRRプロジェクトのCLIにおけるデータの移送（データフロー）を、コンポーネント間の相互作用を中心に説明します。

特に、新たに追加された`groups`フィールドと`InteractionRule`エンティティのデータフローに焦点を当てます。

## アーキテクチャ層の概要

```
┌─────────────────────────────────────────────────────────┐
│  CLI Layer (Entry Point)                                │
│  - cli.py: コマンド解析とルーティング                    │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Adapter Layer (Controllers & Gateways)                 │
│  - Controller: CLIコマンドの制御                         │
│  - Gateway: 外部サービス（LLM、ファイル）へのアクセス     │
│  - Presenter: 出力フォーマット                           │
│  - Mapper: エンティティ⇔DTO変換                         │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  UseCase Layer (Interactors)                            │
│  - ビジネスロジックの実行                                │
│  - ユースケースの調整                                    │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Entity Layer (Domain Entities)                         │
│  - Crop, InteractionRule, Field等                       │
│  - ドメインロジック                                      │
└─────────────────────────────────────────────────────────┘
```

## 1. `agrr crop` コマンドのデータフロー

### 概要
作物の成長要件をLLMから取得し、groupsフィールドを含む完全な情報を出力します。

### データフロー図

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. CLI Input                                                     │
│    $ agrr crop --query "トマト"                                  │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│ 2. cli.py (main)                                                 │
│    - コマンド解析: args[0] == 'crop'                             │
│    - Containerの初期化不要（直接ワイヤリング）                    │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│ 3. CropCliCraftController (Adapter Layer)                        │
│    controller.run(args[1:])                                      │
│    - 引数解析: --query "トマト"                                   │
│    - RequestDTOの作成                                            │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│ 4. CropRequirementCraftRequestDTO (UseCase Layer)                │
│    {                                                             │
│      crop_query: "トマト"                                        │
│    }                                                             │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│ 5. CropRequirementCraftInteractor (UseCase Layer)                │
│    interactor.execute(request)                                   │
│    - Gateway経由でLLM呼び出し                                     │
│    - 3ステップフロー実行:                                         │
│      1) extract_crop_variety()                                   │
│      2) define_growth_stages()                                   │
│      3) research_stage_requirements()                            │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│ 6. CropRequirementGatewayImpl (Adapter Layer)                    │
│    gateway.extract_crop_variety("トマト")                        │
│    - LLMクライアント呼び出し                                      │
│    - レスポンス正規化                                            │
│    - 作物情報抽出:                                               │
│      {                                                           │
│        "crop": "tomato",                                         │
│        "variety": "general",                                     │
│        "groups": ["Solanaceae", "fruiting_vegetables"]  ← NEW   │
│      }                                                           │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│ 7. Crop Entity (Entity Layer)                                    │
│    Crop(                                                         │
│      crop_id="tomato",                                           │
│      name="Tomato",                                              │
│      area_per_unit=0.25,                                         │
│      variety="general",                                          │
│      groups=["Solanaceae", "fruiting_vegetables"]  ← NEW         │
│    )                                                             │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│ 8. CropRequirementAggregate (Entity Layer)                       │
│    CropRequirementAggregate(                                     │
│      crop=crop,                                                  │
│      stage_requirements=[...]                                    │
│    )                                                             │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│ 9. CropRequirementMapper (Adapter Layer)                         │
│    mapper.aggregate_to_payload(aggregate)                        │
│    - Crop → Dict変換                                             │
│    - groupsフィールドも含める                                     │
│    {                                                             │
│      "crop_id": "tomato",                                        │
│      "crop_name": "Tomato",                                      │
│      "groups": ["Solanaceae", "fruiting_vegetables"],  ← NEW     │
│      "stages": [...]                                             │
│    }                                                             │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│ 10. CropRequirementCraftPresenter (Adapter Layer)                │
│     presenter.present_success(payload)                           │
│     - JSON形式でラップ                                           │
│     {                                                            │
│       "success": true,                                           │
│       "data": {                                                  │
│         "crop_id": "tomato",                                     │
│         "groups": ["Solanaceae", "fruiting_vegetables"],  ← NEW  │
│         ...                                                      │
│       }                                                          │
│     }                                                            │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│ 11. CLI Output (stdout)                                          │
│     print(json.dumps(result, ensure_ascii=False))                │
│     {                                                            │
│       "success": true,                                           │
│       "data": {                                                  │
│         "crop_id": "tomato",                                     │
│         "crop_name": "Tomato",                                   │
│         "groups": ["Solanaceae", "fruiting_vegetables"],         │
│         "stages": [...]                                          │
│       }                                                          │
│     }                                                            │
└──────────────────────────────────────────────────────────────────┘
```

### データ移送の重要ポイント

| 層 | コンポーネント | データ型 | 目的 |
|----|-------------|---------|------|
| CLI | cli.py | `List[str]` (args) | コマンドライン引数の解析 |
| Adapter | Controller | `CropRequirementCraftRequestDTO` | リクエストの構造化 |
| UseCase | Interactor | `CropRequirementCraftRequestDTO` | ビジネスロジック実行 |
| Adapter | Gateway | `Dict[str, Any]` (LLMレスポンス) | 外部サービスとの通信 |
| Entity | Crop | `Crop` entity | ドメインモデル |
| Entity | Aggregate | `CropRequirementAggregate` | 集約ルート |
| Adapter | Mapper | `Dict[str, Any]` (payload) | エンティティ→DTO変換 |
| Adapter | Presenter | `Dict[str, Any]` (response) | 出力フォーマット |
| CLI | stdout | JSON string | ユーザーへの出力 |

## 2. JSONファイル経由のデータフロー

### 概要
`agrr crop`コマンドで生成したJSONファイルを、他のコマンド（`progress`, `optimize-period`）で読み込む場合のデータフローです。

### データフロー図

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. JSON File (crop_requirement.json)                             │
│    {                                                             │
│      "crop_id": "tomato",                                        │
│      "crop_name": "Tomato",                                      │
│      "groups": ["Solanaceae", "fruiting_vegetables"],  ← NEW     │
│      "area_per_unit": 0.25,                                      │
│      "revenue_per_area": 50000,                                  │
│      "stages": [...]                                             │
│    }                                                             │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│ 2. CropRequirementGatewayImpl.load_from_file()                   │
│    gateway.load_from_file("crop_requirement.json")               │
│    - FileRepositoryでJSONを読み込み                               │
│    - JSONをパース                                                │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│ 3. Crop Entity再構築                                             │
│    Crop(                                                         │
│      crop_id=data["crop_id"],                                    │
│      name=data["crop_name"],                                     │
│      area_per_unit=data["area_per_unit"],                        │
│      groups=data.get("groups"),  ← NEW (Optional)                │
│      ...                                                         │
│    )                                                             │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│ 4. CropRequirementAggregate再構築                                │
│    CropRequirementAggregate(crop=crop, stage_requirements=[...]) │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│ 5. UseCase Layer (Interactor)での利用                            │
│    - 最適化計算                                                  │
│    - 成長進捗計算                                                │
│    - InteractionRuleとのマッチング（将来実装）                   │
└──────────────────────────────────────────────────────────────────┘
```

## 3. InteractionRule のデータフロー（将来実装）

### 概要
相互作用規則をJSONファイルから読み込み、最適化計算で利用する際のデータフローです。

### データフロー図

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. JSON File (interaction_rules.json)                            │
│    [                                                             │
│      {                                                           │
│        "rule_id": "rule_001",                                    │
│        "rule_type": "continuous_cultivation",                    │
│        "source_group": "Solanaceae",                             │
│        "target_group": "Solanaceae",                             │
│        "impact_ratio": 0.7,                                      │
│        "is_directional": true,                                   │
│        "description": "ナス科の連作障害"                         │
│      }                                                           │
│    ]                                                             │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│ 2. InteractionRuleGateway (将来実装)                             │
│    gateway.load_rules_from_file("interaction_rules.json")        │
│    - FileRepositoryでJSONを読み込み                               │
│    - JSONをパース                                                │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│ 3. InteractionRule Entity構築                                    │
│    [                                                             │
│      InteractionRule(                                            │
│        rule_id="rule_001",                                       │
│        rule_type="continuous_cultivation",                       │
│        source_group="Solanaceae",                                │
│        target_group="Solanaceae",                                │
│        impact_ratio=0.7,                                         │
│        is_directional=True,                                      │
│        description="ナス科の連作障害"                            │
│      ),                                                          │
│      ...                                                         │
│    ]                                                             │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│ 4. Optimizer (UseCase Layer)                                     │
│    - Cropのgroupsを確認                                          │
│    - 適用可能なInteractionRuleを検索                              │
│    - impact_ratioを収益計算に適用                                 │
│                                                                  │
│    例:                                                           │
│    前作: トマト (groups=["Solanaceae"])                          │
│    後作: ナス (groups=["Solanaceae"])                            │
│    → rule_001が適用される (impact_ratio=0.7)                     │
│    → 後作の収益が70%になる                                       │
└──────────────────────────────────────────────────────────────────┘
```

## 4. コンポーネント間の責務

### 4.1 Entity Layer

**責務**: ドメインロジックとビジネスルールの実装

| エンティティ | 責務 |
|------------|------|
| `Crop` | 作物の基本属性、groupsの保持 |
| `InteractionRule` | 相互作用ルールの定義、マッチング判定 |
| `EntityType` | エンティティタイプの型安全性 |

**データの流れ**:
- 入力: Gateway/Mapperから構築される
- 出力: Mapper経由でDTOに変換される

### 4.2 UseCase Layer

**責務**: ビジネスロジックの調整、ユースケースの実行

| コンポーネント | 責務 |
|--------------|------|
| `CropRequirementCraftInteractor` | 作物要件の取得フロー制御 |
| `Optimizer` (将来) | 最適化計算、InteractionRule適用 |

**データの流れ**:
- 入力: RequestDTO
- 出力: ResponseDTO (Presenter経由)

### 4.3 Adapter Layer

**責務**: 外部システムとの統合、データ変換

| コンポーネント | 責務 | データ変換 |
|--------------|------|-----------|
| `Controller` | CLIコマンド制御 | CLI args → RequestDTO |
| `Gateway` | 外部サービス統合 | External API → Entity |
| `Mapper` | エンティティ⇔DTO変換 | Entity → Dict/JSON |
| `Presenter` | 出力フォーマット | Data → Formatted output |

**データの流れ**:
- Controller: CLI → UseCase
- Gateway: External → Entity
- Mapper: Entity ⇔ DTO
- Presenter: UseCase → CLI

## 5. データ型の変換マトリクス

| レイヤー遷移 | 入力型 | 出力型 | 変換コンポーネント |
|------------|-------|--------|------------------|
| CLI → Controller | `List[str]` | `RequestDTO` | Controller |
| Controller → Interactor | `RequestDTO` | `ResponseDTO` | Interactor |
| Interactor → Gateway | Request params | `Entity` | Gateway |
| Gateway → LLM | Request dict | JSON response | LLMClient |
| LLM → Entity | JSON dict | `Crop`, etc. | Gateway |
| Entity → Mapper | `CropRequirementAggregate` | `Dict[str, Any]` | Mapper |
| Mapper → Presenter | `Dict[str, Any]` | Formatted dict | Presenter |
| Presenter → CLI | Response dict | JSON string | Controller |

## 6. groups フィールドの移送追跡

### 6.1 生成フロー (agrr crop)

```
LLM Response (JSON)
  ↓ (CropRequirementGatewayImpl)
Crop Entity (groups: List[str])
  ↓ (CropRequirementAggregate)
Aggregate (crop.groups)
  ↓ (CropRequirementMapper)
Payload Dict (groups: List[str])
  ↓ (Presenter)
Response JSON (groups: [...])
  ↓ (Controller)
stdout (JSON string)
```

### 6.2 読み込みフロー (agrr optimize-period)

```
JSON File (groups: [...])
  ↓ (FileRepository.read())
Dict (groups: List[str])
  ↓ (CropRequirementGatewayImpl.load_from_file)
Crop Entity (groups: List[str])
  ↓ (CropRequirementAggregate)
Aggregate (crop.groups)
  ↓ (Optimizer - 将来)
InteractionRule matching
```

## 7. エラーハンドリングとバリデーション

### 各層での検証

| 層 | 検証内容 | エラーハンドリング |
|----|---------|------------------|
| **Entity** | - groups要素の型チェック<br>- InteractionRuleのimpact_ratio範囲 | ValueError例外 |
| **UseCase** | - RequestDTOのバリデーション<br>- ビジネスルール検証 | ドメイン例外 |
| **Adapter** | - JSON形式の検証<br>- ファイル存在確認 | FileError例外 |
| **CLI** | - コマンド引数の検証 | エラーメッセージ表示 |

## 8. テスタビリティ

### 各層のテスト戦略

| 層 | テスト種別 | 内容 |
|----|----------|------|
| **Entity** | 単体テスト | - Cropのgroups設定/取得<br>- InteractionRuleのマッチング |
| **UseCase** | 単体テスト | - Interactorのロジック<br>- Gatewayのモック化 |
| **Adapter** | 統合テスト | - Gateway実装のファイルI/O<br>- Mapperの変換精度 |
| **CLI** | E2Eテスト | - コマンド実行<br>- JSON出力検証 |

## 9. 将来の拡張ポイント

### 9.1 InteractionRule の統合

```
Optimizer
  ├─ CropAllocationを評価
  ├─ 各Cropのgroupsをチェックsrc
  ├─ 適用可能なInteractionRuleを検索
  ├─ impact_ratioを収益に適用
  └─ 最適解を返す
```

### 9.2 複数ルールの適用

```python
# 複数ルールの累積適用
base_revenue = 100000
applicable_rules = [
    (rule_continuous_cultivation, 0.7),  # 連作障害
    (rule_soil_match, 1.2),              # 土壌適合
]
final_revenue = base_revenue * 0.7 * 1.2  # 84000
```

## まとめ

- **Entity層**: ビジネスロジックとドメインモデル（groups, InteractionRule）
- **UseCase層**: ユースケースの調整とビジネスロジックの実行
- **Adapter層**: 外部システムとの統合とデータ変換
- **CLI層**: ユーザーインターフェースとコマンド解析

新しく追加された`groups`フィールドと`InteractionRule`は、各層を適切に移送され、型安全性とテスタビリティが確保されています。

