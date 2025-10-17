# リファクタリング ロードマップ

最優先で実施すべきリファクタリングの具体的な実装プラン

## 🎯 Phase 1: Interactor分割（最優先）

### 現状の問題

**ファイル: `multi_field_crop_allocation_greedy_interactor.py`**
- 行数: **1,190行** 🔴
- 責任: 10個以上
- テスト: 複雑化

### 分割プラン

#### Before (1ファイル)
```
multi_field_crop_allocation_greedy_interactor.py (1,190行)
├── AllocationCandidate (内部クラス)
├── 候補生成ロジック (200行)
├── DP実装 (150行)
├── Greedy実装 (100行)
├── Hill Climbing (150行)
├── ALNS統合 (50行)
├── ヘルパーメソッド (300行)
└── 結果構築 (200行)
```

#### After (5ファイル)

```
src/agrr_core/usecase/optimization/
├── strategies/
│   ├── allocation_strategy.py              (50行)
│   │   └── class AllocationStrategy(ABC)   # 基底クラス
│   │
│   ├── dp_allocation_strategy.py           (200行)
│   │   ├── class DPAllocationStrategy
│   │   ├── _weighted_interval_scheduling_dp()
│   │   ├── _find_latest_non_overlapping()
│   │   └── _enforce_max_revenue_constraint()
│   │
│   └── greedy_allocation_strategy.py       (250行)
│       ├── class GreedyAllocationStrategy
│       ├── _greedy_allocation()
│       └── _apply_interaction_rules()
│
├── candidate_generator.py                   (350行)
│   ├── class CandidateGenerator
│   ├── _generate_candidates()
│   ├── _generate_candidates_parallel()
│   └── _post_filter_candidates()
│
└── multi_field_optimizer.py                 (300行)
    ├── class MultiFieldOptimizer
    ├── optimize() - メイン処理
    ├── _improve_with_local_search()
    ├── _improve_with_alns()
    └── _build_result()

# Interactor (削減: 1190行 → 100行)
src/agrr_core/usecase/interactors/
└── multi_field_crop_allocation_interactor.py (100行)
    └── class MultiFieldCropAllocationInteractor
        ├── execute() - オーケストレーション
        └── 各コンポーネントの組み立て
```

---

### 実装例

#### 1. 基底Strategy

```python
# src/agrr_core/usecase/optimization/strategies/allocation_strategy.py

from abc import ABC, abstractmethod
from typing import List

from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.crop_allocation_entity import CropAllocation


class AllocationCandidate:
    """割り当て候補（共通データクラス）"""
    # ... (既存のAllocationCandidateをここに移動)


class AllocationStrategy(ABC):
    """割り当て戦略の基底クラス"""
    
    @abstractmethod
    async def allocate(
        self,
        candidates: List[AllocationCandidate],
        fields: List[Field],
        crops: List[Crop],
    ) -> List[CropAllocation]:
        """候補から割り当てを選択
        
        Args:
            candidates: 割り当て候補のリスト
            fields: フィールドのリスト
            crops: 作物のリスト
            
        Returns:
            選択された割り当てのリスト
        """
        pass
```

#### 2. DP Strategy

```python
# src/agrr_core/usecase/optimization/strategies/dp_allocation_strategy.py

from typing import List

from agrr_core.usecase.optimization.strategies.allocation_strategy import (
    AllocationStrategy,
    AllocationCandidate,
)


class DPAllocationStrategy(AllocationStrategy):
    """DP戦略: フィールド単位でWeighted Interval Schedulingを解く"""
    
    async def allocate(
        self,
        candidates: List[AllocationCandidate],
        fields: List[Field],
        crops: List[Crop],
    ) -> List[CropAllocation]:
        """DP最適化による割り当て"""
        # グループ化
        candidates_by_field = self._group_by_field(candidates)
        
        # 各フィールドでDP
        allocations = []
        for field in fields:
            field_candidates = candidates_by_field.get(field.field_id, [])
            selected = self._weighted_interval_scheduling_dp(field_candidates)
            allocations.extend(selected)
        
        # グローバル制約
        allocations = self._enforce_max_revenue_constraint(allocations, crops)
        
        return allocations
    
    def _weighted_interval_scheduling_dp(
        self,
        candidates: List[AllocationCandidate],
    ) -> List[AllocationCandidate]:
        """Weighted Interval Scheduling DP"""
        # ... (既存実装を移動)
```

