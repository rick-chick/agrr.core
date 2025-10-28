# 肥料推奨機能 ドキュメント一覧

## 📚 ドキュメント構成

肥料推奨機能に関する全ドキュメントの一覧と概要です。

### 🎯 概要・入門
- **[FERTILIZER_RECOMMENDATION_README.md](FERTILIZER_RECOMMENDATION_README.md)** - 機能概要、クイックスタート、アーキテクチャ概要
- **[FERTILIZER_RECOMMENDATION_USER_GUIDE.md](FERTILIZER_RECOMMENDATION_USER_GUIDE.md)** - 詳細なユーザーガイド、使用例、トラブルシューティング

### 🏗️ 設計・アーキテクチャ
- **[architecture/FERTILIZER_RECOMMENDATION_DESIGN.md](architecture/FERTILIZER_RECOMMENDATION_DESIGN.md)** - 完全な設計書、Clean Architectureマッピング、データ契約

### 🔌 API・仕様
- **[api/fertilizer_recommendation_api_reference.md](api/fertilizer_recommendation_api_reference.md)** - CLI・HTTP API契約、入出力仕様

### 🧪 技術実装
- **[guides/FERTILIZER_RECOMMENDATION_LLM_STRATEGY.md](guides/FERTILIZER_RECOMMENDATION_LLM_STRATEGY.md)** - LLM戦略、プロンプト設計、検索・検証
- **[guides/FERTILIZER_RECOMMENDATION_TESTING_STRATEGY.md](guides/FERTILIZER_RECOMMENDATION_TESTING_STRATEGY.md)** - テスト戦略、フィクスチャ、検証ヘルパー
- **[technical/CROP_PROFILE_FILE_SCHEMA.md](technical/CROP_PROFILE_FILE_SCHEMA.md)** - 作物プロファイル入力ファイルのJSONスキーマ

## 📖 読み方ガイド

### 👤 ユーザー向け
1. **FERTILIZER_RECOMMENDATION_README.md** - 機能の概要とクイックスタート
2. **FERTILIZER_RECOMMENDATION_USER_GUIDE.md** - 詳細な使用方法と実例

### 👨‍💻 開発者向け
1. **architecture/FERTILIZER_RECOMMENDATION_DESIGN.md** - 設計思想とアーキテクチャ
2. **api/fertilizer_recommendation_api_reference.md** - API仕様
3. **guides/FERTILIZER_RECOMMENDATION_LLM_STRATEGY.md** - LLM実装詳細
4. **guides/FERTILIZER_RECOMMENDATION_TESTING_STRATEGY.md** - テスト戦略

### 🔬 研究者向け
1. **guides/FERTILIZER_RECOMMENDATION_LLM_STRATEGY.md** - LLM戦略とプロンプト設計
2. **technical/CROP_PROFILE_FILE_SCHEMA.md** - データ構造仕様

## 🎯 機能の特徴

### ✅ 実装済み機能
- **CLI統合**: `agrr fertilize recommend` コマンド
- **Mock Gateway**: テスト・開発用のインメモリゲートウェイ
- **LLM Gateway**: 学術ソース引用付きの実際の推奨
- **構造化出力**: N-P-K合計、施肥スケジュール、信頼度スコア
- **単位統一**: すべてg/m²（平方メートルあたりグラム）
- **バリデーション**: 入力検証とエラーハンドリング

### 🎯 出力形式
```json
{
  "crop": { "crop_id": "tomato", "name": "Tomato" },
  "totals": { "N": 18.0, "P": 5.2, "K": 12.4 },
  "applications": [
    {
      "type": "basal",
      "count": 1,
      "schedule_hint": "pre-plant",
      "nutrients": { "N": 6.0, "P": 2.0, "K": 3.0 }
    },
    {
      "type": "topdress",
      "count": 2,
      "schedule_hint": "early fruit set; mid fruiting",
      "nutrients": { "N": 12.0, "P": 3.2, "K": 9.4 },
      "per_application": { "N": 6.0, "P": 1.6, "K": 4.7 }
    }
  ],
  "sources": ["https://example.org/tomato-fertilizer", "JAガイド 2021 p.12-18"],
  "confidence": 0.7,
  "notes": "Adjust based on soil test results"
}
```

