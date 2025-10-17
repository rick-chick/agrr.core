# AGRR.CORE ドキュメント索引

プロジェクトの全ドキュメントへのナビゲーション

---

## 🎯 目的別ガイド

### 👋 初めての方

1. **プロジェクト概要**
   - [../README.md](../README.md) - プロジェクト紹介、インストール方法
   
2. **アーキテクチャ理解**
   - [ARCHITECTURE_SUMMARY.md](ARCHITECTURE_SUMMARY.md) ⭐ **まずここから**
   - [../ARCHITECTURE.md](../ARCHITECTURE.md) - 詳細設計

3. **使い方**
   - [api/README.md](api/README.md) - CLI使い方
   - サンプルデータ: `test_data/` ディレクトリ

### 🔧 開発者向け

1. **アーキテクチャ詳細**
   - [ARCHITECTURE_OVERVIEW_AND_RECOMMENDATIONS.md](ARCHITECTURE_OVERVIEW_AND_RECOMMENDATIONS.md) - 全体俯瞰と提案
   - [REFACTORING_ROADMAP.md](REFACTORING_ROADMAP.md) - リファクタリング計画

2. **アルゴリズム**
   - [../test_data/DP_OPTIMIZATION_BENCHMARK.md](../test_data/DP_OPTIMIZATION_BENCHMARK.md) - DP vs Greedy (4作物)
   - [../test_data/DP_VS_GREEDY_6CROPS_ANALYSIS.md](../test_data/DP_VS_GREEDY_6CROPS_ANALYSIS.md) - DP vs Greedy (6作物)
   - [FINAL_DP_ALNS_SUMMARY.md](FINAL_DP_ALNS_SUMMARY.md) - DP+ALNS実装レポート
   - [LOCAL_SEARCH_ALNS_UNIFICATION.md](LOCAL_SEARCH_ALNS_UNIFICATION.md) - ALNS統合詳細

3. **API Reference**
   - [api/README.md](api/README.md) - CLI API
   - [api/adapter/](api/adapter/) - Adapter層API
   - [api/framework/](api/framework/) - Framework層API

### 🚀 アルゴリズム研究者向け

1. **最適化アルゴリズム**
   - [OPTIMIZATION_ALGORITHM_REVIEW.md](../test_data/OPTIMIZATION_ALGORITHM_REVIEW.md) - アルゴリズムレビュー
   - [DP_ALNS_INTEGRATION.md](DP_ALNS_INTEGRATION.md) - DP+ALNS統合

2. **ベンチマーク結果**
   - [DP_OPTIMIZATION_BENCHMARK.md](../test_data/DP_OPTIMIZATION_BENCHMARK.md) - 4作物問題
   - [DP_VS_GREEDY_6CROPS_ANALYSIS.md](../test_data/DP_VS_GREEDY_6CROPS_ANALYSIS.md) - 6作物問題

3. **実験データ**
   - `test_data/` - 実験用データセット
   - `test_data/ANALYSIS_SUMMARY.md` - 分析サマリー

---

## 📁 ドキュメント一覧

### アーキテクチャ

| ドキュメント | 説明 | 対象者 |
|------------|------|--------|
| [ARCHITECTURE_SUMMARY.md](ARCHITECTURE_SUMMARY.md) | プロジェクト全体俯瞰 | 全員 ⭐ |
| [../ARCHITECTURE.md](../ARCHITECTURE.md) | Clean Architecture詳細 | 開発者 |
| [ARCHITECTURE_OVERVIEW_AND_RECOMMENDATIONS.md](ARCHITECTURE_OVERVIEW_AND_RECOMMENDATIONS.md) | 改善提案 | 開発者 |
| [REFACTORING_ROADMAP.md](REFACTORING_ROADMAP.md) | リファクタリング計画 | 開発者 |

### アルゴリズム

| ドキュメント | 説明 | 対象者 |
|------------|------|--------|
| [../test_data/DP_OPTIMIZATION_BENCHMARK.md](../test_data/DP_OPTIMIZATION_BENCHMARK.md) | DP vs Greedy (4作物) | 研究者 |
| [../test_data/DP_VS_GREEDY_6CROPS_ANALYSIS.md](../test_data/DP_VS_GREEDY_6CROPS_ANALYSIS.md) | DP vs Greedy (6作物) | 研究者 |
| [FINAL_DP_ALNS_SUMMARY.md](FINAL_DP_ALNS_SUMMARY.md) | DP+ALNS実装レポート | 開発者 |
| [LOCAL_SEARCH_ALNS_UNIFICATION.md](LOCAL_SEARCH_ALNS_UNIFICATION.md) | ALNS統合詳細 | 開発者 |
| [DP_ALNS_INTEGRATION.md](DP_ALNS_INTEGRATION.md) | 統合プロセス | 開発者 |