#### 3. 簡素化されたInteractor

```python
# src/agrr_core/usecase/interactors/multi_field_crop_allocation_interactor.py

class MultiFieldCropAllocationInteractor:
    """マルチフィールド作物割り当て最適化 (オーケストレーター)"""
    
    def __init__(
        self,
        field_gateway: FieldGateway,
        crop_gateway: CropProfileGateway,
        weather_gateway: WeatherGateway,
        config: OptimizationConfig,
    ):
        self.field_gateway = field_gateway
        self.crop_gateway = crop_gateway
        self.weather_gateway = weather_gateway
        self.config = config
        
        # コンポーネント作成
        self.candidate_generator = CandidateGenerator(
            weather_gateway=weather_gateway,
            config=config
        )
        
        self.optimizer = MultiFieldOptimizer(config=config)
        
        # 戦略選択
        self.strategy = self._create_strategy(config)
    
    def _create_strategy(self, config: OptimizationConfig) -> AllocationStrategy:
        """設定に基づいて戦略を作成"""
        if config.algorithm.type == "dp":
            return DPAllocationStrategy()
        elif config.algorithm.type == "greedy":
            return GreedyAllocationStrategy(
                interaction_rule_service=self.interaction_rule_service
            )
        else:
            raise ValueError(f"Unknown algorithm: {config.algorithm.type}")
    
    async def execute(
        self,
        request: MultiFieldCropAllocationRequestDTO
    ) -> MultiFieldCropAllocationResponseDTO:
        """最適化を実行（オーケストレーション）"""
        start_time = time.time()
        
        # 1. データ読み込み
        fields = await self._load_fields(request.field_ids)
        crops = await self.crop_gateway.get_all()
        
        # 2. 候補生成（委譲）
        candidates = await self.candidate_generator.generate(
            fields=fields,
            crops=crops,
            planning_start=request.planning_period_start,
            planning_end=request.planning_period_end
        )
        
        # 3. 初期割り当て（戦略に委譲）
        allocations = await self.strategy.allocate(candidates, fields, crops)
        
        # 4. 改善（オプティマイザーに委譲）
        if self.config.local_search.enable:
            allocations = await self.optimizer.improve(
                allocations,
                candidates,
                fields,
                crops
            )
        
        # 5. 結果構築
        result = self._build_result(
            allocations,
            fields,
            time.time() - start_time
        )
        
        return MultiFieldCropAllocationResponseDTO(optimization_result=result)
```

**改善点:**
- ✅ 100行に削減（1190行 → 100行）
- ✅ 各コンポーネントが独立
- ✅ テストが容易
- ✅ 拡張が容易

---

## 🔧 実装手順（Step by Step）

### Step 1: 新ディレクトリ作成

```bash
mkdir -p src/agrr_core/usecase/optimization/strategies
mkdir -p src/agrr_core/usecase/optimization/algorithms
mkdir -p src/agrr_core/usecase/optimization/operators
mkdir -p src/agrr_core/usecase/optimization/utils
mkdir -p src/agrr_core/usecase/domain_services
```

### Step 2: 基底クラス作成

```bash
# allocation_strategy.py を作成
# AllocationCandidateクラスを移動
# AllocationStrategyベースクラスを定義
```

### Step 3: DP Strategy抽出

```bash
# dp_allocation_strategy.py を作成
# _weighted_interval_scheduling_dp() を移動
# _find_latest_non_overlapping() を移動
# _enforce_max_revenue_constraint() を移動
```

### Step 4: Greedy Strategy抽出

