# max_temperature パラメータの代替案分析
**作成日**: 2025-10-14  
**目的**: `max_temperature`を既存パラメータから推定し、パラメータ数を削減

---

## 1. 問題提起

現在の提案では、温度プロファイルに`max_temperature`（発育停止温度）という新しいパラメータを追加しています。

**既存パラメータ**:
- `base_temperature`: GDD基準温度（下限）
- `optimal_min`, `optimal_max`: 最適温度範囲
- `low_stress_threshold`: 低温ストレス閾値
- `high_stress_threshold`: 高温ストレス閾値 ← **これを使えないか？**
- `frost_threshold`: 霜害閾値
- `sterility_risk_threshold`: 不稔リスク閾値（オプション）

**課題**:
- パラメータが増えるとLLMの負担が増える
- 既存のデータに`max_temperature`がない
- 新しいパラメータの推定が必要

---

## 2. 文献分析：high_stress_threshold と max_temperature の関係

### 2.1 主要作物のデータ

| 作物 | high_stress | max_temp | 差分 | 比率 |
|------|-------------|----------|------|------|
| イネ | 35°C | 42°C | +7°C | 1.20 |
| 小麦 | 30°C | 35°C | +5°C | 1.17 |
| トマト | 32°C | 35°C | +3°C | 1.09 |
| トウモロコシ | 35°C | 40°C | +5°C | 1.14 |
| 大豆 | 35°C | 40°C | +5°C | 1.14 |

**平均**: +5°C (範囲: 3-7°C)  
**比率平均**: 1.15 (範囲: 1.09-1.20)

### 2.2 生理学的根拠

**高温ストレス閾値 (high_stress_threshold)**:
- 光合成速度が低下し始める温度
- 生育が遅延するが、完全には停止しない
- ストレス応答が活性化される

**発育停止温度 (max_temperature)**:
- 酵素活動が失活する温度
- 細胞膜が損傷し始める温度
- 生育が完全に停止する

**関係性**:
```
high_stress_threshold < max_temperature
通常の差: 5-10°C
```

---

## 3. 推奨する代替実装

### 案1: オプショナルパラメータ + 自動推定（推奨）⭐

```python
@dataclass(frozen=True)
class TemperatureProfile:
    """Temperature thresholds for a crop at a given growth stage."""
    
    base_temperature: float
    optimal_min: float
    optimal_max: float
    low_stress_threshold: float
    high_stress_threshold: float
    frost_threshold: float
    sterility_risk_threshold: Optional[float] = None
    
    # NEW: Optional parameter with automatic estimation
    max_temperature: Optional[float] = None
    
    # Configuration for auto-estimation
    max_temp_offset: float = 7.0  # Default offset from high_stress_threshold
    
    def __post_init__(self):
        """Auto-estimate max_temperature if not provided."""
        if self.max_temperature is None:
            # Estimate: max_temp = high_stress + offset
            object.__setattr__(
                self, 
                'max_temperature', 
                self.high_stress_threshold + self.max_temp_offset
            )
    
    @property
    def effective_max_temperature(self) -> float:
        """Get effective maximum temperature (auto-estimated if not provided)."""
        if self.max_temperature is not None:
            return self.max_temperature
        return self.high_stress_threshold + self.max_temp_offset
```

**利点**:
- ✅ 既存のデータセットで動作（`max_temperature`未指定でOK）
- ✅ LLMの負担軽減（オプションなので省略可能）
- ✅ 精度が必要な場合は明示的に指定可能
- ✅ デフォルト値が文献ベース

**欠点**:
- △ 自動推定は完璧ではない（±2°C程度の誤差）

---

### 案2: 完全に自動計算（シンプル）

```python
@dataclass(frozen=True)
class TemperatureProfile:
    """Temperature thresholds for a crop at a given growth stage."""
    
    base_temperature: float
    optimal_min: float
    optimal_max: float
    low_stress_threshold: float
    high_stress_threshold: float
    frost_threshold: float
    sterility_risk_threshold: Optional[float] = None
    
    # NO max_temperature field - always calculated
    
    @property
    def max_temperature(self) -> float:
        """Maximum temperature (auto-calculated from high_stress_threshold).
        
        Formula: max_temp = high_stress_threshold + 7°C
        
        This is based on literature analysis showing that developmental
        arrest temperature is typically 5-10°C above stress threshold.
        """
        return self.high_stress_threshold + 7.0
```

**利点**:
- ✅ 最もシンプル
- ✅ パラメータ数が増えない
- ✅ LLMの負担ゼロ

**欠点**:
- ✗ 柔軟性がない（固定オフセット）
- ✗ 作物による違いを考慮できない

---

### 案3: 作物タイプ別の自動推定（高度）

