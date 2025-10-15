# harvest_start_gdd ロールバック可能な実装設計

**作成日**: 2025-10-15  
**目的**: 新しい処理フローを後退しやすい形で実装

---

## 1. 設計原則

### 1.1 後退しやすさ（Rollback-Safe）の要件

1. ✅ **既存フローを残す**: 古い実装を削除しない
2. ✅ **設定で切り替え**: フィーチャーフラグで新旧を切り替え
3. ✅ **段階的移行**: 一部の機能だけ新フローを試せる
4. ✅ **影響範囲の限定**: 他のコマンドに影響を与えない
5. ✅ **簡単な無効化**: 設定変更だけで元に戻せる

---

## 2. 実装戦略: Strategy Pattern + Feature Flag

### 2.1 アーキテクチャ

```
┌───────────────────────────────────────────────────────────────┐
│ CropProfileCraftInteractor                                     │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ ResearchStrategy (Interface)                          │    │
│  └───────────────┬──────────────────────────────────────┘    │
│                  │                                             │
│    ┌─────────────┴──────────────┐                            │
│    │                              │                            │
│  ┌─▼──────────────┐  ┌──────────▼────────────────┐          │
│  │ SinglePrompt   │  │ MultiPromptStrategy         │          │
│  │ Strategy       │  │ (新フロー)                  │          │
│  │ (現行フロー)   │  │ - 収穫タイプ判定            │          │
│  └────────────────┘  │ - タイプ別プロンプト        │          │
│                       │ - 並列処理                  │          │
│                       └─────────────────────────────┘          │
└───────────────────────────────────────────────────────────────┘

設定ファイル or 環境変数で切り替え:
CROP_RESEARCH_STRATEGY=single  ← デフォルト（現行）
CROP_RESEARCH_STRATEGY=multi   ← 新フロー
```

---

## 3. 実装詳細

### 3.1 Strategy Interface

**ファイル**: `src/agrr_core/usecase/strategies/stage_research_strategy.py`

```python
"""Strategy pattern for stage requirement research."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class StageResearchStrategyInterface(ABC):
    """Interface for stage requirement research strategies.
    
    Allows switching between different research flows without breaking existing code.
    """
    
    @abstractmethod
    async def research_all_stages(
        self,
        crop_name: str,
        variety: Optional[str],
        growth_stages: List[Dict],
        crop_groups: List[str],
        gateway
    ) -> List[Dict[str, Any]]:
        """Research all stage requirements.
        
        Args:
            crop_name: Crop name
            variety: Optional variety name
            growth_stages: List of growth stage definitions
            crop_groups: List of crop group names (e.g., ["Solanaceae"])
            gateway: CropProfileGateway instance
            
        Returns:
            List of stage requirement data dictionaries (in order)
        """
        pass
```

---

### 3.2 Single Prompt Strategy（現行フロー）

**ファイル**: `src/agrr_core/usecase/strategies/single_prompt_strategy.py`

```python
"""Single prompt strategy - current implementation."""

from typing import List, Dict, Any, Optional
from agrr_core.usecase.strategies.stage_research_strategy import StageResearchStrategyInterface
from agrr_core.usecase.services.llm_response_normalizer import LLMResponseNormalizer


class SinglePromptStrategy(StageResearchStrategyInterface):
    """Current implementation: use stage3 prompt for all stages.
    
    This is the default strategy that maintains backward compatibility.
    """
    
    async def research_all_stages(
        self,
        crop_name: str,
        variety: Optional[str],
        growth_stages: List[Dict],
        crop_groups: List[str],
        gateway
    ) -> List[Dict[str, Any]]:
        """Research stages sequentially using single prompt (current flow)."""
        results = []
        
        for stage in growth_stages:
            stage_name = LLMResponseNormalizer.normalize_stage_name(stage)
            stage_description = LLMResponseNormalizer.normalize_stage_description(stage)
            
            # Use current stage3 prompt for all stages
            result = await gateway.research_stage_requirements(
                crop_name, variety, stage_name, stage_description
            )
            results.append(result)
        
        return results
```

**ポイント**: 既存のコードをそのまま移行。変更なし。

---

### 3.3 Multi Prompt Strategy（新フロー）

**ファイル**: `src/agrr_core/usecase/strategies/multi_prompt_strategy.py`

