# AGRR Notification System

AGRRアプリケーションの通知システムは、ログ機能、エラー通知、デーモン監視を統合した包括的な監視・通知システムです。

## 📋 概要

### 主要機能

1. **ログ機能の強化**
   - 構造化ログ（ファイル出力、ローテーション）
   - ログレベル別の出力制御
   - デーモン専用ログ

2. **エラー通知システム**
   - メール通知
   - Slack通知
   - エラー分類と詳細情報

3. **デーモン監視**
   - ヘルスチェック
   - 自動復旧
   - 状態監視

## 🚀 使用方法

### 1. 設定ファイル

`agrr_config.yaml`で通知設定を管理します：

```yaml
# ログ設定
logging:
  enabled: true
  log_file: "/tmp/agrr.log"
  daemon_log_file: "/tmp/agrr_daemon.log"
  max_size: "10MB"
  backup_count: 5
  level: "INFO"

# 通知設定
notifications:
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    username: "your-email@gmail.com"
    password: "your-app-password"
    from_email: "agrr-system@example.com"
    to_emails: ["admin@example.com"]
  
  slack:
    enabled: true
    webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# デーモン監視設定
daemon:
  health_check:
    enabled: true
    check_interval: 60
    response_timeout: 5.0
    max_consecutive_failures: 3
  
  auto_recovery:
    enabled: true
    max_retries: 3
    retry_interval: 30
    recovery_command: "agrr daemon restart"
```

### 2. 環境変数での設定

設定ファイルの代わりに環境変数でも設定可能です：

```bash
export AGRR_LOG_LEVEL="DEBUG"
export AGRR_EMAIL_ENABLED="true"
export AGRR_EMAIL_USERNAME="your-email@gmail.com"
export AGRR_EMAIL_PASSWORD="your-password"
export AGRR_EMAIL_TO="admin@example.com,alerts@example.com"
export AGRR_SLACK_ENABLED="true"
export AGRR_SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

## 🔧 実装詳細

### ログ機能

```python
from agrr_core.framework.logging.agrr_logger import setup_logging, get_logger

# ログ設定
logger = setup_logging("/tmp/agrr.log", "INFO")

# ログ出力
logger.info("Application started", user="admin")
logger.error("Database connection failed", error="timeout")
logger.warning("High memory usage", usage="85%")
```

**ログファイルの特徴:**
- 自動ローテーション（10MB、5世代保持）
- タイムスタンプ付き
- 構造化ログ（キー=値形式）
- デーモン専用ログファイル

### エラー通知

```python
from agrr_core.framework.notifications.error_notifier import get_notifier

notifier = get_notifier()

# メール通知設定
notifier.add_email_channel(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    username="your-email@gmail.com",
    password="your-password",
    from_email="agrr-system@example.com",
    to_emails=["admin@example.com"]
)

# Slack通知設定
notifier.add_slack_channel("https://hooks.slack.com/services/YOUR/WEBHOOK/URL")

# エラー通知
notifier.notify_error("DATABASE_ERROR", "Connection failed", {
    "timestamp": "2024-01-01T00:00:00Z",
    "retry_count": 3
})
```

**通知タイプ:**
- `DAEMON_DOWN`: デーモン停止
- `DAEMON_RECOVERY_FAILED`: 復旧失敗
- `PREDICTION_ERROR`: 予測エラー
- `DATABASE_ERROR`: データベースエラー
- `API_ERROR`: API接続エラー

### デーモン監視

```python
from agrr_core.framework.monitoring.daemon_monitor import get_monitor

monitor = get_monitor()

# 監視開始
monitor.start()

# 状態確認
status = monitor.get_status()
print(f"Daemon running: {status['running']}")
print(f"Response time: {status.get('response_time', 'N/A')}s")

# 強制復旧
if not status['running']:
    success = monitor.force_recovery()
    print(f"Recovery successful: {success}")
```

**監視機能:**
- ソケット接続チェック
- レスポンス時間測定
- PIDファイル確認
- 自動復旧試行

## 📊 ログ出力例

### 通常ログ

```
2024-01-01 12:00:00 - agrr - INFO - Application started (user=admin)
2024-01-01 12:00:01 - agrr - DEBUG - Database connection established (host=localhost)
2024-01-01 12:00:02 - agrr - WARNING - High memory usage (usage=85%)
```

### デーモンログ

```
2024-01-01 12:00:00 - agrr - INFO - Daemon started (pid=12345, socket=/tmp/agrr.sock)
2024-01-01 12:00:01 - agrr - DEBUG - Request received (command=predict, client=127.0.0.1)
2024-01-01 12:00:05 - agrr - INFO - Request completed (command=predict, duration=4.2s, exit_code=0)
```

### エラーログ

```
2024-01-01 12:00:00 - agrr - ERROR - Error notification triggered (error_type=DAEMON_DOWN, msg=AGRR daemon is not running)
2024-01-01 12:00:01 - agrr - CRITICAL - All recovery attempts failed (attempts=3)
```

## 🔍 トラブルシューティング

### ログファイルの確認

```bash
# メインログ
tail -f /tmp/agrr.log

