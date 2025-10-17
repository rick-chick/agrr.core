# AGRR.CORE プロジェクトアーキテクチャ 全体俯瞰と提案

## 📊 プロジェクト概要

### 基本情報
- **プロジェクト名**: AGRR.CORE (Agricultural Resource & Risk Management Core)
- **アーキテクチャ**: Clean Architecture
- **実装言語**: Python 3.8+
- **規模**: 
  - ソースファイル: 205 Python files
  - テストファイル: 112 test files
  - 推定コード行数: ~15,000-20,000 LOC

### 主要機能ドメイン

1. **天気データ管理**
   - Open-Meteo API統合
   - JMA（気象庁）データ取得
   - 天気予測（ARIMA、LightGBM）

2. **作物管理**
   - LLMベースの作物プロファイル生成
   - 成長段階シミュレーション
   - 成長進捗計算

3. **最適化エンジン** ⭐ コア機能
   - 最適作付け時期決定（DP最適化）
   - 複数圃場作物割り当て（DP/Greedy + Local Search/ALNS）
   - 連作障害考慮

---

## 🏗️ 現在のアーキテクチャ構造

### Clean Architecture 4層構造

```
┌─────────────────────────────────────────────────────────┐
│                    Framework Layer                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │ CLI, HTTP, Services (External APIs, ML, I/O)     │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         ↓ 依存
┌─────────────────────────────────────────────────────────┐
│                     Adapter Layer                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Controllers, Presenters, Gateways, Mappers       │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         ↓ 依存
┌─────────────────────────────────────────────────────────┐
│                    UseCase Layer                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Interactors, Services, DTOs, Ports, Gateways(I/F)│  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         ↓ 依存
┌─────────────────────────────────────────────────────────┐
│                     Entity Layer                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Entities, Value Objects, Protocols, Validators   │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### ディレクトリ構造

```
src/agrr_core/
├── entity/                      # Entity Layer
│   ├── entities/               # ビジネスエンティティ (26 entities)
│   ├── value_objects/          # 値オブジェクト (3 VOs)
│   ├── protocols/              # プロトコル（インターフェース）
│   ├── validators/             # バリデータ
│   └── exceptions/             # エンティティ例外
│
├── usecase/                     # UseCase Layer
│   ├── interactors/            # ユースケース実装 (10 interactors)
│   ├── services/               # ドメインサービス (8 services)
│   ├── dto/                    # データ転送オブジェクト (25 DTOs)
│   ├── gateways/               # ゲートウェイインターフェース (10 gateways)
│   ├── ports/                  # 入出力ポート
│   │   ├── input/              # 入力ポート (9 ports)
│   │   └── output/             # 出力ポート (5 ports)
│   └── exceptions/             # ユースケース例外
│
├── adapter/                     # Adapter Layer
│   ├── controllers/            # コントローラー (5 controllers)
│   ├── presenters/             # プレゼンター (7 presenters)
│   ├── gateways/               # ゲートウェイ実装 (12 gateways)
│   ├── services/               # アダプターサービス (1 service)
│   ├── mappers/                # データマッパー (1 mapper)
│   └── interfaces/             # Framework層向けインターフェース
│       ├── clients/            # クライアントI/F (2 interfaces)
│       ├── io/                 # I/O I/F (3 interfaces)
│       ├── ml/                 # ML I/F (2 interfaces)
│       └── structures/         # 共通データ構造
│
├── framework/                   # Framework Layer
│   ├── services/               # 技術的サービス実装
│   │   ├── clients/            # 外部クライアント (2 clients)
│   │   ├── io/                 # I/O サービス (3 services)
│   │   ├── ml/                 # ML サービス (4 services)
│   │   └── utils/              # ユーティリティ (1 service)
│   ├── config/                 # 設定・DIコンテナ
│   └── exceptions/             # フレームワーク例外
│
└── cli.py                       # CLIエントリーポイント

