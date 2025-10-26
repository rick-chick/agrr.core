# CLIヘルプテスト - 改善チケット

## 高優先度チケット

### 🚨 TICKET-001: 日付範囲エラーの適切な表示
- **問題**: `weather --days 1`でエラーメッセージが表示されない
- **影響**: ユーザーがエラーの原因を理解できない
- **解決策**: 最小日数要件の明記とエラーメッセージの表示
- **優先度**: 高
- **見積もり**: 2時間
- **ステータス**: 未着手

**🔍 技術報告 (2025-10-26)**:
- **事実確認**: `python3 -m agrr_core weather --location 35.6762,139.6503 --days 1 --json` で出力なしを確認
- **根本原因**: `WeatherCliFetchController.calculate_date_range()` で最小日数検証が実装されていない
- **実装詳細**: `days=1`の場合、`start_date = end_date - timedelta(days=1-1) = end_date`となり、同じ日付になる
- **検証結果**: `days=1` → `('2025-10-25', '2025-10-25')` (同じ日付)
- **修正箇所**: `src/agrr_core/adapter/controllers/weather_cli_controller.py:283-292`
- **修正案**: `if days < 2: raise ValueError("Minimum 2 days required for weather data")`

**💡 理想的な対応方法**:
1. **最小日数検証の実装**:
   ```python
   def calculate_date_range(self, days: int) -> Tuple[str, str]:
       if days < 2:
           raise ValueError("Minimum 2 days required for weather data. Use --days 2 or more, or specify --start-date and --end-date")
       # 既存の実装...
   ```

2. **ヘルプ情報の改善**:
   - `--days` パラメータの説明に最小値要件を明記
   - エラー時の対処法をヘルプに追加

3. **エラーメッセージの統一**:
   - 他のコマンドと同様の形式でエラーメッセージを表示
   - JSON出力時は統一されたエラー形式を使用

4. **テストケースの追加**:
   - `days=1` でのエラーハンドリングテスト
   - エラーメッセージの表示確認テスト

**再現方法:**
```bash
# エラーが表示されない（期待: エラーメッセージ表示）
python3 -m agrr_core weather --location 35.6762,139.6503 --days 1 --json

# 正常動作（期待: 天気データ表示）
python3 -m agrr_core weather --location 35.6762,139.6503 --days 2 --json
```

**実装確認:**
- `WeatherCliFetchController.handle_weather_command`メソッドでdaysパラメータの最小値検証が実装されていない
- `calculate_date_range`メソッドではdays-1の計算はあるが、最小値チェックはない

**期待されるエラーメッセージ:**
```
❌ Error: Minimum 2 days required for weather data
   Use --days 2 or more, or specify --start-date and --end-date
```

### 🚨 TICKET-002: エラーメッセージの統一
- **問題**: 一部のコマンドでエラーメッセージが表示されない
- **影響**: ユーザーがエラーの原因を理解できない
- **解決策**: すべてのコマンドで適切なエラーメッセージを表示
- **優先度**: 高
- **見積もり**: 4時間
- **ステータス**: 未着手

**🔍 技術報告 (2025-10-26)**:
- **事実確認**: コマンドによってエラーメッセージの表示形式が異なる
- **実装状況**:
  - `crop --query "トマト"` → JSON形式: `{"success": false, "error": "Crafting failed: Failed to initialize OpenAI client: [Errno 2] No such file or directory", "code": "CROP_REQUIREMENT_ERROR"}`
  - `forecast --location 35.6762,139.6503` → 出力なし
  - `predict --input "nonexistent.json"` → 出力なし
  - `progress --crop-file "test.json"` → エラーメッセージ: `Error loading crop profile: FILE_ERROR: Failed to read file test.json: [Errno 2] No such file or directory: 'test.json'`
  - `optimize period --crop-file "test.json"` → エラーメッセージ: `❌ Unexpected error: FILE_ERROR: File not found: test.json`