```python
"""Multi prompt strategy - new implementation with parallel execution."""

import asyncio
from typing import List, Dict, Any, Optional
from agrr_core.usecase.strategies.stage_research_strategy import StageResearchStrategyInterface
from agrr_core.usecase.services.llm_response_normalizer import LLMResponseNormalizer


class MultiPromptStrategy(StageResearchStrategyInterface):
    """New implementation: classify harvest type and use specialized prompts.
    
    Flow:
    1. Classify harvest type (continuous vs single) using lightweight LLM
    2. Use specialized prompts for harvest stages
    3. Execute all stage research in parallel
    """
    
    async def research_all_stages(
        self,
        crop_name: str,
        variety: Optional[str],
        growth_stages: List[Dict],
        crop_groups: List[str],
        gateway
    ) -> List[Dict[str, Any]]:
        """Research stages in parallel with type-specific prompts."""
        
        # Step 1: Classify harvest type (if harvest stage exists)
        harvest_type = await self._classify_harvest_type_if_needed(
            crop_name, variety, growth_stages, gateway
        )
        
        # Step 2: Create tasks for parallel execution
        tasks = []
        for stage in growth_stages:
            stage_name = LLMResponseNormalizer.normalize_stage_name(stage)
            stage_description = LLMResponseNormalizer.normalize_stage_description(stage)
            
            if self._is_harvest_stage(stage_name):
                # Use specialized harvest prompt
                if harvest_type == "continuous":
                    task = gateway.research_continuous_harvest_stage(
                        crop_name, variety, stage_name, stage_description
                    )
                else:
                    task = gateway.research_single_harvest_stage(
                        crop_name, variety, stage_name, stage_description
                    )
            else:
                # Use standard stage3 prompt
                task = gateway.research_stage_requirements(
                    crop_name, variety, stage_name, stage_description
                )
            
            tasks.append(task)
        
        # Step 3: Execute all in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Step 4: Handle errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                raise RuntimeError(f"Stage {i+1} research failed: {result}")
        
        return results
    
    async def _classify_harvest_type_if_needed(
        self, crop_name, variety, growth_stages, gateway
    ) -> str:
        """Classify harvest type if harvest stage exists."""
        has_harvest = any(
            self._is_harvest_stage(LLMResponseNormalizer.normalize_stage_name(s))
            for s in growth_stages
        )
        
        if not has_harvest:
            return "single"  # Default
        
        # Call lightweight LLM for classification
        result = await gateway.classify_harvest_type(crop_name, variety)
        return result.get("harvest_type", "single")
    
    def _is_harvest_stage(self, stage_name: str) -> bool:
        """Check if stage is harvest stage."""
        harvest_keywords = ["harvest", "収穫", "maturity", "成熟", "登熟"]
        return any(k in stage_name.lower() for k in harvest_keywords)
```

---

### 3.4 Strategy Factory

**ファイル**: `src/agrr_core/usecase/strategies/stage_research_strategy_factory.py`

```python
"""Factory for creating stage research strategies."""

from typing import Optional
from agrr_core.usecase.strategies.stage_research_strategy import StageResearchStrategyInterface
from agrr_core.usecase.strategies.single_prompt_strategy import SinglePromptStrategy
from agrr_core.usecase.strategies.multi_prompt_strategy import MultiPromptStrategy


class StageResearchStrategyFactory:
    """Factory for creating stage research strategies.
    
    Allows easy switching between strategies via configuration.
    """
    
    _strategies = {
        "single": SinglePromptStrategy,
        "multi": MultiPromptStrategy,
    }
    
    @classmethod
    def create(cls, strategy_name: str = "single") -> StageResearchStrategyInterface:
        """Create strategy instance by name.
        
        Args:
            strategy_name: "single" (default) or "multi"
            
        Returns:
            Strategy instance
            
        Raises:
            ValueError: If strategy_name is unknown
        """
        if strategy_name not in cls._strategies:
            raise ValueError(
                f"Unknown strategy: {strategy_name}. "
                f"Available: {list(cls._strategies.keys())}"
            )
        
        return cls._strategies[strategy_name]()
    
    @classmethod
    def register_strategy(
        cls, name: str, strategy_class: type
    ) -> None:
        """Register custom strategy (for testing or extensions).
        
        Args:
            name: Strategy name
            strategy_class: Strategy class (must implement StageResearchStrategyInterface)
        """
        cls._strategies[name] = strategy_class
```

---

### 3.5 Interactor の更新

**ファイル**: `src/agrr_core/usecase/interactors/crop_profile_craft_interactor.py`

