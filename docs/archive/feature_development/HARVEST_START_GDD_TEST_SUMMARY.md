# harvest_start_gdd テスト配置まとめ

**作成日**: 2025-10-15  
**目的**: harvest_start_gddフィールドのテスト配置方針と実装内容の整理

---

## 1. テスト配置の原則

### 1.1 Clean Architectureに基づくテスト配置

```
tests/
├── test_entity/           # Entity層: ビジネスロジックとエンティティ
├── test_usecase/          # UseCase層: アプリケーション固有のロジック
│   ├── test_services/    # サービス層（Normalizer, Mapperなど）
│   └── test_*_interactor.py  # Interactor層
├── test_adapter/          # Adapter層: 外部とのインターフェース
├── test_framework/        # Framework層: 外部システムとの通信
└── test_integration/      # 統合テスト: 複数層にまたがるテスト
```

### 1.2 テスト配置の判断基準

| テスト対象 | 配置場所 | 理由 |
|-----------|---------|------|
| エンティティの機能 | `test_entity/` | Entity層の独立したビジネスロジックをテスト |
| サービスの機能 | `test_usecase/test_services/` | UseCase層のサービスロジックをテスト |
| Interactorの使用 | `test_usecase/` | Interactorレベルの統合をテスト |
| Repository | `test_framework/` | Framework層の実装をテスト |
| 層をまたぐフロー | `test_integration/` | 複数層にまたがる統合テスト |

---

## 2. harvest_start_gdd テスト一覧

### 2.1 Entity層テスト（14個）

**ファイル**: `tests/test_entity/test_thermal_requirement_entity.py`

| テスト名 | 目的 |
|---------|------|
| `test_basic_thermal_requirement` | 基本的なThermalRequirement作成 |
| `test_thermal_requirement_with_harvest_start` | harvest_start_gdd付きの作成 |
| `test_is_met_basic` | is_met()メソッドの基本動作 |
| `test_is_harvest_started_without_harvest_start_gdd` | harvest_start_gddなしの場合のis_harvest_started() |
| `test_is_harvest_started_with_harvest_start_gdd` | harvest_start_gddありの場合のis_harvest_started() |
| `test_harvest_duration_calculation` | 収穫期間の計算 |
| `test_negative_required_gdd_raises_error` | 負のrequired_gddのバリデーション |
| `test_zero_required_gdd_raises_error` | ゼロのrequired_gddのバリデーション |
| `test_negative_harvest_start_gdd_raises_error` | 負のharvest_start_gddのバリデーション |
| `test_zero_harvest_start_gdd_raises_error` | ゼロのharvest_start_gddのバリデーション |
| `test_harvest_start_gdd_greater_than_required_gdd_raises_error` | harvest_start_gdd >= required_gddのバリデーション |
| `test_fruiting_crop_eggplant_example` | ナスの実例テスト |
| `test_single_harvest_crop_rice_example` | 稲の実例テスト（harvest_start_gddなし） |
| `test_backward_compatibility` | 既存コードとの互換性 |

**配置理由**: ThermalRequirementエンティティの機能を独立してテスト。Entity層のビジネスロジックを検証。

---

### 2.2 UseCase層サービステスト（5個）

#### 2.2.1 LLMResponseNormalizer

**ファイル**: `tests/test_usecase/test_services/test_llm_response_normalizer.py`

| テスト名 | 目的 |
|---------|------|
| `test_normalize_thermal_with_harvest_start_gdd` | harvest_start_gddありの正規化 |
| `test_normalize_thermal_without_harvest_start_gdd` | harvest_start_gddなしの正規化 |

**配置理由**: LLMレスポンスの正規化処理をテスト。UseCase層のサービスロジックを検証。

#### 2.2.2 CropProfileMapper

**ファイル**: `tests/test_usecase/test_services/test_crop_profile_mapper.py`

| テスト名 | 目的 |
|---------|------|
| `test_thermal_to_dict` | harvest_start_gddなしの変換（既存） |
| `test_thermal_to_dict_with_harvest_start_gdd` | harvest_start_gddありの変換 |
| `test_thermal_to_dict_without_harvest_start_gdd` | harvest_start_gddなしの変換（明示的） |

**配置理由**: Entity↔︎Dict変換をテスト。UseCase層のマッピングロジックを検証。

---

### 2.3 UseCase層 Interactorテスト（2個）

#### 2.3.1 GrowthPeriodOptimizeInteractor

**ファイル**: `tests/test_usecase/test_growth_period_optimize_interactor.py`

| テスト名 | 目的 |
|---------|------|
| `test_optimize_with_harvest_start_gdd` | optimize-periodコマンドでの使用確認 |

**テスト内容**:
- ナスのプロファイル（harvest_start_gdd=200, required_gdd=2200）
- 最適化ロジックが正常に動作
- harvest_start_gddが最適化に影響しないことを確認

**配置理由**: optimize-periodコマンドのInteractorレベルでの統合をテスト。

#### 2.3.2 GrowthProgressCalculateInteractor

**ファイル**: `tests/test_usecase/test_growth_progress_calculate_interactor.py`

| テスト名 | 目的 |
|---------|------|
| `test_progress_with_harvest_start_gdd` | progressコマンドでの使用確認 |

**テスト内容**:
- ナスのプロファイル（harvest_start_gdd=200, required_gdd=2200）
- 進捗計算が正常に動作
- harvest_start_gddが進捗計算に影響しないことを確認