```python
@dataclass(frozen=True)
class TemperatureProfile:
    """Temperature thresholds for a crop at a given growth stage."""
    
    base_temperature: float
    optimal_min: float
    optimal_max: float
    low_stress_threshold: float
    high_stress_threshold: float
    frost_threshold: float
    sterility_risk_threshold: Optional[float] = None
    crop_type: str = "general"  # "rice", "wheat", "vegetable", etc.
    
    # Offset table by crop type
    CROP_TYPE_OFFSETS = {
        "rice": 7.0,
        "wheat": 5.0,
        "maize": 5.0,
        "soybean": 5.0,
        "vegetable": 3.0,
        "general": 6.0,
    }
    
    @property
    def max_temperature(self) -> float:
        """Maximum temperature (auto-calculated with crop-specific offset)."""
        offset = self.CROP_TYPE_OFFSETS.get(self.crop_type, 6.0)
        return self.high_stress_threshold + offset
```

**利点**:
- ✅ 作物タイプごとに精度向上
- ✅ LLMは crop_type だけ指定すればOK

**欠点**:
- △ crop_type の分類が必要
- △ やや複雑

---

## 4. 推奨実装（案1の詳細）

### 4.1 完全な実装例

```python
"""Enhanced temperature profile with optional max_temperature."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TemperatureProfile:
    """Temperature thresholds for a crop at a given growth stage.
    
    Enhanced with optional max_temperature that auto-estimates if not provided.
    """
    
    base_temperature: float  # GDD base (T_base)
    optimal_min: float       # Lower optimal temperature
    optimal_max: float       # Upper optimal temperature
    low_stress_threshold: float
    high_stress_threshold: float
    frost_threshold: float
    sterility_risk_threshold: Optional[float] = None
    
    # Optional: Specify if precise value is known
    max_temperature: Optional[float] = None
    
    # Configuration: Offset for auto-estimation
    # Based on literature: max_temp = high_stress + 5-10°C
    max_temp_offset: float = 7.0  # Conservative default
    
    # Flag to enable modified GDD calculation
    use_modified_gdd: bool = False
    
    def get_max_temperature(self) -> float:
        """Get maximum temperature (auto-estimated if not provided).
        
        Returns:
            Maximum temperature in °C
        """
        if self.max_temperature is not None:
            return self.max_temperature
        return self.high_stress_threshold + self.max_temp_offset
    
    def daily_gdd(self, t_mean: Optional[float]) -> float:
        """Return daily growing degree days.
        
        Switches between linear and modified models based on configuration.
        """
        if self.use_modified_gdd:
            return self.daily_gdd_modified(t_mean)
        else:
            return self.daily_gdd_linear(t_mean)
    
    def daily_gdd_linear(self, t_mean: Optional[float]) -> float:
        """Return daily GDD using linear model (original)."""
        if t_mean is None:
            return 0.0
        delta = t_mean - self.base_temperature
        return delta if delta > 0 else 0.0
    
    def daily_gdd_modified(self, t_mean: Optional[float]) -> float:
        """Return daily GDD with temperature efficiency (trapezoidal).
        
        Uses get_max_temperature() for upper limit.
        """
        if t_mean is None:
            return 0.0
        
        max_temp = self.get_max_temperature()
        
        # Outside viable temperature range
        if t_mean <= self.base_temperature or t_mean >= max_temp:
            return 0.0
        
        # Base GDD
        base_gdd = t_mean - self.base_temperature
        
        # Calculate efficiency
        efficiency = self._calculate_temperature_efficiency(t_mean, max_temp)
        
        return base_gdd * efficiency
    
    def _calculate_temperature_efficiency(
        self, 
        t_mean: float, 
        max_temp: float
    ) -> float:
        """Calculate temperature efficiency using trapezoidal function."""
        # Optimal range: full efficiency
        if self.optimal_min <= t_mean <= self.optimal_max:
            return 1.0
        
        # Sub-optimal (cool side)
        elif self.base_temperature < t_mean < self.optimal_min:
            efficiency = (t_mean - self.base_temperature) / \
                        (self.optimal_min - self.base_temperature)
            return max(0.0, min(1.0, efficiency))
        
        # Sub-optimal (warm side)
        elif self.optimal_max < t_mean < max_temp:
            efficiency = (max_temp - t_mean) / \
                        (max_temp - self.optimal_max)
            return max(0.0, min(1.0, efficiency))
        
        # Outside range
        else:
            return 0.0
```

### 4.2 使用例

#### パターンA: max_temperature を指定しない（簡単）

```python
# LLMが提供するパラメータ（max_temperature なし）
rice_profile = TemperatureProfile(
    base_temperature=10.0,
    optimal_min=25.0,
    optimal_max=30.0,
    low_stress_threshold=17.0,
    high_stress_threshold=35.0,
    frost_threshold=5.0,
    sterility_risk_threshold=35.0,
    use_modified_gdd=True,
)

# 自動推定: max_temperature = 35 + 7 = 42°C
print(rice_profile.get_max_temperature())  # 42.0
```

#### パターンB: max_temperature を明示的に指定（精密）

