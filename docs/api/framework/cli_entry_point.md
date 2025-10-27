# CLI Entry Point API Reference

`cli.py`は、agrr.core CLIアプリケーションのメインエントリーポイントです。アプリケーションの起動、設定、エラーハンドリングを担当します。

## ファイル概要

```python
# src/agrr_core/cli.py
"""CLI application entry point."""
```

**パス**: `src/agrr_core/cli.py`

## 主要関数

### `main()`

CLIアプリケーションのメインエントリーポイントです。

```python
def main() -> None
```

**処理フロー**:
1. 依存性注入コンテナの作成
2. コマンドライン引数の取得
3. CLIアプリケーションの実行
4. エラーハンドリング

**設定**:
- Open-Meteo APIのベースURL: `https://archive-api.open-meteo.com/v1/archive`

**例**:
```python
# 直接実行
if __name__ == "__main__":
    main()

# モジュールとして実行
python -m agrr_core.cli weather --location 35.6762,139.6503 --days 7
```

## エラーハンドリング

### KeyboardInterrupt

ユーザーによる操作中断（Ctrl+C）を処理します。

```python
except KeyboardInterrupt:
    print("\n\nOperation cancelled by user.")
    sys.exit(1)
```

**出力例**:
```
Operation cancelled by user.
```

### 一般的な例外

予期しないエラーを処理します。

```python
except Exception as e:
    try:
        print(f"\n❌ Unexpected error: {e}")
    except UnicodeEncodeError:
        print(f"\n[ERROR] Unexpected error: {e}")
    sys.exit(1)
```

**出力例**:
```
[ERROR] Unexpected error: Connection failed
```

## Unicode対応

Windows環境でのUnicode文字表示に対応しています。

```python
try:
    print(f"\n❌ Unexpected error: {e}")
except UnicodeEncodeError:
    # Fallback for systems that don't support Unicode emojis
    print(f"\n[ERROR] Unexpected error: {e}")
```

## 使用方法

### コマンドライン実行

```bash
# ヘルプの表示
python -m agrr_core.cli --help

# 天気予報の取得
python -m agrr_core.cli weather --location 35.6762,139.6503 --days 7

# 特定の日付範囲で取得
python -m agrr_core.cli weather --location 35.6762,139.6503 --start-date 2024-01-01 --end-date 2024-01-07
```

### プログラムからの呼び出し

```python
import asyncio
from agrr_core.cli import main

# 直接実行
main()

# または、コンテナを直接使用
from agrr_core.framework.container import CLIContainer

async def custom_cli():
    container = CLIContainer()
    await container.run_cli(['weather', '--location', '35.6762,139.6503', '--days', '7'])

asyncio.run(custom_cli())
```

## 設定

### デフォルト設定

```python
config = {
    'open_meteo_base_url': 'https://archive-api.open-meteo.com/v1/archive'
}
```

### カスタム設定

環境変数や設定ファイルを使用して設定をカスタマイズできます。

```python
import os

def main():
    # 環境変数から設定を読み込み
    base_url = os.getenv('OPEN_METEO_BASE_URL', 'https://archive-api.open-meteo.com/v1/archive')
    
    config = {
        'open_meteo_base_url': base_url
    }
    container = CLIContainer(config)
    
    # ... 残りの処理
```

## 実行例

### 成功時の実行

```bash
$ python -m agrr_core.cli weather --location 35.6762,139.6503 --days 3

[SUCCESS] Fetching weather data for location (35.6762, 139.6503) from 2024-01-08 to 2024-01-10...

================================================================================
WEATHER FORECAST
================================================================================

Date        Max Temp   Min Temp   Avg Temp   Precip   Sunshine  
----------------------------------------------------------------
2024-01-08  12.5°C     5.2°C      8.9°C      2.1mm    6.5h      
2024-01-09  15.3°C     7.8°C      11.6°C     0.0mm    8.2h      
2024-01-10  18.1°C     9.5°C      13.8°C     0.5mm    7.8h      

================================================================================
Total records: 3
================================================================================
```

### エラー時の実行

```bash
$ python -m agrr_core.cli weather --location 91.0,139.6503 --days 7

[ERROR] VALIDATION_ERROR: Latitude must be between -90 and 90, got 91.0
```

### 中断時の実行

```bash
$ python -m agrr_core.cli weather --location 35.6762,139.6503 --days 7
^C

Operation cancelled by user.
```

## デバッグ

### ログ出力の有効化

```python
import logging

def main():
    # ログレベルの設定
    logging.basicConfig(level=logging.DEBUG)
    
    # ... 残りの処理
```

### エラーの詳細表示

```python
import traceback

def main():
    try:
        # ... 処理
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        traceback.print_exc()  # スタックトレースの表示
        sys.exit(1)
```

## テスト

```python
import pytest
from unittest.mock import patch, MagicMock
from agrr_core.cli import main

class TestCLIEntryPoint:
    def test_main_success(self):
        """Test successful CLI execution."""
        with patch('agrr_core.framework.container.CLIContainer') as mock_container:
            mock_instance = MagicMock()
            mock_container.return_value = mock_instance
            
            # テスト実行
            main()
            
            # 検証
            mock_instance.run_cli.assert_called_once()
    
    def test_main_keyboard_interrupt(self):
        """Test keyboard interrupt handling."""
        with patch('agrr_core.framework.container.CLIContainer') as mock_container:
            mock_instance = MagicMock()
            mock_instance.run_cli.side_effect = KeyboardInterrupt()
            mock_container.return_value = mock_instance
            
            # テスト実行
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            # 検証
            assert exc_info.value.code == 1
    
    def test_main_exception(self):
        """Test exception handling."""
        with patch('agrr_core.framework.container.CLIContainer') as mock_container:
            mock_instance = MagicMock()
            mock_instance.run_cli.side_effect = Exception("Test error")
            mock_container.return_value = mock_instance
            
            # テスト実行
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            # 検証
            assert exc_info.value.code == 1
```

## パッケージ化

### setup.pyでの設定

```python
# setup.py
entry_points={
    'console_scripts': [
        'agrr-weather=agrr_core.cli:main',
    ],
}
```

### インストール後の使用

```bash
# パッケージインストール後
pip install agrr-core

# コマンドラインから直接実行
agrr-weather weather --location 35.6762,139.6503 --days 7
```

## 利用可能なコマンド

### optimize コマンド
- `period` - 最適な栽培期間の計算
- `allocate` - 複数圃場での作物配分最適化
- `adjust` - 既存配分の調整
- `candidates` - 候補リストの提示

### 使用例
```bash
# 候補リスト提示
agrr optimize candidates \
  --allocation current_allocation.json \
  --fields-file fields.json \
  --crops-file crops.json \
  --target-crop tomato \
  --planning-start 2024-04-01 --planning-end 2024-10-31 \
  --weather-file weather.json \
  --output candidates.txt
```

## 拡張

### 新しいコマンドの追加

1. `CLIWeatherController`に新しいコマンドハンドラーを追加
2. 対応するPresenterメソッドを実装
3. テストケースを作成
4. ドキュメントを更新

### 設定の拡張

```python
def main():
    config = {
        'open_meteo_base_url': os.getenv('OPEN_METEO_BASE_URL', 'https://archive-api.open-meteo.com/v1/archive'),
        'timeout': int(os.getenv('API_TIMEOUT', '30')),
        'retry_count': int(os.getenv('RETRY_COUNT', '3')),
    }
    container = CLIContainer(config)
    # ... 残りの処理
```