tests/                           # テスト (112 test files)
├── test_entity/                # エンティティテスト
├── test_usecase/               # ユースケーステスト
├── test_adapter/               # アダプターテスト
├── test_integration/           # 統合テスト
└── test_unit/                  # 単体テスト
```

---

## 🎯 最近の主要な改善（2025年）

### 1. **DP最適化アルゴリズムの導入**

**Before (Greedy Only):**
```
初期割り当て: Greedy (利益率順)
改善: Hill Climbing
品質: 85-95%
```

**After (DP + Hybrid):**
```
初期割り当て: DP (Weighted Interval Scheduling) ← NEW!
           または Greedy (6作物以上推奨)
改善: Hill Climbing または ALNS
品質: 95-100% (DP), 85-95% (Greedy)
```

**実装箇所:**
- `multi_field_crop_allocation_greedy_interactor.py`
  - `_weighted_interval_scheduling_dp()` (O(n log n))
  - `_find_latest_non_overlapping()` (Binary Search)
  - `_dp_allocation()` (収益制約対応)

**成果:**
- 小規模問題（4作物）: **利益+40%** 🎉
- 計算時間: ほぼ同等 or 高速化

### 2. **ALNS（Adaptive Large Neighborhood Search）統合**

**Before (Hill Climbing):**
```
近傍: 小規模（1-2割り当ての変更）
探索: 貪欲（最初の改善を採用）
品質: 90-95%
```

**After (ALNS):**
```
近傍: 大規模（複数割り当ての破壊・修復）
探索: 適応的（成功した操作の重み調整）
品質: 95-100%
```

**実装:**
- `alns_optimizer_service.py` (455行)
  - 5つのDestroy operators
  - 2つのRepair operators
  - 適応的重み調整メカニズム

**共通化:**
- `allocation_utils.py` (370行)
  - Hill ClimbingとALNSの共通ユーティリティ
  - コード重複削減: 200-300行

### 3. **アルゴリズム選択の柔軟性**

**CLI Interface:**
```bash
# デフォルト（DP + Hill Climbing）
agrr optimize allocate --fields-file ... --crops-file ...

# 貪欲法（多作物・厳しい制約向け）
agrr optimize allocate ... --algorithm greedy

# ALNS（最高品質）
agrr optimize allocate ... --enable-alns
```

**設定による制御:**
```python
OptimizationConfig(
    algorithm="dp",              # dp or greedy
    enable_alns=True,            # ALNS vs Hill Climbing
    alns_iterations=1000,
    # ... 30+ configuration options
)
```

---

## ✅ 現状の強み

### 1. **Clean Architecture準拠**
- ✅ 明確な層分離
- ✅ 依存性逆転原則の遵守
- ✅ テスタビリティ（112テストファイル）
- ✅ インターフェース分離

### 2. **最適化アルゴリズムの多様性**
- ✅ DP最適化（厳密解）
- ✅ Greedy（高速・多制約対応）
- ✅ Hill Climbing（バランス型）
- ✅ ALNS（高品質）

### 3. **実用的な機能群**
- ✅ 複数データソース対応（Open-Meteo, JMA）
- ✅ LLM統合（作物プロファイル生成）
- ✅ ML予測（ARIMA, LightGBM）
- ✅ 連作障害考慮

### 4. **拡張性の高い設計**
- ✅ 新しいゲートウェイの追加が容易
- ✅ 新しい最適化アルゴリズムの追加が容易
- ✅ プラグイン可能なプレゼンター

---

## 🚧 現状の課題と改善提案

### 課題1: **UseCase層のサービス肥大化**

**現状:**
```
src/agrr_core/usecase/services/
├── alns_optimizer_service.py          (455行)
├── allocation_utils.py                (370行)
├── neighbor_generator_service.py
├── interaction_rule_service.py
├── neighbor_operations/               (8ファイル)
└── ...
```

**問題:**
- UseCase層にアルゴリズム実装が集中
- ドメインロジック vs アルゴリズム実装の境界が曖昧
- テストの複雑化

**提案: Domain Serviceの再編成**

```
src/agrr_core/usecase/
├── domain_services/           ← NEW! ドメインロジック
│   ├── crop_rotation_service.py      # 輪作ルール
│   ├── field_capacity_service.py     # 圃場能力計算
│   └── interaction_rule_service.py   # 連作障害
│
├── optimization/              ← NEW! 最適化専用
│   ├── algorithms/
│   │   ├── dp_optimizer.py           # DP実装
│   │   ├── greedy_optimizer.py       # Greedy実装
│   │   └── alns_optimizer.py         # ALNS実装
│   ├── operators/                    # 近傍操作
│   │   ├── destroy/
│   │   └── repair/
│   └── utils/
│       └── allocation_utils.py       # 共通ユーティリティ
│
└── interactors/               # 既存のまま
    └── multi_field_crop_allocation_interactor.py
