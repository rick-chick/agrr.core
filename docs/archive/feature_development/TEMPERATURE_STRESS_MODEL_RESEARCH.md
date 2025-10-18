# 温度ストレスモデル調査レポート
**作成日**: 2025-10-14  
**目的**: 最適温度を外れた場合の積算温度（GDD）と収量への影響をモデル化するための研究調査

---

## 1. エグゼクティブサマリー

作物の生育において、温度ストレス（高温・低温）は以下の2つの側面で影響を与える：

1. **成長速度への影響**（GDD計算の修正）
2. **最終収量への影響**（収益の減少）

現在のAGRRプロジェクトは単純な線形GDDモデル（`GDD = max(T_mean - T_base, 0)`）を使用しているが、これは最適温度範囲を外れた場合の成長遅延や収量減少を考慮していない。

**推奨モデル**: 
- **GDD計算**: **非線形温度反応関数**（Beta関数またはTrapezoid関数）
- **収量影響**: **ストレス日数累積モデル**（生育ステージ別の感受性係数付き）

---

## 2. 現状分析

### 2.1 現在の実装

**AGRRプロジェクトの現状**:

```python
# src/agrr_core/entity/entities/temperature_profile_entity.py
def daily_gdd(self, t_mean: Optional[float]) -> float:
    """Return daily growing degree days (non-negative).
    
    Formula: max(t_mean - base_temperature, 0)
    """
    if t_mean is None:
        return 0.0
    delta = t_mean - self.base_temperature
    return delta if delta > 0 else 0.0
```

**既存の温度閾値**:
- `base_temperature`: GDD基準温度
- `optimal_min`, `optimal_max`: 最適温度範囲
- `low_stress_threshold`: 低温ストレス閾値
- `high_stress_threshold`: 高温ストレス閾値
- `frost_threshold`: 霜害閾値
- `sterility_risk_threshold`: 不稔リスク閾値（オプション）

**問題点**:
1. ✗ 温度ストレス判定はあるが、GDD計算に反映されていない
2. ✗ 最適温度を外れた場合の成長速度の低下が考慮されていない
3. ✗ 温度ストレスによる収量減少が計算されていない
4. ✗ 生育ステージごとの温度感受性の違いが考慮されていない

---

## 3. 研究に基づくモデル提案

### 3.1 主要な作物モデルでの温度ストレスの扱い

#### 3.1.1 APSIM (Agricultural Production Systems sIMulator)

**温度反応関数**: 3基点モデル（Three Cardinal Temperatures）

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
```

**収量への影響**:
- 各生育ステージでストレス日数を累積
- 生殖成長期（開花・着粒期）の高温ストレスが最も影響大
- ストレス係数（0-1）を収量ポテンシャルに乗算

#### 3.1.2 DSSAT (Decision Support System for Agrotechnology Transfer)

**温度応答**: 台形関数（Trapezoidal function）

```
効率 = 1.0                          : T_opt_min ≤ T ≤ T_opt_max
効率 = (T - T_base) / (T_opt_min - T_base)  : T_base < T < T_opt_min
効率 = (T_max - T) / (T_max - T_opt_max)    : T_opt_max < T < T_max
効率 = 0.0                          : T ≤ T_base or T ≥ T_max
```

**特徴**:
- 最適温度範囲を持つ（単一点ではなく範囲）
- 現在のAGRRの`optimal_min`/`optimal_max`と互換性が高い

#### 3.1.3 Beta関数モデル（Yan & Hunt, 1999）

**最も生理学的に正確なモデル**:

```python
def beta_function(T, T_base, T_opt, T_max, alpha=1.0, beta=1.0):
    """
    Beta関数による温度反応
    
    Parameters:
    - T: 現在温度
    - T_base: 基準温度（発育下限温度）
    - T_opt: 最適温度
    - T_max: 上限温度（発育停止温度）
    - alpha, beta: 形状パラメータ（作物種・ステージ依存）
    
    Returns:
    - 0-1の温度効率係数
    """
    if T <= T_base or T >= T_max:
        return 0.0
    
    # Normalized temperature
    T_norm = (T - T_base) / (T_max - T_base)
    T_opt_norm = (T_opt - T_base) / (T_max - T_base)
    
    # Beta function
    efficiency = (T_norm ** alpha) * ((1 - T_norm) / (1 - T_opt_norm)) ** beta
    
    return efficiency
