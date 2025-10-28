# AGRR.CORE ドキュメント索引

プロジェクトの全ドキュメントへのナビゲーション

> **📦 アーカイブについて**: 過去の実装レポート、テスト結果、完了報告などは`archive/`ディレクトリに整理されています（152ドキュメント）。現在アクティブなドキュメントのみがこのディレクトリに配置されています（25ドキュメント）。

---

## 🎯 目的別ガイド

### 👋 初めての方

1. **プロジェクト概要**
   - [../README.md](../README.md) - プロジェクト紹介、インストール方法
   
2. **アーキテクチャ理解**
   - [architecture/ARCHITECTURE_SUMMARY.md](architecture/ARCHITECTURE_SUMMARY.md) ⭐ **まずここから**
   - [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md) - 詳細設計

3. **使い方**
   - [api/README.md](api/README.md) - CLI使い方
   - サンプルデータ: `test_data/` ディレクトリ

### 🔧 開発者向け

1. **アーキテクチャ詳細**
   - [architecture/ARCHITECTURE_OVERVIEW_AND_RECOMMENDATIONS.md](architecture/ARCHITECTURE_OVERVIEW_AND_RECOMMENDATIONS.md) - 全体俯瞰と提案
   - [architecture/CLEAN_ARCHITECTURE_GATEWAY_GUIDELINES.md](architecture/CLEAN_ARCHITECTURE_GATEWAY_GUIDELINES.md) - Gateway設計ガイドライン
   - [architecture/REFACTORING_ROADMAP.md](architecture/REFACTORING_ROADMAP.md) - リファクタリング計画

2. **アルゴリズム**
   - [algorithms/QUICK_START_DP_ALNS.md](algorithms/QUICK_START_DP_ALNS.md) - DP+ALNSクイックスタート
   - [algorithms/ALNS_INTEGRATION_GUIDE.md](algorithms/ALNS_INTEGRATION_GUIDE.md) - ALNS統合ガイド
   - [algorithms/algorithm_selection_guide.md](algorithms/algorithm_selection_guide.md) - アルゴリズム選択ガイド

3. **API Reference**
   - [api/README.md](api/README.md) - CLI API
   - [api/adapter/](api/adapter/) - Adapter層API
   - [api/framework/](api/framework/) - Framework層API
   - [api/candidate_suggestion_api_reference.md](api/candidate_suggestion_api_reference.md) - 候補リスト提示機能API

### 🚀 アルゴリズム研究者向け

1. **最適化アルゴリズム**
   - [algorithms/algorithm_selection_guide.md](algorithms/algorithm_selection_guide.md) - アルゴリズム選択ガイド
   - [algorithms/optimization_algorithm_greedy_approach.md](algorithms/optimization_algorithm_greedy_approach.md) - Greedyアプローチ
   - [algorithms/optimization_design_multi_field_crop_allocation.md](algorithms/optimization_design_multi_field_crop_allocation.md) - 複数圃場最適化設計

2. **実験データ**
   - `test_data/` - 実験用データセット

---

## 📁 アクティブドキュメント一覧

### 📐 アーキテクチャ

| ドキュメント | 説明 | 対象者 |
|------------|------|--------|
| [architecture/ARCHITECTURE_SUMMARY.md](architecture/ARCHITECTURE_SUMMARY.md) | プロジェクト全体俯瞰 | 全員 ⭐ |
| [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md) | Clean Architecture詳細 | 開発者 |
| [architecture/ARCHITECTURE_OVERVIEW_AND_RECOMMENDATIONS.md](architecture/ARCHITECTURE_OVERVIEW_AND_RECOMMENDATIONS.md) | 改善提案 | 開発者 |
| [architecture/CLEAN_ARCHITECTURE_GATEWAY_GUIDELINES.md](architecture/CLEAN_ARCHITECTURE_GATEWAY_GUIDELINES.md) | Gateway設計ガイドライン | 開発者 |
| [architecture/REFACTORING_ROADMAP.md](architecture/REFACTORING_ROADMAP.md) | リファクタリング計画 | 開発者 |
| [architecture/FINAL_IMPLEMENTATION_POLICY.md](architecture/FINAL_IMPLEMENTATION_POLICY.md) | 実装ポリシー | 開発者 |

### 🔬 アルゴリズム・最適化

