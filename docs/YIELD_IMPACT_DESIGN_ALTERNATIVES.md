# Yield Impact 設計代替案の比較
**作成日**: 2025-10-14  
**目的**: YieldImpact計算をどこに配置すべきかの設計比較

---

## 1. 設計代替案

### 案A: 独立したクラス（元の計画）

```python
# StressAccumulator (Entity)
class StressAccumulator:
    high_temp_stress_days: Dict[str, int]
    low_temp_stress_days: Dict[str, int]
    
    def accumulate_daily_stress(stage, weather, temp_profile):
        if temp_profile.is_high_temp_stress(weather.temperature_2m_mean):
            self.high_temp_stress_days[stage.name] += 1

# YieldImpactCalculator (Value Object)
class YieldImpactCalculator:
    def calculate(stress_accumulator: StressAccumulator) -> float:
        # ストレス日数から yield_factor を計算
```

**配置**: 別ファイル（2つの新規クラス）

---

### 案B: TemperatureProfileに統合（ユーザー提案）

```python
@dataclass(frozen=True)
class TemperatureProfile:
    base_temperature: float
    optimal_min: float
    optimal_max: float
    # ... existing fields ...
    
    # Existing methods
    def is_high_temp_stress(self, t_mean) -> bool:
        return t_mean > self.high_stress_threshold
    
    def daily_gdd(self, t_mean) -> float:
        # ... existing implementation ...
    
    # NEW: Yield impact methods
    def daily_yield_impact(
        self, 
        weather: WeatherData,
        sensitivity: StressSensitivity
    ) -> float:
        """Calculate daily yield impact from temperature stress.
        
        Returns:
            Daily impact factor (0-1): 1.0 = no impact
        """
        impact = 1.0
        
        # High temp stress
        if self.is_high_temp_stress(weather.temperature_2m_mean):
            impact *= (1.0 - 0.05 * sensitivity.high_temp)
        
        # Low temp stress
        if self.is_low_temp_stress(weather.temperature_2m_mean):
            impact *= (1.0 - 0.08 * sensitivity.low_temp)
        
        # Frost risk
        if self.is_frost_risk(weather.temperature_2m_min):
            impact *= (1.0 - 0.15 * sensitivity.frost)
        
        # Sterility risk
        if self.is_sterility_risk(weather.temperature_2m_max):
            impact *= (1.0 - 0.20 * sensitivity.sterility)
        
        return impact
```

**配置**: `temperature_profile_entity.py` に追加

---

### 案C: ハイブリッド（折衷案）

```python
# TemperatureProfile: 日次判定のみ
@dataclass(frozen=True)
class TemperatureProfile:
    # ... existing fields ...
    
    def calculate_daily_stress_impacts(
        self,
        weather: WeatherData,
        sensitivity: StressSensitivity
    ) -> Dict[str, float]:
        """Calculate daily impact from each stress type.
        
        Returns:
            Dict with keys: high_temp, low_temp, frost, sterility
            Values are daily impact rates (0-1)
        """
        return {
            "high_temp": 0.05 if self.is_high_temp_stress(weather.temperature_2m_mean) else 0.0,
            "low_temp": 0.08 if self.is_low_temp_stress(weather.temperature_2m_mean) else 0.0,
            "frost": 0.15 if self.is_frost_risk(weather.temperature_2m_min) else 0.0,
            "sterility": 0.20 if self.is_sterility_risk(weather.temperature_2m_max) else 0.0,
        }

# YieldImpactAccumulator: 累積計算
class YieldImpactAccumulator:
    cumulative_impact: float = 1.0
    
    def accumulate(
        self,
        daily_impacts: Dict[str, float],
        sensitivity: StressSensitivity
    ):
        """Accumulate daily impacts."""
        for stress_type, impact_rate in daily_impacts.items():
            if impact_rate > 0:
                sens_value = getattr(sensitivity, stress_type)
                self.cumulative_impact *= (1.0 - impact_rate * sens_value)
```

**配置**: TemperatureProfileに日次計算、累積は別クラス

---

## 2. 詳細比較

