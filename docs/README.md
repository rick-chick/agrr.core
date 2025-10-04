# agrr.core Documentation

このディレクトリには、agrr.coreプロジェクトのドキュメントが含まれています。

## ドキュメント構成

- **[API Reference](api/README.md)** - CLI APIの詳細なリファレンス
- **[Architecture](../ARCHITECTURE.md)** - プロジェクトのアーキテクチャ設計
- **[README](../README.md)** - プロジェクトの概要とセットアップ

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