```

**効果:**
- 責任の明確化
- テストの単純化
- 新しいアルゴリズムの追加が容易

---

### 課題2: **Interactorの肥大化**

**現状:**
```python
# multi_field_crop_allocation_greedy_interactor.py
# 1,190行 (!!)

class MultiFieldCropAllocationGreedyInteractor:
    - 候補生成
    - DP最適化
    - Greedy割り当て
    - Hill Climbing
    - ALNS統合
    - 結果構築
    # ... その他多数
```

**問題:**
- 単一責任原則違反
- テストの複雑化（モック地獄）
- 可読性・保守性の低下

**提案: Strategy Patternによる分離**

```python
# NEW: src/agrr_core/usecase/optimization/strategies/

class AllocationStrategy(ABC):
    """割り当て戦略の基底クラス"""
    @abstractmethod
    async def allocate(
        self,
        candidates: List[AllocationCandidate],
        fields: List[Field],
        crops: List[Crop]
    ) -> List[CropAllocation]:
        pass


class DPAllocationStrategy(AllocationStrategy):
    """DP戦略"""
    async def allocate(...) -> List[CropAllocation]:
        # DP実装のみ


class GreedyAllocationStrategy(AllocationStrategy):
    """Greedy戦略"""
    async def allocate(...) -> List[CropAllocation]:
        # Greedy実装のみ


# MODIFIED: multi_field_crop_allocation_interactor.py (削減: 1190行 → 300行)

class MultiFieldCropAllocationInteractor:
    def __init__(self, ..., strategy: AllocationStrategy):
        self.strategy = strategy
    
    async def execute(self, request: RequestDTO) -> ResponseDTO:
        # 1. 候補生成（共通）
        candidates = await self._generate_candidates(...)
        
        # 2. 戦略で割り当て（委譲）
        allocations = await self.strategy.allocate(candidates, fields, crops)
        
        # 3. 改善（共通）
        if enable_local_search:
            allocations = await self._improve(allocations, ...)
        
        # 4. 結果構築（共通）
        return self._build_result(allocations, ...)
```

**効果:**
- 各戦略が独立してテスト可能
- 新しい戦略の追加が容易
- コードの可読性向上（1ファイル300行以下）

---

### 課題3: **ConfigurationとDIの複雑化**

**現状:**
```python
OptimizationConfig(
    # 30+ parameters...
    enable_parallel_candidate_generation: bool = False
    enable_candidate_filtering: bool = True
    enable_adaptive_early_stopping: bool = True
    enable_alns: bool = False
    alns_iterations: int = 1000
    # ... many more
)
```

**問題:**
- 設定パラメータの爆発
- デフォルト値の管理が困難
- バリデーションの欠如

**提案: 階層的Config構造**

```python
# NEW: src/agrr_core/usecase/dto/optimization_config/

@dataclass
class AlgorithmConfig:
    """アルゴリズム設定"""
    type: Literal["dp", "greedy"] = "dp"
    enable_parallel: bool = True


