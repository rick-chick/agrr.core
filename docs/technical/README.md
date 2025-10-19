# 技術リファレンス

このディレクトリには、AGRR.COREプロジェクトの技術的な詳細に関するドキュメントが含まれています。

## 🛠️ ドキュメント一覧

| ドキュメント | 説明 | 対象者 | 重要度 |
|------------|------|--------|--------|
| [PERIOD_TEMPLATE_DESIGN.md](PERIOD_TEMPLATE_DESIGN.md) | **Period Template方式設計 + ベンチマーク結果** | 開発者 | ⭐⭐⭐ |
| [CANDIDATE_POOL_AND_SLIDING_WINDOW.md](CANDIDATE_POOL_AND_SLIDING_WINDOW.md) | レガシー候補プール方式（参考資料） | 開発者 | ⭐ |
| [AUTO_ESTIMATION_EXPLANATION.md](AUTO_ESTIMATION_EXPLANATION.md) | 自動推定の説明 | 開発者 | ⭐⭐ |
| [DISTRIBUTION.md](DISTRIBUTION.md) | 配布方法 | 開発者 | ⭐ |
| [FIELD_CONFIG_FORMAT.md](FIELD_CONFIG_FORMAT.md) | 圃場設定フォーマット | ユーザー・開発者 | ⭐⭐ |

## 📚 関連ドキュメント

- [../README.md](../README.md) - ドキュメント索引
- [../architecture/FINAL_IMPLEMENTATION_POLICY.md](../architecture/FINAL_IMPLEMENTATION_POLICY.md) - 実装ポリシー
- [../algorithms/QUICK_START_DP_ALNS.md](../algorithms/QUICK_START_DP_ALNS.md) - DP+ALNSクイックスタート

## 🎯 目的別ガイド

### Period Template方式を理解したい（推奨）⭐⭐⭐
→ [PERIOD_TEMPLATE_DESIGN.md](PERIOD_TEMPLATE_DESIGN.md)
  - 候補生成の新方式（デフォルト）
  - 実装方法と設計判断
  - **ベンチマーク結果**: 平均22〜30%改善、最大76%改善
  - メモリ効率、探索空間20倍拡大

### レガシー候補プール方式（参考資料）
→ [CANDIDATE_POOL_AND_SLIDING_WINDOW.md](CANDIDATE_POOL_AND_SLIDING_WINDOW.md)
  - 旧方式の詳細説明
  - スライディングウィンドウアルゴリズム
  - 後方互換性のために残されている

### 自動推定の仕組みを理解したい
→ [AUTO_ESTIMATION_EXPLANATION.md](AUTO_ESTIMATION_EXPLANATION.md)

### パッケージ配布方法を知りたい
→ [DISTRIBUTION.md](DISTRIBUTION.md)

### 圃場設定ファイルのフォーマットを確認したい
→ [FIELD_CONFIG_FORMAT.md](FIELD_CONFIG_FORMAT.md)

## 💡 技術リファレンスの活用

これらのドキュメントは、システムの技術的な詳細や設定フォーマットなどのリファレンスとして活用してください。実装時や設定ファイル作成時に参照すると便利です。

---

**最終更新**: 2025-10-19  
**主要更新**: Period Template実装完了、ベンチマーク結果統合