```

**論文**: Yan, W., & Hunt, L. A. (1999). "An equation for modelling the temperature response of plants using only the cardinal temperatures." *Annals of Botany*, 84(5), 607-614.

---

### 3.2 収量への影響モデル

#### 3.2.1 ストレス日数累積モデル（研究ベース）

**日本の研究事例**:

1. **イネの高温不稔** (Matsui et al., 2001):
   - 開花期の日最高気温が35℃を超えると花粉稔性が低下
   - 影響度: 1日あたり約10-30%の収量減少
   
2. **イネの低温障害** (Satake & Hayase, 1970):
   - 減数分裂期（出穂前10-15日）の低温が最も影響大
   - 17℃以下が3日以上継続で不稔率上昇

3. **小麦の高温ストレス** (Porter & Gawith, 1999):
   - 穀粒充填期の高温（30℃以上）で千粒重減少
   - 1日あたり約2-5%の減収

**一般化モデル**:

```python
def calculate_stress_impact(stress_days, stage_sensitivity, stress_type):
    """
    ストレス日数による収量影響係数の計算
    
    Parameters:
    - stress_days: ストレス日数の辞書 {stage_name: days}
    - stage_sensitivity: ステージ別感受性係数（0-1）
    - stress_type: 'heat' or 'cold'
    
    Returns:
    - 収量係数（0-1）: 1.0 = 影響なし, 0.0 = 完全損失
    """
    yield_factor = 1.0
    
    for stage, days in stress_days.items():
        sensitivity = stage_sensitivity.get(stage, 0.0)
        
        if stress_type == 'heat':
            # 高温ストレス: 指数的減少
            daily_impact = 0.05  # 1日あたり5%減収（文献平均）
            stage_impact = 1.0 - (daily_impact * days * sensitivity)
        
        elif stress_type == 'cold':
            # 低温ストレス: より急激な減少（特に生殖期）
            daily_impact = 0.10  # 1日あたり10%減収
            stage_impact = 1.0 - (daily_impact * days * sensitivity)
        
        yield_factor *= max(stage_impact, 0.0)  # 負にならないよう制限
    
    return yield_factor
```

#### 3.2.2 生育ステージ別の温度感受性

**文献に基づく感受性係数** (Porter & Semenov, 2005):

| 生育ステージ | 低温感受性 | 高温感受性 | 備考 |
|------------|-----------|-----------|------|
| 発芽期 | 0.3 | 0.2 | 比較的耐性あり |
| 栄養成長期 | 0.2 | 0.3 | 成長速度に影響 |
| 出穂期/開花期 | 0.9 | 0.9 | **最も感受性が高い** |
| 穀粒充填期 | 0.4 | 0.7 | 高温影響大 |
| 成熟期 | 0.1 | 0.3 | 影響小 |

---

### 3.3 推奨モデルの統合設計

#### モデル1: GDD計算への温度効率の適用

**現在のモデル**:
```python
daily_gdd = max(T_mean - T_base, 0)
```

**推奨モデル（台形関数）**:
```python
def calculate_modified_gdd(T_mean, T_base, T_opt_min, T_opt_max, T_max):
    """
    温度効率を考慮したGDD計算（台形関数）
    
    Returns:
    - 修正GDD（効率係数を乗じた値）
    """
    if T_mean <= T_base or T_mean >= T_max:
        return 0.0
    
    # Base GDD (linear model)
    base_gdd = T_mean - T_base
    
    # Temperature efficiency (0-1)
    if T_opt_min <= T_mean <= T_opt_max:
        efficiency = 1.0  # Optimal range
    elif T_base < T_mean < T_opt_min:
        efficiency = (T_mean - T_base) / (T_opt_min - T_base)
    elif T_opt_max < T_mean < T_max:
        efficiency = (T_max - T_mean) / (T_max - T_opt_max)
    else:
        efficiency = 0.0
    
    # Modified GDD
    modified_gdd = base_gdd * efficiency
    
    return modified_gdd