@dataclass
class LocalSearchConfig:
    """局所探索設定"""
    enable: bool = True
    max_iterations: int = 100
    adaptive_stopping: bool = True


@dataclass
class ALNSConfig:
    """ALNS設定"""
    enable: bool = False
    iterations: int = 1000
    destroy_degree: float = 0.3
    temperature_start: float = 100.0


@dataclass
class OptimizationConfig:
    """統合設定"""
    algorithm: AlgorithmConfig = field(default_factory=AlgorithmConfig)
    local_search: LocalSearchConfig = field(default_factory=LocalSearchConfig)
    alns: ALNSConfig = field(default_factory=ALNSConfig)
    
    def validate(self) -> None:
        """設定の整合性チェック"""
        if self.alns.enable and self.local_search.enable:
            raise ValueError("ALNSとLocal Searchは同時に有効にできません")
```

**効果:**
- 設定の意味が明確
- デフォルト値の管理が容易
- バリデーションの実装箇所が明確

---

### 課題4: **テスト戦略の改善**

**現状:**
```
tests/
├── test_entity/       (10 files)
├── test_usecase/      (45 files)  ← 多い
├── test_adapter/      (8 files)
├── test_integration/  (6 files)   ← 少ない
└── test_unit/         (43 files)
```

**問題:**
- 統合テストが少ない（実際の動作確認が不十分）
- テストの粒度が不均一
- E2Eテストが存在しない

**提案: テストピラミッド強化**

```
tests/
├── unit/                      ← 単体テスト（大量）
│   ├── entity/
│   ├── usecase/
│   │   ├── strategies/       ← NEW
│   │   └── optimization/     ← NEW
│   └── adapter/
│
├── integration/               ← 統合テスト（中程度）
│   ├── gateway_integration/
│   ├── optimizer_integration/
│   └── weather_integration/
│
└── e2e/                       ← NEW: E2Eテスト（少数）
    ├── test_full_optimization_workflow.py
    ├── test_weather_to_prediction.py
    └── test_cli_commands.py
```

**新規テスト例:**
```python
# tests/e2e/test_full_optimization_workflow.py

@pytest.mark.e2e
async def test_complete_optimization_workflow():
    """実際のファイルから完全な最適化を実行"""
    # 1. 実データ読み込み
    fields = load_fields("test_data/allocation_fields_large.json")
    crops = load_crops("test_data/allocation_crops_6types.json")
    weather = load_weather("test_data/allocation_weather_1760447748.json")
    
    # 2. 最適化実行
    result = await run_optimization(fields, crops, weather, algorithm="dp")
    
    # 3. 結果検証
    assert result.total_profit > 100000
    assert all(schedule.is_valid() for schedule in result.field_schedules)
    assert no_time_overlaps(result.field_schedules)
```

---

### 課題5: **ドキュメントの散在**

**現状:**
```
docs/
├── ARCHITECTURE.md
├── OPTIMIZATION_ALGORITHM_IMPROVEMENTS.md
├── DP_ALNS_INTEGRATION.md
├── FINAL_DP_ALNS_SUMMARY.md
├── LOCAL_SEARCH_ALNS_UNIFICATION.md
└── ... 多数
```

**問題:**
- 情報が分散
- 最新ドキュメントが不明
- 新規参加者の学習コスト高

**提案: ドキュメント体系の整理**

```
docs/
├── README.md                          ← ドキュメント索引
│
├── architecture/                      ← アーキテクチャ
│   ├── 01_overview.md                # 概要
│   ├── 02_clean_architecture.md      # Clean Architecture
│   ├── 03_entity_layer.md            # Entity層詳細
│   ├── 04_usecase_layer.md           # UseCase層詳細
│   ├── 05_adapter_layer.md           # Adapter層詳細
│   └── 06_framework_layer.md         # Framework層詳細
│
├── algorithms/                        ← アルゴリズム
│   ├── 01_optimization_overview.md   # 最適化概要
│   ├── 02_dp_algorithm.md            # DP詳細
│   ├── 03_greedy_algorithm.md        # Greedy詳細
│   ├── 04_local_search.md            # Hill Climbing
│   ├── 05_alns.md                    # ALNS詳細
│   └── 06_benchmarks.md              # ベンチマーク結果
│
├── guides/                            ← ガイド
│   ├── getting_started.md            # 入門
│   ├── development_guide.md          # 開発ガイド
│   ├── testing_guide.md              # テストガイド
│   └── deployment_guide.md           # デプロイガイド
│
└── api/                               ← API Reference
    ├── cli_reference.md
    └── python_api_reference.md