```python
from agrr_core.usecase.strategies.stage_research_strategy_factory import StageResearchStrategyFactory

class CropProfileCraftInteractor:
    def __init__(
        self,
        gateway: CropProfileGatewayInterface,
        presenter: CropProfileCraftOutputPort,
        research_strategy: str = "single"  # ← デフォルトは現行フロー
    ):
        self.gateway = gateway
        self.presenter = presenter
        # Strategy pattern で切り替え可能に
        self.strategy = StageResearchStrategyFactory.create(research_strategy)
    
    async def execute(self, request: CropProfileCraftRequestDTO):
        # ... 既存の処理 ...
        
        # Strategy patternを使用
        stage_results = await self.strategy.research_all_stages(
            crop_name=crop_name,
            variety=variety,
            growth_stages=growth_stages,
            crop_groups=groups,
            gateway=self.gateway
        )
        
        # 以降は同じ処理
        stage_requirements = []
        for stage, stage_data in zip(growth_stages, stage_results):
            # ... Entityを構築 ...
            stage_requirements.append(stage_req)
        
        # ...
```

---

### 3.6 設定ファイル

**ファイル**: `src/agrr_core/config/crop_research_config.py`

```python
"""Configuration for crop research strategies."""

from typing import Literal

ResearchStrategyType = Literal["single", "multi"]


class CropResearchConfig:
    """Configuration for crop profile research."""
    
    # Feature flag for strategy selection
    RESEARCH_STRATEGY: ResearchStrategyType = "single"  # デフォルトは現行フロー（安全）
    
    # Optional: Enable/disable parallel execution (for multi strategy)
    ENABLE_PARALLEL_RESEARCH: bool = True
    
    # Optional: LLM model for harvest type classification
    HARVEST_TYPE_CLASSIFICATION_MODEL: str = "gpt-3.5-turbo"  # 軽量モデル


# 切り替えはこの定数を変更するだけ
# RESEARCH_STRATEGY = "single"  ← デフォルト（現行フロー）
# RESEARCH_STRATEGY = "multi"   ← 新フロー（harvest_start_gdd精度向上）
```

---

## 4. ロールバック戦略

### 4.1 切り替え方法

#### 新フローを試す:
```python
# src/agrr_core/config/crop_research_config.py
class CropResearchConfig:
    RESEARCH_STRATEGY = "multi"  # ← この1行を変更するだけ
```

#### 元に戻す:
```python
# src/agrr_core/config/crop_research_config.py
class CropResearchConfig:
    RESEARCH_STRATEGY = "single"  # ← 元に戻す
```

#### Containerでの使用:
```python
# Framework層のContainer
from agrr_core.config.crop_research_config import CropResearchConfig

class AgrrCoreContainer:
    def get_crop_profile_craft_interactor(self):
        return CropProfileCraftInteractor(
            gateway=self.get_crop_profile_gateway(),
            presenter=self.get_crop_profile_presenter(),
            research_strategy=CropResearchConfig.RESEARCH_STRATEGY  # ← 定数を使用
        )
```

---

### 4.2 段階的移行計画

```
Phase 1: 実装（両方のStrategyが動作）
  ├─ SinglePromptStrategy（既存コードそのまま）
  └─ MultiPromptStrategy（新実装）
  デフォルト: single ← 安全

Phase 2: テスト期間（新フローを試す）
  デフォルト: single
  テスト時のみ: multi
  問題があれば即座にsingleに戻す

Phase 3: 新フローが安定したら
  デフォルト: multi
  フォールバック: single（残しておく）

Phase 4: 移行完了後（6ヶ月後）
  デフォルト: multi
  オプション: singleを削除可能（完全に不要になったら）
```

---

### 4.3 問題発生時の対応

| 問題 | 対応 | 所要時間 |
|-----|------|---------|
| 新フローでエラー | `CropResearchConfig.RESEARCH_STRATEGY = "single"` | 即座 |
| 特定の作物だけエラー | その作物だけsingle使用 | 5分 |
| harvest_start_gddが不正 | 定数を"single"に戻す | 即座 |
| 並列処理でタイムアウト | `ENABLE_PARALLEL_RESEARCH = False` | 即座 |

---

## 5. 実装コード

### 5.1 ディレクトリ構造

```
src/agrr_core/
├── usecase/
│   ├── strategies/                    # 新規ディレクトリ
│   │   ├── __init__.py
│   │   ├── stage_research_strategy.py          # Interface
│   │   ├── single_prompt_strategy.py           # 現行フロー
│   │   ├── multi_prompt_strategy.py            # 新フロー
│   │   └── stage_research_strategy_factory.py  # Factory
│   └── interactors/
│       └── crop_profile_craft_interactor.py    # Strategy使用
├── config/
│   └── crop_research_config.py        # 設定
└── prompts/                            # 既存
    ├── stage3_variety_specific_research.md     # 既存（変更なし）
    ├── stage0_harvest_type_classification.md   # 新規
    ├── stage3_continuous_harvest.md            # 新規
    └── stage3_single_harvest.md                # 新規
```

