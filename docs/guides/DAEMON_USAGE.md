# AGRR Daemon Mode - Usage Guide

## 概要

AGRRコマンドラインツールにデーモンモードを実装しました。これにより、**起動時間が4.8倍高速化**されます。

### パフォーマンス

| モード | 実行時間 | 改善率 |
|--------|---------|-------|
| **通常実行** | 2.4秒 | - |
| **デーモン経由** | 0.5秒 | **4.8倍高速** |

---

## 使い方

### 1. デーモン起動（初回のみ）

```bash
# デーモンを起動（バックグラウンドプロセスとして常駐）
python3 -m agrr_core daemon start

# または、PyInstallerビルド版
./dist/agrr/agrr daemon start
```

**出力例：**
```
✓ Daemon started (PID: 12345)
✓ Socket: /tmp/agrr.sock
```

**起動時間：** 約4秒（重いモジュールを事前ロード）

---

### 2. コマンド実行（高速）

```bash
# 通常通りコマンドを実行（自動的にデーモン経由になる）
python3 -m agrr_core --help
python3 -m agrr_core weather --location 35.6762,139.6503 --days 7
python3 -m agrr_core crop --query "トマト"
```

**実行時間：** 約0.5秒（デーモンが処理）

---

### 3. デーモン管理

#### ステータス確認

```bash
python3 -m agrr_core daemon status
```

**出力例：**
```
✓ Daemon is running (PID: 12345)
```

#### デーモン停止

```bash
python3 -m agrr_core daemon stop
```

**出力例：**
```
✓ Daemon stopped
```

#### デーモン再起動

```bash
python3 -m agrr_core daemon restart
```

**出力例：**
```
Restarting daemon...
✓ Daemon stopped
✓ Daemon started (PID: 12346)
✓ Socket: /tmp/agrr.sock
```

---

## 仕組み

### アーキテクチャ

```
┌─────────────────────────────────────────┐
│ python3 -m agrr_core <command>         │
└──────────────┬──────────────────────────┘
               │
               ├─ __main__.py（軽量エントリーポイント）
               │   └─ daemon/__init__.py（0.5秒）
               │       │
               │       ├─ /tmp/agrr.sock 存在？
               │       │
               │       ├─ Yes → daemon/client.py
               │       │        └─ UNIXソケット経由でリクエスト送信
               │       │            └─ daemon/server.py（常駐プロセス）
               │       │                └─ cli.execute_cli_direct()
               │       │                    └─ 結果を返す（高速）
               │       │
               │       └─ No → cli.execute_cli_direct()（遅い、2.4秒）
               │
               └─ 結果を出力
```

### コンポーネント

| ファイル | 役割 |
|---------|------|
| `src/agrr_core/__main__.py` | 軽量エントリーポイント（デーモンチェック） |
| `src/agrr_core/daemon/__init__.py` | デーモン委譲ロジック |
| `src/agrr_core/daemon/server.py` | デーモンサーバー（UNIXソケット） |
| `src/agrr_core/daemon/client.py` | デーモンクライアント（リクエスト送信） |
| `src/agrr_core/daemon/manager.py` | デーモン管理（start/stop/status） |
| `src/agrr_core/cli.py` | 既存CLI（`execute_cli_direct()`関数） |

---

## 技術詳細

### UNIXソケット通信

- **ソケットパス:** `/tmp/agrr.sock`
- **PIDファイル:** `/tmp/agrr.pid`
- **通信プロトコル:** JSON（改行区切り）
- **タイムアウト:** 5分

### リクエスト形式

```json
{
  "args": ["weather", "--location", "35.6762,139.6503", "--days", "7"]
}
```

### レスポンス形式

```json
{
  "stdout": "...",
  "stderr": "...",
  "exit_code": 0
}
```

---

## Railsとの統合

### 基本的な使い方

```ruby
# models/weather_service.rb
class WeatherService
  def self.fetch_weather(lat:, lon:, days:)
    # コマンド実行（デーモンがあれば自動的に高速化）
    result = `python3 -m agrr_core weather --location #{lat},#{lon} --days #{days} --json`
    JSON.parse(result)
  end
end
```

### Railsサーバー起動時にデーモン起動

```ruby
# config/puma.rb
on_worker_boot do
  # デーモンが起動してなければ起動
  unless system("python3 -m agrr_core daemon status > /dev/null 2>&1")
    system("python3 -m agrr_core daemon start")
  end
end

on_worker_shutdown do
  # サーバー停止時にデーモンも停止
  system("python3 -m agrr_core daemon stop")
end
```

---

## トラブルシューティング

### デーモンが起動しない

```bash
# ソケットファイルを手動削除
rm -f /tmp/agrr.sock /tmp/agrr.pid

# 再起動
python3 -m agrr_core daemon start
```

### デーモンが応答しない

```bash
# 強制再起動
python3 -m agrr_core daemon restart
```

### デーモンなしで実行したい

```bash
# デーモンを停止（自動的に通常実行にフォールバック）
python3 -m agrr_core daemon stop

# コマンド実行（デーモンなし、2.4秒）
python3 -m agrr_core weather --location 35.6762,139.6503 --days 7
```

---

## PyInstallerビルドでの使用

### ビルド方法

```bash
# デーモンサポート付きでビルド
./scripts/build_standalone.sh

# または
./scripts/build_standalone.sh --onefile
```

### 使用方法

```bash
# デーモン起動
./dist/agrr/agrr daemon start

# コマンド実行（高速）
./dist/agrr/agrr weather --location 35.6762,139.6503 --days 7

# デーモン停止
./dist/agrr/agrr daemon stop
```

### パフォーマンス（バイナリ版）

| モード | 実行時間 | 改善率 |
|--------|---------|-------|
| **通常実行** | 4.0秒 | - |
| **デーモン経由** | 0.9秒 | **4.4倍高速** |

**注意:** バイナリ版は解凍オーバーヘッドがあるため、Python実行版より若干遅くなりますが、デーモンを使えば十分高速です。

---

## 注意事項

1. **プロセス管理**
   - デーモンはバックグラウンドプロセスとして常駐します
   - 不要になったら `daemon stop` で停止してください

2. **メモリ使用量**
   - デーモンは約200MB程度のメモリを使用します
   - 必要に応じて停止/再起動してください

3. **ソケットファイル**
   - `/tmp/agrr.sock` が存在する場合、自動的にデーモン経由になります
   - システム再起動時は `/tmp` がクリアされるため、デーモンを再起動してください

4. **エラー時のフォールバック**
   - デーモンが応答しない場合、自動的に通常実行にフォールバックします
   - エラーメッセージが表示されますが、コマンドは正常に実行されます

---

## まとめ

- **デーモン起動：** `python3 -m agrr_core daemon start`（初回4秒）
- **コマンド実行：** `python3 -m agrr_core <command>`（0.5秒）
- **4.8倍の高速化**を実現
- **Rails側の変更不要**（自動的に高速化される）
- **フォールバック機能**でデーモンなしでも動作

