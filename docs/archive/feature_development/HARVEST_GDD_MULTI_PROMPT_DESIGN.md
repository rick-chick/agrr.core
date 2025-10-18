# harvest_start_gdd マルチプロンプト戦略設計

**作成日**: 2025-10-15  
**目的**: harvest_start_gddの精度向上のための包括的プロンプト戦略

---

## 1. 設計コンセプト

### 1.1 現在の問題

**単一プロンプトの限界**:
- required_gddとharvest_start_gddを同時に質問すると混乱
- 連続収穫と単収穫の違いが曖昧
- harvest_start_gdd < required_gddの制約が守られない

### 1.2 新しいアプローチ

**3段階プロンプト戦略**:

```
┌────────────────────────────────────────────────────────────────┐
│ Step 1: 収穫タイプ判定（軽量LLM）                               │
│ - 連続収穫 or 単収穫を判定                                      │
│ - 高速・低コスト                                                │
└──────────────┬─────────────────────┬────────────────────────────┘
               ↓                     ↓
    ┌──────────────────┐   ┌──────────────────────┐
    │ 連続収穫         │   │ 単収穫               │
    └──────┬───────────┘   └──────┬───────────────┘
           ↓                      ↓
┌────────────────────────┐ ┌────────────────────────┐
│ Step 2a: 連続収穫用     │ │ Step 2b: 単収穫用       │
│ - required_gdd         │ │ - required_gddのみ      │
│ - harvest_start_gdd    │ │                         │
│ （並列実行）           │ │ （並列実行）            │
└────────────────────────┘ └────────────────────────┘
```

---

## 2. プロンプト設計

### 2.1 Step 1: 収穫タイプ判定プロンプト

**ファイル**: `prompts/stage0_harvest_type_classification.md`

```markdown
# 収穫タイプ分類

作物: {作物名} {品種名}

この作物の収穫期ステージについて、以下のどちらに該当するか判定してください：

## 収穫タイプ

**連続収穫型（continuous）**:
- 長期間にわたって複数回収穫が可能
- 初回収穫から収穫終了まで数週間〜数ヶ月

**単回収穫型（single）**:
- 一度に収穫して栽培終了
- 成熟したら一斉に収穫

## 出力形式

```json
{
  "harvest_type": "continuous" または "single",
  "confidence": 0.95
}
```

**注意**: この判定は収穫期ステージのみに適用されます。
```

---

### 2.2 Step 2a: 連続収穫用プロンプト

**ファイル**: `prompts/stage3_continuous_harvest.md`

```markdown
# 連続収穫型作物の収穫期要件

対象: {作物名} {品種名} - 収穫期ステージ

この作物は**連続収穫型**です。以下の2つのGDDを調査してください：

## 調査項目

### 1. 収穫期全体のGDD（required_gdd）
- 収穫期ステージ開始から収穫終了までの総GDD
- 最大収量を得られるまでの期間

### 2. 初回収穫GDD（harvest_start_gdd）
- 収穫期ステージ開始から初回収穫が可能になるまでのGDD
- 制約: harvest_start_gdd < required_gdd（必須）

## 調査方法

文献から以下を確認：
1. 開花・結実から初回収穫までの日数またはGDD
2. 収穫期間の長さ（収穫開始から終了まで）
3. 総収穫期間のGDD

## 出力形式

```json
{
  "thermal": {
    "required_gdd": 2000.0,
    "harvest_start_gdd": 200.0
  },
  "temperature": {...},
  "sunshine": {...}
}
```

（以降はstage3と同じ）
```

---

### 2.3 Step 2b: 単収穫用プロンプト

**ファイル**: `prompts/stage3_single_harvest.md`

```markdown
# 単回収穫型作物の収穫期要件

対象: {作物名} {品種名} - 収穫期ステージ

この作物は**単回収穫型**です。

## 調査項目

### 1. 成熟までのGDD（required_gdd）
- 収穫期ステージ開始から成熟・収穫までのGDD

### 2. harvest_start_gdd
- 単回収穫型では設定不要: null

## 出力形式

```json
{
  "thermal": {
    "required_gdd": 800.0
  },
  "temperature": {...},
  "sunshine": {...}
}
```

（以降はstage3と同じ）
```

---

## 3. 実装設計

### 3.1 新しいGatewayメソッド