```bash
# greedy_allocation_strategy.py を作成
# _greedy_allocation() を移動
# _apply_interaction_rules() を移動
```

### Step 5: Candidate Generator抽出

```bash
# candidate_generator.py を作成
# _generate_candidates() を移動
# _generate_candidates_parallel() を移動
```

### Step 6: Optimizer抽出

```bash
# multi_field_optimizer.py を作成
# _local_search() → improve_with_hill_climbing() に改名・移動
# ALNS統合コードを移動
```

### Step 7: Interactor簡素化

```bash
# multi_field_crop_allocation_interactor.py に改名
# execute() のみ残す
# 各コンポーネントを組み立て
```

### Step 8: テスト更新

```bash
# 各Strategyの単体テスト作成
# Interactorの統合テスト更新
# E2Eテスト追加
```

---

## ✅ チェックリスト

### リファクタリング前

- [ ] 既存テストが全て成功することを確認
- [ ] 現在のベンチマーク結果を記録
- [ ] ブランチ作成 (`git checkout -b refactor/strategy-pattern`)

### リファクタリング中

- [ ] Step 1-8を順番に実施
- [ ] 各Stepでテスト実行
- [ ] コミットは小さく（1 Step = 1 Commit）

### リファクタリング後

- [ ] 全テストが成功
- [ ] ベンチマーク結果が維持/改善
- [ ] ドキュメント更新
- [ ] コードレビュー
- [ ] マージ

---

## 📊 期待される効果

### コード品質

| メトリクス | Before | After | 改善 |
|-----------|--------|-------|------|
| 最大ファイルサイズ | 1,190行 | 350行 | **-70%** |
| 平均メソッド長 | 30行 | 15行 | **-50%** |
| 循環的複雑度 | 高 | 低 | ✅ |
| テスト容易性 | 困難 | 容易 | ✅ |

### 開発効率

| 項目 | Before | After |
|------|--------|-------|
| 新アルゴリズム追加 | 3日 | **1日** |
| バグ修正時間 | 2時間 | **30分** |
| テスト作成 | 困難 | **容易** |
| コードレビュー | 困難 | **容易** |

### 保守性

- ✅ 各コンポーネントが独立
- ✅ 責任が明確
- ✅ 変更の影響範囲が限定的
- ✅ 新規開発者のオンボーディングが容易

---

## 🚀 Quick Start: 最初の1ファイル分割

最も効果的な最初の一歩を示します。

### ターゲット: AllocationCandidateの分離

**理由:**
- 複数箇所で使用される基本データ構造
- 独立性が高い
- テストが容易

**実装:**

```bash
# 1. ファイル作成
touch src/agrr_core/usecase/optimization/allocation_candidate.py

# 2. コード移動
# AllocationCandidateクラスを新ファイルに移動

# 3. インポート更新
# 各ファイルでimport文を更新

# 4. テスト実行
pytest tests/test_usecase/test_multi_field_crop_allocation_dp.py -v

# 5. コミット
git add .
git commit -m "refactor: Extract AllocationCandidate to separate file"
```

**所要時間**: 30分
**リスク**: 低
**効果**: 
- 1ファイル 100行削減
- AllocationCandidateの再利用性向上

---

## 📝 実装Tips

### 1. **段階的移行**

❌ **Bad: 一度に全部変更**
```bash
# 危険: 大量の変更を一度に
git commit -m "Refactor everything"  # 1000+ lines changed
```

✅ **Good: 小さく段階的に**
```bash
git commit -m "refactor: Extract AllocationCandidate"      # +100 -100
git commit -m "refactor: Extract DPAllocationStrategy"     # +200 -200
git commit -m "refactor: Extract GreedyAllocationStrategy" # +250 -250
# ... 各コミットで必ずテストを実行
```

### 2. **テスト駆動リファクタリング**

