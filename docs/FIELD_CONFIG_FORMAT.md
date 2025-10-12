# フィールド設定ファイルフォーマット

## 概要

フィールド設定ファイルは、圃場（Field）の情報をJSON形式で管理するためのファイルです。
`optimize-period`コマンドで`--field`オプションを使用する際に、このファイルから圃場情報を読み込みます。

## JSONフォーマット

`optimize-period`コマンドでは単一フィールド形式を使用します。

```json
{
  "field_id": "field_01",
  "name": "北圃場",
  "area": 1000.0,
  "daily_fixed_cost": 5000.0,
  "location": "北区画"
}
```

## フィールド定義

| フィールド名 | 型 | 必須 | 説明 |
|------------|-----|------|------|
| `field_id` | string | ✓ | 圃場の一意識別子 |
| `name` | string | ✓ | 圃場名（人間が読める名前） |
| `area` | float | ✓ | 圃場の面積（平方メートル） |
| `daily_fixed_cost` | float | ✓ | 日次固定コスト（円/日）。圃場の賃料、施設管理費、光熱費などを含む |
| `location` | string | | 圃場の位置情報（任意） |

## 使用例

### コマンドライン

```bash
# フィールド設定ファイルを使用して最適な栽培期間を計算
agrr optimize-period optimize \
  --crop rice \
  --variety Koshihikari \
  --evaluation-start 2024-04-01 \
  --evaluation-end 2024-09-30 \
  --weather-file weather.json \
  --field-config field_01.json
```

### daily_fixed_cost について

- フィールド設定ファイルから`daily_fixed_cost`が自動的に読み込まれます
- `--field-config`は必須パラメータです

## バリデーション

以下の条件を満たす必要があります：

1. **必須フィールド**: `field_id`, `name`, `area`, `daily_fixed_cost`は必須
2. **非負値**: `area`と`daily_fixed_cost`は0以上の値
3. **型**: 各フィールドは指定された型に変換可能である必要があります

## エラー処理

### ファイルが見つからない場合

```
Error: File not found: /path/to/fields.json
```

### フィールド設定が指定されていない場合

```
Error: --field-config is required
```

### 必須フィールドが不足している場合

```
Error: Missing required field(s): area, daily_fixed_cost
```

### 不正な値の場合

```
Error: Field 'daily_fixed_cost' must be non-negative
```

## サンプルファイル

プロジェクトの`examples/field_01.json`にサンプルファイルがあります。

## 実装の詳細

- **リポジトリ**: `FieldFileRepository` - JSONファイルからフィールドデータを読み込み
- **エンティティ**: `Field` - フィールド情報を表すエンティティ
- **DTO**: フィールドエンティティをそのままDTOに含めて各層間で受け渡し

## 関連ドキュメント

- [ARCHITECTURE.md](ARCHITECTURE.md) - アーキテクチャ全体の説明
- [optimize-period コマンドヘルプ](../README.md#optimize-period) - コマンドの使い方

