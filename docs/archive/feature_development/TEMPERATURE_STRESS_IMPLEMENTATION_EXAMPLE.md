# 温度ストレスモデル実装例
**作成日**: 2025-10-14  
**関連ドキュメント**: [TEMPERATURE_STRESS_MODEL_RESEARCH.md](TEMPERATURE_STRESS_MODEL_RESEARCH.md)

---

## 1. 実装例の全体像

このドキュメントでは、温度ストレスモデルの具体的な実装例を段階的に示します。

---

## 2. Phase 1: GDD計算の高度化

### 2.1 拡張されたTemperatureProfileエンティティ

```python
"""Enhanced temperature profile entity with stress modeling support."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TemperatureProfile:
    """Temperature thresholds for a crop at a given growth stage.
    
    Enhanced with maximum temperature threshold for stress modeling.
    """
    
    base_temperature: float  # GDD base (T_base)
    optimal_min: float       # Lower optimal temperature (T_opt_min)
    optimal_max: float       # Upper optimal temperature (T_opt_max)
    max_temperature: float   # Upper limit temperature (T_max) - NEW
    low_stress_threshold: float
    high_stress_threshold: float
    frost_threshold: float
    sterility_risk_threshold: Optional[float] = None
    
    # Stress modeling configuration
    use_modified_gdd: bool = False  # Enable modified GDD calculation

    def is_ok_temperature(self, t_mean: Optional[float]) -> bool:
        """Return True if mean temperature is within the optimal range."""
        if t_mean is None:
            return False
        return self.optimal_min <= t_mean <= self.optimal_max

    def is_low_temp_stress(self, t_mean: Optional[float]) -> bool:
        """Return True if mean temperature indicates low-temperature stress."""
        if t_mean is None:
            return False
        return t_mean < self.low_stress_threshold

    def is_high_temp_stress(self, t_mean: Optional[float]) -> bool:
        """Return True if mean temperature indicates high-temperature stress."""
        if t_mean is None:
            return False
        return t_mean > self.high_stress_threshold

    def is_frost_risk(self, t_min: Optional[float]) -> bool:
        """Return True if minimum temperature indicates frost risk."""
        if t_min is None:
            return False
        return t_min <= self.frost_threshold

    def is_sterility_risk(self, t_max: Optional[float]) -> bool:
        """Return True if maximum temperature indicates sterility risk."""
        if t_max is None or self.sterility_risk_threshold is None:
            return False
        return t_max >= self.sterility_risk_threshold

    def daily_gdd(self, t_mean: Optional[float]) -> float:
        """Return daily growing degree days.
        
        Switches between linear and modified models based on configuration.
        """
        if self.use_modified_gdd:
            return self.daily_gdd_modified(t_mean)
        else:
            return self.daily_gdd_linear(t_mean)
    
    def daily_gdd_linear(self, t_mean: Optional[float]) -> float:
        """Return daily GDD using linear model (original implementation).
        
        Formula: max(t_mean - base_temperature, 0)
        """
        if t_mean is None:
            return 0.0
        delta = t_mean - self.base_temperature
        return delta if delta > 0 else 0.0
    
    def daily_gdd_modified(self, t_mean: Optional[float]) -> float:
        """Return daily GDD with temperature efficiency (trapezoidal function).
        
        Formula: GDD_linear × efficiency(T)
        
        Efficiency function (trapezoidal):
        - efficiency = 1.0 when T_opt_min ≤ T ≤ T_opt_max (optimal range)
        - efficiency = (T - T_base) / (T_opt_min - T_base) when T_base < T < T_opt_min
        - efficiency = (T_max - T) / (T_max - T_opt_max) when T_opt_max < T < T_max
        - efficiency = 0.0 when T ≤ T_base or T ≥ T_max
        
        Returns:
            Modified GDD value (0.0 if temperature is outside viable range)
        """
        if t_mean is None:
            return 0.0
        
        # Outside viable temperature range
        if t_mean <= self.base_temperature or t_mean >= self.max_temperature:
            return 0.0
        
        # Base GDD (linear component)
        base_gdd = t_mean - self.base_temperature
        
        # Calculate temperature efficiency (0-1)
        efficiency = self._calculate_temperature_efficiency(t_mean)
        
        # Modified GDD = base GDD × efficiency
        modified_gdd = base_gdd * efficiency
        
        return modified_gdd
    
    def _calculate_temperature_efficiency(self, t_mean: float) -> float:
        """Calculate temperature efficiency using trapezoidal function.
        
        Returns:
            Efficiency value (0.0-1.0)
        """
        # Optimal range: full efficiency
        if self.optimal_min <= t_mean <= self.optimal_max:
            return 1.0
        
        # Sub-optimal (cool side)
        elif self.base_temperature < t_mean < self.optimal_min:
            efficiency = (t_mean - self.base_temperature) / \
                        (self.optimal_min - self.base_temperature)
            return max(0.0, min(1.0, efficiency))
        
        # Sub-optimal (warm side)
        elif self.optimal_max < t_mean < self.max_temperature:
            efficiency = (self.max_temperature - t_mean) / \
                        (self.max_temperature - self.optimal_max)
            return max(0.0, min(1.0, efficiency))
        
        # Outside range
        else:
            return 0.0
    
    def get_efficiency_at_temperature(self, t_mean: float) -> float:
        """Get temperature efficiency at given temperature (for visualization).
        
        Args:
            t_mean: Mean temperature in °C
            
        Returns:
            Efficiency value (0.0-1.0)
        """
        if t_mean <= self.base_temperature or t_mean >= self.max_temperature:
            return 0.0
        return self._calculate_temperature_efficiency(t_mean)
```