### 2.1 責務の分離（Single Responsibility Principle）

| 案 | TemperatureProfileの責務 | 他のクラスの責務 |
|----|------------------------|----------------|
| **案A** | 温度判定のみ | StressAccumulator: ストレス累積<br>YieldImpactCalculator: 収量計算 |
| **案B** | 温度判定 + 収量影響計算 | なし |
| **案C** | 温度判定 + 日次影響率計算 | YieldImpactAccumulator: 累積計算 |

**評価**:
- ✅ 案A: 責務が最も明確に分離
- ⚠️ 案B: TemperatureProfileの責務が増加
- ✅ 案C: バランスが良い

---

### 2.2 コードの凝集度（Cohesion）

| 案 | 温度関連ロジックの集約度 | 評価 |
|----|----------------------|------|
| **案A** | 低（3つのクラスに分散） | △ |
| **案B** | 高（全て1つのクラス） | ✅ |
| **案C** | 中（2つのクラス） | ○ |

**評価**:
- ⚠️ 案A: ロジックが分散しすぎる可能性
- ✅ 案B: 温度関連が全て1箇所
- ✅ 案C: 適度な凝集度

---

### 2.3 ステージ別感受性の扱い

| 案 | 感受性係数の渡し方 | 評価 |
|----|------------------|------|
| **案A** | StressAccumulator が stage_name で記録<br>YieldImpactCalculator がステージ別に計算 | ✅ 柔軟 |
| **案B** | TemperatureProfile の各メソッドに sensitivity を渡す | ○ 可能だが引数が増える |
| **案C** | TemperatureProfile は影響率のみ<br>Accumulator がステージ別に処理 | ✅ 柔軟 |

**評価**:
- ✅ 案A: ステージ別の細かい制御が可能
- ⚠️ 案B: メソッド引数が増える
- ✅ 案C: ステージ別制御が可能

---

### 2.4 テストのしやすさ

#### 案A: 独立したクラス

```python
def test_stress_accumulator():
    """ストレス累積のみをテスト"""
    accumulator = StressAccumulator()
    # テストが独立している

def test_yield_calculator():
    """収量計算のみをテスト"""
    calculator = YieldImpactCalculator()
    # テストが独立している
```

#### 案B: TemperatureProfileに統合

```python
def test_temperature_profile_yield_impact():
    """温度判定と収量計算を一緒にテスト"""
    profile = TemperatureProfile(...)
    # 温度閾値 + 感受性係数 + 影響率の全てをセットアップ
    # テストケースが複雑になる
```

#### 案C: ハイブリッド

```python
def test_temperature_profile_daily_impacts():
    """日次影響率のみをテスト"""
    profile = TemperatureProfile(...)
    # シンプル

def test_yield_accumulator():
    """累積計算のみをテスト"""
    accumulator = YieldImpactAccumulator()
    # シンプル
```

**評価**:
- ✅ 案A: 各クラスが独立してテスト可能
- ⚠️ 案B: テストケースが複雑化
- ✅ 案C: 各部分を独立してテスト可能

---

### 2.5 既存コードへの影響

| 案 | TemperatureProfileの変更 | 新規ファイル数 | 影響度 |
|----|------------------------|-------------|--------|
| **案A** | なし（変更不要） | 2ファイル | 小 |
| **案B** | メソッド追加（大） | 0ファイル | 大 |
| **案C** | メソッド追加（小） | 1ファイル | 中 |

**評価**:
- ✅ 案A: 既存コードに影響なし
- ⚠️ 案B: TemperatureProfileの大幅な変更
- ○ 案C: 小さな変更のみ

---

### 2.6 実装の複雑さ

| 案 | クラス数 | メソッド数 | コード行数 | 評価 |
|----|---------|----------|----------|------|
| **案A** | 3 | 6 | ~350行 | 中 |
| **案B** | 1 | 3 | ~250行 | 小 |
| **案C** | 2 | 4 | ~280行 | 小〜中 |

**評価**:
- ⚠️ 案A: ファイルとクラスが増える
- ✅ 案B: 最もシンプル
- ✅ 案C: バランスが良い

---