# デーモンログ
tail -f /tmp/agrr_daemon.log

# ログレベル別フィルタ
grep "ERROR" /tmp/agrr.log
grep "WARNING" /tmp/agrr.log
```

### デーモン状態の確認

```bash
# デーモン状態
agrr daemon status

# 監視システムの状態確認
python3 -c "
from agrr_core.framework.monitoring.daemon_monitor import get_monitor
monitor = get_monitor()
status = monitor.get_status()
print(f'Running: {status[\"running\"]}')
print(f'Response time: {status.get(\"response_time\", \"N/A\")}s')
"
```

### 通知設定の確認

```bash
# 設定ファイルの確認
cat agrr_config.yaml

# 環境変数の確認
env | grep AGRR_
```

## 🚨 アラート例

### メール通知

```
Subject: AGRR Alert: DAEMON_DOWN

AGRR System Alert

Title: DAEMON_DOWN
Time: 2024-01-01 12:00:00
Message: AGRR daemon is not running (PID: 12345)

Details:
{
  "timestamp": "2024-01-01T12:00:00Z",
  "pid": 12345
}
```

### Slack通知

```
🚨 AGRR Alert: DAEMON_DOWN

Message: AGRR daemon is not running (PID: 12345)
Time: 2024-01-01 12:00:00

Details:
{
  "timestamp": "2024-01-01T12:00:00Z",
  "pid": 12345
}
```

## 📈 パフォーマンス

### ログローテーション

- ファイルサイズ: 10MB
- バックアップ数: 5世代
- 圧縮: 自動

### 通知レート制限

- メール: 制限なし（SMTPサーバー依存）
- Slack: 1分間に最大1回（推奨）

### 監視オーバーヘッド

- ヘルスチェック間隔: 60秒
- レスポンス時間: < 1ms
- メモリ使用量: < 1MB

## 🔧 カスタマイズ

### カスタム通知チャンネル

```python
from agrr_core.framework.notifications.error_notifier import NotificationChannel

class CustomNotificationChannel(NotificationChannel):
    def send(self, title: str, message: str, details: dict = None):
        # カスタム通知ロジック
        pass

# チャンネル追加
notifier = get_notifier()
notifier.channels.append(CustomNotificationChannel())
```

### カスタムログフォーマット

```python
from agrr_core.framework.logging.agrr_logger import AgrrLogger

logger = AgrrLogger(
    log_file="/custom/path/agrr.log",
    max_bytes=20 * 1024 * 1024,  # 20MB
    backup_count=10,
    log_level="DEBUG"
)
```

## 📚 API リファレンス

### AgrrLogger

```python
class AgrrLogger:
    def debug(self, message: str, **kwargs)
    def info(self, message: str, **kwargs)
    def warning(self, message: str, **kwargs)
    def error(self, message: str, **kwargs)
    def critical(self, message: str, **kwargs)
```

### ErrorNotifier

```python
class ErrorNotifier:
    def add_email_channel(self, smtp_server, smtp_port, username, password, from_email, to_emails)
    def add_slack_channel(self, webhook_url)
    def notify_error(self, error_type: str, message: str, details: dict = None)
    def notify_daemon_down(self, pid: int = None)
    def notify_prediction_error(self, model: str, error: str)
```

### DaemonMonitor

```python
class DaemonMonitor:
    def start(self)
    def stop(self)
    def get_status(self) -> dict
    def force_recovery(self) -> bool
```

## 🎯 ベストプラクティス

1. **ログレベル**: 本番環境では`INFO`、開発環境では`DEBUG`
2. **通知設定**: 重要なエラーのみ通知、スパム防止
3. **監視間隔**: 60秒間隔で十分、過度な監視は避ける
4. **ログローテーション**: ディスク容量を考慮した設定
5. **セキュリティ**: 通知認証情報の適切な管理

## 🔄 更新履歴

- **v1.0.0**: 初期実装
  - 基本的なログ機能
  - メール・Slack通知
  - デーモン監視

- **v1.1.0**: 機能強化
  - 自動復旧機能
  - 設定ファイル対応
  - 環境変数サポート

- **v1.2.0**: パフォーマンス改善
  - ログローテーション最適化
  - 通知レート制限
  - 監視オーバーヘッド削減
