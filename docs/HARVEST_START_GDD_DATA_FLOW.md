# harvest_start_gdd データフロー整理

**作成日**: 2025-10-15  
**目的**: harvest_start_gddフィールドのコンポーネント間データ移送の確認

---

## 1. データフロー概要

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. LLM (AI) → JSON Response                                     │
│    harvest_start_gdd: 200.0                                      │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. CropProfileLLMRepository (Framework層)                        │
│    - LLMのJSONレスポンスを受け取る                               │
│    - harvest_start_gddを含むDictを返す                           │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. LLMResponseNormalizer (UseCase層)                            │
│    - Dictを正規化                                                │
│    - harvest_start_gddを含むDictを返す                           │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. CropProfileMapper (UseCase層)                                │
│    - Dictをエンティティに変換                                    │
│    - ThermalRequirement(harvest_start_gdd=200.0) を生成         │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. ThermalRequirement (Entity層)                                │
│    - harvest_start_gdd: Optional[float] = None                  │
│    - is_harvest_started(gdd) メソッド                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 各コンポーネントの責務

### 2.1 Framework層: CropProfileLLMRepository

**ファイル**: `src/agrr_core/framework/repositories/crop_profile_llm_repository.py`

**責務**: LLMのレスポンスをそのまま返す（変換なし）

**期待される出力**:
```python
{
    "thermal": {
        "required_gdd": 2000.0,
        "harvest_start_gdd": 200.0  # LLMからのレスポンスをそのまま返す
    }
}
```

**確認項目**:
- ✅ LLMのレスポンスをそのまま返しているか
- ⚠️ harvest_start_gddをフィルタリングしていないか

---

### 2.2 UseCase層: LLMResponseNormalizer

**ファイル**: `src/agrr_core/usecase/services/llm_response_normalizer.py`

**責務**: LLMのレスポンスを正規化（デフォルト値の設定など）

**期待される動作**:
```python
def normalize_thermal_requirement(thermal_data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "required_gdd": thermal_data.get("required_gdd", 400.0),
        "harvest_start_gdd": thermal_data.get("harvest_start_gdd", None),  # 追加必要
    }
```

**確認項目**:
- ❌ harvest_start_gddを処理しているか
- ❌ harvest_start_gddのデフォルト値はNoneか

---

### 2.3 UseCase層: CropProfileMapper

**ファイル**: `src/agrr_core/usecase/services/crop_profile_mapper.py`

**責務**: DictをThermalRequirementエンティティに変換

**期待される動作**:
```python
def map_thermal_requirement(thermal_data: Dict[str, Any]) -> ThermalRequirement:
    return ThermalRequirement(
        required_gdd=thermal_data["required_gdd"],
        harvest_start_gdd=thermal_data.get("harvest_start_gdd", None),  # 追加必要
    )
```

**確認項目**:
- ❌ harvest_start_gddをThermalRequirementに渡しているか

---

### 2.4 Entity層: ThermalRequirement

**ファイル**: `src/agrr_core/entity/entities/thermal_requirement_entity.py`

**責務**: harvest_start_gddを保持し、検証する

**実装状態**:
- ✅ harvest_start_gddフィールド追加済み
- ✅ バリデーション実装済み
- ✅ is_harvest_started()メソッド実装済み

---

## 3. 問題箇所の特定

### ❌ 問題1: LLMResponseNormalizer

`llm_response_normalizer.py` の `normalize_thermal_requirement()` メソッドが
harvest_start_gddを処理していない可能性が高い。

### ❌ 問題2: CropProfileMapper

`crop_profile_mapper.py` の `map_thermal_requirement()` メソッドが
harvest_start_gddをThermalRequirementに渡していない可能性が高い。

---

## 4. 修正計画

### Step 1: LLMResponseNormalizer の修正
- harvest_start_gddを正規化処理に追加
- 単体テスト追加

### Step 2: CropProfileMapper の修正
- harvest_start_gddをエンティティ生成時に渡す
- 単体テスト追加

### Step 3: 統合テスト
- LLM → Normalizer → Mapper → Entity の全体フローをテスト

### Step 4: CLI確認
- `agrr crop --query "ナス"` で実際に動作確認

---

## 5. テスト戦略

### 5.1 単体テスト

#### Test 1: LLMResponseNormalizer
```python
def test_normalize_thermal_requirement_with_harvest_start_gdd():
    thermal_data = {
        "required_gdd": 2000.0,
        "harvest_start_gdd": 200.0
    }
    result = normalize_thermal_requirement(thermal_data)
    assert result["harvest_start_gdd"] == 200.0

def test_normalize_thermal_requirement_without_harvest_start_gdd():
    thermal_data = {
        "required_gdd": 2000.0
    }
    result = normalize_thermal_requirement(thermal_data)
    assert result["harvest_start_gdd"] is None
```

#### Test 2: CropProfileMapper
```python
def test_map_thermal_requirement_with_harvest_start_gdd():
    thermal_data = {
        "required_gdd": 2000.0,
        "harvest_start_gdd": 200.0
    }
    thermal = map_thermal_requirement(thermal_data)
    assert thermal.required_gdd == 2000.0
    assert thermal.harvest_start_gdd == 200.0

def test_map_thermal_requirement_without_harvest_start_gdd():
    thermal_data = {
        "required_gdd": 2000.0
    }
    thermal = map_thermal_requirement(thermal_data)
    assert thermal.required_gdd == 2000.0
    assert thermal.harvest_start_gdd is None
```

### 5.2 統合テスト

```python
def test_full_data_flow_harvest_start_gdd():
    """Test complete data flow from LLM response to Entity."""
    # LLM response simulation
    llm_response = {
        "thermal": {
            "required_gdd": 2000.0,
            "harvest_start_gdd": 200.0
        }
    }
    
    # Normalize
    normalized = normalize_thermal_requirement(llm_response["thermal"])
    
    # Map to entity
    thermal = map_thermal_requirement(normalized)
    
    # Verify
    assert thermal.harvest_start_gdd == 200.0
    assert thermal.is_harvest_started(200.0) == True
    assert thermal.is_met(200.0) == False
```

---

## 6. 実装チェックリスト

- [ ] LLMResponseNormalizer の修正
- [ ] LLMResponseNormalizer の単体テスト
- [ ] CropProfileMapper の修正
- [ ] CropProfileMapper の単体テスト
- [ ] 統合テスト
- [ ] CLI動作確認