### 2.2 テストコード例

```python
"""Tests for enhanced temperature profile with modified GDD."""

import pytest
from agrr_core.entity.entities.temperature_profile_entity import TemperatureProfile


class TestModifiedGDD:
    """Test cases for modified GDD calculation."""
    
    @pytest.fixture
    def rice_temperature_profile(self):
        """Rice temperature profile for testing."""
        return TemperatureProfile(
            base_temperature=10.0,
            optimal_min=25.0,
            optimal_max=30.0,
            max_temperature=42.0,
            low_stress_threshold=17.0,
            high_stress_threshold=35.0,
            frost_threshold=5.0,
            sterility_risk_threshold=35.0,
            use_modified_gdd=True,
        )
    
    def test_gdd_in_optimal_range(self, rice_temperature_profile):
        """Test GDD calculation within optimal temperature range."""
        # Within optimal range: efficiency = 1.0
        temp = 27.0  # Between 25-30°C
        gdd = rice_temperature_profile.daily_gdd_modified(temp)
        
        expected_base_gdd = 27.0 - 10.0  # = 17.0
        expected_efficiency = 1.0
        expected_gdd = expected_base_gdd * expected_efficiency
        
        assert gdd == pytest.approx(expected_gdd)
    
    def test_gdd_below_optimal(self, rice_temperature_profile):
        """Test GDD calculation below optimal range."""
        # Below optimal: efficiency < 1.0
        temp = 17.5  # Between base(10) and optimal_min(25)
        gdd = rice_temperature_profile.daily_gdd_modified(temp)
        
        base_gdd = 17.5 - 10.0  # = 7.5
        efficiency = (17.5 - 10.0) / (25.0 - 10.0)  # = 7.5/15 = 0.5
        expected_gdd = base_gdd * efficiency  # = 7.5 * 0.5 = 3.75
        
        assert gdd == pytest.approx(expected_gdd)
        assert gdd < base_gdd  # Modified GDD should be less than base GDD
    
    def test_gdd_above_optimal(self, rice_temperature_profile):
        """Test GDD calculation above optimal range."""
        # Above optimal: efficiency < 1.0
        temp = 36.0  # Between optimal_max(30) and max(42)
        gdd = rice_temperature_profile.daily_gdd_modified(temp)
        
        base_gdd = 36.0 - 10.0  # = 26.0
        efficiency = (42.0 - 36.0) / (42.0 - 30.0)  # = 6/12 = 0.5
        expected_gdd = base_gdd * efficiency  # = 26.0 * 0.5 = 13.0
        
        assert gdd == pytest.approx(expected_gdd)
        assert gdd < base_gdd
    
    def test_gdd_at_base_temperature(self, rice_temperature_profile):
        """Test GDD at base temperature (should be 0)."""
        gdd = rice_temperature_profile.daily_gdd_modified(10.0)
        assert gdd == 0.0
    
    def test_gdd_below_base_temperature(self, rice_temperature_profile):
        """Test GDD below base temperature (should be 0)."""
        gdd = rice_temperature_profile.daily_gdd_modified(5.0)
        assert gdd == 0.0
    
    def test_gdd_at_max_temperature(self, rice_temperature_profile):
        """Test GDD at maximum temperature (should be 0)."""
        gdd = rice_temperature_profile.daily_gdd_modified(42.0)
        assert gdd == 0.0
    
    def test_gdd_above_max_temperature(self, rice_temperature_profile):
        """Test GDD above maximum temperature (should be 0)."""
        gdd = rice_temperature_profile.daily_gdd_modified(45.0)
        assert gdd == 0.0
    
    def test_efficiency_curve_continuity(self, rice_temperature_profile):
        """Test that efficiency curve is continuous."""
        # Test at boundaries
        temps = [10.0, 15.0, 20.0, 25.0, 27.5, 30.0, 35.0, 40.0, 42.0]
        efficiencies = [
            rice_temperature_profile.get_efficiency_at_temperature(t)
            for t in temps
        ]
        
        # All efficiencies should be between 0 and 1
        assert all(0.0 <= e <= 1.0 for e in efficiencies)
        
        # Optimal range should have efficiency = 1.0
        optimal_indices = [3, 4, 5]  # 25, 27.5, 30
        for i in optimal_indices:
            assert efficiencies[i] == pytest.approx(1.0)
    
    def test_backward_compatibility_with_linear_model(self, rice_temperature_profile):
        """Test backward compatibility: linear model option."""
        profile_linear = TemperatureProfile(
            base_temperature=10.0,
            optimal_min=25.0,
            optimal_max=30.0,
            max_temperature=42.0,
            low_stress_threshold=17.0,
            high_stress_threshold=35.0,
            frost_threshold=5.0,
            use_modified_gdd=False,  # Use linear model
        )
        
        temp = 27.0
        gdd_linear = profile_linear.daily_gdd(temp)
        
        # Linear model: GDD = T - T_base
        expected = 27.0 - 10.0
        assert gdd_linear == pytest.approx(expected)
```

