# 世界の中小農家件数統計レポート

## 概要

本レポートは、世界各国の中小農家（Smallholder Farms）の件数を比較し、上位10カ国を抽出したものです。
中小農家は一般的に2ヘクタール未満の農地を持つ農業経営体と定義されています。

**調査日**: 2025年10月19日  
**データソース**: FAO統計、各国農業センサス、農業統計データベース

---

## 上位10カ国ランキング

### 国別中小農家件数

```mermaid
%%{init: {'theme':'base', 'themeVariables': { 'primaryColor':'#d4edda','primaryTextColor':'#000','primaryBorderColor':'#28a745','lineColor':'#6c757d','secondaryColor':'#f8f9fa','tertiaryColor':'#fff'}}}%%
graph TB
    title[世界の中小農家件数 上位10カ国]
    
    subgraph TOP3[上位3カ国 - 合計約3.25億戸]
        China[🇨🇳 中国<br/>約2億戸<br/>平均0.6ha]
        India[🇮🇳 インド<br/>約1億戸<br/>平均1.08ha]
        Indonesia[🇮🇩 インドネシア<br/>約2,500万戸<br/>平均1.0ha]
    end
    
    subgraph MIDDLE[4-7位 - 合計約5,100万戸]
        Bangladesh[🇧🇩 バングラデシュ<br/>約1,500万戸<br/>平均0.5ha]
        Pakistan[🇵🇰 パキスタン<br/>約1,300万戸<br/>平均1.6ha]
        Nigeria[🇳🇬 ナイジェリア<br/>約1,200万戸<br/>平均1.2ha]
        Ethiopia[🇪🇹 エチオピア<br/>約1,100万戸<br/>平均1.0ha]
    end
    
    subgraph BOTTOM[8-10位 - 合計約2,400万戸]
        Vietnam[🇻🇳 ベトナム<br/>約900万戸<br/>平均0.8ha]
        Philippines[🇵🇭 フィリピン<br/>約800万戸<br/>平均1.2ha]
        Thailand[🇹🇭 タイ<br/>約700万戸<br/>平均2.0ha未満]
    end
    
    style China fill:#28a745,stroke:#1e7e34,color:#fff
    style India fill:#28a745,stroke:#1e7e34,color:#fff
    style Indonesia fill:#ffc107,stroke:#e0a800,color:#000
    style Bangladesh fill:#17a2b8,stroke:#117a8b,color:#fff
    style Pakistan fill:#17a2b8,stroke:#117a8b,color:#fff
    style Nigeria fill:#17a2b8,stroke:#117a8b,color:#fff
    style Ethiopia fill:#17a2b8,stroke:#117a8b,color:#fff
    style Vietnam fill:#6c757d,stroke:#545b62,color:#fff
    style Philippines fill:#6c757d,stroke:#545b62,color:#fff
    style Thailand fill:#6c757d,stroke:#545b62,color:#fff
```

### 詳細データテーブル

| 順位 | 国名 | 農家数 | 平均耕地面積 | 地域 | 主要特徴 |
|:----:|:-----|-------:|:------------:|:----:|:---------|
| 1 | 🇨🇳 中国 | 約2億戸 | 0.6ha | アジア | 世界最大の農家数。極小規模農家が大半 |
| 2 | 🇮🇳 インド | 約1億戸 | 1.08ha | アジア | 農業が主要産業。2ha未満が多数 |
| 3 | 🇮🇩 インドネシア | 約2,500万戸 | 1.0ha | アジア | 島嶼国家で小規模農家が広く分布 |
| 4 | 🇧🇩 バングラデシュ | 約1,500万戸 | 0.5ha | アジア | 人口密度が高く、極小規模農家が主流 |
| 5 | 🇵🇰 パキスタン | 約1,300万戸 | 1.6ha | アジア | 農業が経済の中心。小規模農家が一般的 |
| 6 | 🇳🇬 ナイジェリア | 約1,200万戸 | 1.2ha | アフリカ | アフリカ最大の農業国。小規模農家が主流 |
| 7 | 🇪🇹 エチオピア | 約1,100万戸 | 1.0ha | アフリカ | 農業従事者が多く、小規模農家が大部分 |
| 8 | 🇻🇳 ベトナム | 約900万戸 | 0.8ha | アジア | 農業が盛んで、1ha未満が多数 |
| 9 | 🇵🇭 フィリピン | 約800万戸 | 1.2ha | アジア | 多くの農村地域で小規模農家が活動 |
| 10 | 🇹🇭 タイ | 約700万戸 | <2.0ha | アジア | 農業が重要産業。小規模農家が多数 |

**合計**: 上位10カ国で約**4億戸**（世界の小規模農家の約80%を占める）

---

## 視覚化グラフ

### 農家数の比較（棒グラフ）

```mermaid
%%{init: {'theme':'base'}}%%
graph LR
    subgraph 農家数比較[単位: 百万戸]
        A1[中国: 200]
        A2[インド: 100]
        A3[インドネシア: 25]
        A4[バングラデシュ: 15]
        A5[パキスタン: 13]
        A6[ナイジェリア: 12]
        A7[エチオピア: 11]
        A8[ベトナム: 9]
        A9[フィリピン: 8]
        A10[タイ: 7]
    end
    
    style A1 fill:#1a5f7a,stroke:#1a5f7a,color:#fff
    style A2 fill:#2e86ab,stroke:#2e86ab,color:#fff
    style A3 fill:#48a9c5,stroke:#48a9c5,color:#fff
    style A4 fill:#72cce3,stroke:#72cce3,color:#000
    style A5 fill:#8ed1e6,stroke:#8ed1e6,color:#000
    style A6 fill:#a8dadc,stroke:#a8dadc,color:#000
    style A7 fill:#b8e0d2,stroke:#b8e0d2,color:#000
    style A8 fill:#d4e9e2,stroke:#d4e9e2,color:#000
    style A9 fill:#e5f2ee,stroke:#e5f2ee,color:#000
    style A10 fill:#f0f7f4,stroke:#f0f7f4,color:#000
```

