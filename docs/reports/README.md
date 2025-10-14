# 調査・分析レポート

このディレクトリには、agrr.coreプロジェクトの調査・分析レポートが格納されています。

## 📌 総合サマリー

### メインレポート

**ファイル**: [INVESTIGATION_SUMMARY.md](./INVESTIGATION_SUMMARY.md) ⭐

「期間不足」問題の調査から解決までの全体像。
- 問題の特定と原因分析
- 天気予測データの検証
- LightGBM実装による解決
- 最終推奨事項

**まずこちらをお読みください！**

### アーキテクチャ検証

**ファイル**: [ARCHITECTURE_VERIFICATION.md](./ARCHITECTURE_VERIFICATION.md) ⭐⭐

Clean Architectureへの準拠確認。
- 正しいレイヤー配置
- Interface定義の場所（Adapter層）
- 依存関係の流れ
- DI（依存性注入）の実装

**アーキテクチャを確認する際はこちら！**

---

## 詳細レポート一覧

### 1. 作物配分最適化の分析

**ファイル**: [ALLOCATION_ANALYSIS_REPORT.md](./ALLOCATION_ANALYSIS_REPORT.md)

**内容**:
- `agrr optimize allocate` コマンドの「期間不足」問題の調査結果
- 天気予測データの妥当性検証
- 作物プロファイル（GDD要件、基準温度）の問題点
- 推奨される対策と解決策

**作成日**: 2025年10月14日

---

### 2. 409日栽培計画の説明

**ファイル**: [EXPLANATION_409DAYS_BREAKDOWN.md](./EXPLANATION_409DAYS_BREAKDOWN.md)

**内容**:
- キュウリの409日栽培計画の内訳
- 検証済み期間（32%）vs 未検証期間（68%）の説明
- タイムラインと具体的なリスク
- 図解による分かりやすい解説

**作成日**: 2025年10月14日

---

### 3. 天気予測データの精度検証

**ファイル**: [WEATHER_FORECAST_VALIDATION_REPORT.md](./WEATHER_FORECAST_VALIDATION_REPORT.md)

**内容**:
- 2025年予測データの実測値との比較（287日分）
- 月別・季節別の精度分析
- GDD（積算温度）への影響評価
- 過去3年（2022-2024）との比較
- データソースの推定と信頼性評価

**主な発見**:
- 過去期間の精度: MAE=1.08°C（良好）
- 系統的バイアス: +0.81°C（暖かめ）
- 未来期間: 14.7ヶ月先の予測は信頼性が低い
- 過去3年との比較: 53.8%が異常値

**作成日**: 2025年10月14日

---

### 4. 天気予測精度向上計画

**ファイル**: [WEATHER_PREDICTION_IMPROVEMENT_PLAN.md](./WEATHER_PREDICTION_IMPROVEMENT_PLAN.md)

**内容**:
- ARIMAモデルの現状分析と改善案
- LightGBMの導入計画（詳細設計）
- Prophet、XGBoost、LSTMなどの代替モデル
- アンサンブル手法
- 実装ロードマップ（フェーズ1-4）

**期待される改善**:
- フェーズ1（Auto ARIMA）: 40%精度向上
- フェーズ2（LightGBM）: 53%精度向上
- フェーズ3（アンサンブル）: さらなる改善

**作成日**: 2025年10月14日

---

### 5. LightGBM実装完了レポート

**ファイル**: [LIGHTGBM_IMPLEMENTATION_SUMMARY.md](./LIGHTGBM_IMPLEMENTATION_SUMMARY.md)

**内容**:
- LightGBM予測モデルの実装詳細
- 特徴量エンジニアリング（50+特徴量）
- テストスイート（18テスト）
- CLI統合（--modelオプション）
- 使用方法とインストール手順

**実装されたファイル**:
- `src/agrr_core/adapter/services/feature_engineering_service.py`
- `src/agrr_core/adapter/services/prediction_lightgbm_service.py`
- `tests/test_adapter/test_prediction_lightgbm_service.py`

**ステータス**: ✅ 実装完了

**作成日**: 2025年10月14日

---

### 6. LightGBM検証結果レポート ⭐

**ファイル**: [LIGHTGBM_FINAL_RESULTS.md](./LIGHTGBM_FINAL_RESULTS.md)

**内容**:
- 20年分データ（2005-2024）での訓練結果
- 2025年実測データでの精度検証
- Climatological手法の有効性
- 月別精度分析
- 重要特徴量分析
- 1年以上の予測問題の解決方法

**精度結果**:
- MAE: 2.20°C（90日予測）
- RMSE: 2.71°C
- 訓練データ: 5,521日（20年分）
- Climatological手法で誤差累積を防止

**主な発見**:
- Autoregressive: MAE=7.88°C ❌
- Climatological: MAE=2.20°C ✅（72%改善）
- 過去の同時期データ活用が極めて有効

**ステータス**: ✅ 検証完了

**作成日**: 2025年10月14日

---

## レポート作成の経緯

### 調査の発端

`agrr optimize allocate` コマンドの実行時に、キュウリの栽培期間が409日と長くなる問題が発生。

### 調査プロセス

1. **最適化アルゴリズムの検証**
   - 全候補（199個）が完了可能
   - アルゴリズムは正常動作

2. **作物プロファイルの分析**
   - 必要GDD: 2,200度日（厳しい）
   - 基準温度: 10°C（寒冷地には高い）
   - 平均GDD/日: 4.05度日（低い）

3. **天気データの検証**
   - 実測データとの比較
   - 過去3年との比較
   - データソースの推定

### 主な発見

1. **「期間不足」は誤認** - 全候補で完了可能
2. **基準温度とGDD要件が不適切** - 寒冷地に厳しすぎる
3. **天気予測データに問題** - 未来14.7ヶ月先の予測は信頼できない
4. **データの53.8%が異常** - 過去実績と大きく乖離

### 解決策

1. **短期**: 過去の実測データ（2024年）を使用
2. **中期**: 作物プロファイルの調整
3. **長期**: 予測モデルの改善（LightGBM導入）

---

## 関連ドキュメント

- [アーキテクチャ設計](../ARCHITECTURE.md)
- [API リファレンス](../api/README.md)
- [CLI 使用方法](../../README.md)

---

**最終更新**: 2025年10月14日