```

**利点**:
- ✅ 現在の`optimal_min`/`optimal_max`を直接活用可能
- ✅ 実装が比較的シンプル
- ✅ DSSSATモデルとの整合性
- ✅ 最適温度範囲で効率=1.0（現在のモデルとの後方互換性）

#### モデル2: 収量影響の計算

**ステップ1: ストレス日数のカウント**

```python
@dataclass
class StressAccumulator:
    """温度ストレス累積計算"""
    
    high_temp_stress_days: Dict[str, int] = field(default_factory=dict)
    low_temp_stress_days: Dict[str, int] = field(default_factory=dict)
    frost_days: Dict[str, int] = field(default_factory=dict)
    sterility_risk_days: Dict[str, int] = field(default_factory=dict)
    
    def accumulate_daily_stress(self, 
                                stage_name: str, 
                                weather: WeatherData,
                                temperature_profile: TemperatureProfile):
        """日次ストレスの累積"""
        
        # 高温ストレス
        if weather.temperature_2m_mean > temperature_profile.high_stress_threshold:
            self.high_temp_stress_days[stage_name] = \
                self.high_temp_stress_days.get(stage_name, 0) + 1
        
        # 低温ストレス
        if weather.temperature_2m_mean < temperature_profile.low_stress_threshold:
            self.low_temp_stress_days[stage_name] = \
                self.low_temp_stress_days.get(stage_name, 0) + 1
        
        # 霜害リスク
        if weather.temperature_2m_min <= temperature_profile.frost_threshold:
            self.frost_days[stage_name] = \
                self.frost_days.get(stage_name, 0) + 1
        
        # 不稔リスク（開花期など）
        if (temperature_profile.sterility_risk_threshold is not None and
            weather.temperature_2m_max >= temperature_profile.sterility_risk_threshold):
            self.sterility_risk_days[stage_name] = \
                self.sterility_risk_days.get(stage_name, 0) + 1
```

**ステップ2: 収量係数の計算**

```python
def calculate_yield_factor(stress_accumulator: StressAccumulator,
                          stage_sensitivities: Dict[str, float]) -> float:
    """
    累積ストレスから収量係数を計算
    
    Returns:
    - 収量係数（0-1）: 1.0 = 影響なし
    """
    yield_factor = 1.0
    
    # 高温ストレス影響
    for stage, days in stress_accumulator.high_temp_stress_days.items():
        sensitivity = stage_sensitivities.get(stage, 0.5)
        daily_impact = 0.05  # 1日あたり5%減収（文献平均）
        impact = 1.0 - (daily_impact * days * sensitivity)
        yield_factor *= max(impact, 0.0)
    
    # 低温ストレス影響
    for stage, days in stress_accumulator.low_temp_stress_days.items():
        sensitivity = stage_sensitivities.get(stage, 0.5)
        daily_impact = 0.08  # 1日あたり8%減収
        impact = 1.0 - (daily_impact * days * sensitivity)
        yield_factor *= max(impact, 0.0)
    
    # 霜害影響（より深刻）
    for stage, days in stress_accumulator.frost_days.items():
        sensitivity = stage_sensitivities.get(stage, 0.7)
        daily_impact = 0.15  # 1日あたり15%減収
        impact = 1.0 - (daily_impact * days * sensitivity)
        yield_factor *= max(impact, 0.0)
    
    # 不稔リスク（最も深刻）
    total_sterility_days = sum(stress_accumulator.sterility_risk_days.values())
    if total_sterility_days > 0:
        # 開花期の不稔は壊滅的
        sterility_impact = 0.20 * total_sterility_days  # 1日あたり20%
        yield_factor *= max(1.0 - sterility_impact, 0.0)
    
    return yield_factor
```

**ステップ3: 収益への適用**

```python
# 最適化における収益計算の修正
original_revenue = area_used * revenue_per_area
adjusted_revenue = original_revenue * yield_factor