- **根本原因**: 各コントローラーで異なるエラーハンドリング実装
- **修正箇所**: 
  - `src/agrr_core/adapter/controllers/weather_cli_controller.py:462-467`
  - `src/agrr_core/adapter/presenters/weather_cli_presenter.py:210-221`
  - `src/agrr_core/adapter/presenters/crop_profile_craft_presenter.py:13-14`

**💡 理想的な対応方法**:
1. **統一エラーハンドリングの実装**:
   ```python
   # 共通エラーハンドリングクラスの作成
   class CLIErrorHandler:
       @staticmethod
       def handle_error(error: Exception, json_output: bool = False) -> None:
           if json_output:
               print(json.dumps({"success": False, "error": str(error), "code": "CLI_ERROR"}))
           else:
               print(f"❌ Error: {str(error)}")
   ```

2. **各コントローラーの統一**:
   - すべてのコントローラーで同じエラーハンドリングパターンを使用
   - JSON出力時は統一された形式でエラーを表示
   - テキスト出力時は統一された絵文字とメッセージ形式を使用

3. **エラーメッセージの標準化**:
   - エラーコードの統一（`FILE_ERROR`, `NETWORK_ERROR`, `VALIDATION_ERROR`など）
   - エラーメッセージの形式統一（`❌ Error [CODE]: message`）
   - 対処法の提示（「ファイルが存在しません → ファイルパスを確認してください」など）

4. **forecast/predictコマンドの改善**:
   - `--output` パラメータを必須入力に変更
   - Gateway経由でのファイル出力処理を実装
   - 出力ファイルの形式統一（JSON形式で統一）

5. **テストケースの追加**:
   - 各コマンドでのエラーメッセージ表示テスト
   - JSON出力時のエラー形式テスト
   - エラーハンドリングの統一性テスト
   - forecast/predictの必須outputパラメータテスト

**再現方法:**
```bash
# エラーメッセージが表示されないコマンド
python3 -m agrr_core weather --location 35.6762,139.6503 --days 1 --json
python3 -m agrr_core forecast --location 35.6762,139.6503
python3 -m agrr_core predict --input "nonexistent.json" --output "output.json" --days 7

# エラーメッセージが表示されるコマンド（参考）
python3 -m agrr_core crop --query "トマト"
# 結果: {"success": false, "error": "Crafting failed: Failed to initialize OpenAI client: [Errno 2] No such file or directory", "code": "CROP_REQUIREMENT_ERROR"}
```

**🔧 追加の技術詳細 (forecast/predictコマンド)**:
- **現在の問題**: `forecast`と`predict`コマンドで`--output`パラメータがオプション
- **改善案**: `--output`パラメータを必須入力に変更
- **実装方法**: Gateway経由でのファイル出力処理を実装
  ```python
  # WeatherCliController での実装例
  def create_argument_parser(self) -> argparse.ArgumentParser:
      # forecastコマンド
      forecast_parser.add_argument(
          '--output', '-o',
          required=True,  # 必須入力に変更
          help='Output file path (required)'
      )
      
      # predictコマンド  
      predict_parser.add_argument(
          '--output', '-o',
          required=True,  # 必須入力に変更
          help='Output file path (required)'
      )
  ```
- **Gateway経由の実装**: `WeatherFileGateway`を使用してファイル出力を統一

**期待される統一エラーメッセージ:**
```python
# ネットワークエラー
print("❌ Network Error: Unable to connect to weather API")

# ファイルエラー
print("❌ File Error: Required file not found")

# 認証エラー
print("❌ Authentication Error: Invalid API key")

# 必須パラメータエラー（forecast/predict）
print("❌ Validation Error: --output parameter is required for forecast/predict commands")
```

## 中優先度チケット