```

---

## 🎯 提案する改善ロードマップ

### Phase 1: リファクタリング（優先度: 高）

**目標: コードの整理と責任の明確化**

1. **UseCase層の再編成**（2-3日）
   - [ ] `optimization/` ディレクトリ作成
   - [ ] Strategy Patternの導入
   - [ ] Interactorの分割（1190行 → 300行）

2. **Config階層化**（1日）
   - [ ] 階層的Config構造の実装
   - [ ] バリデーション追加

3. **テスト整理**（1-2日）
   - [ ] テストディレクトリ再編成
   - [ ] E2Eテスト追加（3-5ケース）

**成果物:**
- より保守しやすいコードベース
- 明確な責任分離
- 安定性の向上

---

### Phase 2: 機能強化（優先度: 中）

**目標: 最適化性能のさらなる向上**

1. **ハイブリッドアルゴリズム**（3-4日）
   - [ ] DP + Greedy ハイブリッド実装
   - [ ] 問題特性による自動選択
   - [ ] ベンチマーク

2. **並列処理の強化**（2-3日）
   - [ ] 候補生成の完全並列化
   - [ ] ALNS内の並列評価
   - [ ] GPU対応検討（LightGBM予測）

3. **インタラクティブ最適化**（2-3日）
   - [ ] 中間結果の保存・再開
   - [ ] リアルタイム進捗表示
   - [ ] ユーザーフィードバック機能

**成果物:**
- 10-20%の性能向上
- より良いユーザー体験
- 大規模問題への対応

---

### Phase 3: プラットフォーム化（優先度: 低）

**目標: 再利用可能なプラットフォームへ**

1. **Web API化**（5-7日）
   - [ ] FastAPI導入
   - [ ] RESTful API実装
   - [ ] WebSocketリアルタイム通信

2. **Web UI開発**（10-14日）
   - [ ] React/Vue.js フロントエンド
   - [ ] インタラクティブな結果表示
   - [ ] パラメータ調整UI

3. **プラグインシステム**（7-10日）
   - [ ] カスタムアルゴリズムプラグイン
   - [ ] カスタムゲートウェイプラグイン
   - [ ] カスタム制約プラグイン

**成果物:**
- マルチユーザー対応
- ブラウザベースUI
- 拡張可能なプラットフォーム

---

## 📐 推奨アーキテクチャ（改善版）

### 改善後のディレクトリ構造

```
src/agrr_core/
├── entity/                      # Entity Layer (変更なし)
│   ├── entities/
│   ├── value_objects/
│   ├── protocols/
│   ├── validators/
│   └── exceptions/
│
├── usecase/                     # UseCase Layer (再編成)
│   ├── interactors/            # 簡素化されたInteractor
│   │   ├── weather_fetch_interactor.py
│   │   ├── crop_profile_craft_interactor.py
│   │   └── multi_field_crop_allocation_interactor.py  (300行)
│   │
│   ├── optimization/           ← NEW: 最適化専用
│   │   ├── strategies/         # 戦略パターン
│   │   │   ├── base_strategy.py
│   │   │   ├── dp_strategy.py
│   │   │   └── greedy_strategy.py
│   │   ├── algorithms/         # アルゴリズム実装
│   │   │   ├── dp_optimizer.py
│   │   │   ├── greedy_optimizer.py
│   │   │   ├── hill_climbing.py
│   │   │   └── alns_optimizer.py
│   │   ├── operators/          # 近傍操作
│   │   │   ├── destroy/
│   │   │   └── repair/
│   │   └── utils/
│   │       └── allocation_utils.py
│   │
│   ├── domain_services/        ← NEW: ドメインサービス
│   │   ├── crop_rotation_service.py
│   │   ├── field_capacity_service.py
│   │   └── interaction_rule_service.py
│   │
│   ├── dto/                    # 階層化されたDTO
│   │   ├── config/
│   │   │   ├── algorithm_config.py
│   │   │   ├── local_search_config.py
│   │   │   └── alns_config.py
│   │   └── ... (既存のDTO)
│   │
│   ├── gateways/               # 変更なし
│   ├── ports/                  # 変更なし
│   └── exceptions/             # 変更なし
│
├── adapter/                     # Adapter Layer (変更なし)
│   ├── controllers/
│   ├── presenters/
│   ├── gateways/
│   └── ...
│
└── framework/                   # Framework Layer (変更なし)
    ├── services/
    └── config/