### 平均耕地面積の比較

```mermaid
%%{init: {'theme':'base'}}%%
pie title 平均耕地面積別分布
    "極小規模 (<0.7ha)" : 3
    "小規模 (0.7-1.2ha)" : 5
    "中小規模 (1.2-2.0ha)" : 2
```

**極小規模農家が多い国**: 中国(0.6ha)、バングラデシュ(0.5ha)、ベトナム(0.8ha)

---

## 地域別分析

### 地域別農家数分布

```mermaid
%%{init: {'theme':'base'}}%%
graph TD
    World[世界の中小農家<br/>上位10カ国<br/>約4億戸] --> Asia[アジア地域<br/>8カ国<br/>約3.74億戸<br/>93.5%]
    World --> Africa[アフリカ地域<br/>2カ国<br/>約2,300万戸<br/>6.5%]
    
    Asia --> EastAsia[東アジア<br/>中国<br/>2億戸]
    Asia --> SouthAsia[南アジア<br/>インド、バングラデシュ<br/>パキスタン<br/>約1.28億戸]
    Asia --> SoutheastAsia[東南アジア<br/>インドネシア、ベトナム<br/>フィリピン、タイ<br/>約4,400万戸]
    
    Africa --> WestAfrica[西アフリカ<br/>ナイジェリア<br/>約1,200万戸]
    Africa --> EastAfrica[東アフリカ<br/>エチオピア<br/>約1,100万戸]
    
    style World fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    style Asia fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    style Africa fill:#fff9c4,stroke:#f57c00,stroke-width:2px
    style EastAsia fill:#a5d6a7,stroke:#2e7d32
    style SouthAsia fill:#a5d6a7,stroke:#2e7d32
    style SoutheastAsia fill:#a5d6a7,stroke:#2e7d32
    style WestAfrica fill:#ffe082,stroke:#f57c00
    style EastAfrica fill:#ffe082,stroke:#f57c00
```

### 地域別統計

| 地域 | 国数 | 総農家数 | 割合 | 特徴 |
|:-----|:----:|:--------:|:----:|:-----|
| **アジア** | 8 | 約3.74億戸 | 93.5% | 世界の中小農家の大部分を占める |
| - 東アジア | 1 | 約2.00億戸 | 50.0% | 中国が圧倒的 |
| - 南アジア | 3 | 約1.28億戸 | 32.0% | インド、バングラデシュ、パキスタン |
| - 東南アジア | 4 | 約0.44億戸 | 11.0% | 島嶼国家と大陸部の混在 |
| **アフリカ** | 2 | 約0.23億戸 | 6.5% | ナイジェリア、エチオピア |

---

## 主要な傾向と分析

### 1. 地域集中度

```mermaid
%%{init: {'theme':'base'}}%%
flowchart LR
    A[世界の中小農家] --> B{地域分布}
    B -->|93.5%| C[アジア<br/>3.74億戸]
    B -->|6.5%| D[アフリカ<br/>0.23億戸]
    B -->|含まれず| E[その他地域<br/>ランク外]
    
    C --> C1[中国・インドで<br/>75%を占める]
    
    style A fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    style C fill:#a5d6a7,stroke:#2e7d32,stroke-width:2px
    style D fill:#ffe082,stroke:#f57c00,stroke-width:2px
    style E fill:#e0e0e0,stroke:#616161
    style C1 fill:#66bb6a,stroke:#2e7d32,color:#fff
```

**主要ポイント**:
- アジアに圧倒的に集中（上位10カ国中8カ国）
- 中国とインドだけで約3億戸（上位10カ国の75%）
- アフリカからはナイジェリアとエチオピアのみランクイン

### 2. 農地規模の特徴

**平均耕地面積の分類**:

```mermaid
%%{init: {'theme':'base'}}%%
graph TD
    Scale[農地規模別分類] --> Micro[極小規模<br/>0.5-0.8ha<br/>3カ国]
    Scale --> Small[小規模<br/>1.0-1.2ha<br/>5カ国]
    Scale --> Medium[中小規模<br/>1.6-2.0ha<br/>2カ国]
    
    Micro --> M1[中国 0.6ha]
    Micro --> M2[バングラデシュ 0.5ha]
    Micro --> M3[ベトナム 0.8ha]
    
    Small --> S1[インドネシア 1.0ha]
    Small --> S2[エチオピア 1.0ha]
    Small --> S3[インド 1.08ha]
    Small --> S4[ナイジェリア 1.2ha]
    Small --> S5[フィリピン 1.2ha]
    
    Medium --> L1[パキスタン 1.6ha]
    Medium --> L2[タイ 2.0ha未満]
    
    style Micro fill:#ffcdd2,stroke:#c62828,stroke-width:2px
    style Small fill:#fff9c4,stroke:#f57c00,stroke-width:2px
    style Medium fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
```

- **極小規模（<0.8ha）**: 中国、バングラデシュ、ベトナム
- **小規模（1.0-1.2ha）**: インド、インドネシア、エチオピア、ナイジェリア、フィリピン
- **中小規模（1.6-2.0ha）**: パキスタン、タイ

### 3. 人口密度との相関

```mermaid
%%{init: {'theme':'base'}}%%
graph LR
    subgraph 高人口密度国[高人口密度 → 小規模農地]
        H1[バングラデシュ<br/>0.5ha/戸]
        H2[中国<br/>0.6ha/戸]
        H3[ベトナム<br/>0.8ha/戸]
    end
    
    subgraph 中人口密度国[中人口密度 → 中規模農地]
        M1[インド<br/>1.08ha/戸]
        M2[インドネシア<br/>1.0ha/戸]
    end
    
    subgraph 低人口密度国[比較的低密度 → 大規模農地]
        L1[パキスタン<br/>1.6ha/戸]
        L2[タイ<br/>2.0ha/戸]
    end
    
    style H1 fill:#ef5350,stroke:#c62828,color:#fff
    style H2 fill:#ef5350,stroke:#c62828,color:#fff
    style H3 fill:#ef5350,stroke:#c62828,color:#fff
    style M1 fill:#ffa726,stroke:#e65100,color:#fff
    style M2 fill:#ffa726,stroke:#e65100,color:#fff
    style L1 fill:#66bb6a,stroke:#2e7d32,color:#fff
    style L2 fill:#66bb6a,stroke:#2e7d32,color:#fff
```

