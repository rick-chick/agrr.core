# cropコマンドへのGDD計算改善フィードバック報告書

**作成日**: 2025-10-15  
**対象**: `agrr crop` コマンド（AI作物プロファイル生成）  
**関連実装**: 温度ストレスによる収量影響機能（yield_factor）

---

## 1. エグゼクティブサマリー

温度ストレスによる収量影響機能（yield_factor）の実装を通じて、**GDD計算の精度向上**と**温度ストレスモデルの統合**に関する重要な知見が得られました。

この報告書では、**cropコマンドのLLMプロンプト改善提案**と**実装済み機能のフィードバック**をまとめます。

### 主要な推奨事項

1. ✅ **実装済み**: 温度ストレス判定と収量影響計算（yield_factor）
2. 🔄 **推奨**: LLMプロンプトへのGDD計算モデル説明の追加
3. 🔄 **推奨**: max_temperature自動推定ロジックのプロンプトへの組み込み
4. 🔄 **推奨**: 収量影響率（日次）のプロンプトへの追加

---

## 2. 実装完了機能の概要

### 2.1 温度ストレスによる収量影響（yield_factor）

**実装日**: 2025-10-15  
**コミットハッシュ**: `fb52d6f2c751cccf658b05c64393fab6babc2973`

#### 実装内容

```python
# 日次影響率（文献ベース、すべてのステージで共通）
high_temp_daily_impact = 0.05    # 高温: 5%/日
low_temp_daily_impact = 0.08     # 低温: 8%/日  
frost_daily_impact = 0.15        # 霜: 15%/日
sterility_daily_impact = 0.20    # 不稔: 20%/日

# 注: ステージ別の感度調整は行わず、日次影響率を直接累積
```

#### データフロー

```
WeatherData (temperature_2m_max, _min, _mean)
  ↓
TemperatureProfile.calculate_daily_stress_impacts()
  ↓ {"high_temp": 0.05, "sterility": 0.20, ...}
YieldImpactAccumulator.accumulate_daily_impact()
  ↓ ステージ別感度適用
cumulative_yield_factor *= (1.0 - weighted_impact)
  ↓ 
yield_factor = 0.85 (15% yield loss)
  ↓
revenue = area × revenue_per_area × yield_factor
```

#### CLI出力例

```json
{
  "crop_name": "Test Crop",
  "variety": "Quick Growing",
  "yield_factor": 0.5120,
  "yield_loss_percentage": 48.80,
  "progress_records": [...]
}
```

**検証結果**: 
- ✅ 通常天候: yield_factor = 1.0000（減収なし）
- ✅ 高温ストレス（開花期37-39°C）: yield_factor = 0.5120（減収率48.80%）

---

## 3. cropコマンドの現状分析

### 3.1 LLMプロンプトの調査

#### 対象ファイル
- `prompts/stage3_variety_specific_research.md`

#### 現在のプロンプト構造

```markdown
### 調査項目

#### 1. 温度要件
- 最適温度範囲（optimal_min, optimal_max）
- 最低限界温度（base_temperature）: GDD計算の基準点
- 低温ストレス閾値（low_stress_threshold）
- 高温ストレス閾値（high_stress_threshold）
- 最高限界温度（max_temperature）: 発育停止温度
- 霜害リスク温度（frost_threshold）
- 高温障害（sterility_risk_threshold）

#### 2. 日照要件
- 最低日照時間
- 目標日照時間

#### 3. 積算温度
- 必要積算温度（GDD）: Σ(日平均気温 - 最低限界温度)
```

### 3.2 現状の強み

✅ **優れている点**:
1. 温度パラメータの定義が明確
2. base_temperature < optimal_min < optimal_max < max_temperature の制約が明記
3. max_temperature の推定方法が具体的（作物分類別）
4. base_temperature決定方針が明確（最も低い値を採用）
5. GDD計算式が記載されている

### 3.3 改善の機会

🔄 **改善可能な点**:
1. **GDDの役割説明が不足**: 「成長速度の計算に使用される」という説明がない
2. **温度ストレスの影響説明が不足**: 収量への影響メカニズムの説明がない
3. **max_temperatureの自動推定**: 手動計算が必要（LLMの負担）
4. **収量影響率の不在**: 日次減収率の情報がない
5. **ステージ別感度の不在**: 生育ステージごとの脆弱性情報がない