## 3. 具体的な実装例の比較

### 3.1 使用例

#### 案A: 独立したクラス

```python
# UseCase層での使用
accumulator = StressAccumulator()

for weather in weather_data_list:
    stage = determine_current_stage(cumulative_gdd)
    
    # ストレス累積
    accumulator.accumulate_daily_stress(
        stage=stage.stage,
        weather=weather,
        temperature_profile=stage.temperature,
    )

# 収量係数計算
calculator = YieldImpactCalculator()
yield_factor = calculator.calculate(accumulator)
```

**特徴**:
- 各ステップが明確
- ストレス記録と計算が分離
- ステージ情報が保持される

---

#### 案B: TemperatureProfileに統合

```python
# UseCase層での使用
cumulative_impact = 1.0

for weather in weather_data_list:
    stage = determine_current_stage(cumulative_gdd)
    
    # 日次の収量影響を直接計算
    sensitivity = get_stage_sensitivity(stage.stage.name)
    daily_impact = stage.temperature.daily_yield_impact(
        weather=weather,
        sensitivity=sensitivity,
    )
    cumulative_impact *= daily_impact

yield_factor = cumulative_impact
```

**特徴**:
- シンプルで直感的
- TemperatureProfileが全て処理
- ステージ情報は UseCase 層で管理

---

#### 案C: ハイブリッド

```python
# UseCase層での使用
accumulator = YieldImpactAccumulator()

for weather in weather_data_list:
    stage = determine_current_stage(cumulative_gdd)
    
    # 日次影響率を取得
    daily_impacts = stage.temperature.calculate_daily_stress_impacts(
        weather=weather,
        sensitivity=get_stage_sensitivity(stage.stage.name),
    )
    
    # 累積
    accumulator.accumulate(daily_impacts)

yield_factor = accumulator.get_cumulative_impact()
```

**特徴**:
- 責務が適度に分散
- TemperatureProfileは判定に集中
- 累積ロジックは別クラス

---

## 4. 推奨案の決定

### 4.1 評価マトリクス

| 評価項目 | 重要度 | 案A | 案B | 案C |
|---------|--------|-----|-----|-----|
| 責務の分離 | 高 | ✅ 5 | ⚠️ 2 | ✅ 4 |
| コードの凝集度 | 中 | △ 3 | ✅ 5 | ○ 4 |
| 柔軟性 | 高 | ✅ 5 | ⚠️ 3 | ✅ 5 |
| テストのしやすさ | 高 | ✅ 5 | ⚠️ 3 | ✅ 5 |
| 既存コードへの影響 | 高 | ✅ 5 | ⚠️ 2 | ○ 4 |
| 実装の複雑さ | 中 | ⚠️ 3 | ✅ 5 | ✅ 4 |
| **重み付け合計** | - | **26** | **20** | **26** |

**スコアリング**: 5=優秀、4=良好、3=普通、2=注意、1=問題

---

### 4.2 推奨: 案C（ハイブリッド）⭐

**理由**:
1. ✅ **責務の分離**: TemperatureProfileは「判定」、Accumulatorは「累積」
2. ✅ **凝集度**: 温度関連ロジックはTemperatureProfileに集約
3. ✅ **柔軟性**: ステージ別の細かい制御が可能
4. ✅ **テスト**: 各部分を独立してテスト可能
5. ✅ **影響最小**: TemperatureProfileへの変更は小さい
6. ✅ **バランス**: シンプルさと柔軟性のバランス

**案Aとの違い**:
- StressAccumulatorを廃止（日数記録が不要）
- TemperatureProfileに日次影響率計算を追加（シンプル）
- YieldImpactCalculatorの代わりにYieldImpactAccumulator（より軽量）

**案Bとの違い**:
- 累積ロジックを分離（TemperatureProfileの責務を削減）
- テストがシンプルに

---

## 5. 推奨案（案C）の詳細設計

### 5.1 TemperatureProfile への追加