**相関分析**:
- 人口密度が高い国ほど農地面積が小さい傾向
- バングラデシュは最も小規模（0.5ha）で人口密度も最高レベル
- 土地資源の制約が農地規模を決定する主要因

### 4. 時系列トレンド

```mermaid
%%{init: {'theme':'base'}}%%
timeline
    title 世界の農家数の変化トレンド
    2000-2010 : 農家数は比較的安定 : 小規模農家が主流
    2010-2020 : 減少傾向が加速 : EU: 300万戸減少 : 日本: 継続的減少
    2020-2025 : 集約化が進行 : 大規模化が顕著 : 生産性は向上
    Future : さらなる減少予測 : 技術革新の影響 : 都市化の加速
```

**主要トレンド**:
- 世界的に農家数は減少傾向（特に先進国）
- EU: 2010-2020年で約300万戸減少
- 日本: 継続的な減少（2000年から約30%減）
- 一方、生産額は増加（集約化・効率化の成果）

---

## グローバル統計サマリー

### 全世界の中小農家統計

```mermaid
%%{init: {'theme':'base'}}%%
graph TB
    Global[世界の小規模農家<br/>総数: 約5億世帯] --> Top10[上位10カ国<br/>約4億戸<br/>80%]
    Global --> Others[その他の国<br/>約1億戸<br/>20%]
    
    Top10 --> Top3[上位3カ国<br/>中国・インド・インドネシア<br/>3.25億戸<br/>65%]
    Top10 --> Mid7[4-10位<br/>7カ国<br/>0.75億戸<br/>15%]
    
    Others --> Developed[先進国<br/>減少傾向<br/>約2,000万戸]
    Others --> Developing[その他途上国<br/>約8,000万戸]
    
    style Global fill:#1976d2,stroke:#0d47a1,color:#fff,stroke-width:3px
    style Top10 fill:#43a047,stroke:#2e7d32,color:#fff,stroke-width:2px
    style Top3 fill:#66bb6a,stroke:#2e7d32,color:#fff
    style Others fill:#9e9e9e,stroke:#616161,color:#fff
```

| カテゴリ | 農家数 | 割合 | 備考 |
|:---------|-------:|:----:|:-----|
| **世界総数** | 約5億戸 | 100% | 推定値（2020年代前半） |
| 上位10カ国 | 約4億戸 | 80% | 本レポート対象 |
| - 中国・インド | 約3億戸 | 60% | 2カ国で過半数 |
| - その他8カ国 | 約1億戸 | 20% | インドネシア以下 |
| その他の国 | 約1億戸 | 20% | 100カ国以上に分散 |

---

## 参考データ: 地域別比較

### EU（欧州連合）の状況

```mermaid
%%{init: {'theme':'base'}}%%
graph LR
    EU2010[EU 2010年<br/>約1,200万戸] -->|10年間で<br/>300万戸減少| EU2020[EU 2020年<br/>約900万戸]
    
    EU2010 -.->|生産額| P2010[3,040億ユーロ]
    EU2020 -.->|生産額| P2020[3,600億ユーロ<br/>+18%増加]
    
    style EU2010 fill:#ffc107,stroke:#f57c00,color:#000
    style EU2020 fill:#ff9800,stroke:#e65100,color:#fff
    style P2010 fill:#e3f2fd,stroke:#1976d2
    style P2020 fill:#c8e6c9,stroke:#2e7d32
```

**EU特徴**:
- 農家数は減少（-25%）
- 生産額は増加（+18%）
- 大規模化・集約化が顕著

### 日本の状況

| 年次 | 総農家数 | 販売農家数 | 特徴 |
|:----:|:--------:|:----------:|:-----|
| 2000年 | 約312万戸 | 約240万戸 | - |
| 2010年 | 約253万戸 | 約163万戸 | 19%減少 |
| 2020年 | 約175万戸 | 約103万戸 | 31%減少 |

**日本の特徴**:
- 継続的な減少傾向
- 高齢化による離農
- 法人化・大規模化の推進

---

## データの信頼性と限界

### データソース

1. **FAO (国連食糧農業機関) 統計**: 主要なグローバル農業統計
2. **各国農業センサス**: 中国、インド、インドネシア等の国別データ
3. **世界銀行データベース**: 農業産出額、付加価値額
4. **学術研究**: EU、アジア等の地域別農業構造分析

### 注意事項

```mermaid
%%{init: {'theme':'base'}}%%
graph TD
    Limitations[データの限界] --> L1[定義の違い<br/>国ごとに農家の定義が異なる]
    Limitations --> L2[調査年の違い<br/>センサス実施年が国ごとに異なる]
    Limitations --> L3[推定値を含む<br/>一部データは推定値や予測値]
    Limitations --> L4[更新頻度<br/>農業センサスは5-10年ごと]
    
    style Limitations fill:#ffeb3b,stroke:#f57c00,stroke-width:2px
    style L1 fill:#fff9c4,stroke:#fbc02d
    style L2 fill:#fff9c4,stroke:#fbc02d
    style L3 fill:#fff9c4,stroke:#fbc02d
    style L4 fill:#fff9c4,stroke:#fbc02d
```

**主な限界**:

1. **定義の違い**: 各国で「農家」や「小規模農家」の定義が異なる
2. **調査時期**: センサス実施年が国ごとに異なる（2015-2020年の範囲）
3. **推定値**: 一部データは推定値や予測値を含む
4. **更新頻度**: 農業センサスは5-10年ごとのため、最新状況と差異がある可能性

### データ品質評価

