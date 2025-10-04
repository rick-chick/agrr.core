# CLI API Reference

agrr.coreのCLIアプリケーションに関するAPIリファレンスです。

## 概要

agrr.core CLIは、コマンドラインから天気予報データを取得・表示するためのアプリケーションです。クリーンアーキテクチャに基づいて設計されており、以下のコンポーネントで構成されています。

## CLI構成要素

### Adapter Layer
- **[CLI Controller](adapter/cli_controller.md)** - コマンドライン引数の処理とユースケースの呼び出し
- **[CLI Presenter](adapter/cli_presenter.md)** - コンソール出力のフォーマットと表示

### Framework Layer
- **[CLI Container](framework/cli_container.md)** - 依存性注入コンテナ
- **[CLI Entry Point](framework/cli_entry_point.md)** - アプリケーションのエントリーポイント

## 使用方法

### 基本的な使用方法

```bash
# ヘルプの表示
python -m agrr_core.cli --help

# 天気予報コマンドのヘルプ
python -m agrr_core.cli weather --help

# 天気予報の取得（過去7日間）
python -m agrr_core.cli weather --location 35.6762,139.6503 --days 7

# 特定の日付範囲で天気予報を取得
python -m agrr_core.cli weather --location 35.6762,139.6503 --start-date 2024-01-01 --end-date 2024-01-07
```

### コマンドライン引数

| 引数 | 説明 | 例 |
|---|---|---|
| `--location, -l` | 位置情報（緯度,経度） | `35.6762,139.6503` |
| `--days, -d` | 過去何日分のデータ（デフォルト: 7） | `7` |
| `--start-date, -s` | 開始日（YYYY-MM-DD形式） | `2024-01-01` |
| `--end-date, -e` | 終了日（YYYY-MM-DD形式） | `2024-01-07` |
| `--json` | JSON形式で出力 | - |

### 主要都市の座標

| 都市 | 座標 |
|------|------|
| 東京 | `35.6762,139.6503` |
| 大阪 | `34.6937,135.5023` |
| 名古屋 | `35.1815,136.9066` |
| 福岡 | `33.5904,130.4017` |
| 札幌 | `43.0642,141.3469` |
| ニューヨーク | `40.7128,-74.0060` |
| ロンドン | `51.5074,-0.1278` |
| パリ | `48.8566,2.3522` |
| シドニー | `-33.8688,151.2093` |

## 出力例

### 成功時の出力

```
[SUCCESS] Fetching weather data for location (35.6762, 139.6503) from 2024-01-08 to 2024-01-14...

================================================================================
WEATHER FORECAST
================================================================================

Date        Max Temp   Min Temp   Avg Temp   Precip   Sunshine  
----------------------------------------------------------------
2024-01-08  12.5°C     5.2°C      8.9°C      2.1mm    6.5h      
2024-01-09  15.3°C     7.8°C      11.6°C     0.0mm    8.2h      
2024-01-10  18.1°C     9.5°C      13.8°C     0.5mm    7.8h      
2024-01-11  16.7°C     8.2°C      12.4°C     3.2mm    5.1h      
2024-01-12  14.9°C     6.8°C      10.9°C     1.8mm    6.9h      
2024-01-13  17.2°C     9.1°C      13.2°C     0.0mm    8.7h      
2024-01-14  19.5°C     11.3°C     15.4°C     0.2mm    9.1h      

================================================================================
Total records: 7
================================================================================
```

### エラー時の出力

```
[ERROR] VALIDATION_ERROR: Latitude must be between -90 and 90, got 91.0

[ERROR] API_ERROR: Failed to fetch weather data from API: Connection timeout
```

## アーキテクチャ

CLIアプリケーションは以下の層で構成されています：

```
CLI Entry Point (トップレベル)
    ↓
CLI Container (Framework Layer)
    ↓
CLI Controller (Adapter Layer)
    ↓
CLI Presenter (Adapter Layer)
    ↓
UseCase Interactor (UseCase Layer)
    ↓
Repository (Adapter Layer)
    ↓
Open-Meteo API (External)
```

## エラーハンドリング

CLIアプリケーションは以下のエラーを適切に処理します：

- **バリデーションエラー**: 無効な引数や座標
- **APIエラー**: 外部APIの接続エラー
- **データエラー**: 天気データの取得失敗
- **システムエラー**: 予期しないエラー

## 開発者向け情報

### テストの実行

```bash
# CLI関連のテストを実行
pytest tests/test_adapter/test_cli_weather_controller.py -v
pytest tests/test_adapter/test_cli_weather_presenter.py -v
pytest tests/test_framework/test_container.py -v
```

### デバッグ

CLIアプリケーションのデバッグには、以下の方法があります：

1. **ログ出力の確認**
2. **単体テストの実行**
3. **モックデータでの動作確認**

### 拡張

新しいCLIコマンドを追加する場合：

1. `CLIWeatherController`に新しいコマンドハンドラーを追加
2. 対応するPresenterメソッドを実装
3. テストケースを作成
4. ドキュメントを更新