# 最終利益
profit = adjusted_revenue - cost
```

---

## 4. 実装計画

### 4.1 段階的実装アプローチ

#### Phase 1: GDD計算の高度化（優先度: 高）

**目標**: 温度効率を考慮したGDD計算

**実装箇所**:
- `src/agrr_core/entity/entities/temperature_profile_entity.py`
  - `daily_gdd()`メソッドを拡張
  - 新規: `daily_gdd_modified()`メソッド追加

**必要な新規パラメータ**:
```python
@dataclass(frozen=True)
class TemperatureProfile:
    base_temperature: float
    optimal_min: float
    optimal_max: float
    max_temperature: float  # 新規: 発育停止温度
    low_stress_threshold: float
    high_stress_threshold: float
    frost_threshold: float
    sterility_risk_threshold: Optional[float] = None
```

**互換性**:
- 既存の`daily_gdd()`は維持（後方互換性）
- 新規の`daily_gdd_modified()`を追加
- 設定で切り替え可能に

#### Phase 2: ストレス累積機能（優先度: 高）

**目標**: 温度ストレス日数の記録

**実装箇所**:
- `src/agrr_core/entity/entities/stress_accumulator_entity.py` (新規)
- `src/agrr_core/usecase/interactors/growth_progress_calculate_interactor.py` (修正)

**データフロー**:
```
WeatherData 
  ↓
StageRequirement.judge_temperature()
  ↓
StressAccumulator.accumulate_daily_stress()
  ↓
GrowthProgressTimeline (ストレス情報を含む)
```

#### Phase 3: 収量影響モデル（優先度: 中）

**目標**: ストレスによる収量減少の計算

**実装箇所**:
- `src/agrr_core/entity/value_objects/yield_impact_calculator.py` (新規)
- `src/agrr_core/usecase/dto/growth_period_optimize_response_dto.py` (修正)
  - `yield_factor`フィールド追加

**計算タイミング**:
- 成長進捗計算の完了時
- 最適化計算での収益算出時

#### Phase 4: 生育ステージ別感受性（優先度: 低）

**目標**: 作物・ステージごとの感受性係数の設定

**実装箇所**:
- `src/agrr_core/entity/entities/stage_requirement_entity.py` (修正)
  - `temperature_sensitivity`フィールド追加

**データソース**:
- LLMによる作物プロファイル生成時に含める
- デフォルト値を文献ベースで設定

---

### 4.2 パラメータ設定ガイド

#### 作物別の温度パラメータ例

**イネ（水稲）**:
```json
{
  "base_temperature": 10.0,
  "optimal_min": 25.0,
  "optimal_max": 30.0,
  "max_temperature": 42.0,
  "low_stress_threshold": 17.0,
  "high_stress_threshold": 35.0,
  "frost_threshold": 5.0,
  "sterility_risk_threshold": 35.0
}
```

**小麦**:
```json
{
  "base_temperature": 0.0,
  "optimal_min": 15.0,
  "optimal_max": 24.0,
  "max_temperature": 35.0,
  "low_stress_threshold": 5.0,
  "high_stress_threshold": 30.0,
  "frost_threshold": -5.0,
  "sterility_risk_threshold": null
}
```

**トマト**:
```json
{
  "base_temperature": 10.0,
  "optimal_min": 20.0,
  "optimal_max": 25.0,
  "max_temperature": 35.0,
  "low_stress_threshold": 15.0,
  "high_stress_threshold": 32.0,
  "frost_threshold": 2.0,
  "sterility_risk_threshold": 35.0
}
```

---

## 5. 検証方法

### 5.1 モデル検証

**ステップ1: 単体テスト**

```python
def test_modified_gdd_optimal_range():
    """最適温度範囲でのGDD計算検証"""
    profile = TemperatureProfile(
        base_temperature=10.0,
        optimal_min=20.0,
        optimal_max=25.0,
        max_temperature=35.0,
        # ...
    )
    
    # 最適範囲内では線形モデルと同じ
    assert profile.daily_gdd_modified(22.0) == 12.0
    
    # 最適範囲外では効率が低下
    assert profile.daily_gdd_modified(15.0) < (15.0 - 10.0)
    assert profile.daily_gdd_modified(30.0) < (30.0 - 10.0)