```python
# src/agrr_core/usecase/gateways/crop_profile_gateway.py

class CropProfileGatewayInterface(ABC):
    @abstractmethod
    async def classify_harvest_type(
        self, crop_name: str, variety: Optional[str]
    ) -> Dict[str, Any]:
        """Classify harvest type (continuous or single).
        
        Returns:
            {"harvest_type": "continuous" | "single", "confidence": float}
        """
        pass
    
    @abstractmethod
    async def research_continuous_harvest_stage(
        self, crop_name: str, variety: Optional[str], stage_name: str, stage_description: str
    ) -> Dict[str, Any]:
        """Research harvest stage requirements for continuous-harvest crops."""
        pass
    
    @abstractmethod
    async def research_single_harvest_stage(
        self, crop_name: str, variety: Optional[str], stage_name: str, stage_description: str
    ) -> Dict[str, Any]:
        """Research harvest stage requirements for single-harvest crops."""
        pass
```

---

### 3.2 Interactorの実装

```python
# src/agrr_core/usecase/interactors/crop_profile_craft_interactor.py

async def execute(self, request: CropProfileCraftRequestDTO):
    # ... 既存の処理 ...
    
    # 収穫期ステージの処理を並列化
    harvest_stages = []
    non_harvest_stages = []
    
    for i, stage in enumerate(growth_stages):
        stage_name = LLMResponseNormalizer.normalize_stage_name(stage)
        if self._is_harvest_stage(stage_name):
            harvest_stages.append((i, stage))
        else:
            non_harvest_stages.append((i, stage))
    
    # Step 1: 非収穫期ステージの要件取得（並列）
    non_harvest_tasks = [
        self._research_non_harvest_stage(crop_name, variety, stage)
        for _, stage in non_harvest_stages
    ]
    
    # Step 2: 収穫期ステージの要件取得（並列、タイプ判定付き）
    harvest_tasks = [
        self._research_harvest_stage_with_type_check(crop_name, variety, stage, groups)
        for _, stage in harvest_stages
    ]
    
    # 並列実行
    non_harvest_results = await asyncio.gather(*non_harvest_tasks)
    harvest_results = await asyncio.gather(*harvest_tasks)
    
    # ... 結果を統合 ...

async def _research_harvest_stage_with_type_check(
    self, crop_name, variety, stage, crop_groups
):
    """Research harvest stage with type classification."""
    stage_name = LLMResponseNormalizer.normalize_stage_name(stage)
    stage_description = LLMResponseNormalizer.normalize_stage_description(stage)
    
    # Step 2-1: 収穫タイプ判定（軽量LLM）
    harvest_type_result = await self.gateway.classify_harvest_type(
        crop_name, variety
    )
    harvest_type = harvest_type_result.get("harvest_type", "single")
    
    # Step 2-2: タイプに応じたプロンプトで要件取得
    if harvest_type == "continuous":
        return await self.gateway.research_continuous_harvest_stage(
            crop_name, variety, stage_name, stage_description
        )
    else:
        return await self.gateway.research_single_harvest_stage(
            crop_name, variety, stage_name, stage_description
        )

def _is_harvest_stage(self, stage_name: str) -> bool:
    """Check if stage is harvest stage."""
    harvest_keywords = ["harvest", "収穫", "maturity", "成熟", "登熟"]
    return any(k in stage_name.lower() for k in harvest_keywords)
```

---

### 3.3 並列処理の最適化

```python
async def execute(self, request: CropProfileCraftRequestDTO):
    # ... 既存の処理 ...
    
    # すべてのステージ要件を並列取得
    stage_tasks = []
    for i, stage in enumerate(growth_stages):
        stage_name = LLMResponseNormalizer.normalize_stage_name(stage)
        
        if self._is_harvest_stage(stage_name):
            # 収穫期: タイプ判定 + 専用プロンプト
            task = self._research_harvest_stage_with_type_check(
                crop_name, variety, stage, groups
            )
        else:
            # 非収穫期: 通常プロンプト
            stage_description = LLMResponseNormalizer.normalize_stage_description(stage)
            task = self.gateway.research_stage_requirements(
                crop_name, variety, stage_name, stage_description
            )
        
        stage_tasks.append((i, stage_name, task))
    
    # すべてを並列実行
    results = await asyncio.gather(*[task for _, _, task in stage_tasks])
    
    # StageRequirementを構築
    stage_requirements = []
    for (idx, stage_name, _), result in zip(stage_tasks, results):
        # ... Entityを構築 ...
        stage_requirements.append(stage_req)
    
    # ... 残りの処理 ...
```

---

## 4. 実装ロードマップ

