# アメリカ長期歴史気象データ取得ガイド（2000年以降）

## ✅ 実装完了：NOAA ISD FTPゲートウェイ

**2000年以降のアメリカ主要地点の長期歴史データを完全無料で取得可能になりました。**

### 特徴

- ✅ **完全無料** - 登録不要、API制限なし
- ✅ **長期データ** - 1901年〜現在（2000年以降推奨）
- ✅ **高品質** - NOAA公式データ（空港観測所）
- ✅ **毎日更新** - 1-2日遅れで最新データ追加
- ✅ **アメリカ主要15都市対応**

## 使用方法

### 1. 基本的な使用（2000年以降）

```bash
# ニューヨーク 2023年全体
agrr weather --location 40.7128,-74.0060 \
  --start-date 2023-01-01 --end-date 2023-12-31 \
  --data-source noaa-ftp

# ロサンゼルス 2020年から2023年
agrr weather --location 34.0522,-118.2437 \
  --start-date 2020-01-01 --end-date 2023-12-31 \
  --data-source noaa-ftp --json > la_2020_2023.json

# シカゴ 2000年1月
agrr weather --location 41.8781,-87.6298 \
  --start-date 2000-01-01 --end-date 2000-01-31 \
  --data-source noaa-ftp
```

### 2. 長期的なデータ分析

```bash
# 過去20年間のデータを取得（2004-2023）
agrr weather --location 40.7128,-74.0060 \
  --start-date 2004-01-01 --end-date 2023-12-31 \
  --data-source noaa-ftp --json > ny_20years.json

# GDD計算に使用
agrr crop --query "corn Field Corn" > corn.json
agrr progress --crop-file corn.json \
  --start-date 2023-05-01 \
  --weather-file ny_20years.json
```

### 3. データソースの比較

| データソース | 期間 | 対象地域 | 品質 | 登録 |
|--------------|------|----------|------|------|
| **noaa-ftp** | 1901年〜現在 | アメリカ主要都市 | ⭐⭐⭐⭐⭐ | 不要 |
| openmeteo | 2-3年前〜現在 | 世界中 | ⭐⭐⭐⭐ | 不要 |
| jma | 数年前〜現在 | 日本のみ | ⭐⭐⭐⭐⭐ | 不要 |

## アメリカ主要都市（NOAA FTP対応）

### 東海岸

```bash
# New York, NY
agrr weather --location 40.7128,-74.0060 --start-date 2020-01-01 --end-date 2020-12-31 --data-source noaa-ftp

# Boston, MA
agrr weather --location 42.3601,-71.0589 --start-date 2020-01-01 --end-date 2020-12-31 --data-source noaa-ftp

# Washington, DC
agrr weather --location 38.9072,-77.0369 --start-date 2020-01-01 --end-date 2020-12-31 --data-source noaa-ftp

# Miami, FL
agrr weather --location 25.7617,-80.1918 --start-date 2020-01-01 --end-date 2020-12-31 --data-source noaa-ftp

# Atlanta, GA
agrr weather --location 33.7490,-84.3880 --start-date 2020-01-01 --end-date 2020-12-31 --data-source noaa-ftp
```

### 中西部

```bash
# Chicago, IL
agrr weather --location 41.8781,-87.6298 --start-date 2020-01-01 --end-date 2020-12-31 --data-source noaa-ftp

# Denver, CO
agrr weather --location 39.7392,-104.9903 --start-date 2020-01-01 --end-date 2020-12-31 --data-source noaa-ftp

# Houston, TX
agrr weather --location 29.7604,-95.3698 --start-date 2020-01-01 --end-date 2020-12-31 --data-source noaa-ftp

# Dallas, TX
agrr weather --location 32.7767,-96.7970 --start-date 2020-01-01 --end-date 2020-12-31 --data-source noaa-ftp
```

### 西海岸

```bash
# Los Angeles, CA
agrr weather --location 34.0522,-118.2437 --start-date 2020-01-01 --end-date 2020-12-31 --data-source noaa-ftp

# San Francisco, CA
agrr weather --location 37.7749,-122.4194 --start-date 2020-01-01 --end-date 2020-12-31 --data-source noaa-ftp

# Seattle, WA
agrr weather --location 47.6062,-122.3321 --start-date 2020-01-01 --end-date 2020-12-31 --data-source noaa-ftp

# Portland, OR
agrr weather --location 45.5152,-122.6784 --start-date 2020-01-01 --end-date 2020-12-31 --data-source noaa-ftp

# San Diego, CA
agrr weather --location 32.7157,-117.1611 --start-date 2020-01-01 --end-date 2020-12-31 --data-source noaa-ftp
```

### その他

```bash
# Las Vegas, NV
agrr weather --location 36.1699,-115.1398 --start-date 2020-01-01 --end-date 2020-12-31 --data-source noaa-ftp

# Phoenix, AZ
agrr weather --location 33.4484,-112.0740 --start-date 2020-01-01 --end-date 2020-12-31 --data-source noaa-ftp

# Austin, TX
agrr weather --location 30.2672,-97.7431 --start-date 2020-01-01 --end-date 2020-12-31 --data-source noaa-ftp
```