```

---

## 🎓 実装ガイドライン

### 1. **新しいアルゴリズムの追加**

```python
# Step 1: Strategyを実装
class MyNewStrategy(AllocationStrategy):
    async def allocate(...) -> List[CropAllocation]:
        # アルゴリズム実装
        pass

# Step 2: Interactorに登録
class MultiFieldCropAllocationInteractor:
    def _create_strategy(self, config: OptimizationConfig):
        if config.algorithm.type == "my_new":
            return MyNewStrategy()
        elif config.algorithm.type == "dp":
            return DPAllocationStrategy()
        # ...

# Step 3: テスト追加
class TestMyNewStrategy:
    async def test_allocate_simple_case(self):
        strategy = MyNewStrategy()
        result = await strategy.allocate(...)
        assert ...
```

### 2. **新しい制約の追加**

```python
# Step 1: Entityに制約を定義
@dataclass
class FieldConstraint:
    """圃場制約"""
    max_consecutive_days: int
    required_rest_days: int

# Step 2: Domain Serviceで検証
class FieldConstraintService:
    def validate(self, allocation, constraint):
        # 制約チェック
        pass

# Step 3: Strategyで利用
class DPAllocationStrategy:
    def __init__(self, constraint_service: FieldConstraintService):
        self.constraint_service = constraint_service
    
    async def allocate(...):
        # 制約を考慮した割り当て
        pass
```

### 3. **新しいゲートウェイの追加**

```python
# Step 1: UseCase層でインターフェース定義
class MyDataGateway(ABC):
    @abstractmethod
    async def fetch(self, params) -> MyData:
        pass

# Step 2: Adapter層で実装
class MyDataApiGateway(MyDataGateway):
    async def fetch(self, params) -> MyData:
        # API呼び出し
        pass

# Step 3: DIで注入
interactor = MyInteractor(my_data_gateway=MyDataApiGateway())
```

---

## 📊 メトリクスと品質指標

### 現状

| メトリクス | 値 | 目標 | 状態 |
|-----------|-----|------|------|
| テストカバレッジ | 30% | 80% | 🔴 要改善 |
| 平均ファイルサイズ | ~100行 | <200行 | 🟢 良好 |
| 最大ファイルサイズ | 1,190行 | <500行 | 🔴 要改善 |
| 循環的複雑度 | 不明 | <10 | ⚪ 計測必要 |
| 技術的負債 | 中程度 | 低 | 🟡 改善中 |

### 改善後の目標

| メトリクス | 目標値 |
|-----------|-------|
| テストカバレッジ | 80%+ |
| 平均ファイルサイズ | ~80行 |
| 最大ファイルサイズ | <300行 |
| 循環的複雑度 | <10 |
| E2Eテスト | 10+ cases |

---

## 🔬 技術的推奨事項

### 1. **型ヒントの徹底**

```python
# Good
async def allocate(
    candidates: List[AllocationCandidate],
    fields: List[Field],
    crops: List[Crop]
) -> List[CropAllocation]:
    ...

