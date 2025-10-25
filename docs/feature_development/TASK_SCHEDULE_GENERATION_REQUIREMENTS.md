# 作業スケジュール生成機能 要件定義書

## 1. 概要

### 1.1 機能概要
LLMを活用して、作物のステージ要件と作業一覧を入力として、GDDベースの作業スケジュールを自動生成する機能。

### 1.2 目的
- 科学的根拠に基づいた作業スケジュールの自動生成
- 農家の作業計画の効率化
- 天候条件を考慮した実用的なスケジュール提供

## 2. 入力データ

### 2.1 作業一覧 (`agricultural_tasks`)
```json
{
  "task_id": "string",           // 作業ID
  "task_name": "string",         // 作業名
  "description": "string",       // 作業説明
  "time_per_sqm": "number",      // 1㎡あたり作業時間（時間）
  "weather_dependency": "string", // 天候依存度（high/medium/low）
  "precipitation_max": "number",  // 最大降水量（mm）
  "wind_speed_max": "number",     // 最大風速（m/s）
  "temperature_min": "number",    // 最低温度（℃）- オプション
  "temperature_max": "number"     // 最高温度（℃）- オプション
}
```

### 2.2 ステージ要件 (`stage_requirements`)
既存の作物ステージ要件システムから取得：
- 作物名・品種
- ステージ順序（`stage_order`）
- GDD要件
- 温度・日照要件

### 2.3 作物情報
- 作物名（`crop_name`）
- 品種（`variety`）

## 3. 出力データ

### 3.1 作業スケジュール (`task_schedule`)
```json
{
  "task_id": "string",           // 作業ID
  "stage_order": "number",       // ステージ順序番号
  "gdd_trigger": "number",       // GDDトリガー
  "gdd_tolerance": "number",     // GDD許容範囲
  "priority": "number",          // 優先度
  "precipitation_max": "number", // 最大降水量（mm）
  "wind_speed_max": "number",     // 最大風速（m/s）
  "temperature_min": "number",    // 最低温度（℃）- オプション
  "temperature_max": "number",    // 最高温度（℃）- オプション
  "description": "string"        // 説明
}
```

## 4. 設計仕様

### 4.1 スケジュール設定方法
- **GDDベース統一**: 既存システムとの整合性を保つ
- **日数ベースは除外**: 混乱を避けるため

### 4.2 作業分類
- **開始時点の作業**: `gdd_tolerance = 0`
  - 土壌準備、播種、育苗開始など
- **継続的な作業**: `gdd_tolerance > 0`
  - 定植、除草、収穫など

### 4.3 天候依存度
- **high**: 厳しい条件（農薬散布、収穫）
- **medium**: 中程度の条件（定植、収穫）
- **low**: 緩い条件（土壌準備、播種、除草）

### 4.4 除外作業
- **農薬散布・病害虫防除**: 別の最適化システムで管理
- **施肥・追肥**: 別の最適化システムで管理

## 5. サンプルデータ

### 5.1 作業一覧サンプル
```json
{
  "agricultural_tasks": [
    {
      "task_id": "soil_preparation",
      "task_name": "土壌準備",
      "description": "畑の耕起、施肥、マルチング",
      "time_per_sqm": 0.5,
      "weather_dependency": "low",
      "precipitation_max": 0.5,
      "wind_speed_max": 10.0
    },
    {
      "task_id": "seeding",
      "task_name": "播種",
      "description": "種子の播種作業",
      "time_per_sqm": 0.1,
      "weather_dependency": "low",
      "precipitation_max": 0.1,
      "wind_speed_max": 5.0
    },
    {
      "task_id": "transplanting",
      "task_name": "定植",
      "description": "苗の定植作業",
      "time_per_sqm": 0.2,
      "weather_dependency": "medium",
      "precipitation_max": 0.5,
      "wind_speed_max": 8.0
    },
    {
      "task_id": "weeding",
      "task_name": "除草",
      "description": "雑草の除去作業",
      "time_per_sqm": 0.3,
      "weather_dependency": "low",
      "precipitation_max": 1.0,
      "wind_speed_max": 10.0
    },
    {
      "task_id": "harvesting",
      "task_name": "収穫",
      "description": "作物の収穫作業",
      "time_per_sqm": 0.4,
      "weather_dependency": "medium",
      "precipitation_max": 0.5,
      "wind_speed_max": 8.0
    }
  ]
}
```