| ドキュメント | 説明 | 対象者 |
|------------|------|--------|
| [algorithms/QUICK_START_DP_ALNS.md](algorithms/QUICK_START_DP_ALNS.md) | DP+ALNSクイックスタート | 開発者 |
| [algorithms/ALNS_INTEGRATION_GUIDE.md](algorithms/ALNS_INTEGRATION_GUIDE.md) | ALNS統合ガイド | 開発者 |
| [algorithms/algorithm_selection_guide.md](algorithms/algorithm_selection_guide.md) | アルゴリズム選択ガイド | 研究者 |
| [algorithms/optimization_algorithm_greedy_approach.md](algorithms/optimization_algorithm_greedy_approach.md) | Greedyアプローチ | 研究者 |
| [algorithms/optimization_design_multi_field_crop_allocation.md](algorithms/optimization_design_multi_field_crop_allocation.md) | 複数圃場最適化設計 | 研究者 |

### 📖 ガイド・マニュアル

| ドキュメント | 説明 | 対象者 |
|------------|------|--------|
| [guides/ALLOCATION_ADJUST_GUIDE.md](guides/ALLOCATION_ADJUST_GUIDE.md) | 配分調整ガイド | ユーザー |
| [guides/CLI_USER_GUIDE_FALLOW_PERIOD.md](guides/CLI_USER_GUIDE_FALLOW_PERIOD.md) | 休閑期間ユーザーガイド | ユーザー |
| [guides/MIGRATION_GUIDE_MAX_TEMPERATURE.md](guides/MIGRATION_GUIDE_MAX_TEMPERATURE.md) | 最高温度マイグレーションガイド | 開発者 |
| [guides/TEST_EXECUTION_GUIDE.md](guides/TEST_EXECUTION_GUIDE.md) | テスト実行ガイド | 開発者 |
| [guides/TEST_FIX_GUIDE.md](guides/TEST_FIX_GUIDE.md) | テスト修正ガイド | 開発者 |
| [guides/US_WEATHER_GUIDE.md](guides/US_WEATHER_GUIDE.md) | US天気ガイド | ユーザー |
| [guides/US_WEATHER_LONG_TERM_GUIDE.md](guides/US_WEATHER_LONG_TERM_GUIDE.md) | US天気長期ガイド | ユーザー |

### 🔄 データフロー

| ドキュメント | 説明 | 対象者 |
|------------|------|--------|
| [data_flows/CLI_DATA_FLOW.md](data_flows/CLI_DATA_FLOW.md) | CLIデータフロー | 開発者 |
| [data_flows/CLI_DATA_FLOW_JMA.md](data_flows/CLI_DATA_FLOW_JMA.md) | 気象庁データフロー | 開発者 |
| [data_flows/DATA_FLOW_CROP_FAMILY.md](data_flows/DATA_FLOW_CROP_FAMILY.md) | 作物ファミリーデータフロー | 開発者 |
| [data_flows/FIELD_DATA_FLOW_SIMPLIFIED.md](data_flows/FIELD_DATA_FLOW_SIMPLIFIED.md) | 圃場データフロー（簡易版） | 開発者 |

### 🛠️ 技術リファレンス

| ドキュメント | 説明 | 対象者 |
|------------|------|--------|
| [technical/AUTO_ESTIMATION_EXPLANATION.md](technical/AUTO_ESTIMATION_EXPLANATION.md) | 自動推定の説明 | 開発者 |
| [technical/DISTRIBUTION.md](technical/DISTRIBUTION.md) | 配布方法 | 開発者 |
| [technical/FIELD_CONFIG_FORMAT.md](technical/FIELD_CONFIG_FORMAT.md) | 圃場設定フォーマット | ユーザー |

### 📊 API Reference

| ドキュメント | 説明 |
|------------|------|
| [api/README.md](api/README.md) | CLI API概要 |
| [api/adapter/cli_presenter.md](api/adapter/cli_presenter.md) | Presenter API |
| [api/candidate_suggestion_api_reference.md](api/candidate_suggestion_api_reference.md) | 候補リスト提示機能API |

### 🌱 候補リスト提示機能

| ドキュメント | 説明 | 対象者 |
|------------|------|--------|
| [CANDIDATE_SUGGESTION_FEATURE.md](CANDIDATE_SUGGESTION_FEATURE.md) | 要件定義書 | 開発者 |
| [CANDIDATE_SUGGESTION_TEST_DESIGN.md](CANDIDATE_SUGGESTION_TEST_DESIGN.md) | テスト設計書 | 開発者 |
| [CANDIDATE_SUGGESTION_USER_GUIDE.md](CANDIDATE_SUGGESTION_USER_GUIDE.md) | ユーザーガイド | ユーザー |
| [api/candidate_suggestion_api_reference.md](api/candidate_suggestion_api_reference.md) | APIリファレンス | 開発者 |