---

### 5.2 Interactor の変更（最小限）

```python
class CropProfileCraftInteractor:
    def __init__(
        self,
        gateway: CropProfileGatewayInterface,
        presenter: CropProfileCraftOutputPort,
        research_strategy: str = "single"  # デフォルトは現行
    ):
        self.gateway = gateway
        self.presenter = presenter
        self.strategy = StageResearchStrategyFactory.create(research_strategy)
    
    async def execute(self, request: CropProfileCraftRequestDTO):
        # ... 既存の変数取得処理 ...
        
        # ★ 唯一の変更箇所: 既存のループを Strategy に委譲
        stage_results = await self.strategy.research_all_stages(
            crop_name=crop_name,
            variety=variety,
            growth_stages=growth_stages,
            crop_groups=groups,
            gateway=self.gateway
        )
        
        # ★ ここから先は既存コードそのまま
        stage_requirements = []
        for i, (stage, stage_data) in enumerate(zip(growth_stages, stage_results)):
            # ... 既存のEntity構築コード（変更なし）...
            stage_requirements.append(stage_req)
        
        # ... 既存の返却処理 ...
```

**変更箇所**: たった10行程度！

---

## 6. テスト戦略

### 6.1 Strategy単体テスト

**ファイル**: `tests/test_usecase/test_strategies/test_single_prompt_strategy.py`

```python
@pytest.mark.asyncio
async def test_single_prompt_strategy_maintains_current_behavior():
    """Test that SinglePromptStrategy behaves exactly like current implementation."""
    strategy = SinglePromptStrategy()
    gateway = AsyncMock()
    
    gateway.research_stage_requirements.return_value = {
        "thermal": {"required_gdd": 400.0},
        # ... other fields ...
    }
    
    stages = [{"name": "Vegetative", "order": 1}]
    results = await strategy.research_all_stages(
        "tomato", None, stages, [], gateway
    )
    
    assert len(results) == 1
    assert results[0]["thermal"]["required_gdd"] == 400.0
    gateway.research_stage_requirements.assert_called_once()
```

**ファイル**: `tests/test_usecase/test_strategies/test_multi_prompt_strategy.py`

```python
@pytest.mark.asyncio
async def test_multi_prompt_strategy_classifies_harvest_type():
    """Test that MultiPromptStrategy classifies harvest type."""
    strategy = MultiPromptStrategy()
    gateway = AsyncMock()
    
    # Mock harvest type classification
    gateway.classify_harvest_type.return_value = {
        "harvest_type": "continuous"
    }
    
    # Mock harvest stage research
    gateway.research_continuous_harvest_stage.return_value = {
        "thermal": {
            "required_gdd": 2000.0,
            "harvest_start_gdd": 200.0
        },
        # ...
    }
    
    stages = [{"name": "Harvest", "order": 1}]
    results = await strategy.research_all_stages(
        "eggplant", None, stages, ["Solanaceae"], gateway
    )
    
    assert len(results) == 1
    assert results[0]["thermal"]["required_gdd"] == 2000.0
    assert results[0]["thermal"]["harvest_start_gdd"] == 200.0
    gateway.classify_harvest_type.assert_called_once()
    gateway.research_continuous_harvest_stage.assert_called_once()
```

---

### 6.2 Interactor統合テスト

```python
@pytest.mark.asyncio
async def test_interactor_with_single_strategy():
    """Test interactor with single prompt strategy (current)."""
    interactor = CropProfileCraftInteractor(
        gateway=mock_gateway,
        presenter=mock_presenter,
        research_strategy="single"  # ← 明示的に指定
    )
    result = await interactor.execute(request)
    # ... assertions ...

@pytest.mark.asyncio
async def test_interactor_with_multi_strategy():
    """Test interactor with multi prompt strategy (new)."""
    interactor = CropProfileCraftInteractor(
        gateway=mock_gateway,
        presenter=mock_presenter,
        research_strategy="multi"  # ← 新フロー
    )
    result = await interactor.execute(request)
    # ... assertions ...
```

---

## 7. ロールバックシナリオ

### 7.1 シナリオ1: harvest_start_gddの精度が低い

**対応**:
```python
# src/agrr_core/config/crop_research_config.py
class CropResearchConfig:
    RESEARCH_STRATEGY = "single"  # ← この1行を変更
```

