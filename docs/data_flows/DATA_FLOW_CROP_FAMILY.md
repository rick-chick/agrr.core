# データフロー: 作物の科（family）をgroupsに追加する機能

## 概要
このドキュメントは、`agrr crop crop --query "トマト"` コマンド実行時のコンポーネント間データ移送を説明します。

## アーキテクチャ層とコンポーネント

```
Framework Layer (外側)
    └─ LLM Client (llm_client_impl.py)
        ↓
Adapter Layer
    ├─ Controller (crop_cli_craft_controller.py)
    ├─ Gateway (crop_requirement_gateway_impl.py)
    ├─ Presenter (crop_requirement_craft_presenter.py)
    └─ Mapper (crop_requirement_mapper.py)
        ↓
UseCase Layer
    ├─ Interactor (crop_requirement_craft_interactor.py)
    ├─ DTO (crop_requirement_craft_request_dto.py)
    └─ Gateway Interface (crop_requirement_gateway.py)
        ↓
Entity Layer (内側)
    └─ Crop, StageRequirement, etc.
```

## データフロー詳細

### 1️⃣ CLI → Controller

**入力データ:**
```bash
agrr crop crop --query "トマト"
```

**処理:**
- `cli.py` (line 160-166): コマンドライン引数をパース
- Gateway、Presenterを注入してControllerをインスタンス化

**出力データ:**
```python
args = ["--query", "トマト"]
```

---

### 2️⃣ Controller → Interactor

**入力データ:**
```python
args = ["--query", "トマト"]
```

**処理:**
- `crop_cli_craft_controller.py` (line 105-111)
- 引数をDTOに変換
- Interactorの`execute()`メソッドを呼び出し

**出力データ:**
```python
CropRequirementCraftRequestDTO(
    crop_query="トマト"
)
```

---

### 3️⃣ Interactor → Gateway (Step 1: 品種抽出)

**入力データ:**
```python
crop_query = "トマト"
```

**処理:**
- `crop_requirement_craft_interactor.py` (line 49)
- `gateway.extract_crop_variety(crop_query)` 呼び出し

**Gateway処理:**
- `crop_requirement_gateway_impl.py` (line 110-120)
- `llm_client.step1_crop_variety_selection(crop_query)` 呼び出し

**LLM Client処理:**
- `llm_client_impl.py` (line 193-215)
- OpenAI APIに問い合わせ

**出力データ:**
```python
{
    "crop_name": "Tomato",
    "variety": "default"
}
```

---

### 4️⃣ Interactor → Gateway (Step 2: 成長ステージ定義)

**入力データ:**
```python
crop_name = "Tomato"
variety = "default"
```

**処理:**
- `crop_requirement_craft_interactor.py` (line 54)
- `gateway.define_growth_stages(crop_name, variety)` 呼び出し

**出力データ:**
```python
{
    "crop_info": {
        "name": "Tomato",
        "variety": "default"
    },
    "growth_periods": [
        {
            "period_name": "発芽期",
            "order": 1,
            "period_description": "種子から芽が出る時期"
        },
        {
            "period_name": "栄養成長期",
            "order": 2,
            "period_description": "茎葉が成長する時期"
        },
        # ... more stages
    ]
}
```

---

### 5️⃣ Interactor → Gateway (Step 3a: 経済情報取得)

**入力データ:**
```python
crop_name = "Tomato"
variety = "default"
```

**処理:**
- `crop_requirement_craft_interactor.py` (line 62)
- `gateway.extract_crop_economics(crop_name, variety)` 呼び出し

**Gateway処理:**
- `crop_requirement_gateway_impl.py` (line 169-192)
- `llm_client.extract_crop_economics(crop_name, variety)` 呼び出し

**LLM Client処理:**
- `llm_client_impl.py` (line 310-351)
- OpenAI APIに経済情報を問い合わせ

**出力データ:**
```python
{
    "area_per_unit": 0.5,      # m² per unit
    "revenue_per_area": 2000.0  # yen per m²
}
```

---

### 6️⃣ Interactor → Gateway (Step 3b: 科情報取得) ⭐ 今回追加

**入力データ:**
```python
crop_name = "Tomato"
variety = "default"
```

**処理:**
- `crop_requirement_craft_interactor.py` (line 68-69) ← 新規追加
- `gateway.extract_crop_family(crop_name, variety)` 呼び出し

**Gateway処理:**
- `crop_requirement_gateway_impl.py` (line 194-217) ← 新規追加
- `llm_client.extract_crop_family(crop_name, variety)` 呼び出し

**LLM Client処理:**
- `llm_client_impl.py` (line 353-391) ← 新規追加
- OpenAI APIに植物学的な科を問い合わせ