```python
# Step 1: 既存の動作を保証するテストを追加
def test_existing_behavior():
    # 現在の動作をテスト
    assert current_behavior_works()

# Step 2: リファクタリング実施
# ... コード変更 ...

# Step 3: テストが通ることを確認
# pytest で全テスト実行

# Step 4: 新しいテストを追加
def test_new_structure():
    # 新しい構造のテスト
    assert new_structure_works()
```

### 3. **後方互換性の維持**

```python
# 移行期間中は旧インターフェースも提供

# NEW: 新しいインターフェース
from agrr_core.usecase.optimization.strategies import DPAllocationStrategy

# DEPRECATED: 旧インターフェース（互換性のため）
from agrr_core.usecase.interactors.multi_field_crop_allocation_greedy_interactor import (
    AllocationCandidate  # DeprecationWarning
)

import warnings

class AllocationCandidate:  # 旧クラス
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "AllocationCandidate will be removed in v2.0. "
            "Use agrr_core.usecase.optimization.allocation_candidate instead.",
            DeprecationWarning
        )
        # ... 実装
```

---

## 🎯 マイルストーン

### Milestone 1: 基礎構造 (1週間)

- [ ] `optimization/` ディレクトリ作成
- [ ] `AllocationCandidate` 分離
- [ ] `AllocationStrategy` 基底クラス作成
- [ ] 基本テスト作成

**検証基準:**
- テストカバレッジ維持
- ベンチマーク結果維持

### Milestone 2: Strategy分離 (1週間)

- [ ] `DPAllocationStrategy` 実装
- [ ] `GreedyAllocationStrategy` 実装
- [ ] 各Strategyの単体テスト
- [ ] ベンチマーク実行

**検証基準:**
- 全テスト成功
- ベンチマーク結果 ±5%以内

### Milestone 3: Interactor簡素化 (3日)

- [ ] `CandidateGenerator` 抽出
- [ ] `MultiFieldOptimizer` 抽出
- [ ] Interactor書き換え（100行）
- [ ] 統合テスト更新

**検証基準:**
- E2Eテスト成功
- 実データでの動作確認

### Milestone 4: 完成 (2日)

- [ ] ドキュメント更新
- [ ] サンプルコード更新
- [ ] Deprecationワーニング追加
- [ ] リリースノート作成

**検証基準:**
- 全ドキュメント整合性確認
- CI/CD通過

---

## 📈 ROI（投資対効果）分析

### 投資

| 項目 | 工数 |
|------|------|
| 設計 | 1日 |
| 実装 | 10日 |
| テスト | 3日 |
| ドキュメント | 2日 |
| **合計** | **16日** |

### リターン（年間）

| 項目 | Before | After | 削減 |
|------|--------|-------|------|
| 新機能開発 | 3日 | 1日 | **-66%** |
| バグ修正 | 2時間 | 30分 | **-75%** |
| コードレビュー | 1時間 | 20分 | **-66%** |
| オンボーディング | 2週間 | 3日 | **-78%** |

**推定年間削減工数:** 60-80日相当

**ROI:** 16日投資 → 60-80日削減 = **375-500% ROI** 🚀

---

## 💡 追加提案

### 提案1: パフォーマンスモニタリング

```python
# src/agrr_core/framework/monitoring/performance_monitor.py

import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class PerformanceMetric:
    operation: str
    duration: float
    timestamp: float
    metadata: Dict


class PerformanceMonitor:
    """パフォーマンス計測"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
    
    @contextmanager
    def measure(self, operation: str, **metadata):
        start = time.time()
        yield
        duration = time.time() - start
        
        self.metrics.append(PerformanceMetric(
            operation=operation,
            duration=duration,
            timestamp=start,
            metadata=metadata
        ))
    
    def report(self) -> Dict:
        """レポート生成"""
        return {
            "total_operations": len(self.metrics),
            "total_duration": sum(m.duration for m in self.metrics),
            "by_operation": self._group_by_operation(),
        }

# 使用例
monitor = PerformanceMonitor()

with monitor.measure("candidate_generation", num_fields=10):
    candidates = await generate_candidates(...)

with monitor.measure("dp_optimization", num_candidates=1000):
    allocations = dp_optimize(...)

print(monitor.report())
```