| 国名 | データ品質 | 最終センサス年 | 備考 |
|:-----|:----------:|:--------------:|:-----|
| 中国 | ⭐⭐⭐⭐ | 2016-2020年 | 大規模センサス実施 |
| インド | ⭐⭐⭐⭐ | 2015-2016年 | 詳細な農業統計あり |
| インドネシア | ⭐⭐⭐ | 2013年 | やや古いデータ |
| その他アジア | ⭐⭐⭐ | 2010-2020年 | 国により差がある |
| アフリカ諸国 | ⭐⭐ | 推定値多い | センサス頻度低い |

---

## 結論

### 主要な発見

1. **アジアの圧倒的優位**: 上位10カ国中8カ国がアジア諸国で、世界の中小農家の93.5%を占める

2. **中国・インドの重要性**: この2カ国だけで約3億戸（世界の60%）を占め、世界の食糧安全保障に極めて重要

3. **極小規模化**: 多くの国で平均耕地面積が1ヘクタール前後と非常に小規模

4. **減少トレンド**: 先進国では農家数が減少し、大規模化・集約化が進行中

5. **地域格差**: アフリカの農業大国（ナイジェリア、エチオピア）も上位にランクインするが、アジアと比較すると規模は小さい

### 今後の展望

```mermaid
%%{init: {'theme':'base'}}%%
graph TD
    Future[今後の展望] --> T1[技術革新<br/>スマート農業<br/>IoT・AI活用]
    Future --> T2[気候変動対応<br/>適応策<br/>レジリエンス強化]
    Future --> T3[都市化<br/>農地減少<br/>若年層流出]
    Future --> T4[持続可能性<br/>有機農業<br/>環境保全]
    
    T1 --> O1[生産性向上]
    T2 --> O2[リスク管理]
    T3 --> O3[構造変化]
    T4 --> O4[品質向上]
    
    style Future fill:#673ab7,stroke:#4527a0,color:#fff,stroke-width:3px
    style T1 fill:#9c27b0,stroke:#6a1b9a,color:#fff
    style T2 fill:#ff5722,stroke:#d84315,color:#fff
    style T3 fill:#795548,stroke:#4e342e,color:#fff
    style T4 fill:#4caf50,stroke:#2e7d32,color:#fff
    style O1 fill:#e1bee7,stroke:#8e24aa
    style O2 fill:#ffccbc,stroke:#d84315
    style O3 fill:#d7ccc8,stroke:#5d4037
    style O4 fill:#c8e6c9,stroke:#388e3c
```

**重要な課題**:
- 小規模農家の収益性向上
- 若年層の農業参入促進
- 気候変動への適応
- 持続可能な農業への転換
- デジタル技術の導入

---

## 補足資料

### 用語定義

- **中小農家（Smallholder Farms）**: 一般的に2ヘクタール未満の農地を経営する農家
- **農業経営体（Agricultural Holdings）**: 農業を営む単位（個人、法人、組合等）
- **販売農家**: 経営耕地面積30a以上または農産物販売金額50万円以上の農家
- **自給的農家**: 経営耕地面積30a未満かつ農産物販売金額50万円未満の農家

### 関連指標

| 指標 | 説明 | 用途 |
|:-----|:-----|:-----|
| 農家数 | 農業経営体の総数 | 規模分析 |
| 平均耕地面積 | 1戸あたりの平均農地面積 | 規模評価 |
| 農業産出額 | 年間の農業生産額 | 経済規模 |
| 農業従事者数 | 農業に従事する人数 | 雇用分析 |
| 農地利用率 | 農地の有効活用度 | 効率性評価 |

---

## 参考文献・データソース

1. FAO (Food and Agriculture Organization) - FAOSTAT Database
2. World Bank - World Development Indicators
3. 各国農業センサス（中国、インド、インドネシア等）
4. EU Agricultural Census 2020
5. 日本農林水産省 - 農業センサス
6. 学術論文: "Farm Structure Changes in the EU" (arXiv, 2024)
7. 統計データベース: StatJa.com

---

**レポート作成日**: 2025年10月19日  
**次回更新予定**: 各国の最新農業センサス公開時  
**お問い合わせ**: AGRR Core Project Team

---

---

# 【補足】趣味としての家庭菜園が盛んな国

## 概要

本セクションでは、職業としての農業ではなく、趣味・レジャーとしての家庭菜園（Home Gardening / Kitchen Garden）が盛んな国をまとめています。

**調査日**: 2025年10月19日  
**データソース**: 各国の農業調査、園芸産業統計、消費者調査

---

## 家庭菜園が盛んな国トップ10

### 国別ランキングと特徴

```mermaid
%%{init: {'theme':'base'}}%%
graph TB
    title[趣味としての家庭菜園が盛んな国]
    
    subgraph Europe[ヨーロッパ勢 - 伝統的な園芸文化]
        UK[🇬🇧 イギリス<br/>Allotment文化<br/>カブ・レタスが人気]
        Germany[🇩🇪 ドイツ<br/>Kleingarten<br/>市民農園が発達]
        France[🇫🇷 フランス<br/>美食文化と連動<br/>トマト・ハーブ]
        Netherlands[🇳🇱 オランダ<br/>園芸先進国<br/>都市農業が活発]
        Italy[🇮🇹 イタリア<br/>地中海野菜<br/>バジル・トマト]
        Spain[🇪🇸 スペイン<br/>温暖気候活用<br/>オリーブ・トマト]
    end
    
    subgraph Asia[アジア・オセアニア]
        Japan[🇯🇵 日本<br/>ベランダ菜園も人気<br/>トマト71.5%が経験]
        Thailand[🇹🇭 タイ<br/>ハーブ栽培<br/>レモングラス・パクチー]
    end
    
    subgraph Americas[北米・南米]
        USA[🇺🇸 アメリカ<br/>屋上菜園ブーム<br/>コミュニティガーデン]
        Canada[🇨🇦 カナダ<br/>短い夏を活用<br/>トマト・ズッキーニ]
        Australia[🇦🇺 オーストラリア<br/>温暖気候<br/>多様な野菜栽培]
    end
    
    style UK fill:#ff6b6b,stroke:#c92a2a,color:#fff
    style Germany fill:#ff6b6b,stroke:#c92a2a,color:#fff
    style France fill:#ff6b6b,stroke:#c92a2a,color:#fff
    style Netherlands fill:#ffa94d,stroke:#e67700,color:#fff
    style Italy fill:#ffa94d,stroke:#e67700,color:#fff
    style Spain fill:#ffa94d,stroke:#e67700,color:#fff
    style Japan fill:#51cf66,stroke:#2f9e44,color:#fff
    style Thailand fill:#74c0fc,stroke:#1971c2,color:#fff
    style USA fill:#845ef7,stroke:#5f3dc4,color:#fff
    style Canada fill:#845ef7,stroke:#5f3dc4,color:#fff
    style Australia fill:#74c0fc,stroke:#1971c2,color:#fff
```