### 🌾 肥料推奨機能

| ドキュメント | 説明 | 対象者 |
|------------|------|--------|
| [FERTILIZER_RECOMMENDATION_README.md](FERTILIZER_RECOMMENDATION_README.md) | 機能概要・クイックスタート | 全員 ⭐ |
| [FERTILIZER_RECOMMENDATION_USER_GUIDE.md](FERTILIZER_RECOMMENDATION_USER_GUIDE.md) | ユーザーガイド・使用例 | ユーザー ⭐ |
| [architecture/FERTILIZER_RECOMMENDATION_DESIGN.md](architecture/FERTILIZER_RECOMMENDATION_DESIGN.md) | 設計書・アーキテクチャ | 開発者 |
| [api/fertilizer_recommendation_api_reference.md](api/fertilizer_recommendation_api_reference.md) | API・CLI仕様 | 開発者 |
| [guides/FERTILIZER_RECOMMENDATION_LLM_STRATEGY.md](guides/FERTILIZER_RECOMMENDATION_LLM_STRATEGY.md) | LLM戦略・プロンプト設計 | 開発者 |
| [guides/FERTILIZER_RECOMMENDATION_TESTING_STRATEGY.md](guides/FERTILIZER_RECOMMENDATION_TESTING_STRATEGY.md) | テスト戦略 | 開発者 |
| [technical/CROP_PROFILE_FILE_SCHEMA.md](technical/CROP_PROFILE_FILE_SCHEMA.md) | 入力ファイルスキーマ | 開発者 |

---

## 🗺️ 学習パス

### パス1: 利用者 (所要時間: 1-2時間)

```
1. README.md を読む (15分)
   └─ インストール、基本使い方
   
2. api/README.md を読む (15分)
   └─ CLI コマンド詳細
   
3. 肥料推奨機能体験 (20分)
   └─ FERTILIZER_RECOMMENDATION_README.md を読む
   └─ FERTILIZER_RECOMMENDATION_USER_GUIDE.md で詳細確認
   └─ agrr crop → agrr fertilize recommend の流れ
   
4. サンプル実行 (30分)
   └─ test_data/ のデータで実験
   
5. ベンチマーク確認 (30分)
   └─ 各アルゴリズムの性能比較
```

### パス2: 開発者 (所要時間: 2-3日)

```
Day 1: アーキテクチャ理解
  1. architecture/ARCHITECTURE_SUMMARY.md (1時間)
  2. architecture/ARCHITECTURE.md (2時間)
  3. コードベース探索 (3時間)

Day 2: ドメイン理解
  1. Entity層のコード読解 (2時間)
  2. UseCase層のコード読解 (2時間)
  3. 肥料推奨機能の実装例学習 (2時間)
     └─ FERTILIZER_RECOMMENDATION_DESIGN.md
     └─ fertilizer_recommendation_entity.py
     └─ fertilizer_llm_recommend_interactor.py

Day 3: 実装理解
  1. テストコード読解 (2時間)
  2. デバッグ実行 (2時間)
  3. 小規模機能の実装 (2時間)
```

### パス3: アルゴリズム研究者 (所要時間: 1-2日)

```
Day 1: アルゴリズム理解
  1. DP_OPTIMIZATION_BENCHMARK.md (1時間)
  2. DP_VS_GREEDY_6CROPS_ANALYSIS.md (1時間)
  3. 実装コード読解 (4時間)

Day 2: 実験
  1. ベンチマーク再現 (2時間)
  2. 新しいデータでの実験 (3時間)
  3. 結果分析 (1時間)
```

---

## 🔍 ドキュメントマップ