---

## 3. Phase 2: ストレス累積機能

### 3.1 StressAccumulatorエンティティ

```python
"""Entity for accumulating temperature stress during crop growth."""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class StressAccumulator:
    """Accumulator for tracking temperature stress days by growth stage.
    
    This entity records the number of days with various types of temperature
    stress for each growth stage, which will be used to calculate yield impact.
    
    Attributes:
        high_temp_stress_days: Days with high temperature stress by stage
        low_temp_stress_days: Days with low temperature stress by stage
        frost_days: Days with frost risk by stage
        sterility_risk_days: Days with sterility risk by stage
    """
    
    high_temp_stress_days: Dict[str, int] = field(default_factory=dict)
    low_temp_stress_days: Dict[str, int] = field(default_factory=dict)
    frost_days: Dict[str, int] = field(default_factory=dict)
    sterility_risk_days: Dict[str, int] = field(default_factory=dict)
    
    def accumulate_daily_stress(
        self,
        stage_name: str,
        is_high_temp_stress: bool,
        is_low_temp_stress: bool,
        is_frost_risk: bool,
        is_sterility_risk: bool,
    ):
        """Accumulate stress indicators for a single day.
        
        Args:
            stage_name: Name of current growth stage
            is_high_temp_stress: True if high temperature stress occurred
            is_low_temp_stress: True if low temperature stress occurred
            is_frost_risk: True if frost risk occurred
            is_sterility_risk: True if sterility risk occurred
        """
        # High temperature stress
        if is_high_temp_stress:
            self.high_temp_stress_days[stage_name] = \
                self.high_temp_stress_days.get(stage_name, 0) + 1
        
        # Low temperature stress
        if is_low_temp_stress:
            self.low_temp_stress_days[stage_name] = \
                self.low_temp_stress_days.get(stage_name, 0) + 1
        
        # Frost risk
        if is_frost_risk:
            self.frost_days[stage_name] = \
                self.frost_days.get(stage_name, 0) + 1
        
        # Sterility risk (flowering stage only)
        if is_sterility_risk:
            self.sterility_risk_days[stage_name] = \
                self.sterility_risk_days.get(stage_name, 0) + 1
    
    def get_total_stress_days(self, stress_type: str) -> int:
        """Get total stress days across all stages.
        
        Args:
            stress_type: One of 'high_temp', 'low_temp', 'frost', 'sterility'
            
        Returns:
            Total number of stress days
        """
        stress_dict_map = {
            'high_temp': self.high_temp_stress_days,
            'low_temp': self.low_temp_stress_days,
            'frost': self.frost_days,
            'sterility': self.sterility_risk_days,
        }
        
        stress_dict = stress_dict_map.get(stress_type, {})
        return sum(stress_dict.values())
    
    def get_stress_summary(self) -> Dict[str, Dict[str, int]]:
        """Get comprehensive stress summary.
        
        Returns:
            Dictionary with stress types and their stage-wise counts
        """
        return {
            'high_temp_stress': dict(self.high_temp_stress_days),
            'low_temp_stress': dict(self.low_temp_stress_days),
            'frost': dict(self.frost_days),
            'sterility': dict(self.sterility_risk_days),
        }
```