### Phase 1: プロンプトファイルの作成

**新規ファイル**:
1. `prompts/stage0_harvest_type_classification.md`
2. `prompts/stage3_continuous_harvest.md`
3. `prompts/stage3_single_harvest.md`

**工数**: 2-3時間

---

### Phase 2: Gateway層の拡張

**変更ファイル**:
1. `src/agrr_core/usecase/gateways/crop_profile_gateway.py` - Interface追加
2. `src/agrr_core/adapter/gateways/crop_profile_gateway_impl.py` - 実装追加
3. `src/agrr_core/framework/repositories/crop_profile_llm_repository.py` - LLM呼び出し追加

**新規メソッド**:
- `classify_harvest_type()`
- `research_continuous_harvest_stage()`
- `research_single_harvest_stage()`

**工数**: 3-4時間

---

### Phase 3: Interactor層の更新

**変更ファイル**:
1. `src/agrr_core/usecase/interactors/crop_profile_craft_interactor.py`

**変更内容**:
- `_is_harvest_stage()` メソッド追加
- `_research_harvest_stage_with_type_check()` メソッド追加
- 並列処理の実装（`asyncio.gather`）

**工数**: 2-3時間

---

### Phase 4: テストの追加

**新規テスト**:
1. `tests/test_usecase/test_crop_profile_craft_interactor.py` - 並列処理テスト
2. `tests/test_adapter/test_crop_profile_gateway_impl.py` - 新規メソッドテスト
3. `tests/test_adapter/test_crop_profile_llm_repository.py` - LLM呼び出しテスト

**工数**: 3-4時間

---

### Phase 5: E2Eテストとドキュメント

**工数**: 2時間

---

## 5. データフロー

### 5.1 現在のフロー（単一プロンプト）

```
Stage 1 → stage3 プロンプト → required_gdd
Stage 2 → stage3 プロンプト → required_gdd
Stage 3 → stage3 プロンプト → required_gdd
Stage 4 (収穫期) → stage3 プロンプト → required_gdd + harvest_start_gdd ❌混乱
```

**LLM呼び出し**: 4回（直列）

---

### 5.2 新しいフロー（マルチプロンプト＋並列）

```
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: 収穫タイプ判定（軽量LLM、1回）                           │
│ classify_harvest_type("ナス") → {"harvest_type": "continuous"}  │
└───────────────────────┬─────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: 並列実行（4つのLLM呼び出しを同時実行）                  │
│                                                                  │
│ ┌──────────────────┐  ┌──────────────────┐                     │
│ │ Stage 1: 育苗期  │  │ Stage 2: 定植期  │                     │
│ │ stage3プロンプト │  │ stage3プロンプト │                     │
│ └──────────────────┘  └──────────────────┘                     │
│                                                                  │
│ ┌──────────────────┐  ┌──────────────────────────────┐         │
│ │ Stage 3: 生育期  │  │ Stage 4: 収穫期              │         │
│ │ stage3プロンプト │  │ stage3_continuous_harvest    │         │
│ └──────────────────┘  │ (harvest_start_gdd付き)      │         │
│                        └──────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

**LLM呼び出し**: 5回（1回判定 + 4回並列）

**処理時間**: 
- 現在: T1 + T2 + T3 + T4（直列）
- 新: T_classify + max(T1, T2, T3, T4)（並列）
- **短縮効果**: 約60-70%の時間短縮

---

## 6. 実装詳細

### 6.1 収穫タイプ判定の実装

```python
# src/agrr_core/framework/repositories/crop_profile_llm_repository.py

async def classify_harvest_type(
    self, crop_name: str, variety: Optional[str]
) -> Dict[str, Any]:
    """Classify harvest type using lightweight LLM call.
    
    Uses: gpt-3.5-turbo or equivalent (fast, low-cost)
    """
    prompt = self._load_prompt("stage0_harvest_type_classification.md").format(
        crop_name=crop_name,
        variety=variety or ""
    )
    
    response = await self.llm_client.chat(
        prompt=prompt,
        model="gpt-3.5-turbo",  # 軽量モデル
        temperature=0.1,         # 低temperature（判定タスク）
        max_tokens=100           # 短い応答
    )
    
    return json.loads(response)