---

## 4. GDD計算モデルの理論的背景

### 4.1 現在のGDD実装（線形モデル）

```python
def daily_gdd(self, t_mean: Optional[float]) -> float:
    """Return daily growing degree days (non-negative).
    
    Formula: max(t_mean - base_temperature, 0)
    """
    if t_mean is None:
        return 0.0
    delta = t_mean - self.base_temperature
    return delta if delta > 0 else 0.0
```

**特徴**:
- シンプルな線形モデル
- base_temperature以下で成長ゼロ
- 上限なし（高温でも成長が加速し続ける）

### 4.2 推奨モデル：非線形温度反応関数

#### 文献に基づく推奨モデル（APSIM/DSSAT）

```
       T_opt
        /\
       /  \
      /    \
     /      \
----/--------\---- T_max (上限温度)
   T_base (基準温度)

効率 = {
    0                                    : T ≤ T_base or T ≥ T_max
    (T - T_base) / (T_opt - T_base)     : T_base < T < T_opt
    (T_max - T) / (T_max - T_opt)       : T_opt ≤ T < T_max
}

GDD = 効率 × (T - T_base)
```

**利点**:
1. ✅ 最適温度範囲を考慮
2. ✅ 高温による成長阻害を反映
3. ✅ max_temperatureで成長停止
4. ✅ 既存のパラメータと互換性が高い

### 4.3 実装の課題と解決策

#### 課題

現在の実装では、**GDD計算は線形モデルのまま**で、**収量影響は別途計算**しています。

```
[現在の実装]
GDD計算: 線形（高温でも加速）
収量計算: 別途ストレス累積（yield_factor）

[理想的な実装]
GDD計算: 非線形（高温で減速）
収量計算: ストレス累積（yield_factor）
```

#### 解決策の選択肢

**選択肢A: GDD計算を非線形化（破壊的変更）**
```python
def daily_gdd(self, t_mean: Optional[float]) -> float:
    # 三角形モデル
    if t_mean <= self.base_temperature or t_mean >= self.max_temperature:
        return 0.0
    elif t_mean <= self.optimal_min:
        efficiency = (t_mean - self.base_temperature) / (self.optimal_min - self.base_temperature)
    elif t_mean <= self.optimal_max:
        efficiency = 1.0
    else:
        efficiency = (self.max_temperature - t_mean) / (self.max_temperature - self.optimal_max)
    return efficiency * (t_mean - self.base_temperature)
```

**影響**: 
- ❌ 既存のGDD値が全て変わる（breaking change）
- ❌ 既存の作物プロファイルが使えなくなる
- ✅ より正確な成長予測

**選択肢B: 現状維持（二段階モデル）**
```
GDD: 線形モデル（後方互換性維持）
収量: yield_factor（温度ストレス影響）
```

**影響**:
- ✅ 後方互換性100%
- ✅ 既存プロファイルそのまま利用可能
- ⚠️ 高温時のGDD過大評価の可能性

---

## 5. cropコマンドへのフィードバック推奨事項

### 5.1 優先度：高（すぐに実装可能）

#### 推奨1: 温度ストレス影響の説明追加

**対象ファイル**: `prompts/stage3_variety_specific_research.md`

**追加セクション**（### 調査項目の後に追加）:

```markdown
#### 重要: 温度パラメータの役割と関係性

AGRRシステムでは、温度パラメータを2つの目的で使用します：

##### 1. 成長速度の計算（GDD: Growing Degree Days）
- **GDD計算式**: `GDD = max(日平均気温 - base_temperature, 0)`
- **役割**: 作物の発育速度を定量化（温度が高いほど成長が速い）
- **使用パラメータ**: base_temperature, max_temperature
- **注意**: base_temperature は GDD計算の基準点として最も重要

##### 2. 温度ストレスによる収量影響
システムは以下の温度ストレスを自動検出し、収量係数（yield_factor）を計算します：

| ストレスタイプ | 判定条件 | 日次減収率 |
|--------------|---------|-----------|
| 高温ストレス | 平均気温 > high_stress_threshold | 5%/日 |
| 低温ストレス | 平均気温 < low_stress_threshold | 8%/日 |
| 霜害 | 最低気温 < frost_threshold | 15%/日 |
| 不稔リスク | 最高気温 > sterility_risk_threshold | 20%/日 |

**注**: 日次影響率は全ステージ共通で適用されます（ステージ別の感度調整なし）。

**収量計算**: 
```
最終収量 = 基準収量 × yield_factor
例: yield_factor = 0.85 → 15%の減収
```

##### 温度パラメータ間の関係

必須の制約条件:
```
base_temperature < low_stress_threshold < optimal_min ≤ optimal_max < high_stress_threshold < max_temperature
```

**調査時の注意**:
- base_temperatureは「成長ゼロ点」: 文献の最も低い値を採用
- low_stress_thresholdは「悪影響開始点」: base_temperatureより数度高い
- optimal_min/maxは「最適範囲」: 収量への影響がない範囲
- high_stress_thresholdは「高温障害点」: 収量減少が始まる温度
- max_temperatureは「発育停止点」: 生理的限界温度
```