## 🏗️ アーキテクチャ

### Clean Architecture層
- **Entities**: `Nutrients`, `FertilizerApplication`, `FertilizerPlan`
- **UseCase**: `FertilizerLLMRecommendInteractor`（1クラス1ユースケース）
- **Gateway**: `FertilizerRecommendGateway`インターフェース（LLM・インメモリ実装）
- **Adapter**: CLIコントローラー、プレゼンター、ファイルサービス統合

### ファイル構造
```
src/agrr_core/
├── entity/entities/fertilizer_recommendation_entity.py
├── usecase/
│   ├── gateways/fertilizer_recommend_gateway.py
│   └── interactors/fertilizer_llm_recommend_interactor.py
└── adapter/
    ├── controllers/fertilizer_cli_recommend_controller.py
    ├── gateways/
    │   ├── fertilizer_llm_recommend_gateway.py
    │   └── fertilizer_recommend_inmemory_gateway.py
    └── presenters/fertilizer_recommend_cli_presenter.py
```

## 🧪 テスト

### テストカバレッジ
- **ユニットテスト**: フェイクゲートウェイを使用したUseCaseインタラクター
- **統合テスト**: モックデータを使用したCLIコントローラー
- **エンドツーエンド**: Mock・LLM両ゲートウェイでの完全CLIワークフロー

### テスト実行
```bash
# ユニットテスト
python -m pytest tests/test_usecase/test_fertilizer_llm_recommend_interactor.py -v

# 統合テスト
python -m pytest tests/test_adapter/test_fertilizer_cli_recommend_controller.py -v

# 全肥料テスト
python -m pytest tests/test_usecase/test_fertilizer_llm_recommend_interactor.py tests/test_adapter/test_fertilizer_cli_recommend_controller.py -v
```

## 🚀 使用例

### 基本使用
```bash
# 作物プロファイル生成
agrr crop --query "rice" > rice_profile.json

# 推奨取得（JSON出力）
agrr fertilize recommend --crop-file rice_profile.json --json

# ファイル保存
agrr fertilize recommend --crop-file rice_profile.json --output rice_fertilizer.json
```

### 開発・テスト
```bash
# テスト用モックゲートウェイ使用
agrr fertilize recommend --crop-file rice_profile.json --mock-fertilizer --json
```

## 📊 実装状況

### ✅ 完了済み
- [x] 設計ドキュメント
- [x] ドメインエンティティ
- [x] UseCaseインタラクター
- [x] ゲートウェイインターフェース・実装
- [x] CLIコントローラー・プレゼンター
- [x] ユニット・統合テスト
- [x] CLI統合・ヘルプドキュメント
- [x] テスト用モックゲートウェイ
- [x] 学術ソース引用付きLLMゲートウェイ

### 🔄 将来の拡張
- [ ] HTTP APIエンドポイント
- [ ] 追加作物タイプ・地域
- [ ] 土壌特化推奨
- [ ] 気象ベースタイミング調整
- [ ] コスト最適化機能

## 🤝 貢献

この機能を拡張する際は：
1. Clean Architecture原則に従う
2. テストファーストアプローチを維持
3. 新機能のドキュメントを更新
4. CLIヘルプドキュメントを最新に保つ
5. 適切なバリデーション・エラーハンドリングを追加

## 📞 関連ドキュメント
- [アーキテクチャ概要](architecture/ARCHITECTURE.md)
- [Clean Architectureガイドライン](architecture/CLEAN_ARCHITECTURE_GATEWAY_GUIDELINES.md)
- [CLIユーザーガイド](../CLI_HELP_TEST_CASES.md)

---

**最終更新**: 2025年1月  
**バージョン**: 1.0  
**ステータス**: 実装完了・ドキュメント整備済み