### 3.2 修正されたGrowthProgressCalculateInteractor

```python
"""Enhanced growth progress calculation with stress tracking."""

from agrr_core.entity.entities.stress_accumulator_entity import StressAccumulator


class GrowthProgressCalculateInteractor(GrowthProgressCalculateInputPort):
    """Interactor for calculating growth progress timeline with stress tracking."""

    def __init__(
        self,
        crop_profile_gateway: CropProfileGateway,
        weather_gateway: WeatherGateway,
        enable_stress_tracking: bool = True,  # NEW
    ):
        self.crop_profile_gateway = crop_profile_gateway
        self.weather_gateway = weather_gateway
        self.enable_stress_tracking = enable_stress_tracking

    async def execute(
        self, request: GrowthProgressCalculateRequestDTO
    ) -> GrowthProgressCalculateResponseDTO:
        """Calculate growth progress timeline with optional stress tracking."""
        # Get crop profile
        crop_profile = await self._get_crop_profile(
            request.crop_id, request.variety
        )

        # Get weather data
        weather_data_list = await self.weather_gateway.get()

        # Calculate growth progress with stress tracking
        timeline, stress_accumulator = self._calculate_growth_progress_with_stress(
            crop_profile, request.start_date, weather_data_list
        )

        # Convert to response DTO (including stress data)
        return self._to_response_dto(timeline, stress_accumulator)

    def _calculate_growth_progress_with_stress(
        self,
        crop_profile: CropProfile,
        start_date,
        weather_data_list: List[WeatherData],
    ) -> tuple[GrowthProgressTimeline, StressAccumulator]:
        """Calculate growth progress with stress accumulation."""
        # Calculate total required GDD
        total_required_gdd = sum(
            sr.thermal.required_gdd for sr in crop_profile.stage_requirements
        )

        if total_required_gdd <= 0:
            raise ValueError("Total required GDD must be positive")

        cumulative_gdd = 0.0
        progress_list = []
        
        # NEW: Initialize stress accumulator
        stress_accumulator = StressAccumulator() if self.enable_stress_tracking else None

        for weather_data in weather_data_list:
            # Determine current stage
            current_stage = self._determine_current_stage(
                cumulative_gdd, crop_profile.stage_requirements
            )

            # Calculate daily GDD (uses modified model if enabled)
            daily_gdd = current_stage.daily_gdd(weather_data)
            cumulative_gdd += daily_gdd

            # NEW: Track temperature stress
            if stress_accumulator:
                temp_judgments = current_stage.judge_temperature(weather_data)
                stress_accumulator.accumulate_daily_stress(
                    stage_name=current_stage.stage.name,
                    is_high_temp_stress=temp_judgments['highTempStress'],
                    is_low_temp_stress=temp_judgments['lowTempStress'],
                    is_frost_risk=temp_judgments['frostRisk'],
                    is_sterility_risk=temp_judgments['sterilityRisk'],
                )

            # Calculate growth percentage
            growth_percentage = min(
                (cumulative_gdd / total_required_gdd) * 100.0, 100.0
            )

            # Create progress record
            progress = GrowthProgress(
                date=weather_data.time,
                cumulative_gdd=cumulative_gdd,
                total_required_gdd=total_required_gdd,
                growth_percentage=growth_percentage,
                current_stage=current_stage.stage,
                is_complete=(growth_percentage >= 100.0),
            )
            progress_list.append(progress)

        timeline = GrowthProgressTimeline(
            crop=crop_profile.crop,
            start_date=start_date,
            progress_list=progress_list,
        )
        
        return timeline, stress_accumulator
```