### 📋 TICKET-003: ヘルプ情報の改善
- **問題**: 事前要件の明記が不足
- **影響**: ユーザーが外部依存関係を理解できない
- **解決策**: ヘルプに「事前要件」セクションを追加
- **優先度**: 中
- **見積もり**: 3時間
- **ステータス**: 未着手

**🔍 技術報告 (2025-10-26)**:
- **事実確認**: ヘルプ情報に事前要件セクションが存在しない
- **実装状況**:
  - `crop --help` → AI使用の記載はあるが、OpenAI clientの設定方法は記載なし
  - `schedule --help` → ファイルパスの指定方法のみで、事前要件の説明なし
  - メインヘルプ → 設定ファイルの存在は記載されているが、設定方法の詳細はなし
- **修正箇所**: `src/agrr_core/cli.py:30-310` (print_help関数)
- **修正案**: ヘルプに「事前要件」セクションを追加し、外部依存関係と設定方法を明記

**💡 理想的な対応方法**:
1. **事前要件セクションの追加**:
   ```markdown
   ## 事前要件
   
   ### 外部依存関係
   - Open-Meteo API: 天気データ取得（無料、APIキー不要）
   - OpenAI API: 作物プロファイル生成（APIキー必要）
   - 設定ファイル: agrr_config.yaml
   
   ### 設定方法
   1. 設定ファイルの作成: `cp config/agrr_config.yaml .`
   2. OpenAI APIキーの設定: 環境変数 `OPENAI_API_KEY` または設定ファイル
   3. ネットワーク接続の確認: インターネット接続が必要
   ```

2. **各コマンドのヘルプ改善**:
   - `crop --help`: OpenAI APIキーの設定方法を明記
   - `schedule --help`: 必要なファイルの形式とサンプルを明記
   - `weather --help`: 最小日数要件を明記
   - `forecast --help`: `--output`パラメータが必須であることを明記
   - `predict --help`: `--output`パラメータが必須であることを明記

3. **設定ガイドの作成**:
   - 設定ファイルのテンプレート提供
   - 環境変数の設定方法説明
   - トラブルシューティングガイド

4. **サンプルファイルの案内**:
   - ヘルプでサンプルファイルの存在を明記
   - サンプルファイルの使用方法を説明
   - クイックスタートガイドの提供

**再現方法:**
```bash
# 外部依存関係エラーが発生
python3 -m agrr_core crop --query "トマト"
# 結果: OpenAI client初期化エラー

python3 -m agrr_core schedule --crop-name "トマト" --variety "アイコ" --stage-requirements "test.json" --agricultural-tasks "test.json"
# 結果: ファイルが見つからないエラー
```

**期待されるヘルプ追加:**
```markdown
## 事前要件

### 外部依存関係
- Open-Meteo API: 天気データ取得
- OpenAI API: 作物プロファイル生成
- 設定ファイル: agrr_config.yaml

### 設定方法
1. 設定ファイルの作成
2. APIキーの設定
3. ネットワーク接続の確認
```

### 📋 TICKET-004: 設定ファイルの説明
- **問題**: 設定ファイルの設定方法が不明
- **影響**: ユーザーがAPIキーなどの設定方法を理解できない
- **解決策**: 設定ファイルの設定方法を説明
- **優先度**: 中
- **見積もり**: 2時間
- **ステータス**: 未着手

**🔍 技術報告 (2025-10-26)**:
- **事実確認**: 設定ファイルは存在するが、ヘルプでの説明が不十分
- **実装状況**:
  - `config/agrr_config.yaml` は存在
  - メインヘルプで `agrr_config.yaml` の存在は記載されているが、具体的な設定方法は説明なし
  - OpenAI clientの設定方法がヘルプに記載されていない
- **設定ファイル内容**: `config/agrr_config.yaml` にログ設定、通知設定、デーモン設定が含まれている
- **修正箇所**: `src/agrr_core/cli.py:30-310` (print_help関数)
- **修正案**: ヘルプに設定ファイルの具体的な設定方法とAPIキーの設定方法を明記