```python
@dataclass(frozen=True)
class TemperatureProfile:
    """Temperature thresholds for a crop at a given growth stage."""
    
    # ... existing fields ...
    
    # Stress impact rates (literature-based, can be overridden)
    high_temp_daily_impact: float = 0.05  # 5% per day
    low_temp_daily_impact: float = 0.08   # 8% per day
    frost_daily_impact: float = 0.15      # 15% per day
    sterility_daily_impact: float = 0.20  # 20% per day
    
    # ... existing methods ...
    
    def calculate_daily_stress_impacts(
        self,
        weather: WeatherData,
    ) -> Dict[str, float]:
        """Calculate daily stress impact rates.
        
        Returns impact rates (0-1) for each stress type.
        0.0 = no stress, 0.05 = 5% reduction, etc.
        
        Args:
            weather: Daily weather data
            
        Returns:
            Dict with keys: high_temp, low_temp, frost, sterility
            Values are impact rates (0-1)
        """
        impacts = {
            "high_temp": 0.0,
            "low_temp": 0.0,
            "frost": 0.0,
            "sterility": 0.0,
        }
        
        # High temperature stress
        if self.is_high_temp_stress(weather.temperature_2m_mean):
            impacts["high_temp"] = self.high_temp_daily_impact
        
        # Low temperature stress
        if self.is_low_temp_stress(weather.temperature_2m_mean):
            impacts["low_temp"] = self.low_temp_daily_impact
        
        # Frost risk
        if self.is_frost_risk(weather.temperature_2m_min):
            impacts["frost"] = self.frost_daily_impact
        
        # Sterility risk
        if self.is_sterility_risk(weather.temperature_2m_max):
            impacts["sterility"] = self.sterility_daily_impact
        
        return impacts
```

**変更点**:
- フィールド追加: 4つの影響率（デフォルト値あり）
- メソッド追加: `calculate_daily_stress_impacts()` 1つのみ
- 既存メソッドは変更なし

**行数**: 約40行追加

---

### 5.2 YieldImpactAccumulator（新規）

```python
"""Yield impact accumulator.

Accumulates daily yield impacts across growth stages with stage-specific sensitivity.
"""

from dataclasses import dataclass, field
from typing import Dict

from agrr_core.entity.entities.growth_stage_entity import GrowthStage


@dataclass(frozen=True)
class StressSensitivity:
    """Stage-specific sensitivity to stress types (0-1)."""
    
    high_temp: float = 0.5
    low_temp: float = 0.5
    frost: float = 0.7
    sterility: float = 0.9


# Default sensitivities by stage (literature-based)
DEFAULT_STAGE_SENSITIVITIES: Dict[str, StressSensitivity] = {
    "germination": StressSensitivity(0.2, 0.3, 0.5, 0.0),
    "vegetative": StressSensitivity(0.3, 0.2, 0.5, 0.3),
    "flowering": StressSensitivity(0.9, 0.9, 0.9, 1.0),
    "heading": StressSensitivity(0.9, 0.9, 0.9, 1.0),
    "grain_filling": StressSensitivity(0.7, 0.4, 0.7, 0.5),
    "ripening": StressSensitivity(0.3, 0.1, 0.3, 0.0),
}


@dataclass
class YieldImpactAccumulator:
    """Accumulates yield impacts from daily temperature stress."""
    
    cumulative_yield_factor: float = 1.0
    stage_sensitivities: Dict[str, StressSensitivity] = field(
        default_factory=lambda: DEFAULT_STAGE_SENSITIVITIES.copy()
    )
    
    def accumulate_daily_impact(
        self,
        stage: GrowthStage,
        daily_impacts: Dict[str, float],
    ) -> None:
        """Accumulate daily impact for a specific stage.
        
        Args:
            stage: Current growth stage
            daily_impacts: Impact rates from TemperatureProfile.calculate_daily_stress_impacts()
        """
        sensitivity = self._get_sensitivity(stage.name)
        
        # Apply sensitivity-weighted impacts (multiplicative)
        for stress_type, impact_rate in daily_impacts.items():
            if impact_rate > 0:
                sens_value = getattr(sensitivity, stress_type)
                weighted_impact = impact_rate * sens_value
                self.cumulative_yield_factor *= (1.0 - weighted_impact)
    
    def get_yield_factor(self) -> float:
        """Get final yield factor (0-1).
        
        Returns:
            Yield factor: 1.0 = no impact, 0.0 = total loss
        """
        return max(0.0, self.cumulative_yield_factor)
    
    def _get_sensitivity(self, stage_name: str) -> StressSensitivity:
        """Get sensitivity for a stage with fallback."""
        normalized = stage_name.lower().replace(" ", "_")
        
        if normalized in self.stage_sensitivities:
            return self.stage_sensitivities[normalized]
        
        # Fallback to moderate sensitivity
        return StressSensitivity(0.5, 0.5, 0.7, 0.5)
```