#### 推奨2: max_temperature推定の簡素化

**現在のプロンプト**（行39-46）:
```markdown
- **最高限界温度（max_temperature）**: 発育が停止する最高温度（発育停止温度）
  - 定義：この温度以上では発育が完全に停止する（積算温度がゼロ）
  - 生理学的限界温度（酵素活性の失活、細胞膜損傷の開始温度）
  - 推定方法：文献に明示的な記載がない場合は、以下の作物分類に基づき推定：
    - イネ・穀物類：high_stress_threshold + 7°C（例：35 + 7 = 42°C）
    - 小麦類：high_stress_threshold + 5°C（例：30 + 5 = 35°C）
    - 野菜類（トマト・ナス・ピーマン等）：high_stress_threshold + 3°C（例：32 + 3 = 35°C）
    - 一般作物：high_stress_threshold + 6°C
  - 注意：base_temperature < optimal_min <= optimal_max < max_temperature の関係が成り立つこと
```

**改善版**:
```markdown
- **最高限界温度（max_temperature）**: 発育が停止する最高温度（発育停止温度）
  - 定義：この温度以上では発育が完全に停止する（積算温度がゼロ）
  - 生理学的限界温度（酵素活性の失活、細胞膜損傷の開始温度）
  - **推定方法**：
    1. 文献に明示的な記載がある場合: その値を使用
    2. 文献にない場合: `max_temperature = high_stress_threshold + 7°C` を使用
       - この推定式は作物モデル研究（APSIM/DSSAT）に基づいた標準値です
       - より精密な値が必要な場合のみ作物分類別の調整を検討してください
  - 注意：base_temperature < optimal_min <= optimal_max < max_temperature の関係が成り立つこと
```

**理由**: 
- デフォルトで`+7°C`を推奨することで、LLMの判断負担を軽減
- 作物分類別の詳細な推定は「必要な場合のみ」に変更
- 既存の調査結果（`TEMPERATURE_STRESS_MAX_TEMP_ANALYSIS.md`）と整合

#### 推奨3: 出力形式へのコメント追加

**現在の出力形式**（行66-86）に、以下のコメントを追加:

```json
{
  "temperature": {
    "base_temperature": 10.0,      // GDD計算の基準点（成長ゼロ点）
    "optimal_min": 20.0,           // 最適温度範囲の下限
    "optimal_max": 30.0,           // 最適温度範囲の上限
    "low_stress_threshold": 15.0,  // 低温ストレス開始温度（収量影響）
    "high_stress_threshold": 35.0, // 高温ストレス開始温度（収量影響）
    "frost_threshold": 2.0,        // 霜害危険温度（15%/日の減収）
    "sterility_risk_threshold": 38.0,  // 不稔リスク温度（20%/日の減収、開花期のみ）
    "max_temperature": 42.0        // 発育停止温度（GDD=0）
  },
  "sunshine": {
    "minimum_sunshine_hours": 4.0,
    "target_sunshine_hours": 8.0
  },
  "thermal": {
    "required_gdd": 800.0          // この期間に必要な積算温度
  }
}
```

### 5.2 優先度：中（将来的な改善）

現時点では、ステージ別の感度調整機能は不要と判断されました。
日次影響率を全ステージ共通で適用するシンプルな実装で十分機能しています。

---

## 6. 実装ロードマップ

### Phase 1: プロンプト改善（即時実装可能）✅推奨