**影響**: ゼロ（元の動作に戻る）

---

### 7.2 シナリオ2: 並列処理でタイムアウト

**対応**:
```python
# src/agrr_core/config/crop_research_config.py
class CropResearchConfig:
    RESEARCH_STRATEGY = "single"  # ← 元に戻す
```

**影響**: ゼロ

---

### 7.3 シナリオ3: 特定の作物だけ問題がある

**対応**:
```python
# Interactor内で作物ごとに戦略を切り替え
async def execute(self, request):
    # 特定の作物は旧フローを使う
    if request.crop_query in ["問題のある作物"]:
        strategy = SinglePromptStrategy()
    else:
        strategy = self.strategy  # デフォルト戦略を使用
    
    # ...
```

**影響**: 問題のある作物のみ旧フローに戻る

---

## 8. 実装チェックリスト

### Phase 1: Strategy Pattern基盤（2-3時間）

- [ ] `stage_research_strategy.py` Interface作成
- [ ] `single_prompt_strategy.py` 既存コード移行
- [ ] `stage_research_strategy_factory.py` Factory作成
- [ ] `crop_research_config.py` 設定ファイル作成
- [ ] Interactorを Strategy使用に変更（最小限）
- [ ] 既存テストが全て通過することを確認

**ゴール**: 既存の動作を壊さずにStrategy Patternを導入

---

### Phase 2: 新プロンプトの作成（2-3時間）

- [ ] `stage0_harvest_type_classification.md`
- [ ] `stage3_continuous_harvest.md`  
- [ ] `stage3_single_harvest.md`
- [ ] プロンプトのレビューとテスト

---

### Phase 3: Multi Prompt Strategy実装（3-4時間）

- [ ] `multi_prompt_strategy.py` 実装
- [ ] Gateway層に新メソッド追加
  - [ ] `classify_harvest_type()`
  - [ ] `research_continuous_harvest_stage()`
  - [ ] `research_single_harvest_stage()`
- [ ] Repository層に実装追加

---

### Phase 4: 並列処理の実装（2-3時間）

- [ ] `asyncio.gather()` による並列実行
- [ ] エラーハンドリング
- [ ] タイムアウト処理

---

### Phase 5: テスト（3-4時間）

- [ ] Strategy単体テスト（各5-10個）
- [ ] Interactor統合テスト
- [ ] E2Eテスト（CLI経由）
- [ ] 性能テスト（並列効果の測定）

---

### Phase 6: ドキュメントと移行（1-2時間）

- [ ] 使用方法ドキュメント
- [ ] ロールバック手順
- [ ] 移行計画

---

## 9. ロールバックの容易さ

### 9.1 コード変更が必要な箇所

**Interactor**: 1箇所のみ
```python
# Before
for stage in growth_stages:
    result = await self.gateway.research_stage_requirements(...)

# After  
results = await self.strategy.research_all_stages(...)
```

**ロールバック**: Strategyを`single`にするだけ

---

### 9.2 完全ロールバック（全削除）の容易さ

もし新フローが完全に不要になった場合：

**削除するファイル**:
- `src/agrr_core/usecase/strategies/` ディレクトリ全体
- `prompts/stage0_*`, `stage3_continuous_*`, `stage3_single_*`
- 該当テストファイル

**Interactorを元に戻す**:
```python
# Strategyを使わない元のコードに戻すだけ
```

**影響**: ゼロ（既存の動作に完全に戻る）

---

## 10. まとめ

### 10.1 後退しやすい理由

1. ✅ **Strategy Pattern**: 既存コードを削除せず、選択可能に
2. ✅ **Feature Flag**: 設定で即座に切り替え可能
3. ✅ **デフォルトは安全**: 既存フローがデフォルト
4. ✅ **完全分離**: 新フローは独立したファイル
5. ✅ **段階的移行**: 一部の作物だけ新フロー適用可能

### 10.2 実装規模

**総工数**: 13-19時間
**新規ファイル**: 7個
**変更ファイル**: 3個（最小限）
**削除**: ゼロ

### 10.3 リスク管理

| リスク | 軽減策 | ロールバック時間 |
|--------|--------|-----------------|
| 新フロー失敗 | デフォルトsingle | 即座（環境変数） |
| 並列処理エラー | タイムアウト設定 | 即座 |
| harvest_start_gdd精度低下 | singleに切り替え | 即座 |
| 完全撤退が必要 | ファイル削除のみ | 1時間 |

---

**次のステップ**: Phase 1（Strategy Pattern基盤）から実装を開始しますか？