```python
# より精密な値が必要な場合
tomato_profile = TemperatureProfile(
    base_temperature=10.0,
    optimal_min=20.0,
    optimal_max=25.0,
    low_stress_threshold=15.0,
    high_stress_threshold=32.0,
    frost_threshold=2.0,
    max_temperature=35.0,  # 明示的に指定
    use_modified_gdd=True,
)

print(tomato_profile.get_max_temperature())  # 35.0 (指定値)
```

#### パターンC: オフセットをカスタマイズ

```python
# 作物特性に応じてオフセット調整
wheat_profile = TemperatureProfile(
    base_temperature=0.0,
    optimal_min=15.0,
    optimal_max=24.0,
    low_stress_threshold=5.0,
    high_stress_threshold=30.0,
    frost_threshold=-5.0,
    max_temp_offset=5.0,  # 小麦は差が小さい
    use_modified_gdd=True,
)

print(wheat_profile.get_max_temperature())  # 35.0 (30 + 5)
```

---

## 5. 精度評価

### 5.1 自動推定の精度

| 作物 | 実際のmax_temp | high_stress | 推定値(+7°C) | 誤差 |
|------|---------------|-------------|-------------|------|
| イネ | 42°C | 35°C | 42°C | 0°C ✓ |
| 小麦 | 35°C | 30°C | 37°C | +2°C |
| トマト | 35°C | 32°C | 39°C | +4°C |
| トウモロコシ | 40°C | 35°C | 42°C | +2°C |
| 大豆 | 40°C | 35°C | 42°C | +2°C |

**平均誤差**: ±2°C  
**最大誤差**: 4°C（トマト）

### 5.2 GDD計算への影響

40°C での GDD計算（イネ、base=10°C）:

| max_temp設定 | 効率 | GDD | 備考 |
|-------------|------|-----|------|
| 42°C（正確） | 0.17 | 5.0 | 正確な値 |
| 42°C（推定+7） | 0.17 | 5.0 | ✓ 完全一致 |
| 37°C（推定+7、小麦） | 0.0 | 0.0 | やや過小評価 |

**結論**: 
- イネ、トウモロコシ、大豆 → +7°Cで十分な精度
- 小麦、トマトなどの野菜 → やや過大評価だが、安全側の推定

---

## 6. 推奨される実装戦略

### Phase 1: オプショナル実装（推奨）

```python
# Step 1: TemperatureProfile に get_max_temperature() 追加
# Step 2: daily_gdd_modified() で get_max_temperature() 使用
# Step 3: 既存のJSONデータは変更不要
# Step 4: 必要に応じて max_temperature を明示的に追加
```

**メリット**:
1. ✅ 既存データとの互換性100%
2. ✅ LLMの負担最小（オプション）
3. ✅ 段階的な精度向上が可能
4. ✅ 後方互換性の維持

### Phase 2: 作物タイプ別オフセット（オプション）

```python
# 精度が必要な場合のみ実装
# crop_type フィールドを追加
# オフセット表を整備
```

---

## 7. 実装の影響範囲

### 7.1 変更が必要なファイル

```
src/agrr_core/entity/entities/temperature_profile_entity.py
├─ get_max_temperature() メソッド追加
├─ daily_gdd_modified() で使用
└─ [変更規模: 小]

docs/TEMPERATURE_STRESS_MODEL_RESEARCH.md
├─ max_temperature がオプションであることを明記
└─ [変更規模: 小]

docs/TEMPERATURE_STRESS_IMPLEMENTATION_EXAMPLE.md
├─ 実装例の更新
└─ [変更規模: 小]
```

### 7.2 変更が不要なファイル

- 既存のJSONデータファイル（変更不要）
- テストケース（追加のみ）
- UseCase層のコード（変更不要）

---

## 8. 結論と推奨事項

### 推奨: 案1（オプショナルパラメータ + 自動推定）⭐

**理由**:
1. ✅ **互換性**: 既存データで動作
2. ✅ **柔軟性**: 精度が必要な場合は指定可能
3. ✅ **簡便性**: LLMの負担軽減
4. ✅ **精度**: 平均±2°C、イネなどは完全一致
5. ✅ **安全性**: やや過大評価で安全側

### デフォルト設定の推奨

```python
# 保守的な設定（ほとんどの作物に適用）
max_temp_offset: float = 7.0

# 作物タイプ別の推奨オフセット（Phase 2以降）
RECOMMENDED_OFFSETS = {
    "cereals": 7.0,      # イネ、トウモロコシ、大豆
    "wheat": 5.0,        # 小麦類
    "vegetables": 4.0,   # トマト、ナス、ピーマン
    "general": 6.0,      # その他
}
```

### 次のアクション

1. ⬜ `TemperatureProfile` に `get_max_temperature()` を実装
2. ⬜ テストケースを追加
3. ⬜ ドキュメントを更新
4. ⬜ 既存のJSONデータは変更不要であることを確認

---

**結論**: `max_temperature` は **オプションパラメータ** として実装し、指定がない場合は `high_stress_threshold + 7°C` で自動推定することを強く推奨します。これにより、実装の複雑さを最小限に抑えつつ、必要な精度を確保できます。