```

---

### 6.2 連続収穫用プロンプトの実装

```python
async def research_continuous_harvest_stage(
    self,
    crop_name: str,
    variety: Optional[str],
    stage_name: str,
    stage_description: str
) -> Dict[str, Any]:
    """Research harvest stage for continuous-harvest crops.
    
    Uses: stage3_continuous_harvest.md prompt
    Includes: both required_gdd and harvest_start_gdd
    """
    prompt = self._load_prompt("stage3_continuous_harvest.md").format(
        crop_name=crop_name,
        variety=variety or "",
        stage_name=stage_name,
        stage_description=stage_description
    )
    
    response = await self.llm_client.structured_output(
        prompt=prompt,
        schema=self._build_stage_requirement_schema()
    )
    
    return response
```

---

### 6.3 並列実行の実装

```python
# src/agrr_core/usecase/interactors/crop_profile_craft_interactor.py

async def _research_all_stages_parallel(
    self,
    crop_name: str,
    variety: Optional[str],
    growth_stages: List[Dict],
    crop_groups: List[str]
) -> List[Dict[str, Any]]:
    """Research all stage requirements in parallel.
    
    Returns:
        List of stage requirement data in order
    """
    # Step 1: 収穫タイプ判定（1回）
    has_harvest_stage = any(
        self._is_harvest_stage(LLMResponseNormalizer.normalize_stage_name(s))
        for s in growth_stages
    )
    
    harvest_type = None
    if has_harvest_stage:
        harvest_type_result = await self.gateway.classify_harvest_type(
            crop_name, variety
        )
        harvest_type = harvest_type_result.get("harvest_type", "single")
    
    # Step 2: すべてのステージ要件を並列取得
    tasks = []
    for stage in growth_stages:
        stage_name = LLMResponseNormalizer.normalize_stage_name(stage)
        stage_description = LLMResponseNormalizer.normalize_stage_description(stage)
        
        if self._is_harvest_stage(stage_name):
            # 収穫期: タイプに応じたプロンプト
            if harvest_type == "continuous":
                task = self.gateway.research_continuous_harvest_stage(
                    crop_name, variety, stage_name, stage_description
                )
            else:
                task = self.gateway.research_single_harvest_stage(
                    crop_name, variety, stage_name, stage_description
                )
        else:
            # 非収穫期: 通常プロンプト
            task = self.gateway.research_stage_requirements(
                crop_name, variety, stage_name, stage_description
            )
        
        tasks.append(task)
    
    # 並列実行
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # エラーハンドリング
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            raise RuntimeError(f"Failed to research stage {i+1}: {result}")
    
    return results
```

---

## 7. 期待される効果

### 7.1 精度の向上

| 項目 | 現在 | 新フロー |
|-----|------|---------|
| harvest_start_gdd精度 | 低（混乱） | 高（専用プロンプト） |
| required_gdd精度 | 中 | 高（単純化） |
| エラー率 | 高 | 低（タイプ分岐） |

### 7.2 処理時間の短縮

```
現在: T1 + T2 + T3 + T4 ≈ 40-60秒（直列）
新: T_class + max(T1, T2, T3, T4) ≈ 15-25秒（並列）
短縮率: 約60%
```

### 7.3 コスト

```
現在: 4回 × gpt-4（高コスト）
新: 1回 × gpt-3.5（低コスト） + 4回 × gpt-4（並列）
差分: +1回の軽量LLM呼び出し（コスト増は微小）
```

---

## 8. 実装優先順位

### 🔥 優先度: 高（すぐ実装すべき）

**Phase 1-2: プロンプトとGatewayの実装**
- 理由: harvest_start_gddの精度が大幅に向上
- 工数: 5-7時間
- リスク: 低（既存機能に影響なし）

### 🔄 優先度: 中（Phase 1-2の後に実施）

**Phase 3-4: 並列処理とテスト**
- 理由: 処理時間短縮とテストカバレッジ向上
- 工数: 5-7時間
- リスク: 中（並列処理の複雑性）

---

## 9. まとめ

### 提案する新しい処理フロー

**3段階マルチプロンプト戦略**:
1. ✅ 収穫タイプ判定（軽量LLM、1回）
2. ✅ タイプ別専用プロンプト（連続/単収穫）
3. ✅ 並列処理による高速化

**期待される効果**:
- harvest_start_gdd精度: 大幅向上
- 処理時間: 約60%短縮
- コスト: ほぼ同等（軽量LLM1回追加のみ）

**実装規模**:
- 総工数: 10-14時間
- 新規ファイル: 3個のプロンプト
- 変更ファイル: Gateway, Interactor層
- テスト: 10-15個追加

この設計で実装を進めますか？