**行数**: 約100行

---

### 5.3 UseCase層での使用

```python
# growth_progress_calculate_interactor.py
def _calculate_growth_progress(
    self,
    crop_profile: CropProfile,
    start_date,
    weather_data_list: List[WeatherData],
) -> GrowthProgressTimeline:
    """Calculate growth progress with yield impact."""
    
    # ... existing GDD calculation ...
    
    # NEW: Initialize yield impact accumulator
    yield_accumulator = YieldImpactAccumulator()
    
    for weather_data in weather_data_list:
        current_stage = self._determine_current_stage(...)
        
        # Calculate GDD (existing)
        daily_gdd = current_stage.daily_gdd(weather_data)
        cumulative_gdd += daily_gdd
        
        # NEW: Calculate and accumulate yield impact
        daily_impacts = current_stage.temperature.calculate_daily_stress_impacts(
            weather=weather_data
        )
        yield_accumulator.accumulate_daily_impact(
            stage=current_stage.stage,
            daily_impacts=daily_impacts,
        )
        
        # ... rest of existing code ...
    
    # Get final yield factor
    yield_factor = yield_accumulator.get_yield_factor()
    
    return GrowthProgressTimeline(
        crop=crop_profile.crop,
        start_date=start_date,
        progress_list=progress_list,
        yield_factor=yield_factor,  # NEW
    )
```

---

## 6. 案C 実装計画（更新版）

### 6.1 変更ファイル

| ファイル | 変更内容 | 行数 |
|---------|---------|------|
| `entity/entities/temperature_profile_entity.py` | メソッド追加 | +40行 |
| `entity/value_objects/yield_impact_accumulator.py` | 新規作成 | ~100行 |
| `entity/entities/growth_progress_timeline_entity.py` | フィールド追加 | +2行 |
| `entity/value_objects/optimization_objective.py` | `yield_factor`追加 | +5行 |
| `usecase/interactors/growth_progress_calculate_interactor.py` | 累積ロジック追加 | +15行 |
| `usecase/interactors/growth_period_optimize_interactor.py` | yield_factor使用 | +10行 |

**合計**: 新規1ファイル、修正5ファイル

---

### 6.2 工数見積もり（更新）

| Phase | タスク | 工数 |
|-------|--------|------|
| **Phase 1** | TemperatureProfile拡張 + テスト | 1日 |
| **Phase 2** | YieldImpactAccumulator実装 + テスト | 1日 |
| **Phase 3** | UseCase層統合 | 2日 |
| **Phase 4** | 統合テスト + ドキュメント | 1日 |

**合計**: 5日間（元の計画より3日短縮）

---

## 7. まとめ

### 最終推奨: 案C（ハイブリッド）⭐

**採用理由**:
1. ✅ TemperatureProfileに日次影響計算を追加（凝集度向上）
2. ✅ 累積ロジックは別クラス（責務分離）
3. ✅ 既存コードへの影響最小
4. ✅ テストが簡潔
5. ✅ 実装工数が短い（5日間）

**案Aとの比較**:
- ファイル数: 2個 → 1個（削減）
- 行数: ~350行 → ~170行（半減）
- 工数: 8日 → 5日（短縮）

**案Bとの比較**:
- TemperatureProfileの責務: 過大 → 適正
- テストの複雑さ: 高 → 低
- 柔軟性: 低 → 高

---

**次のステップ**:
1. ⬜ 案Cの承認
2. ⬜ Phase 1実装開始