### 提案2: 設定プロファイル

```python
# src/agrr_core/usecase/dto/config/presets.py

class OptimizationPresets:
    """よく使う設定のプリセット"""
    
    @staticmethod
    def small_problem() -> OptimizationConfig:
        """小規模問題（≤5フィールド、≤4作物）"""
        return OptimizationConfig(
            algorithm=AlgorithmConfig(type="dp"),
            local_search=LocalSearchConfig(max_iterations=100),
            enable_parallel=False,
        )
    
    @staticmethod
    def large_problem() -> OptimizationConfig:
        """大規模問題（10+フィールド、6+作物）"""
        return OptimizationConfig(
            algorithm=AlgorithmConfig(type="greedy"),
            local_search=LocalSearchConfig(max_iterations=50),
            enable_parallel=True,
        )
    
    @staticmethod
    def high_quality() -> OptimizationConfig:
        """最高品質（時間に余裕がある場合）"""
        return OptimizationConfig(
            algorithm=AlgorithmConfig(type="dp"),
            alns=ALNSConfig(enable=True, iterations=2000),
            enable_parallel=True,
        )

# 使用例
config = OptimizationPresets.small_problem()
```

### 提案3: 最適化結果の可視化

```python
# src/agrr_core/adapter/presenters/optimization_visualizer.py

import matplotlib.pyplot as plt
from typing import List

class OptimizationVisualizer:
    """最適化結果の可視化"""
    
    def plot_gantt_chart(
        self,
        result: MultiFieldOptimizationResult,
        output_path: str
    ):
        """ガントチャートで作付けスケジュールを表示"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        for i, schedule in enumerate(result.field_schedules):
            for alloc in schedule.allocations:
                ax.barh(
                    y=i,
                    width=(alloc.completion_date - alloc.start_date).days,
                    left=alloc.start_date.toordinal(),
                    height=0.8,
                    label=alloc.crop.name
                )
        
        plt.savefig(output_path)
    
    def plot_profit_breakdown(self, result):
        """利益の内訳を円グラフで表示"""
        # ...

# CLI統合
agrr optimize allocate ... --visualize gantt --output result.png
```

---

## 🎓 学習リソース

### 新規開発者向け

1. **アーキテクチャ理解**（2-3日）
   - [ ] ARCHITECTURE.md を読む
   - [ ] Clean Architecture書籍
   - [ ] コードベース探索

2. **ドメイン理解**（2-3日）
   - [ ] Entity層のコード読解
   - [ ] 作物成長モデル理解
   - [ ] 最適化問題の理解

3. **実装理解**（3-5日）
   - [ ] 小規模機能から着手
   - [ ] テストを読む
   - [ ] デバッグ実行

### アルゴリズム開発者向け

1. **既存アルゴリズム理解**（1-2日）
   - [ ] DP実装の読解
   - [ ] Greedy実装の読解
   - [ ] ベンチマーク結果分析

2. **新アルゴリズム開発**（3-7日）
   - [ ] Strategy実装
   - [ ] 単体テスト作成
   - [ ] ベンチマーク実行

---

## 🤝 コントリビューション

このリファクタリングに参加したい場合：

1. **Issue作成**
   - タイトル: "Refactoring: Strategy Pattern Introduction"
   - 内容: このドキュメントを参照

2. **ブランチ作成**
   ```bash
   git checkout -b refactor/strategy-pattern
   ```

3. **PR作成**
   - 各Milestoneごとに別PR
   - レビュー依頼

---

**次のアクション:**

即座に始められるQuick Wins:
1. ✅ **AllocationCandidate分離** (30分) ← 今すぐ可能！
2. ✅ **基本E2Eテスト追加** (1時間)
3. ✅ **ドキュメント索引作成** (30分)

**リファクタリングを始めますか？**

