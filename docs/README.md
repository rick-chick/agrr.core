# agrr.core Documentation

このディレクトリには、agrr.coreプロジェクトのドキュメントが含まれています。

## ドキュメント構成

### 基本ドキュメント

- **[API Reference](api/README.md)** - CLI APIの詳細なリファレンス
- **[Architecture](../ARCHITECTURE.md)** - プロジェクトのアーキテクチャ設計
- **[README](../README.md)** - プロジェクトの概要とセットアップ

### 最適化・モデリング

- **[Algorithm Selection Guide](algorithm_selection_guide.md)** - 最適化アルゴリズムの選択ガイド
- **[Optimization Design](optimization_design_multi_field_crop_allocation.md)** - 複数圃場作物配置の最適化設計
- **[Interaction Rule Usage](INTERACTION_RULE_USAGE.md)** - 相互作用ルール（連作影響）の使用方法

### 温度ストレスモデリング（New! 2025-10-14）

- **[Temperature Stress Model Research](TEMPERATURE_STRESS_MODEL_RESEARCH.md)** - 温度ストレスモデルの研究調査レポート
- **[Temperature Stress Implementation Example](TEMPERATURE_STRESS_IMPLEMENTATION_EXAMPLE.md)** - 実装例とコードサンプル
- **[Temperature Stress Visual Summary](TEMPERATURE_STRESS_VISUAL_SUMMARY.md)** - ビジュアルサマリーと図表

## アーキテクチャ概要

agrr.coreはクリーンアーキテクチャに基づいて設計された天気予報システムです。以下の4つの主要層で構成されています：

1. **Entity Layer** - ビジネスロジックとエンティティ
2. **UseCase Layer** - アプリケーション固有のビジネスルール
3. **Adapter Layer** - 外部システムとの接続とデータ変換
4. **Framework Layer** - 外部フレームワークとの統合

## クイックスタート

### CLIアプリケーションの使用

```bash
# 天気予報を取得（過去7日間）
python -m agrr_core.cli weather --location 35.6762,139.6503 --days 7

# JSON形式で出力
python -m agrr_core.cli weather --location 35.6762,139.6503 --days 7 --json
```

## 開発者向け情報

- テストの実行: `pytest`
- カバレッジ付きテスト: `pytest --cov=agrr_core`
- コードフォーマット: `black src/`
- 型チェック: `mypy src/`
