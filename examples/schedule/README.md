# Schedule Command Examples

このディレクトリには、`agrr schedule`コマンドで使用するサンプルファイルが含まれています。

## ファイル構成

- `stage_requirements_tomato.json`: トマトの栽培ステージ要件
- `agricultural_tasks_tomato.json`: トマト栽培で使用する農業作業一覧

## 使用方法

### 基本的な使用方法

```bash
# トマトの作業スケジュールを生成（コンソール表示）
python3 -m agrr_core.cli schedule \
  --crop-name "トマト" \
  --variety "アイコ" \
  --stage-requirements examples/schedule/stage_requirements_tomato.json \
  --agricultural-tasks examples/schedule/agricultural_tasks_tomato.json

# 結果をファイルに保存
python3 -m agrr_core.cli schedule \
  --crop-name "トマト" \
  --variety "アイコ" \
  --stage-requirements examples/schedule/stage_requirements_tomato.json \
  --agricultural-tasks examples/schedule/agricultural_tasks_tomato.json \
  --output tomato_schedule.json
```

### ファイル形式の説明

#### Stage Requirements File (stage_requirements_tomato.json)

作物の各栽培ステージの要件を定義します：

- **stage**: ステージ名と順序
- **temperature**: 温度要件（基本温度、最適範囲、ストレス閾値など）
- **thermal**: 熱量要件（必要なGDD）
- **sunshine**: 日照要件（最小・目標日照時間）

#### Agricultural Tasks File (agricultural_tasks_tomato.json)

実行可能な農業作業の一覧を定義します：

- **task_id**: 作業の一意ID
- **name**: 作業名
- **description**: 作業の詳細説明
- **time_per_sqm**: 1平方メートルあたりの作業時間（時間）
- **weather_dependency**: 天候依存度（low/medium/high）
- **required_tools**: 必要な工具・機械
- **skill_level**: 必要な技能レベル（beginner/intermediate/advanced）

### 出力形式

生成されるスケジュールには以下の情報が含まれます：

- **task_schedules**: 各作業のスケジュール情報
  - `stage_order`: 実行ステージ順序
  - `gdd_trigger`: GDDトリガー値
  - `gdd_tolerance`: GDD許容範囲
  - `priority`: 優先度
  - `precipitation_max`: 最大降水量制限
  - `wind_speed_max`: 最大風速制限
  - `temperature_min/max`: 温度制限
- **total_duration_days**: 総作業日数
- **weather_dependencies**: 天候依存度の種類

### カスタマイズ

他の作物用のファイルを作成する場合は、以下の点に注意してください：

1. **stage_requirements**: 作物の特性に応じて温度・日照要件を調整
2. **agricultural_tasks**: 実際に実行する作業のみを含める
3. **weather_dependency**: 作業の天候依存度を正確に設定
4. **time_per_sqm**: 実際の作業効率に基づいて時間を設定

### トラブルシューティング

- **ファイルが見つからない**: ファイルパスが正しいか確認
- **JSON形式エラー**: JSONの構文が正しいか確認
- **AI生成エラー**: LLMサービスが利用可能か確認