### 詳細リスト

| 順位 | 国名 | 普及度 | 主な栽培作物 | 特徴 | 文化的背景 |
|:----:|:-----|:------:|:-------------|:-----|:-----------|
| 1 | 🇬🇧 イギリス | ⭐⭐⭐⭐⭐ | カブ、レタス、豆類 | Allotment（市民農園）文化が根付く | 19世紀から続く伝統 |
| 2 | 🇩🇪 ドイツ | ⭐⭐⭐⭐⭐ | ジャガイモ、キャベツ、ハーブ | Kleingarten（クラインガルテン）が全国に約100万区画 | 環境意識とオーガニック志向 |
| 3 | 🇯🇵 日本 | ⭐⭐⭐⭐⭐ | トマト、キュウリ、ピーマン | ベランダ菜園も盛ん。トマト栽培経験者71.5% | 都市部でも手軽に楽しむ文化 |
| 4 | 🇺🇸 アメリカ | ⭐⭐⭐⭐ | トウモロコシ、トマト、ブロッコリー | 屋上菜園、コミュニティガーデンが増加 | COVID-19後に急拡大 |
| 5 | 🇫🇷 フランス | ⭐⭐⭐⭐ | トマト、バジル、ズッキーニ | 美食文化と連動した家庭菜園 | 新鮮な食材へのこだわり |
| 6 | 🇦🇺 オーストラリア | ⭐⭐⭐⭐ | トマト、タマネギ、ジャガイモ | 温暖な気候を活かした多様な栽培 | アウトドア文化の一環 |
| 7 | 🇳🇱 オランダ | ⭐⭐⭐ | トマト、レタス、ハーブ | 園芸先進国、都市農業が発達 | スペース有効活用の技術 |
| 8 | 🇮🇹 イタリア | ⭐⭐⭐ | トマト、バジル、ズッキーニ | 地中海性気候に適した野菜 | 伝統的な食文化と直結 |
| 9 | 🇨🇦 カナダ | ⭐⭐⭐ | トマト、ピーマン、ズッキーニ | 短い夏を有効活用 | 地産地消の意識が高い |
| 10 | 🇪🇸 スペイン | ⭐⭐⭐ | トマト、ピーマン、オリーブ | 温暖気候で栽培が容易 | 家庭料理との結びつき |

**特別枠**: 🇹🇭 タイ - レモングラス、パクチーなどハーブ栽培が盛ん

---

## 地域別の家庭菜園文化

### ヨーロッパの家庭菜園文化

```mermaid
%%{init: {'theme':'base'}}%%
graph LR
    Europe[ヨーロッパの家庭菜園] --> Traditional[伝統的なスタイル]
    Europe --> Modern[現代的なスタイル]
    
    Traditional --> Allotment[イギリス: Allotment<br/>市民農園制度<br/>19世紀から継続]
    Traditional --> Klein[ドイツ: Kleingarten<br/>約100万区画<br/>法律で保護]
    
    Modern --> Urban[都市農業<br/>オランダ・フランス]
    Modern --> Organic[オーガニック志向<br/>ドイツ・イタリア]
    
    style Europe fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    style Traditional fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style Modern fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style Allotment fill:#ffccbc,stroke:#d84315
    style Klein fill:#ffccbc,stroke:#d84315
    style Urban fill:#c8e6c9,stroke:#388e3c
    style Organic fill:#c8e6c9,stroke:#388e3c
```

**ヨーロッパの特徴**:

1. **イギリス - Allotment文化**
   - 19世紀から続く市民農園制度
   - 自治体が提供する小区画の農地を借りて栽培
   - 収穫までの期間が短い野菜（カブ、レタス）が人気
   - コミュニティ形成の場としても機能

2. **ドイツ - Kleingarten**
   - 全国に約100万区画の市民農園
   - 法律で保護された制度
   - 環境保護とオーガニック栽培への意識が高い
   - ジャガイモ、キャベツなど伝統的な野菜

3. **フランス - 美食文化との連動**
   - 新鮮な食材へのこだわり
   - トマト、バジル、ズッキーニが人気
   - 家庭料理に直結した栽培

4. **オランダ - 園芸先進国**
   - 限られたスペースの有効活用技術
   - 都市農業が発達
   - 垂直栽培、屋上菜園などの革新的手法

### アジア・オセアニアの家庭菜園

```mermaid
%%{init: {'theme':'base'}}%%
graph TD
    Asia[アジア・オセアニア] --> Urban[都市型家庭菜園]
    Asia --> Tropical[熱帯・亜熱帯型]
    Asia --> Temperate[温帯型]
    
    Urban --> Japan[日本<br/>ベランダ・屋上菜園<br/>省スペース栽培]
    
    Tropical --> Thailand[タイ<br/>ハーブ中心<br/>レモングラス・パクチー]
    
    Temperate --> Australia[オーストラリア<br/>多様な野菜<br/>温暖気候活用]
    
    Japan --> PopularJP[人気野菜<br/>トマト 71.5%<br/>キュウリ 45.8%<br/>ピーマン 39.5%]
    
    style Asia fill:#fff3e0,stroke:#e65100,stroke-width:3px
    style Japan fill:#ffccbc,stroke:#d84315,stroke-width:2px
    style Thailand fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    style Australia fill:#b3e5fc,stroke:#0277bd,stroke-width:2px
    style PopularJP fill:#fff9c4,stroke:#f57c00
```