**💡 理想的な対応方法**:
1. **設定ファイルの詳細説明**:
   ```markdown
   ## 設定ファイル (agrr_config.yaml)
   
   ### 基本設定
   ```yaml
   # OpenAI API設定
   openai:
     api_key: "your-api-key-here"  # 環境変数 OPENAI_API_KEY でも設定可能
     model: "gpt-4"
   
   # ログ設定
   logging:
     level: "INFO"
     log_file: "/tmp/agrr.log"
   
   # 通知設定
   notifications:
     email:
       enabled: false
     slack:
       enabled: false
   ```
   ```

2. **環境変数での設定方法**:
   - `OPENAI_API_KEY`: OpenAI APIキー
   - `AGRR_LOG_LEVEL`: ログレベル
   - `AGRR_EMAIL_ENABLED`: メール通知の有効化

3. **設定ファイルのテンプレート提供**:
   - デフォルト設定ファイルのコピー方法
   - 必須設定項目の明記
   - オプション設定項目の説明

4. **設定検証機能の追加**:
   - 設定ファイルの妥当性チェック
   - 環境変数の確認機能
   - 設定不備時のエラーメッセージ改善

**再現方法:**
```bash
# 設定ファイルが存在しない場合のエラー
python3 -m agrr_core crop --query "トマト"
# 結果: "Failed to initialize OpenAI client: [Errno 2] No such file or directory"
```

**期待される設定ファイル例:**
```yaml
# agrr_config.yaml
openai:
  api_key: "your-api-key-here"
  model: "gpt-4"

logging:
  level: "INFO"

notifications:
  email:
    enabled: false
  slack:
    enabled: false
```

### 📋 TICKET-005: サンプルデータファイルの提供
- **問題**: テスト用のサンプルファイルが不足
- **影響**: ユーザーがコマンドをテストできない
- **解決策**: サンプルデータファイルの提供
- **優先度**: 中
- **見積もり**: 2時間
- **ステータス**: 未着手

**🔍 技術報告 (2025-10-26)**:
- **事実確認**: サンプルファイルは存在するが、ヘルプでの案内が不十分
- **実装状況**:
  - `test_data/` ディレクトリにサンプルファイルが存在
  - `weather_sample.json`, `agricultural_tasks_sample.json`, `stage_requirements_sample.json` など
  - しかし、ヘルプでこれらのサンプルファイルの存在や使用方法が案内されていない
- **修正箇所**: `src/agrr_core/cli.py:30-310` (print_help関数)
- **修正案**: ヘルプにサンプルファイルの存在と使用方法を明記

**💡 理想的な対応方法**:
1. **サンプルファイルの案内追加**:
   ```markdown
   ## サンプルファイル
   
   ### 利用可能なサンプルファイル
   - `test_data/weather_sample.json`: 天気データのサンプル
   - `test_data/agricultural_tasks_sample.json`: 農業タスクのサンプル
   - `test_data/stage_requirements_sample.json`: 成長段階要件のサンプル
   
   ### 使用方法
   ```bash
   # サンプルファイルを使用したコマンド実行例
   agrr progress --crop-file test_data/stage_requirements_sample.json \
     --start-date 2024-05-01 --weather-file test_data/weather_sample.json
   ```
   ```

2. **クイックスタートガイドの作成**:
   - サンプルファイルを使った基本的な使用方法
   - ステップバイステップのチュートリアル
   - よくある使用パターンの例

3. **サンプルファイルの改善**:
   - より実用的なサンプルデータの提供
   - コメント付きのサンプルファイル
   - 複数の使用例を含むサンプル

4. **サンプルファイルの自動検出**:
   - ヘルプでサンプルファイルの一覧を動的に表示
   - サンプルファイルの存在確認機能
   - サンプルファイルの使用方法の自動生成