```
docs/
│
├── 📘 入門編
│   ├── README.md (このファイル)
│   └── ../README.md (プロジェクト概要)
│
├── 🏗️ アーキテクチャ編
│   └── architecture/
│       ├── ARCHITECTURE_SUMMARY.md                      ⭐ 全体俯瞰
│       ├── ARCHITECTURE.md                              ⭐ Clean Architecture詳細
│       ├── ARCHITECTURE_OVERVIEW_AND_RECOMMENDATIONS.md
│       ├── CLEAN_ARCHITECTURE_GATEWAY_GUIDELINES.md
│       ├── REFACTORING_ROADMAP.md
│       └── FINAL_IMPLEMENTATION_POLICY.md
│
├── 🔬 アルゴリズム・最適化編
│   └── algorithms/
│       ├── QUICK_START_DP_ALNS.md                       ⭐ クイックスタート
│       ├── ALNS_INTEGRATION_GUIDE.md
│       ├── algorithm_selection_guide.md
│       ├── optimization_algorithm_greedy_approach.md
│       └── optimization_design_multi_field_crop_allocation.md
│
├── 📖 ガイド・マニュアル編
│   └── guides/
│       ├── ALLOCATION_ADJUST_GUIDE.md
│       ├── CLI_USER_GUIDE_FALLOW_PERIOD.md
│       ├── MIGRATION_GUIDE_MAX_TEMPERATURE.md
│       ├── TEST_EXECUTION_GUIDE.md
│       ├── TEST_FIX_GUIDE.md
│       ├── US_WEATHER_GUIDE.md
│       └── US_WEATHER_LONG_TERM_GUIDE.md
│
├── 🔄 データフロー編
│   └── data_flows/
│       ├── CLI_DATA_FLOW.md
│       ├── CLI_DATA_FLOW_JMA.md
│       ├── DATA_FLOW_CROP_FAMILY.md
│       └── FIELD_DATA_FLOW_SIMPLIFIED.md
│
├── 🛠️ 技術リファレンス編
│   └── technical/
│       ├── AUTO_ESTIMATION_EXPLANATION.md
│       ├── DISTRIBUTION.md
│       └── FIELD_CONFIG_FORMAT.md
│
├── 📊 API編
│   └── api/
│       ├── README.md
│       ├── fertilizer_recommendation_api_reference.md
│       └── adapter/
│
├── 🌾 肥料推奨機能編
│   ├── FERTILIZER_RECOMMENDATION_README.md              ⭐ 機能概要
│   ├── FERTILIZER_RECOMMENDATION_USER_GUIDE.md          ⭐ ユーザーガイド
│   ├── architecture/FERTILIZER_RECOMMENDATION_DESIGN.md ⭐ 設計書
│   ├── guides/FERTILIZER_RECOMMENDATION_LLM_STRATEGY.md
│   ├── guides/FERTILIZER_RECOMMENDATION_TESTING_STRATEGY.md
│   └── technical/CROP_PROFILE_FILE_SCHEMA.md
│
├── 📊 調査レポート編
│   └── reports/
│
└── 📦 アーカイブ編 (過去のレポート)
    └── archive/
        ├── implementation_reports/
        ├── test_reports/
        ├── refactoring_reports/
        ├── feature_development/
        └── algorithm_research/
```

---

## 🎯 現在地と次のステップ

### 現在地: Phase 0 完了 ✅

- ✅ DP最適化実装完了
- ✅ ALNS統合完了
- ✅ アルゴリズム選択機能実装
- ✅ 肥料推奨機能実装完了
- ✅ 包括的ベンチマーク実施
- ✅ ドキュメント体系化

### 次のステップ: Phase 1 開始

**優先度1: リファクタリング**
- [ ] Strategy Pattern導入
- [ ] Interactor分割（1,190行 → 300行）
- [ ] テストカバレッジ向上（30% → 70%）

**タイムライン:**
- Week 1-2: 基礎リファクタリング
- Week 3-4: 品質向上
- Week 5-6: 機能強化

---

## 📞 サポート

### 質問・相談

- **アーキテクチャ**: [architecture/ARCHITECTURE_OVERVIEW_AND_RECOMMENDATIONS.md](architecture/ARCHITECTURE_OVERVIEW_AND_RECOMMENDATIONS.md) 参照
- **アルゴリズム選択**: [DP_VS_GREEDY_6CROPS_ANALYSIS.md](../test_data/DP_VS_GREEDY_6CROPS_ANALYSIS.md) 参照
- **実装詳細**: コード内のdocstring参照

### 貢献方法

1. Issue作成
2. ブランチ作成
3. 実装
4. テスト
5. PR作成

詳細: [architecture/REFACTORING_ROADMAP.md](architecture/REFACTORING_ROADMAP.md)

---

**バージョン**: 1.0  
**最終更新**: 2025年  
**ステータス**: 現行版