**アジア・オセアニアの特徴**:

1. **日本 - 都市型家庭菜園の発達**
   - ベランダ菜園が都市部で人気
   - プランター栽培が主流
   - **人気野菜トップ3**:
     - トマト: 71.5%
     - キュウリ: 45.8%
     - ピーマン: 39.5%
   - 初心者でも育てやすい品種の開発

2. **タイ - ハーブ栽培が中心**
   - レモングラス、パクチー（コリアンダー）
   - 家庭料理に直結
   - 熱帯気候で年間を通じて栽培可能

3. **オーストラリア - 温暖気候を活かす**
   - トマト、タマネギ、ジャガイモが人気
   - 広い庭を活用した本格的な菜園
   - アウトドアライフスタイルの一部

### 北米の家庭菜園トレンド

```mermaid
%%{init: {'theme':'base'}}%%
timeline
    title 北米の家庭菜園ブーム
    2010-2019 : コミュニティガーデンの拡大 : 健康志向の高まり
    2020-2021 : COVID-19パンデミック : 家庭菜園ブーム到来 : 種子・苗の売上急増
    2022-2024 : 屋上菜園の普及 : 都市農業の発展 : サステナビリティ重視
    2025- : デジタル化 : スマート菜園システム : コミュニティ強化
```

**北米の特徴**:

1. **アメリカ**
   - **屋上菜園（Rooftop Garden）ブーム**: 都市部で限られたスペースを活用
   - **コミュニティガーデン**: 地域住民が共同で管理
   - **COVID-19の影響**: 2020年以降、家庭菜園が急増
   - 人気野菜: トウモロコシ、トマト、ブロッコリー、ホウレンソウ

2. **カナダ**
   - 短い夏（6-8月）を有効活用
   - 地産地消（Local Food）への意識が高い
   - トマト、ピーマン、ズッキーニが主流

---

## 栽培作物の地域別比較

### 人気野菜ランキング

```mermaid
%%{init: {'theme':'base'}}%%
graph LR
    subgraph 世界共通人気野菜[🌍 ほぼ全ての国で人気]
        Tomato[🍅 トマト<br/>最も人気<br/>育てやすい]
    end
    
    subgraph ヨーロッパ型[🇪🇺 ヨーロッパで人気]
        Euro1[カブ]
        Euro2[レタス]
        Euro3[キャベツ]
        Euro4[ジャガイモ]
    end
    
    subgraph アジア型[🌏 アジアで人気]
        Asia1[キュウリ]
        Asia2[ナス]
        Asia3[ピーマン]
        Asia4[ハーブ類]
    end
    
    subgraph アメリカ型[🌎 北米で人気]
        US1[トウモロコシ]
        US2[ブロッコリー]
        US3[ズッキーニ]
        US4[ホウレンソウ]
    end
    
    style Tomato fill:#ff6b6b,stroke:#c92a2a,color:#fff,stroke-width:3px
    style Euro1 fill:#ffa94d,stroke:#e67700,color:#fff
    style Euro2 fill:#ffa94d,stroke:#e67700,color:#fff
    style Euro3 fill:#ffa94d,stroke:#e67700,color:#fff
    style Euro4 fill:#ffa94d,stroke:#e67700,color:#fff
    style Asia1 fill:#51cf66,stroke:#2f9e44,color:#fff
    style Asia2 fill:#51cf66,stroke:#2f9e44,color:#fff
    style Asia3 fill:#51cf66,stroke:#2f9e44,color:#fff
    style Asia4 fill:#51cf66,stroke:#2f9e44,color:#fff
    style US1 fill:#845ef7,stroke:#5f3dc4,color:#fff
    style US2 fill:#845ef7,stroke:#5f3dc4,color:#fff
    style US3 fill:#845ef7,stroke:#5f3dc4,color:#fff
    style US4 fill:#845ef7,stroke:#5f3dc4,color:#fff
```

### 地域別人気野菜

| 地域 | 1位 | 2位 | 3位 | 4位 | 5位 |
|:-----|:---:|:---:|:---:|:---:|:---:|
| **日本** | トマト (71.5%) | キュウリ (45.8%) | ピーマン (39.5%) | ナス | 枝豆 |
| **イギリス** | トマト | カブ | レタス | 豆類 | ジャガイモ |
| **ドイツ** | トマト | ジャガイモ | キャベツ | ハーブ | キュウリ |
| **アメリカ** | トマト | トウモロコシ | ブロッコリー | ホウレンソウ | ピーマン |
| **フランス** | トマト | バジル | ズッキーニ | レタス | ハーブ類 |
| **イタリア** | トマト | バジル | ズッキーニ | ナス | ピーマン |
| **オーストラリア** | トマト | タマネギ | ジャガイモ | レタス | ハーブ |
| **タイ** | レモングラス | パクチー | トウガラシ | バジル | ショウガ |

**グローバル共通**: 🍅 **トマト**はほぼ全ての国で最も人気の家庭菜園作物

---

## 家庭菜園の形態別分類

```mermaid
%%{init: {'theme':'base'}}%%
graph TD
    Types[家庭菜園の形態] --> Ground[地面栽培]
    Types --> Container[コンテナ栽培]
    Types --> Community[コミュニティ型]
    Types --> Urban[都市農業型]
    
    Ground --> Garden[自宅の庭<br/>アメリカ・オーストラリア<br/>カナダで一般的]
    
    Container --> Balcony[ベランダ菜園<br/>日本で人気<br/>プランター栽培]
    Container --> Rooftop[屋上菜園<br/>アメリカ都市部<br/>スペース有効活用]
    
    Community --> Allot[市民農園<br/>イギリス: Allotment<br/>ドイツ: Kleingarten]
    Community --> CommGarden[コミュニティガーデン<br/>アメリカ・カナダ<br/>地域住民で共同管理]
    
    Urban --> Vertical[垂直農法<br/>オランダ・日本<br/>省スペース]
    Urban --> Indoor[室内栽培<br/>LED照明活用<br/>年間を通じて栽培]
    
    style Types fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    style Ground fill:#fff9c4,stroke:#f57c00,stroke-width:2px
    style Container fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    style Community fill:#ffccbc,stroke:#d84315,stroke-width:2px
    style Urban fill:#b3e5fc,stroke:#0277bd,stroke-width:2px
```