# Add mypy to CI/CD
mypy src/agrr_core --strict
```

### 2. **依存性注入の改善**

```python
# Current: 手動DI
controller = Controller(
    gateway1=Gateway1(),
    gateway2=Gateway2(),
    # ... many dependencies
)

# Recommended: DIコンテナ
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    
    # Gateways
    weather_gateway = providers.Singleton(
        WeatherApiGateway,
        http_client=...
    )
    
    # Interactors
    weather_interactor = providers.Factory(
        WeatherFetchInteractor,
        weather_gateway=weather_gateway
    )
```

### 3. **ロギングの統一**

```python
# 構造化ログ導入
import structlog

logger = structlog.get_logger()

logger.info(
    "optimization_started",
    algorithm="dp",
    num_fields=10,
    num_crops=6
)

logger.info(
    "optimization_completed",
    total_profit=217450,
    computation_time=4.85
)
```

### 4. **パフォーマンス計測の自動化**

```python
# デコレータで自動計測
from functools import wraps
import time

def measure_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        
        logger.info(
            "performance_metric",
            function=func.__name__,
            duration=duration
        )
        return result
    return wrapper

@measure_performance
async def allocate(...):
    ...
```

---

## 📚 参考資料

### 内部ドキュメント
- [ARCHITECTURE.md](../ARCHITECTURE.md) - 基本アーキテクチャ
- [FINAL_DP_ALNS_SUMMARY.md](FINAL_DP_ALNS_SUMMARY.md) - DP+ALNS実装レポート
- [DP_VS_GREEDY_6CROPS_ANALYSIS.md](../test_data/DP_VS_GREEDY_6CROPS_ANALYSIS.md) - ベンチマーク分析

### 外部参考
- Clean Architecture (Robert C. Martin)
- Domain-Driven Design (Eric Evans)
- ALNS (Pisinger & Ropke, 2010)
- Weighted Interval Scheduling (Kleinberg & Tardos)

---

## 🎯 まとめと次のステップ

### 現状評価: ⭐⭐⭐⭐☆ (4/5)

**強み:**
- ✅ Clean Architecture準拠
- ✅ 豊富なアルゴリズム選択肢
- ✅ 実用的な機能
- ✅ 拡張性の高い設計

**改善点:**
- 🔧 Interactorの肥大化
- 🔧 テストカバレッジ不足
- 🔧 ドキュメント整理
- 🔧 UseCase層の責任分離

### 即座に実施すべきこと（Quick Wins）

1. **最大ファイル分割** (1日)
   - `multi_field_crop_allocation_greedy_interactor.py` (1190行) を300行×4ファイルに分割

2. **E2Eテスト追加** (1日)
   - 3つの基本E2Eテストを追加

3. **ドキュメント索引作成** (0.5日)
   - `docs/README.md` を作成し、全ドキュメントを整理

### 中長期的に取り組むべきこと

1. **Phase 1: リファクタリング** (1-2週間)
2. **Phase 2: 機能強化** (2-3週間)
3. **Phase 3: プラットフォーム化** (1-2ヶ月)

---

## 🤝 貢献ガイドライン

新しいコードを追加する際は以下を遵守：

1. **Clean Architectureの原則**
   - 依存の方向を守る
   - インターフェースを通じた依存

2. **単一責任原則**
   - 1ファイル < 300行
   - 1クラス 1責任

3. **テストファースト**
   - 新機能には必ずテスト
   - カバレッジ 80%+

4. **ドキュメント更新**
   - コードと同時にドキュメント更新
   - 型ヒントとdocstring必須

---

**作成日**: 2025年
**バージョン**: 1.0
**ステータス**: 提案中