### 5.2 作業スケジュールサンプル
```json
{
  "task_schedule": [
    {
      "task_id": "soil_preparation",
      "stage_order": 1,
      "gdd_trigger": 0,
      "gdd_tolerance": 0,
      "priority": 1,
      "precipitation_max": 0.5,
      "wind_speed_max": 10.0,
      "description": "栽培開始前の土壌準備"
    },
    {
      "task_id": "seeding",
      "stage_order": 1,
      "gdd_trigger": 0,
      "gdd_tolerance": 0,
      "priority": 2,
      "precipitation_max": 0.1,
      "wind_speed_max": 5.0,
      "description": "栽培開始時の播種作業"
    },
    {
      "task_id": "transplanting",
      "stage_order": 2,
      "gdd_trigger": 200,
      "gdd_tolerance": 50,
      "priority": 3,
      "precipitation_max": 0.5,
      "wind_speed_max": 8.0,
      "description": "定植期の定植作業"
    },
    {
      "task_id": "weeding",
      "stage_order": 3,
      "gdd_trigger": 500,
      "gdd_tolerance": 100,
      "priority": 4,
      "precipitation_max": 1.0,
      "wind_speed_max": 10.0,
      "description": "生育期の除草作業"
    },
    {
      "task_id": "harvesting",
      "stage_order": 4,
      "gdd_trigger": 1000,
      "gdd_tolerance": 100,
      "priority": 5,
      "precipitation_max": 0.5,
      "wind_speed_max": 8.0,
      "description": "収穫期の収穫作業"
    }
  ]
}
```

## 6. LLMプロンプト設計

### 6.1 プロンプトテンプレート
```markdown
# 作業スケジュール生成プロンプト

## 入力データ
- 作物名: {crop_name}
- 品種: {variety}
- ステージ要件: {stage_requirements}
- 作業一覧: {agricultural_tasks}

## 生成要件
1. 各作業に適したステージ順序（stage_order）を設定
2. 各作業に適したGDDトリガーを設定
3. 作業の優先度を設定
4. 天候条件を考慮した実行条件を設定
5. 作業間の依存関係を考慮

## 出力形式
```json
{
  "task_schedules": [
    {
      "task_id": "string",
      "stage_order": "number",
      "gdd_trigger": "number",
      "gdd_tolerance": "number",
      "priority": "number",
      "precipitation_max": "number",
      "wind_speed_max": "number",
      "temperature_min": "number",
      "temperature_max": "number",
      "description": "string"
    }
  ]
}
```
```

### 6.2 WebSearch活用
- 最新の農業技術情報
- 地域別の栽培技術
- 天候パターンの分析
- 作業効率化の手法

## 7. アーキテクチャ設計

### 7.1 既存システムとの整合性
- 既存のLLM作物ステージ要件生成機能と同様のアーキテクチャ
- クリーンアーキテクチャ準拠
- 既存のエンティティ構造を活用

### 7.2 エンティティ設計
```python
@dataclass(frozen=True)
class AgriculturalTask:
    task_id: str
    task_name: str
    description: str
    time_per_sqm: float
    weather_dependency: str
    precipitation_max: float
    wind_speed_max: float
    temperature_min: Optional[float] = None
    temperature_max: Optional[float] = None

@dataclass(frozen=True)
class TaskSchedule:
    task_id: str
    stage_order: int
    gdd_trigger: float
    gdd_tolerance: float
    priority: int
    precipitation_max: float
    wind_speed_max: float
    temperature_min: Optional[float] = None
    temperature_max: Optional[float] = None
    description: str
```

## 8. 実装方針

### 8.1 段階的実装
1. **Phase 1**: 基本的な作業スケジュール生成
2. **Phase 2**: 天候条件の考慮
3. **Phase 3**: 作業間の依存関係の考慮

### 8.2 テスト戦略
- アーキテクチャに沿って各層の単体テスト
- 統合テストでの動作確認
- LLM応答の妥当性検証

### 8.3 拡張性
- 新しい作業カテゴリの追加
- 地域別の作業スケジュール
- 年次変動への対応

## 9. 制約事項

### 9.1 技術的制約
- LLM応答の一貫性
- 天候データの精度
- GDD計算の精度

### 9.2 機能的制約
- 農薬散布・施肥は別システムで管理
- 基本的な農作業のみ対象
- 地域・年次変動への対応は将来拡張

## 10. 成功指標

### 10.1 機能指標
- 作業スケジュールの生成精度
- 天候条件の考慮度
- 農家の満足度

### 10.2 技術指標
- LLM応答の一貫性
- 処理時間
- エラー率

この要件定義書に基づいて、実用的な作業スケジュール生成機能を実装します。