5. **forecast/predictコマンドの改善**:
   - `--output`パラメータを必須入力に変更
   - Gateway経由でのファイル出力処理を実装
   - 出力ファイルの形式統一（JSON形式で統一）
   - ヘルプで必須パラメータであることを明記

**再現方法:**
```bash
# 存在しないファイルを指定してエラー
python3 -m agrr_core progress --crop-file "test.json" --start-date "2024-05-01" --weather-file "test.json"
# 結果: "Error loading crop profile: FILE_ERROR: Failed to read file test.json: [Errno 2] No such file or directory: 'test.json'"
```

**期待されるサンプルファイル:**
- `sample_fields.json` - フィールド設定のサンプル
- `sample_crops.json` - 作物設定のサンプル
- `sample_weather.json` - 天気データのサンプル

### 📋 TICKET-006: ファイルパス指定の改善
- **問題**: 相対パスでファイルが見つからない
- **影響**: ユーザーがファイルパスの指定方法を理解できない
- **解決策**: ヘルプにファイルパス指定方法を明記
- **優先度**: 中
- **見積もり**: 1時間
- **ステータス**: 未着手

**再現方法:**
```bash
# 相対パスでエラー
python3 -m agrr_core optimize allocate --fields-file "fields.json" --crops-file "crops.json" --planning-start 2024-04-01 --planning-end 2024-10-31 --weather-file "weather.json"
# 結果: "Error loading fields: FILE_ERROR: File not found: fields.json"

# 絶対パスで成功
python3 -m agrr_core optimize allocate --fields-file "/home/akishige/projects/agrr.core/fields.json" --crops-file "/home/akishige/projects/agrr.core/crops.json" --planning-start 2024-04-01 --planning-end 2024-10-31 --weather-file "/home/akishige/projects/agrr.core/weather.json"
# 結果: 正常に動作
```

**期待されるヘルプ追加:**
```markdown
## ファイルパス指定
- 絶対パス: /home/user/project/file.json
- 相対パス: ./file.json または file.json
- 注意: 相対パスは現在の作業ディレクトリからの相対パス
```

## 低優先度チケット

### 🔧 TICKET-007: エラー時の対処法の詳細化
- **問題**: エラー時の対処法が不明
- **影響**: ユーザーがエラーを解決できない
- **解決策**: エラー時の対処法を詳細化
- **優先度**: 低
- **見積もり**: 3時間
- **ステータス**: 未着手

### 🔧 TICKET-008: トラブルシューティングガイドの作成
- **問題**: トラブルシューティング情報が散在
- **影響**: ユーザーが問題を解決しにくい
- **解決策**: 包括的なトラブルシューティングガイドの作成
- **優先度**: 低
- **見積もり**: 4時間
- **ステータス**: 未着手

## 完了基準

### TICKET-001: 日付範囲エラーの適切な表示
- [ ] 最小日数要件の明記
- [ ] エラーメッセージの表示
- [ ] テストケースの実行

### TICKET-002: エラーメッセージの統一
- [ ] すべてのコマンドでエラーメッセージが表示される
- [ ] エラーメッセージの統一
- [ ] テストケースの実行

### TICKET-003: ヘルプ情報の改善
- [ ] ヘルプに「事前要件」セクションを追加
- [ ] 外部依存関係の明記
- [ ] 設定方法の説明

### TICKET-004: 設定ファイルの説明
- [ ] 設定ファイルの作成方法を説明
- [ ] APIキーの設定方法を説明
- [ ] 設定ファイルの場所を明記

### TICKET-005: サンプルデータファイルの提供
- [ ] fields.jsonのサンプル提供
- [ ] crops.jsonのサンプル提供
- [ ] weather.jsonのサンプル提供

### TICKET-006: ファイルパス指定の改善
- [ ] 絶対パス指定方法を明記
- [ ] 相対パス指定方法を明記
- [ ] ファイルパス指定の例を追加