**プロンプト例:**
```
作物: Tomato
品種: default

この作物の植物学的な科（family）を調査してください。
例:
- トマト → ナス科（Solanaceae）
- キュウリ → ウリ科（Cucurbitaceae）
- イネ → イネ科（Poaceae）

日本語の科名と学名の両方を返してください。
```

**出力データ:**
```python
{
    "family_ja": "ナス科",
    "family_scientific": "Solanaceae"
}
```

---

### 7️⃣ Interactor: groupsリスト構築 ⭐ 今回追加

**入力データ:**
```python
family_scientific = "Solanaceae"
```

**処理:**
- `crop_requirement_craft_interactor.py` (line 71-74) ← 新規追加
- 学名をgroupsリストの最初の要素として追加

**コード:**
```python
# Build groups list with family at the beginning
groups = []
if family_scientific:
    groups.append(family_scientific)
```

**出力データ:**
```python
groups = ["Solanaceae"]
```

---

### 8️⃣ Interactor → Gateway (Step 3c: ステージ要件研究)

**入力データ:**
```python
crop_name = "Tomato"
variety = "default"
stage_name = "発芽期"
stage_description = "種子から芽が出る時期"
```

**処理:**
- `crop_requirement_craft_interactor.py` (line 83-84)
- `gateway.research_stage_requirements(...)` をステージごとに呼び出し

**出力データ:**
```python
{
    "temperature": {
        "base_temperature": 10.0,
        "optimal_min": 20.0,
        "optimal_max": 30.0,
        "low_stress_threshold": 12.0,
        "high_stress_threshold": 32.0,
        "frost_threshold": 0.0,
        "sterility_risk_threshold": 35.0
    },
    "sunshine": {
        "minimum_sunshine_hours": 3.0,
        "target_sunshine_hours": 6.0
    },
    "thermal": {
        "required_gdd": 150.0
    }
}
```

---

### 9️⃣ Interactor: Entityオブジェクト構築

**処理:**
- `crop_requirement_craft_interactor.py` (line 77-85)
- 収集したデータからCropエンティティを生成

**コード:**
```python
crop = Crop(
    crop_id=crop_name.lower(),       # "tomato"
    name=crop_name,                  # "Tomato"
    area_per_unit=area_per_unit,     # 0.5
    variety=variety if variety and variety != "default" else None,
    revenue_per_area=revenue_per_area,  # 2000.0
    max_revenue=max_revenue,            # None
    groups=groups if groups else None   # ["Solanaceae"] ⭐
)
```

**出力データ (Cropエンティティ):**
```python
Crop(
    crop_id="tomato",
    name="Tomato",
    area_per_unit=0.5,
    variety=None,
    revenue_per_area=2000.0,
    max_revenue=None,
    groups=["Solanaceae"]  # ⭐ 科が追加されている
)
```

---

### 🔟 Interactor: Aggregateオブジェクト構築

**処理:**
- `crop_requirement_craft_interactor.py` (line 86-117)
- StageRequirementリストを構築
- CropRequirementAggregateを生成

**出力データ:**
```python
CropRequirementAggregate(
    crop=Crop(..., groups=["Solanaceae"]),
    stage_requirements=[
        StageRequirement(
            stage=GrowthStage(name="発芽期", order=1),
            temperature=TemperatureProfile(...),
            sunshine=SunshineProfile(...),
            thermal=ThermalRequirement(...)
        ),
        # ... more stages
    ]
)
```

---

### 1️⃣1️⃣ Mapper: Entity → Dict変換

**処理:**
- `crop_requirement_craft_interactor.py` (line 120)
- `CropRequirementMapper.aggregate_to_payload(aggregate)` 呼び出し

**Mapper処理:**
- `crop_requirement_mapper.py` (line 33-65)
- エンティティをJSONシリアライズ可能な辞書に変換

**出力データ:**
```python
{
    "crop_id": "tomato",
    "crop_name": "Tomato",
    "variety": None,
    "area_per_unit": 0.5,
    "revenue_per_area": 2000.0,
    "max_revenue": None,
    "groups": ["Solanaceae"],  # ⭐ groupsフィールドが含まれる
    "stages": [
        {
            "name": "発芽期",
            "order": 1,
            "temperature": {...},
            "sunshine": {...},
            "thermal": {...}
        },
        # ... more stages
    ]
}
```

---

### 1️⃣2️⃣ Presenter: 成功レスポンスのフォーマット

**処理:**
- `crop_requirement_craft_interactor.py` (line 122)
- `presenter.format_success(payload)` 呼び出し

**Presenter処理:**
- `crop_requirement_craft_presenter.py` (line 16-17)
- データをレスポンス形式でラップ

**出力データ:**
```python
{
    "success": True,
    "data": {
        "crop_id": "tomato",
        "crop_name": "Tomato",
        "variety": None,
        "area_per_unit": 0.5,
        "revenue_per_area": 2000.0,
        "max_revenue": None,
        "groups": ["Solanaceae"],  # ⭐
        "stages": [...]
    }
}
```