---

## 4. Phase 3: 収量影響モデル

### 4.1 YieldImpactCalculator（Value Object）

```python
"""Yield impact calculator based on accumulated temperature stress."""

from dataclasses import dataclass
from typing import Dict, Optional
from agrr_core.entity.entities.stress_accumulator_entity import StressAccumulator


@dataclass(frozen=True)
class StageSensitivity:
    """Temperature stress sensitivity coefficients for a growth stage.
    
    Attributes:
        stage_name: Name of growth stage
        high_temp_sensitivity: Sensitivity to high temperature (0-1)
        low_temp_sensitivity: Sensitivity to low temperature (0-1)
        frost_sensitivity: Sensitivity to frost (0-1)
        sterility_sensitivity: Sensitivity to sterility risk (0-1)
    """
    stage_name: str
    high_temp_sensitivity: float = 0.5
    low_temp_sensitivity: float = 0.5
    frost_sensitivity: float = 0.7
    sterility_sensitivity: float = 0.9  # High for reproductive stages


class YieldImpactCalculator:
    """Calculator for yield impact based on temperature stress.
    
    This calculator uses accumulated stress days and stage-specific
    sensitivity coefficients to estimate yield reduction factor.
    
    Based on literature:
    - High temperature stress: ~5% reduction per day (Porter & Gawith, 1999)
    - Low temperature stress: ~8% reduction per day
    - Frost damage: ~15% reduction per day
    - Sterility risk: ~20% reduction per day (Matsui et al., 2001)
    """
    
    # Daily impact rates (from literature)
    HIGH_TEMP_DAILY_IMPACT = 0.05  # 5% per day
    LOW_TEMP_DAILY_IMPACT = 0.08   # 8% per day
    FROST_DAILY_IMPACT = 0.15      # 15% per day
    STERILITY_DAILY_IMPACT = 0.20  # 20% per day
    
    def __init__(self, stage_sensitivities: Dict[str, StageSensitivity]):
        """Initialize calculator with stage sensitivities.
        
        Args:
            stage_sensitivities: Dictionary mapping stage names to sensitivity objects
        """
        self.stage_sensitivities = stage_sensitivities
    
    def calculate_yield_factor(
        self,
        stress_accumulator: StressAccumulator
    ) -> float:
        """Calculate yield factor (0-1) based on accumulated stress.
        
        Args:
            stress_accumulator: Accumulated stress data
            
        Returns:
            Yield factor (1.0 = no impact, 0.0 = complete loss)
        """
        yield_factor = 1.0
        
        # High temperature stress impact
        for stage, days in stress_accumulator.high_temp_stress_days.items():
            sensitivity = self._get_sensitivity(stage, 'high_temp')
            impact = 1.0 - (self.HIGH_TEMP_DAILY_IMPACT * days * sensitivity)
            yield_factor *= max(impact, 0.0)
        
        # Low temperature stress impact
        for stage, days in stress_accumulator.low_temp_stress_days.items():
            sensitivity = self._get_sensitivity(stage, 'low_temp')
            impact = 1.0 - (self.LOW_TEMP_DAILY_IMPACT * days * sensitivity)
            yield_factor *= max(impact, 0.0)
        
        # Frost damage impact (more severe)
        for stage, days in stress_accumulator.frost_days.items():
            sensitivity = self._get_sensitivity(stage, 'frost')
            impact = 1.0 - (self.FROST_DAILY_IMPACT * days * sensitivity)
            yield_factor *= max(impact, 0.0)
        
        # Sterility risk impact (most severe for reproductive stages)
        total_sterility_days = sum(stress_accumulator.sterility_risk_days.values())
        if total_sterility_days > 0:
            # Sterility has catastrophic impact on yield
            sterility_impact = self.STERILITY_DAILY_IMPACT * total_sterility_days
            yield_factor *= max(1.0 - sterility_impact, 0.0)
        
        return yield_factor
    
    def _get_sensitivity(self, stage_name: str, stress_type: str) -> float:
        """Get sensitivity coefficient for a stage and stress type.
        
        Args:
            stage_name: Name of growth stage
            stress_type: One of 'high_temp', 'low_temp', 'frost', 'sterility'
            
        Returns:
            Sensitivity coefficient (0-1)
        """
        stage_sensitivity = self.stage_sensitivities.get(stage_name)
        
        if stage_sensitivity is None:
            # Default sensitivity if stage not found
            return 0.5
        
        sensitivity_map = {
            'high_temp': stage_sensitivity.high_temp_sensitivity,
            'low_temp': stage_sensitivity.low_temp_sensitivity,
            'frost': stage_sensitivity.frost_sensitivity,
            'sterility': stage_sensitivity.sterility_sensitivity,
        }
        
        return sensitivity_map.get(stress_type, 0.5)
    
    def get_detailed_impact_breakdown(
        self,
        stress_accumulator: StressAccumulator
    ) -> Dict[str, float]:
        """Get detailed breakdown of yield impact by stress type.
        
        Args:
            stress_accumulator: Accumulated stress data
            
        Returns:
            Dictionary with impact factors for each stress type
        """
        breakdown = {}
        
        # Calculate individual impacts
        high_temp_factor = self._calculate_stress_type_factor(
            stress_accumulator.high_temp_stress_days,
            'high_temp',
            self.HIGH_TEMP_DAILY_IMPACT
        )
        
        low_temp_factor = self._calculate_stress_type_factor(
            stress_accumulator.low_temp_stress_days,
            'low_temp',
            self.LOW_TEMP_DAILY_IMPACT
        )
        
        frost_factor = self._calculate_stress_type_factor(
            stress_accumulator.frost_days,
            'frost',
            self.FROST_DAILY_IMPACT
        )
        
        # Sterility impact
        total_sterility_days = sum(stress_accumulator.sterility_risk_days.values())
        sterility_factor = max(
            1.0 - (self.STERILITY_DAILY_IMPACT * total_sterility_days),
            0.0
        )
        
        return {
            'high_temp_factor': high_temp_factor,
            'low_temp_factor': low_temp_factor,
            'frost_factor': frost_factor,
            'sterility_factor': sterility_factor,
            'combined_factor': high_temp_factor * low_temp_factor * frost_factor * sterility_factor
        }
    
    def _calculate_stress_type_factor(
        self,
        stress_days: Dict[str, int],
        stress_type: str,
        daily_impact: float
    ) -> float:
        """Calculate yield factor for a specific stress type.
        
        Returns:
            Yield factor for this stress type (0-1)
        """
        factor = 1.0
        for stage, days in stress_days.items():
            sensitivity = self._get_sensitivity(stage, stress_type)
            impact = 1.0 - (daily_impact * days * sensitivity)
            factor *= max(impact, 0.0)
        return factor


def create_default_rice_sensitivities() -> Dict[str, StageSensitivity]:
    """Create default sensitivity coefficients for rice (Oryza sativa).
    
    Based on literature (Matsui et al., 2001; Satake & Hayase, 1970)
    """
    return {
        'germination': StageSensitivity(
            stage_name='germination',
            high_temp_sensitivity=0.2,
            low_temp_sensitivity=0.3,
            frost_sensitivity=0.5,
            sterility_sensitivity=0.0,
        ),
        'vegetative': StageSensitivity(
            stage_name='vegetative',
            high_temp_sensitivity=0.3,
            low_temp_sensitivity=0.2,
            frost_sensitivity=0.6,
            sterility_sensitivity=0.0,
        ),
        'reproductive': StageSensitivity(
            stage_name='reproductive',
            high_temp_sensitivity=0.9,  # High sensitivity to high temp
            low_temp_sensitivity=0.9,   # High sensitivity to low temp
            frost_sensitivity=0.9,
            sterility_sensitivity=0.9,  # Critical stage
        ),
        'grain_filling': StageSensitivity(
            stage_name='grain_filling',
            high_temp_sensitivity=0.7,
            low_temp_sensitivity=0.4,
            frost_sensitivity=0.7,
            sterility_sensitivity=0.0,
        ),
        'maturity': StageSensitivity(
            stage_name='maturity',
            high_temp_sensitivity=0.3,
            low_temp_sensitivity=0.1,
            frost_sensitivity=0.3,
            sterility_sensitivity=0.0,
        ),
    }
```