### 技術詳細

| ドキュメント | 説明 | 対象者 |
|------------|------|--------|
| [OPTIMIZATION_ALGORITHM_IMPROVEMENTS.md](OPTIMIZATION_ALGORITHM_IMPROVEMENTS.md) | 最適化改善履歴 | 研究者 |
| [../test_data/OPTIMIZATION_ALGORITHM_REVIEW.md](../test_data/OPTIMIZATION_ALGORITHM_REVIEW.md) | アルゴリズムレビュー | 研究者 |
| [../test_data/HYBRID_MODEL_INTEGRATION.md](../test_data/HYBRID_MODEL_INTEGRATION.md) | ハイブリッドモデル | 開発者 |
| [../test_data/WEATHER_INTERPOLATION_IMPLEMENTATION.md](../test_data/WEATHER_INTERPOLATION_IMPLEMENTATION.md) | 天気補間 | 開発者 |

### API Reference

| ドキュメント | 説明 |
|------------|------|
| [api/README.md](api/README.md) | CLI API概要 |
| [api/adapter/cli_controller.md](api/adapter/cli_controller.md) | Controller API |
| [api/adapter/cli_presenter.md](api/adapter/cli_presenter.md) | Presenter API |
| [api/framework/cli_container.md](api/framework/cli_container.md) | DIコンテナ |
| [api/framework/cli_entry_point.md](api/framework/cli_entry_point.md) | CLIエントリ |

---

## 🗺️ 学習パス

### パス1: 利用者 (所要時間: 1-2時間)

```
1. README.md を読む (15分)
   └─ インストール、基本使い方
   
2. api/README.md を読む (15分)
   └─ CLI コマンド詳細
   
3. サンプル実行 (30分)
   └─ test_data/ のデータで実験
   
4. ベンチマーク確認 (30分)
   └─ 各アルゴリズムの性能比較
```

### パス2: 開発者 (所要時間: 2-3日)

```
Day 1: アーキテクチャ理解
  1. ARCHITECTURE_SUMMARY.md (1時間)
  2. ARCHITECTURE.md (2時間)
  3. コードベース探索 (3時間)

Day 2: ドメイン理解
  1. Entity層のコード読解 (3時間)
  2. UseCase層のコード読解 (3時間)

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
│   ├── ARCHITECTURE_SUMMARY.md          ⭐ 全体俯瞰
│   ├── ../ARCHITECTURE.md               ⭐ Clean Architecture詳細
│   ├── ARCHITECTURE_OVERVIEW_AND_RECOMMENDATIONS.md
│   └── REFACTORING_ROADMAP.md
│
├── 🔬 アルゴリズム編
│   ├── DP_OPTIMIZATION_BENCHMARK.md      ⭐ ベンチマーク
│   ├── DP_VS_GREEDY_6CROPS_ANALYSIS.md   ⭐ 詳細分析
│   ├── FINAL_DP_ALNS_SUMMARY.md
│   ├── LOCAL_SEARCH_ALNS_UNIFICATION.md
│   ├── DP_ALNS_INTEGRATION.md
│   └── OPTIMIZATION_ALGORITHM_IMPROVEMENTS.md
│
├── 🔧 技術編
│   ├── HYBRID_MODEL_INTEGRATION.md
│   ├── WEATHER_INTERPOLATION_IMPLEMENTATION.md
│   ├── INTERPOLATION_REFACTORING_REPORT.md
│   └── OPTIMIZATION_INVESTIGATION_REPORT.md
│
└── 📖 API編
    ├── api/README.md
    ├── api/adapter/
    └── api/framework/
```

---

## 🎯 現在地と次のステップ

### 現在地: Phase 0 完了 ✅

- ✅ DP最適化実装完了
- ✅ ALNS統合完了
- ✅ アルゴリズム選択機能実装
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

- **アーキテクチャ**: [ARCHITECTURE_OVERVIEW_AND_RECOMMENDATIONS.md](ARCHITECTURE_OVERVIEW_AND_RECOMMENDATIONS.md) 参照
- **アルゴリズム選択**: [DP_VS_GREEDY_6CROPS_ANALYSIS.md](../test_data/DP_VS_GREEDY_6CROPS_ANALYSIS.md) 参照
- **実装詳細**: コード内のdocstring参照

### 貢献方法

1. Issue作成
2. ブランチ作成
3. 実装
4. テスト
5. PR作成

詳細: [REFACTORING_ROADMAP.md](REFACTORING_ROADMAP.md)

---

**バージョン**: 1.0  
**最終更新**: 2025年  
**ステータス**: 現行版