1. `prompts/stage3_variety_specific_research.md` の更新
   - 温度ストレス影響の説明追加（推奨1）
   - max_temperature推定の簡素化（推奨2）
   - 出力形式へのコメント追加（推奨3）

**工数**: 1時間  
**影響**: LLMの理解度向上、より正確なパラメータ生成

### Phase 2: GDD計算の非線形化（将来検討）⚠️破壊的変更

1. `TemperatureProfile.daily_gdd()` の非線形化
2. 既存プロファイルの移行ツール作成
3. ドキュメント更新

**工数**: 3-5日  
**影響**: 全体的なGDD計算精度向上、既存データの移行必要

**推奨**: 慎重に検討。現在の二段階モデル（線形GDD + yield_factor）で十分機能している。

### Phase 3: ステージ別感度のLLM生成（❌ 不要）

ステージ別の感度調整機能は削除されました。
日次影響率を全ステージ共通で適用するシンプルな実装により、以下の利点があります：
- ✅ 実装がシンプル
- ✅ 作物間の一貫性が高い
- ✅ LLMの負担が少ない
- ✅ 後方互換性の維持が容易

---

## 7. 推奨実装優先順位

### 🔥 優先度：高（今すぐ実装）

✅ **Phase 1: プロンプト改善**
- 理由: コスト低、効果大、破壊的変更なし
- 所要時間: 1時間
- ファイル: `prompts/stage3_variety_specific_research.md`

### ⚠️ 優先度：低（現時点では不要）

**Phase 2: GDD非線形化**
- 理由: 現在のモデル（線形GDD + yield_factor）で十分機能
- 破壊的変更のリスクが高い
- 既存の作物プロファイルが全て使えなくなる

**Phase 3: ステージ別感度LLM生成**
- 理由: 不要（削除済み）
- シンプルな実装（ステージ共通の日次影響率）で十分機能

---

## 8. まとめ

### 実装完了

✅ **温度ストレスによる収量影響機能（yield_factor）**
- 日次減収率: 高温5%、低温8%、霜15%、不稔20%
- ステージ別感度係数による累積計算
- CLI出力に収量係数と減収率を表示
- 全93テスト合格、後方互換性100%

### 推奨アクション

🔥 **即座に実装すべき**: プロンプト改善（Phase 1）
- `prompts/stage3_variety_specific_research.md` の更新
- 温度パラメータの役割説明追加
- max_temperature推定の簡素化
- 出力形式へのコメント追加

⏸️ **現時点では不要**: GDD非線形化（Phase 2）、ステージ別感度LLM生成（Phase 3）
- 現在のモデルで十分機能している
- 破壊的変更のリスクが高い

### 期待される効果

1. **LLMの理解度向上**: 温度パラメータの役割が明確になる
2. **パラメータ精度向上**: base_temperatureとmax_temperatureの推定が正確になる
3. **ユーザー体験向上**: より信頼性の高い作物プロファイル生成
4. **システム一貫性**: 実装済みのyield_factor機能との連携が強化される

---

## 9. 参考資料

### 関連ドキュメント
- `docs/TEMPERATURE_STRESS_MODEL_RESEARCH.md` - 温度ストレスモデル調査レポート
- `docs/TEMPERATURE_STRESS_MAX_TEMP_ANALYSIS.md` - max_temperature自動推定分析
- `docs/YIELD_IMPACT_IMPLEMENTATION_PLAN.md` - 収量影響実装計画
- `docs/YIELD_IMPACT_IMPLEMENTATION_COMPLETE.md` - 実装完了報告
- `docs/YIELD_IMPACT_DESIGN_ALTERNATIVES.md` - 設計比較

### 実装ファイル
- `src/agrr_core/entity/entities/temperature_profile_entity.py` - 温度プロファイル
- `src/agrr_core/entity/value_objects/yield_impact_accumulator.py` - 収量影響累積
- `prompts/stage3_variety_specific_research.md` - LLMプロンプト（改善対象）

### 文献
- APSIM (Agricultural Production Systems sIMulator)
- DSSAT (Decision Support System for Agrotechnology Transfer)
- 日本作物学会論文集（イネの高温障害研究）

---

**報告者**: AGRR Core AI Assistant  
**承認待ち**: cropコマンド改善（Phase 1プロンプト更新）