---

## 5. 統合例: 最適化での使用

### 5.1 収益計算への統合

```python
"""Integration example: Using yield factor in optimization."""

class CandidateResultDTO:
    """Candidate result with yield impact."""
    
    def get_metrics(self) -> OptimizationMetrics:
        """Get optimization metrics with yield impact applied."""
        
        # Calculate base revenue
        base_revenue_per_area = self.crop.revenue_per_area
        
        # Apply yield factor from temperature stress
        adjusted_revenue_per_area = None
        if base_revenue_per_area is not None and self.yield_factor is not None:
            adjusted_revenue_per_area = base_revenue_per_area * self.yield_factor
        
        # Apply interaction impact (continuous cultivation)
        if adjusted_revenue_per_area is not None:
            adjusted_revenue_per_area *= self.interaction_impact
        
        # Calculate max revenue with yield factor
        adjusted_max_revenue = None
        if self.crop.max_revenue is not None and self.yield_factor is not None:
            adjusted_max_revenue = self.crop.max_revenue * self.yield_factor
            if self.interaction_impact != 1.0:
                adjusted_max_revenue *= self.interaction_impact
        
        return OptimizationMetrics(
            area_used=self.area_used,
            revenue_per_area=adjusted_revenue_per_area,
            max_revenue=adjusted_max_revenue,
            growth_days=self.growth_days,
            daily_fixed_cost=self.field.daily_fixed_cost,
        )
```