---

### 1️⃣3️⃣ Controller: JSON出力

**処理:**
- `crop_cli_craft_controller.py` (line 110)
- `print(json.dumps(result, ensure_ascii=False))` でJSON出力

**最終出力 (CLI):**
```json
{
  "success": true,
  "data": {
    "crop_id": "tomato",
    "crop_name": "Tomato",
    "variety": null,
    "area_per_unit": 0.5,
    "revenue_per_area": 2000.0,
    "max_revenue": null,
    "groups": ["Solanaceae"],
    "stages": [
      {
        "name": "発芽期",
        "order": 1,
        "temperature": {
          "base_temperature": 10.0,
          "optimal_min": 20.0,
          "optimal_max": 30.0,
          "low_stress_threshold": 12.0,
          "high_stress_threshold": 32.0,
          "frost_threshold": 0.0,
          "sterility_risk_threshold": 35.0
        },
        "sunshine": {
          "minimum_sunshine_hours": 3.0,
          "target_sunshine_hours": 6.0
        },
        "thermal": {
          "required_gdd": 150.0
        }
      }
    ]
  }
}
```

## データ変換のポイント

### 依存性の方向（Clean Architecture準拠）

```
CLI (Framework)
  ↓ インスタンス化・呼び出し
Controller (Adapter) ← Gateway/Presenter注入
  ↓ DTO変換
Interactor (UseCase) ← Gateway Interface依存
  ↓ Interface呼び出し
Gateway Impl (Adapter) ← LLM Client注入
  ↓ 具体的な実装
LLM Client (Framework)
  ↓ 外部API呼び出し
OpenAI API
```

### 重要な設計パターン

1. **依存性注入 (DI)**
   - ControllerはGateway実装とPresenterを注入される
   - GatewayはLLM Clientを注入される
   - テストでモックに置き換え可能

2. **インターフェース分離 (ISP)**
   - Interactorは`CropRequirementGateway`インターフェースのみに依存
   - 実装の詳細を知らない

3. **依存性逆転 (DIP)**
   - UseCaseレイヤーがインターフェースを定義
   - Adapterレイヤーがそれを実装

4. **単一責任 (SRP)**
   - 各コンポーネントは一つの責任のみ
   - Mapper: Entity ↔ Dict変換のみ
   - Presenter: レスポンスフォーマットのみ

## 今回の変更点まとめ

### ⭐ 新規追加コンポーネント

1. **LLM Client** (`llm_client_impl.py`)
   - `extract_crop_family()` メソッド追加
   - 作物の科を取得するLLM呼び出し

2. **Gateway** (`crop_requirement_gateway_impl.py`)
   - `extract_crop_family()` メソッド追加
   - LLM Clientへの委譲とフォールバック処理

3. **Interactor** (`crop_requirement_craft_interactor.py`)
   - 科取得の呼び出し追加
   - groupsリストの構築ロジック追加

### データフローへの影響

**変更前:**
```
Interactor → extract_crop_economics() → Crop(groups=None)
```

**変更後:**
```
Interactor → extract_crop_economics() → crop_economics
          → extract_crop_family() → crop_family  ⭐ 新規
          → groups = [family_scientific] ⭐ 新規
          → Crop(groups=["Solanaceae"]) ⭐ 科が含まれる
```

## テストでの確認

### テストコード追加箇所

1. **conftest.py** (line 208-211)
   ```python
   gateway.extract_crop_family.return_value = {
       "family_ja": "ナス科",
       "family_scientific": "Solanaceae"
   }
   ```

2. **test_crop_requirement_craft_interactor.py** (line 64-88)
   ```python
   @pytest.mark.asyncio
   async def test_craft_includes_family_in_groups(...):
       result = await interactor.execute(req)
       assert data["groups"][0] == "Solanaceae"
       mock_gateway.extract_crop_family.assert_called_once()
   ```

## 活用シーン

この科情報（groups）は以下の機能で活用されます：

1. **連作障害判定** (`interaction_rule_service.py`)
   - 同じ科の作物の連続栽培を検出
   - ペナルティ適用

2. **輪作計画** (`optimize-period`)
   - 異なる科の作物を推奨
   - 最適化スコア計算

3. **圃場-作物相性** 
   - 科単位での相性ルール適用
   - 例: "この圃場はナス科に適している"

## まとめ

今回の実装により、**作物情報取得時に自動的に植物学的な科が取得され、groupsフィールドに格納される**ようになりました。

各層の責任が明確に分離されており：
- **Entity層**: データ構造定義のみ
- **UseCase層**: ビジネスロジック（科の取得と格納）
- **Adapter層**: 外部システム（LLM）との連携
- **Framework層**: 具体的なAPI実装

この設計により、テストが容易で、保守性の高いコードが実現されています。