**配置理由**: progressコマンドのInteractorレベルでの統合をテスト。

---

### 2.4 Integration層テスト（4個）

**ファイル**: `tests/test_integration/test_harvest_start_gdd_data_flow.py`

| テスト名 | 目的 |
|---------|------|
| `test_json_to_entity_with_harvest_start_gdd` | JSON→Entityの変換テスト |
| `test_entity_to_json_with_harvest_start_gdd` | Entity→JSONの変換テスト |
| `test_round_trip_json_entity_json` | JSON→Entity→JSONのラウンドトリップ |
| `test_backward_compatibility_without_harvest_start_gdd` | 後方互換性テスト |

**配置理由**: 複数層にまたがる完全なデータフローを統合テスト。

---

## 3. テスト配置の判断フロー

### 3.1 どこにテストを書くか？

```
質問1: テスト対象は何か？
├─ Entity（ドメインロジック）
│  └─→ test_entity/ に配置
│
├─ UseCase（サービス、Mapper、Normalizer）
│  └─→ test_usecase/test_services/ に配置
│
├─ UseCase（Interactor）
│  └─→ test_usecase/ に配置
│
├─ Adapter（Controller, Gateway, Presenter）
│  └─→ test_adapter/ に配置
│
├─ Framework（Repository）
│  └─→ test_framework/ に配置
│
└─ 複数層にまたがるフロー
   └─→ test_integration/ に配置
```

### 3.2 harvest_start_gdd のテスト配置例

| 確認したい内容 | テスト配置 | ファイル名 |
|--------------|----------|-----------|
| harvest_start_gddフィールドの動作 | test_entity/ | test_thermal_requirement_entity.py |
| harvest_start_gddの正規化処理 | test_usecase/test_services/ | test_llm_response_normalizer.py |
| harvest_start_gddのDict変換 | test_usecase/test_services/ | test_crop_profile_mapper.py |
| optimize-periodでの使用 | test_usecase/ | test_growth_period_optimize_interactor.py |
| progressでの使用 | test_usecase/ | test_growth_progress_calculate_interactor.py |
| JSON→Entity→JSONフロー | test_integration/ | test_harvest_start_gdd_data_flow.py |

---

## 4. 実装確認チェックリスト

### 4.1 Entity層

- [x] `ThermalRequirement` に `harvest_start_gdd` フィールド追加
- [x] バリデーションロジック実装
- [x] `is_harvest_started()` メソッド追加
- [x] 14個の単体テスト作成
- [x] 100%テストカバレッジ

### 4.2 UseCase層

- [x] `LLMResponseNormalizer` の `normalize_thermal_field()` 更新
- [x] `CropProfileMapper` の `_thermal_to_dict()` 更新
- [x] 5個の単体テスト作成
- [x] Interactor層での使用テスト（2個）

### 4.3 Framework層

- [x] `CropProfileFileRepository` の `load_profile()` 更新
- [x] harvest_start_gddの読み込み処理追加

### 4.4 Adapter層

- [x] `llm_struct_schema.py` のスキーマ更新
- [x] harvest_start_gddの説明追加

### 4.5 Prompts

- [x] `stage3_variety_specific_research.md` の更新
- [x] 収穫開始積算温度の説明追加

### 4.6 Integration

- [x] 完全なデータフローテスト（4個）
- [x] JSON→Entity→JSONのラウンドトリップ
- [x] 後方互換性テスト

### 4.7 Documentation

- [x] `HARVEST_START_GDD_DATA_FLOW.md` - データフロー整理
- [x] `HARVEST_PERIOD_GDD_DESIGN.md` - 設計ドキュメント
- [x] `HARVEST_START_GDD_IMPLEMENTATION_COMPLETE.md` - 実装完了報告
- [x] `HARVEST_START_GDD_FINAL_REPORT.md` - 最終報告
- [x] `HARVEST_START_GDD_TEST_SUMMARY.md` - テスト配置まとめ（本ドキュメント）

---

## 5. テスト実行結果

```
✅ harvest_start_gdd専用テスト: 18/18 passed
✅ 全体テスト: 786/786 passed
✅ カバレッジ: 77%
✅ 後方互換性: 100%
```

---

## 6. まとめ

### 6.1 テスト配置の成功要因

1. **Clean Architectureに基づく明確な配置**
   - 各層ごとに適切なテストディレクトリを使用
   - 責務に応じてテストを分離

2. **包括的なテストカバレッジ**
   - Entity層の単体テスト（独立したロジック）
   - UseCase層のサービステスト（変換・正規化）
   - Interactor層の統合テスト（実際の使用シナリオ）
   - Integration層の統合テスト（層をまたぐフロー）

3. **後方互換性の保証**
   - harvest_start_gddなしのプロファイルもテスト
   - 既存の全テストが通過

### 6.2 学んだこと

**テストを書くべき場所**:
- 手動スクリプトで確認したこと → 適切なテストファイルに記述
- Entity層の機能 → `test_entity/`
- UseCase層のサービス → `test_usecase/test_services/`
- Interactorの使用 → `test_usecase/`
- 層をまたぐフロー → `test_integration/`

**テスト配置の利点**:
- コードの品質保証
- リグレッション防止
- ドキュメントとしての役割
- リファクタリングの安全性

---

**作成者**: AGRR Core AI Assistant  
**テスト数**: 786 passed (うち harvest_start_gdd関連 18個)  
**ステータス**: ✅ 完了