---

## 6. 使用例

### 6.1 基本的な使用例

```python
"""Example: Calculate growth progress with temperature stress impact."""

# Step 1: Configure temperature profile with modified GDD
rice_temp_profile = TemperatureProfile(
    base_temperature=10.0,
    optimal_min=25.0,
    optimal_max=30.0,
    max_temperature=42.0,
    low_stress_threshold=17.0,
    high_stress_threshold=35.0,
    frost_threshold=5.0,
    sterility_risk_threshold=35.0,
    use_modified_gdd=True,  # Enable modified GDD
)

# Step 2: Calculate growth progress with stress tracking
interactor = GrowthProgressCalculateInteractor(
    crop_profile_gateway=crop_gateway,
    weather_gateway=weather_gateway,
    enable_stress_tracking=True,
)

response = await interactor.execute(request)

# Step 3: Calculate yield impact
stage_sensitivities = create_default_rice_sensitivities()
yield_calculator = YieldImpactCalculator(stage_sensitivities)

yield_factor = yield_calculator.calculate_yield_factor(
    response.stress_accumulator
)

# Step 4: Apply to revenue
base_revenue = 5000000  # 500万円
adjusted_revenue = base_revenue * yield_factor

print(f"Base revenue: ¥{base_revenue:,}")
print(f"Yield factor: {yield_factor:.2%}")
print(f"Adjusted revenue: ¥{adjusted_revenue:,.0f}")
print(f"Revenue loss: ¥{base_revenue - adjusted_revenue:,.0f}")
```

---

## 7. まとめ

このドキュメントでは、温度ストレスモデルの具体的な実装例を示しました。

**実装の特徴**:
1. ✅ 後方互換性の維持（既存コードは動作継続）
2. ✅ 段階的な導入が可能（フラグで切り替え）
3. ✅ テスト可能な設計
4. ✅ 文献ベースのパラメータ

**次のステップ**:
- 実装のレビューと承認
- テストの追加
- ドキュメントの更新
- パフォーマンステストの実施