## 農業研究での使用例

### 1. 過去20年の気候変動分析

```bash
# 2004年から2023年までの20年間のデータを取得
for year in {2004..2023}; do
  echo "Fetching $year..."
  agrr weather --location 40.7128,-74.0060 \
    --start-date ${year}-01-01 --end-date ${year}-12-31 \
    --data-source noaa-ftp --json > ny_${year}.json
done

# すべてのデータを結合して分析
python analyze_climate_trend.py ny_*.json
```

### 2. 最適な栽培期間の歴史分析

```bash
# 過去10年分のデータで最適な栽培期間を分析
agrr weather --location 34.0522,-118.2437 \
  --start-date 2014-01-01 --end-date 2023-12-31 \
  --data-source noaa-ftp --json > la_10years.json

# 作物プロファイル作成
agrr crop --query "tomato Beefsteak" > tomato.json

# 各年の最適栽培期間を計算
for year in {2014..2023}; do
  agrr optimize period \
    --crop-file tomato.json \
    --evaluation-start ${year}-04-01 \
    --evaluation-end ${year}-09-30 \
    --weather-file la_10years.json \
    --field-file field.json
done
```

### 3. 異常気象イベントの影響分析

```bash
# 2012年（ハリケーン・サンディ）のデータ取得
agrr weather --location 40.7128,-74.0060 \
  --start-date 2012-10-01 --end-date 2012-11-30 \
  --data-source noaa-ftp --json > sandy_2012.json

# 通常年との比較
agrr weather --location 40.7128,-74.0060 \
  --start-date 2011-10-01 --end-date 2011-11-30 \
  --data-source noaa-ftp --json > normal_2011.json
```

## 技術的詳細

### データソース

- **NOAA Integrated Surface Database (ISD)**
- FTPサーバー: `ftp.ncei.noaa.gov`
- パス: `/pub/data/noaa/{year}/{station}.gz`
- 形式: 固定幅テキスト（gzip圧縮）

### データ品質

- **観測頻度**: 1時間ごと
- **日次集計**: 自動的に日次統計（最高・最低・平均）に集計
- **欠損データ**: 欠損がある場合は該当時間のデータをスキップ
- **品質管理**: NOAAの品質管理済みデータ

### 取得可能なデータ項目

- ✅ 気温（最高・最低・平均）
- ✅ 風速
- ❌ 降水量（時間単位では取得困難）
- ❌ 日照時間（ISに含まれず）

### パフォーマンス

- **ダウンロード速度**: 約0.5-1MB/年（圧縮済み）
- **処理時間**: 1年分で約5-10秒
- **推奨期間**: 一度に1-5年分

## トラブルシューティング

### エラー: "Failed to fetch FTP data"

**原因**: ネットワーク接続、FTPサーバーのタイムアウト

**解決策**:
```bash
# タイムアウトを長くする（実装内部で60秒に設定済み）
# 年単位で分割して取得
agrr weather --location 40.7128,-74.0060 \
  --start-date 2020-01-01 --end-date 2020-12-31 \
  --data-source noaa-ftp
```

### エラー: "No weather data found"

**原因**: 指定した観測所にその年のデータが存在しない

**解決策**:
- 2000年以降のデータを推奨
- 他の近くの都市を試す

### データが少ない

**原因**: ISDデータは時間単位のため、欠損があると日次データも少なくなる

**対策**:
- より長い期間を指定して平均化
- Open-Meteoと組み合わせて使用

## 推奨ワークフロー

### 長期データ分析（2000年以降）

```bash
# 1. NOAA FTPで長期データ取得
agrr weather --location 40.7128,-74.0060 \
  --start-date 2000-01-01 --end-date 2023-12-31 \
  --data-source noaa-ftp --json > ny_long_term.json

# 2. 気候トレンド分析
python analyze_trends.py ny_long_term.json

# 3. 作物成長シミュレーション
agrr crop --query "rice Koshihikari" > rice.json
agrr progress --crop-file rice.json \
  --start-date 2023-05-01 \
  --weather-file ny_long_term.json
```

### 最近のデータ（過去2-3年）

```bash
# Open-Meteoの方が高速で使いやすい
agrr weather --location 40.7128,-74.0060 --days 365
```

## まとめ

### ✅ 実装完了

- **NOAA FTP Gateway**: 完全実装・テスト済み
- **データ期間**: 1901年〜現在（2000年以降推奨）
- **対応都市**: アメリカ主要15都市
- **品質**: NOAA公式データ

### 🎯 ユースケース

| ユースケース | データソース | 理由 |
|--------------|--------------|------|
| 長期気候分析（2000年以降） | **noaa-ftp** | 長期データ、無料 |
| 最近のデータ（2-3年） | openmeteo | 高速、使いやすい |
| 日本国内 | jma | 高品質、47都道府県 |
| 予測（16日先） | openmeteo (forecast) | 予測データ提供 |

### 📚 参考資料

- [NOAA ISD Documentation](https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database)
- [FTP Access](ftp://ftp.ncei.noaa.gov/pub/data/noaa/)
- `tests/test_e2e/test_noaa_ftp_long_term.py` - E2Eテスト例