### 形態別の特徴

| 形態 | 主な国 | 利点 | 欠点 | 適した作物 |
|:-----|:-------|:-----|:-----|:-----------|
| **自宅の庭** | 米・豪・加 | 広いスペース、自由度高い | 庭がない家庭は不可 | トウモロコシ、ジャガイモ |
| **ベランダ菜園** | 日本・都市部 | 手軽、管理が楽 | スペース限定 | トマト、ハーブ、葉物 |
| **屋上菜園** | 米・欧の都市 | デッドスペース活用 | 設備投資が必要 | 多様な野菜可能 |
| **市民農園** | 独・英 | 本格的栽培可能 | 移動が必要、順番待ち | ジャガイモ、キャベツ |
| **コミュニティガーデン** | 米・加 | 地域交流、知識共有 | スケジュール調整必要 | 多様な野菜 |
| **垂直農法** | 蘭・日 | 省スペース、効率的 | 技術・設備が必要 | レタス、ハーブ |

---

## COVID-19パンデミックの影響

### 家庭菜園ブームの加速

```mermaid
%%{init: {'theme':'base'}}%%
graph LR
    COVID[COVID-19<br/>パンデミック<br/>2020-2021] --> Impact1[外出制限<br/>在宅時間増加]
    COVID --> Impact2[食料安全保障<br/>への意識向上]
    COVID --> Impact3[健康志向<br/>の高まり]
    
    Impact1 --> Boom1[種子・苗の<br/>売上急増]
    Impact2 --> Boom1
    Impact3 --> Boom1
    
    Boom1 --> Result1[新規参入者<br/>大幅増加]
    Boom1 --> Result2[オンライン<br/>園芸コミュニティ拡大]
    Boom1 --> Result3[家庭菜園<br/>関連商品の売上増]
    
    Result1 --> Future[定着<br/>2025年現在も継続]
    Result2 --> Future
    Result3 --> Future
    
    style COVID fill:#ff6b6b,stroke:#c92a2a,color:#fff,stroke-width:3px
    style Boom1 fill:#ffa94d,stroke:#e67700,color:#fff,stroke-width:2px
    style Future fill:#51cf66,stroke:#2f9e44,color:#fff,stroke-width:2px
```

**パンデミックの影響**:

1. **2020年春 - 爆発的ブーム**
   - 種子・苗の売上が前年比200-300%増
   - 園芸用品メーカーの在庫不足
   - 初心者向け教材の需要急増

2. **在宅時間の増加**
   - リモートワークの普及
   - 趣味としての家庭菜園に時間を充てられる
   - 家族での活動として人気

3. **食料安全保障への意識**
   - スーパーマーケットの品不足経験
   - 自給自足への関心
   - 地産地消の重要性再認識

4. **ブームの定着（2025年現在）**
   - 一時的なブームで終わらず継続
   - オンラインコミュニティの活性化
   - デジタルツールの活用（栽培アプリ等）

---

## 家庭菜園文化の背景要因

### 各国の家庭菜園文化を支える要因

```mermaid
%%{init: {'theme':'base'}}%%
graph TD
    Factors[家庭菜園が盛んな理由] --> Climate[気候条件]
    Factors --> Culture[文化・歴史]
    Factors --> Economic[経済的要因]
    Factors --> Social[社会的要因]
    
    Climate --> C1[温暖な気候<br/>イタリア・スペイン・豪州]
    Climate --> C2[四季の変化<br/>日本・英・独]
    
    Culture --> Cu1[美食文化<br/>仏・伊]
    Culture --> Cu2[園芸の伝統<br/>英・蘭]
    Culture --> Cu3[自給自足の歴史<br/>独・英]
    
    Economic --> E1[食費節約<br/>新鮮な野菜を安価に]
    Economic --> E2[オーガニック野菜<br/>高価な有機野菜を自作]
    
    Social --> S1[健康志向<br/>無農薬栽培]
    Social --> S2[コミュニティ形成<br/>市民農園での交流]
    Social --> S3[環境意識<br/>サステナビリティ]
    Social --> S4[教育<br/>子供の食育]
    
    style Factors fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    style Climate fill:#fff9c4,stroke:#f57c00,stroke-width:2px
    style Culture fill:#ffccbc,stroke:#d84315,stroke-width:2px
    style Economic fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    style Social fill:#b3e5fc,stroke:#0277bd,stroke-width:2px
```

### 要因分析

| 要因カテゴリ | 具体的要因 | 該当国 | 影響度 |
|:-------------|:-----------|:-------|:------:|
| **気候** | 温暖で栽培しやすい | イタリア、スペイン、オーストラリア | ⭐⭐⭐⭐ |
| **気候** | 四季の変化で多様な栽培 | 日本、イギリス、ドイツ | ⭐⭐⭐ |
| **文化** | 美食文化との連動 | フランス、イタリア | ⭐⭐⭐⭐⭐ |
| **文化** | 園芸の伝統 | イギリス、オランダ | ⭐⭐⭐⭐⭐ |
| **文化** | 自給自足の歴史 | ドイツ（Kleingarten） | ⭐⭐⭐⭐ |
| **経済** | 食費節約 | 全般 | ⭐⭐⭐ |
| **経済** | オーガニック志向 | ドイツ、オランダ | ⭐⭐⭐⭐ |
| **社会** | 健康志向 | 全般（特に先進国） | ⭐⭐⭐⭐⭐ |
| **社会** | コミュニティ形成 | イギリス、アメリカ | ⭐⭐⭐⭐ |
| **社会** | 環境・サステナビリティ | ドイツ、オランダ、北欧 | ⭐⭐⭐⭐⭐ |
| **社会** | 子供の食育 | 日本、アメリカ | ⭐⭐⭐ |