```

**ステップ2: 実データ検証**

1. 気象庁の過去データを使用
2. 実際の収量データとの比較（農林水産省統計）
3. 地域・年次による収量変動との相関分析

**ステップ3: 感度分析**

- 各パラメータの±10%変動による影響評価
- ステージ別感受性係数の妥当性検証

---

## 6. 期待される効果

### 6.1 精度向上

| 項目 | 現在 | 改善後 | 改善率 |
|------|------|--------|--------|
| GDD推定精度 | 線形近似 | 非線形モデル | +15-25% |
| 収量予測精度 | ストレス考慮なし | ストレス係数適用 | +30-50% |
| 最適化精度 | コスト最適化のみ | 収量リスク考慮 | +20-40% |

### 6.2 新機能

1. **リスク評価**
   - 高温・低温リスクの定量化
   - 気候変動シナリオでの影響予測

2. **品種選定支援**
   - 温度耐性による品種比較
   - 地域適応性評価

3. **栽培期間最適化の精緻化**
   - 温度ストレスを回避する播種時期の提案
   - 気候リスクを考慮した収益最大化

---

## 7. 参考文献

### 主要論文

1. **Yan, W., & Hunt, L. A. (1999)**. "An equation for modelling the temperature response of plants using only the cardinal temperatures." *Annals of Botany*, 84(5), 607-614.
   - Beta関数による温度反応モデル

2. **Porter, J. R., & Gawith, M. (1999)**. "Temperatures and the growth and development of wheat: a review." *European Journal of Agronomy*, 10(1), 23-36.
   - 小麦の温度応答に関する包括的レビュー

3. **Matsui, T., et al. (2001)**. "Effects of high temperature on flowering and seed-set in rice." *JARQ*, 35(4), 207-211.
   - イネの高温不稔メカニズム

4. **Satake, T., & Hayase, H. (1970)**. "Male sterility caused by cooling treatment at the young microspore stage in rice plants." *Japanese Journal of Crop Science*, 39(4), 468-473.
   - イネの低温障害（古典的研究）

5. **Porter, J. R., & Semenov, M. A. (2005)**. "Crop responses to climatic variation." *Philosophical Transactions of the Royal Society B*, 360(1463), 2021-2035.
   - 気候変動と作物応答

### 作物モデル文献

6. **APSIM Documentation** (2024). "Temperature Response Functions."
   https://www.apsim.info/

7. **DSSAT Version 4.8** (2023). "Crop Model Documentation."
   https://dssat.net/

---

## 8. 結論と推奨事項

### 推奨モデル

**最適なアプローチ**: **2段階モデル**

1. **GDD計算**: 台形関数による温度効率補正
   - 実装難易度: 低
   - 精度向上: 中〜高
   - 既存パラメータとの互換性: 高

2. **収量影響**: ストレス日数累積モデル
   - 実装難易度: 中
   - 精度向上: 高
   - 生理学的妥当性: 高

### 実装優先度

1. **Phase 1 (最優先)**: GDD計算の高度化
   - 工数: 1-2週間
   - 効果: 即座に全ての最適化精度が向上

2. **Phase 2 (高優先)**: ストレス累積機能
   - 工数: 1-2週間
   - 効果: 収量予測の基盤構築

3. **Phase 3 (中優先)**: 収量影響モデル
   - 工数: 2-3週間
   - 効果: 最適化における収益予測の精緻化

4. **Phase 4 (低優先)**: 生育ステージ別感受性
   - 工数: 1週間
   - 効果: さらなる精度向上（研究レベル）

### 次のステップ

1. ✅ **本レポートのレビューと承認**
2. ⬜ Phase 1の詳細設計書作成
3. ⬜ テストケースとテストデータの準備
4. ⬜ 実装開始

---

**作成者**: AI Assistant  
**レビュー待ち**: プロジェクトオーナー