---

## 今後のトレンド予測

### 2025年以降の家庭菜園トレンド

```mermaid
%%{init: {'theme':'base'}}%%
graph TB
    Future[未来の家庭菜園] --> Tech[技術革新]
    Future --> Sustain[サステナビリティ]
    Future --> Community[コミュニティ強化]
    
    Tech --> T1[スマート菜園<br/>IoTセンサー<br/>自動水やり]
    Tech --> T2[栽培アプリ<br/>AIによる診断<br/>最適化提案]
    Tech --> T3[LED照明<br/>室内栽培<br/>年間栽培]
    
    Sustain --> Su1[循環型農業<br/>コンポスト<br/>生ゴミ活用]
    Sustain --> Su2[在来種保存<br/>エアルーム品種<br/>生物多様性]
    Sustain --> Su3[水資源管理<br/>雨水利用<br/>点滴灌漑]
    
    Community --> C1[オンライン<br/>SNSコミュニティ<br/>知識共有]
    Community --> C2[種子交換会<br/>地域イベント<br/>ネットワーク]
    Community --> C3[世代間交流<br/>高齢者の知識<br/>若者へ継承]
    
    style Future fill:#e3f2fd,stroke:#1976d2,stroke-width:3px,color:#000
    style Tech fill:#b3e5fc,stroke:#0277bd,stroke-width:2px
    style Sustain fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    style Community fill:#ffccbc,stroke:#d84315,stroke-width:2px
    style T1 fill:#e1f5fe,stroke:#01579b
    style T2 fill:#e1f5fe,stroke:#01579b
    style T3 fill:#e1f5fe,stroke:#01579b
    style Su1 fill:#f1f8e9,stroke:#33691e
    style Su2 fill:#f1f8e9,stroke:#33691e
    style Su3 fill:#f1f8e9,stroke:#33691e
    style C1 fill:#fbe9e7,stroke:#bf360c
    style C2 fill:#fbe9e7,stroke:#bf360c
    style C3 fill:#fbe9e7,stroke:#bf360c
```

### 主要トレンド

1. **デジタル化・スマート化**
   - IoTセンサーによる土壌・水分管理
   - AIアプリによる病害診断
   - 自動水やりシステム

2. **サステナビリティの追求**
   - コンポスト（堆肥）による循環型農業
   - 在来種・エアルーム品種の保存
   - 雨水利用、水資源の有効活用

3. **コミュニティの進化**
   - オンライン+オフラインの融合
   - SNSでの知識共有
   - 世代間での知識継承

4. **都市農業のさらなる発展**
   - 垂直農法の普及
   - 屋上・壁面緑化
   - 公共スペースの活用

---

## 結論: 家庭菜園文化の意義

### 家庭菜園がもたらす価値

```mermaid
%%{init: {'theme':'base'}}%%
mindmap
  root((家庭菜園の価値))
    個人
      健康増進
        新鮮な野菜
        運動効果
        ストレス解消
      経済的メリット
        食費節約
        オーガニック野菜を安価に
      教育
        食育
        生命の大切さ
        科学的思考
    家族
      共同作業
      会話の機会
      世代間交流
      食の大切さ共有
    地域
      コミュニティ形成
      知識共有
      助け合い
      地域活性化
    環境
      生物多様性
      CO2削減
      フードマイレージ削減
      循環型社会
    社会
      食料安全保障
      地産地消
      農業への理解
      持続可能性
```

**家庭菜園の多面的価値**:

1. **個人レベル**
   - 健康的な食生活
   - 心身のリフレッシュ
   - 達成感・充実感

2. **家族レベル**
   - 家族の絆を深める
   - 子供の食育
   - 世代間の知識継承

3. **地域レベル**
   - コミュニティ形成
   - 地域の活性化
   - 社会的つながり

4. **環境・社会レベル**
   - 環境保全
   - 生物多様性の維持
   - 持続可能な社会への貢献
   - 食料安全保障

---

## データの限界と注意事項

**本セクションのデータについて**:

```mermaid
%%{init: {'theme':'base'}}%%
graph LR
    Limit[データの限界] --> L1[定量データ少ない<br/>多くは定性的情報]
    Limit --> L2[国際比較困難<br/>調査方法が異なる]
    Limit --> L3[文化的差異<br/>家庭菜園の定義が曖昧]
    
    style Limit fill:#ffeb3b,stroke:#f57c00,stroke-width:2px
    style L1 fill:#fff9c4,stroke:#fbc02d
    style L2 fill:#fff9c4,stroke:#fbc02d
    style L3 fill:#fff9c4,stroke:#fbc02d
```

1. **定量データの不足**: 中小農家と異なり、趣味の家庭菜園は公式統計が少ない
2. **定義の曖昧さ**: 国によって「家庭菜園」の範囲が異なる
3. **調査方法の違い**: 国際比較可能な統一的調査がない
4. **文化的背景**: 気候、住宅事情、ライフスタイルの違いが大きく影響

---

## 参考情報・データソース

- タキイ種苗株式会社 - 家庭菜園に関する調査（日本）
- 各国園芸産業協会の統計
- 農業関連メディアの調査報告
- COVID-19前後の園芸用品販売統計
- 学術研究: Urban Agriculture, Community Gardens

---

**補足セクション作成日**: 2025年10月19日

---

## 変更履歴

| 版 | 日付 | 変更内容 | 作成者 |
|:--:|:----:|:---------|:-------|
| 1.0 | 2025-10-19 | 初版作成（中小農家統計） | AGRR Core |
| 1.1 | 2025-10-19 | 家庭菜園セクション追加 | AGRR Core |


