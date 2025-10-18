# Clean Architecture - Gateway設計ガイドライン

**目的**: UseCase層のGateway interfaceに技術詳細を混入させないための方針  
**重要度**: ★★★ 最重要（アーキテクチャ原則）

---

## ❌ よくある間違い

### 間違い1: 技術詳細をメソッド名に含める

**NG例**:
```python
# ❌ 悪い例 - "load_from_file"はファイルという技術詳細を露呈
class OptimizationResultGateway(ABC):
    @abstractmethod
    async def load_from_file(self) -> Optional[MultiFieldOptimizationResult]:
        """Load from file..."""
        pass
    
    @abstractmethod
    async def save_to_database(self, result: MultiFieldOptimizationResult) -> None:
        """Save to database..."""
        pass
```

**問題点**:
1. **技術詳細の露呈**: "file", "database"などの実装詳細がインターフェースに現れる
2. **抽象化の失敗**: データソースが変わるとインターフェースも変更が必要
3. **UseCase層の汚染**: Interactorが「ファイル」という技術を知ってしまう
4. **テスタビリティ低下**: モック作成時に技術詳細を意識する必要がある

### 間違い2: 複数の抽象レベルが混在

**NG例**:
```python
# ❌ 悪い例 - get_all()とload_from_file()が混在
class MoveInstructionGateway(ABC):
    @abstractmethod
    async def get_all(self) -> List[MoveInstruction]:  # 抽象的 ✓
        pass
    
    @abstractmethod
    async def load_from_file(self) -> List[MoveInstruction]:  # 具体的 ✗
        pass
```

**問題点**:
1. **一貫性の欠如**: 同じインターフェースに抽象/具体が混在
2. **どちらを使うか不明確**: 呼び出し側が混乱
3. **将来の拡張性低下**: 新しいデータソース追加時に対応困難

---

## ✅ 正しい設計

### 原則1: 抽象的なメソッド名のみ使用

**OK例**:
```python
# ✅ 良い例 - データソースを隠蔽した抽象的メソッド
class OptimizationResultGateway(ABC):
    """Gateway interface for optimization result operations.
    
    Note:
        Source configuration (file path, database connection, etc.) is provided
        at initialization time, not at method call time.
    """
    
    @abstractmethod
    async def get(self) -> Optional[MultiFieldOptimizationResult]:
        """Get optimization result from configured source.
        
        Returns:
            Optimization result entity if found, None otherwise
            
        Note:
            Source is configured at gateway initialization.
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, optimization_id: str) -> Optional[MultiFieldOptimizationResult]:
        """Get optimization result by ID."""
        pass
```

**利点**:
1. **データソース非依存**: file, database, API, memoryどれでも対応可能
2. **UseCase層の純粋性**: Interactorはデータの取得先を知らない
3. **テスト容易性**: モックがシンプル
4. **拡張性**: 新しいデータソースを追加しても界面変更不要

### 原則2: 設定は初期化時に渡す

**OK例**:
```python
# ✅ 良い例 - データソースの設定を初期化時に注入
class OptimizationResultFileGateway(OptimizationResultGateway):
    """File-based implementation."""
    
    def __init__(self, file_repository: FileServiceInterface, file_path: str):
        """Initialize with file repository and path.
        
        Args:
            file_repository: File service for I/O
            file_path: Path to the file (configuration)
        """
        self.file_repository = file_repository
        self.file_path = file_path  # ← 設定を保持
    
    async def get(self) -> Optional[MultiFieldOptimizationResult]:
        """Get from configured source (file in this case)."""
        # ← self.file_path を使用してファイル読み込み
        if not self.file_path:
            return None
        
        content = await self.file_repository.read(self.file_path)
        # ... parsing logic ...
        return result
```

**利点**:
1. **設定の分離**: 「何を取得するか」と「どこから取得するか」を分離
2. **再利用性**: 同じgatewayインスタンスで複数回呼び出し可能
3. **明確な責任**: 初期化＝設定、メソッド呼び出し＝データ取得

---

## 📋 Gateway設計チェックリスト

### UseCase層（Gateway Interface）

- [ ] メソッド名に技術用語を含まない（file, database, api, memory等）
- [ ] 抽象的な動詞を使用（get, save, delete, update, create等）
- [ ] データソースをメソッド引数に含めない
- [ ] docstringに「configured source」と明記
- [ ] 複数の抽象レベルを混在させない

**推奨メソッド名**:
- `get()` - 単一のエンティティを取得
- `get_all()` - 全てのエンティティを取得
- `get_by_id(id)` - IDで検索
- `save(entity)` - エンティティを保存
- `delete(id)` - IDで削除
- `update(entity)` - エンティティを更新

**禁止メソッド名**:
- `load_from_file()` ❌
- `save_to_database()` ❌
- `fetch_from_api()` ❌
- `read_from_memory()` ❌

### Adapter層（Gateway Implementation）

- [ ] コンストラクタで設定を受け取る（file_path, connection_string等）
- [ ] `get()`などの抽象メソッド内で技術詳細を実装
- [ ] 同じinterfaceで複数の実装を提供可能（FileGateway, DatabaseGateway等）
- [ ] エラーハンドリングを適切に行う

**実装例**:
```python
# File実装
class EntityFileGateway(EntityGateway):
    def __init__(self, file_service, file_path):
        self.file_service = file_service
        self.file_path = file_path
    
    async def get(self):
        # ファイル読み込みロジック
        content = await self.file_service.read(self.file_path)
        return self._parse(content)

# Database実装
class EntityDatabaseGateway(EntityGateway):
    def __init__(self, db_connection, table_name):
        self.db = db_connection
        self.table = table_name
    
    async def get(self):
        # データベース読み込みロジック
        row = await self.db.query(self.table)
        return self._map_to_entity(row)
```

---

## 🔍 既存コードのパターン分析

### ✅ 正しい例

#### FieldGateway
```python
class FieldGateway(ABC):
    @abstractmethod
    async def get(self, field_id: str) -> Optional[Field]:
        """Get field by ID."""
        pass
    
    @abstractmethod
    async def get_all(self) -> List[Field]:
        """Get all fields from configured source."""
        pass
```
**評価**: ✅ 完璧 - 抽象的、技術非依存

#### CropProfileGateway
```python
class CropProfileGateway(ABC):
    @abstractmethod
    async def get_all(self) -> List[CropProfile]:
        """Get all crop profiles from the configured data source."""
        pass
    
    @abstractmethod
    async def generate(self, crop_query: str) -> CropProfile:
        """Generate a crop profile from the given query."""
        pass
```
**評価**: ✅ 完璧 - "configured data source"と明記

#### InteractionRuleGateway
```python
class InteractionRuleGateway(ABC):
    @abstractmethod
    async def get_rules(self) -> List[InteractionRule]:
        """Load interaction rules from configured source."""
        pass
```
**評価**: ✅ 完璧 - get_rulesは適切な抽象化

### ❌ 修正した例（今回の問題）

#### Before（間違い）:
```python
class OptimizationResultGateway(ABC):
    @abstractmethod
    async def get_by_id(self, optimization_id: str):
        pass
    
    @abstractmethod
    async def load_from_file(self):  # ❌ 技術詳細
        pass
```

#### After（修正後）:
```python
class OptimizationResultGateway(ABC):
    @abstractmethod
    async def get_by_id(self, optimization_id: str):
        pass
    
    @abstractmethod
    async def get(self):  # ✅ 抽象的
        """Get from configured source."""
        pass
```

---

## 🛡️ 再発防止策

### 1. コードレビュー時のチェック項目

**Gateway Interface作成時**:
```markdown
□ メソッド名に技術用語が含まれていないか？
  - file, database, api, memory, cache, http, sql 等
□ "configured source"と明記されているか？
□ データソースがメソッド引数になっていないか？
□ 複数の抽象レベルが混在していないか？
```

**Interactor作成時**:
```markdown
□ Gatewayメソッドを呼ぶ際、技術を意識していないか？
  - `gateway.load_from_file()` ❌
  - `gateway.get()` ✅
□ データソース設定をGateway呼び出しに渡していないか？
```

### 2. 命名規則の統一

#### Gateway Interfaceメソッド名パターン

| 操作 | 推奨メソッド名 | 説明 |
|-----|-------------|------|
| 取得（単一） | `get()` | 設定済みソースから取得 |
| 取得（全件） | `get_all()` | 全て取得 |
| 検索 | `get_by_id(id)` | IDで検索 |
| 検索（複雑） | `find_by_*()` | 条件で検索 |
| 保存 | `save(entity)` | エンティティを保存 |
| 更新 | `update(entity)` | エンティティを更新 |
| 削除 | `delete(id)` | IDで削除 |

#### 禁止パターン
- `*_from_file()`
- `*_from_database()`
- `*_from_api()`
- `*_to_*()`
- `read_*()` (代わりに `get_*()`)
- `write_*()` (代わりに `save_*()`)

### 3. docstringテンプレート

```python
@abstractmethod
async def get_all(self) -> List[Entity]:
    """Get all entities from configured source.
    
    Returns:
        List of Entity instances
        
    Note:
        Source is configured at gateway initialization (file, database, API, etc.)
    """
    pass
```

**必須文言**: "from configured source" + "Note: Source is configured at initialization"

### 4. 実装クラスの命名

**パターン**:
- `EntityFileGateway` - ファイルベース実装
- `EntityDatabaseGateway` - DBベース実装
- `EntityApiGateway` - APIベース実装
- `EntityInMemoryGateway` - メモリベース実装

**重要**: 技術詳細は**実装クラス名**に含めるのはOK、**Interface**に含めるのはNG

---

## 📖 正しい実装フロー

### Step 1: Gateway Interface定義（UseCase層）

```python
# src/agrr_core/usecase/gateways/entity_gateway.py

from abc import ABC, abstractmethod
from typing import Optional, List
from agrr_core.entity.entities.entity import Entity


class EntityGateway(ABC):
    """Gateway interface for entity operations.
    
    Note:
        Data source configuration (file path, DB connection, API endpoint, etc.)
        is provided at gateway initialization time, not at method call time.
    """
    
    @abstractmethod
    async def get_all(self) -> List[Entity]:
        """Get all entities from configured source.
        
        Returns:
            List of Entity instances
            
        Note:
            Source is configured at gateway initialization.
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID from configured source.
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            Entity if found, None otherwise
        """
        pass
```

### Step 2: Gateway実装（Adapter層）

```python
# src/agrr_core/adapter/gateways/entity_file_gateway.py

from agrr_core.usecase.gateways.entity_gateway import EntityGateway
from agrr_core.adapter.interfaces.io.file_service_interface import FileServiceInterface


class EntityFileGateway(EntityGateway):
    """File-based gateway implementation for entity operations."""
    
    def __init__(self, file_repository: FileServiceInterface, file_path: str = ""):
        """Initialize with file repository and file path.
        
        Args:
            file_repository: File service for file I/O operations
            file_path: Path to the entity data file (configuration)
        """
        self.file_repository = file_repository
        self.file_path = file_path  # ← 設定として保持
    
    async def get_all(self) -> List[Entity]:
        """Get all entities from configured source (file in this implementation)."""
        if not self.file_path:
            return []
        
        try:
            # ← ここでファイル読み込み（技術詳細）
            content = await self.file_repository.read(self.file_path)
            data = json.loads(content)
            
            # Parse and return entities
            entities = self._parse_entities(data)
            return entities
            
        except FileNotFoundError:
            return []
        except Exception as e:
            raise ValueError(f"Invalid entity file format: {e}")
    
    async def get_by_id(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID from configured source (file in this implementation)."""
        all_entities = await self.get_all()  # ← get_all()を再利用
        return next((e for e in all_entities if e.entity_id == entity_id), None)
    
    def _parse_entities(self, data: dict) -> List[Entity]:
        """Private helper for parsing."""
        # ... implementation ...
        pass
```

**ポイント**:
- `get_all()` の中でファイル読み込みを実装
- `self.file_path` を初期化時に設定
- `load_from_file()` のような技術詳細メソッドは作らない

### Step 3: Interactorでの使用（UseCase層）

```python
# src/agrr_core/usecase/interactors/entity_process_interactor.py

class EntityProcessInteractor:
    def __init__(self, entity_gateway: EntityGateway):
        """Initialize with gateway.
        
        Args:
            entity_gateway: Gateway for entity operations (implementation unknown)
        """
        self.entity_gateway = entity_gateway  # ← Interfaceのみ知る
    
    async def execute(self, request: RequestDTO) -> ResponseDTO:
        """Execute use case."""
        # ✅ 正しい - 抽象的なメソッドを呼ぶ
        entities = await self.entity_gateway.get_all()
        
        # ❌ 間違い - 技術詳細を呼ぶ
        # entities = await self.entity_gateway.load_from_file()
        
        # Process entities...
        return response
```

### Step 4: CLIでの配線（Framework層）

```python
# src/agrr_core/cli.py

# ファイルパスを引数から取得
file_path = args.entity_file

# Gatewayを初期化（ここで技術詳細を注入）
entity_gateway = EntityFileGateway(
    file_repository=file_service,
    file_path=file_path  # ← 初期化時に設定
)

# Interactorに渡す
interactor = EntityProcessInteractor(
    entity_gateway=entity_gateway  # ← Interfaceとして渡す
)

# 実行
await interactor.execute(request)
```

---

## 🎯 今回の修正内容

### 修正前（間違い）

**OptimizationResultGateway** (UseCase層):
```python
@abstractmethod
async def load_from_file(self) -> Optional[MultiFieldOptimizationResult]:
    """Load from configured file."""  # ❌ "file"という技術詳細
    pass
```

**AllocationAdjustInteractor** (UseCase層):
```python
current_result = await self.optimization_result_gateway.load_from_file()  # ❌
```

### 修正後（正しい）

**OptimizationResultGateway** (UseCase層):
```python
@abstractmethod
async def get(self) -> Optional[MultiFieldOptimizationResult]:
    """Get from configured source."""  # ✅ 抽象的
    pass
```

**AllocationAdjustInteractor** (UseCase層):
```python
current_result = await self.optimization_result_gateway.get()  # ✅
```

**OptimizationResultFileGateway** (Adapter層):
```python
async def get(self) -> Optional[MultiFieldOptimizationResult]:
    """Get from configured source (file in this implementation)."""
    # ← この中でファイル読み込みを実装
    if not self.file_path:
        return None
    content = await self.file_repository.read(self.file_path)
    # ...
```

---

## 🚨 レビュー時の危険信号

以下のパターンを見つけたら即座に修正：

### 危険信号1: Gateway Interfaceに技術用語
```python
# ❌ これを見つけたら即座に修正
async def load_from_file(self):
async def save_to_database(self):
async def fetch_from_api(self):
```

### 危険信号2: Interactorでデータソースを意識
```python
# ❌ Interactorがファイルパスを知っている
file_path = request.file_path
result = await gateway.load(file_path)

# ✅ 正しくはgateway初期化時に設定済み
result = await gateway.get()
```

### 危険信号3: メソッド名の不統一
```python
# ❌ 同じinterfaceで抽象度が異なる
async def get_all(self):  # 抽象的
async def load_from_file(self):  # 具体的
```

---

## 📚 参考: 既存の正しい実装

### WeatherGateway
```python
class WeatherGateway(ABC):
    """Note: Data source is injected at initialization, not passed as arguments."""
    
    @abstractmethod
    async def get(self) -> List[WeatherData]:
        """Get weather data from configured source."""
        pass
```
✅ 完璧な設計

### FieldGateway
```python
class FieldGateway(ABC):
    @abstractmethod
    async def get_all(self) -> List[Field]:
        """Get all fields from configured source.
        
        Note: Source configuration is provided at initialization.
        """
        pass
```
✅ 完璧な設計

### CropProfileGateway
```python
class CropProfileGateway(ABC):
    @abstractmethod
    async def get_all(self) -> List[CropProfile]:
        """Get all crop profiles from the configured data source.
        
        Data sources may include: files, SQL databases, in-memory storage, sessions, etc.
        The implementation determines the actual source.
        """
        pass
```
✅ 完璧な設計 - データソースの例示も含む

---

## 🎯 設計原則まとめ

### Clean Architecture Gateway原則

1. **抽象化原則**: Interfaceは技術非依存であるべき
2. **依存性逆転**: Interactorは抽象（Interface）に依存、具体（Implementation）に依存しない
3. **設定の分離**: データソース設定は初期化時、データ操作は実行時
4. **単一責任**: 1つのメソッド＝1つの明確な責任
5. **開放閉鎖**: 新しいデータソースを追加してもInterfaceは変更しない

---

## 🔧 実践的ガイドライン

### Gateway Interface作成時

#### ステップ1: データソースを忘れる
「ファイル」「データベース」「API」を忘れて、**ビジネス的に何をするか**だけ考える。

**質問**: "何を取得/保存するのか？"
- 最適化結果を取得する → `get()`
- 全ての移動指示を取得する → `get_all()`
- IDで検索する → `get_by_id(id)`

#### ステップ2: メソッド名を決める
技術用語を使わない動詞を選択。

**推奨**: get, save, delete, update, create, find  
**禁止**: load, read, write, fetch, store（技術的すぎる）

#### ステップ3: docstringに明記
```python
"""Get all entities from configured source.

Note:
    Source is configured at gateway initialization (file, database, API, etc.)
"""
```

#### ステップ4: 既存Gatewayと比較
`FieldGateway`, `CropProfileGateway`, `WeatherGateway` と比較して、同じパターンか確認。

### Gateway実装時

#### ステップ1: 設定をコンストラクタで受け取る
```python
def __init__(self, file_repository, file_path):
    self.file_repository = file_repository
    self.file_path = file_path  # ← 設定
```

#### ステップ2: get()等の中で技術詳細を実装
```python
async def get(self):
    # ← ここでファイル読み込み、DB接続等
    content = await self.file_repository.read(self.file_path)
    return self._parse(content)
```

---

## 📋 チェックリスト（新規Gateway作成時）

### UseCase層 - Gateway Interface

- [ ] クラス名: `*Gateway` (interfaceは`*GatewayInterface`としない)
- [ ] 継承: `ABC`
- [ ] メソッドは全て `@abstractmethod`
- [ ] メソッド名: 技術用語なし（get, save, delete等）
- [ ] docstring: "configured source"明記
- [ ] 引数: データソース設定を含まない
- [ ] 戻り値: Entityまたはそのリスト
- [ ] 既存Gatewayと命名規則が統一されているか確認

### Adapter層 - Gateway Implementation

- [ ] クラス名: `*FileGateway`, `*DatabaseGateway`等（技術詳細OK）
- [ ] 継承: 対応するGateway Interface
- [ ] コンストラクタ: 設定を受け取る（file_path, connection等）
- [ ] メソッド実装: get()等の中で技術詳細を実装
- [ ] エラーハンドリング: 適切な例外処理
- [ ] docstring: "in this implementation"と明記

### Interactor（UseCase層）

- [ ] Gateway依存: Interfaceのみ（実装を知らない）
- [ ] メソッド呼び出し: `get()`, `get_all()`等のみ
- [ ] 技術非依存: ファイル、DB等を意識しない
- [ ] テスト容易: モックで簡単にテスト可能

---

## 🎓 教訓

### なぜこの間違いが起きやすいか

1. **直感的すぎる命名**: "ファイルから読む" → `load_from_file()`は自然に見える
2. **実装先行**: Gateway実装を先に考えて、Interfaceに引きずられる
3. **抽象化の難しさ**: 「ファイル」を忘れて「取得」だけ考えるのは練習が必要

### 正しい思考プロセス

#### ❌ 間違った思考
```
「ファイルから読み込む」
  ↓
load_from_file()  ← 技術詳細が混入
```

#### ✅ 正しい思考
```
「最適化結果を取得する」（データソース不問）
  ↓
get()  ← 抽象的
  ↓
実装側で「ファイルから読む」と決める
```

---

## 🔄 修正チェックリスト（今回の対応）

### 修正済み ✅

- [x] `OptimizationResultGateway.load_from_file()` → `get()`に変更
- [x] `MoveInstructionGateway.load_from_file()` → 削除（`get_all()`のみ）
- [x] `AllocationAdjustInteractor` で `get()` を使用
- [x] テストコードを `get()` / `get_all()` に修正
- [x] 全31テスト合格確認 ✅

### 影響調査 ✅

- [x] 他の機能への影響なし確認
- [x] 既存Gatewayパターンとの整合性確認
- [x] テスト実行で動作確認

---

## 📖 このガイドラインの使い方

### 新規Gateway作成時
1. このドキュメントを開く
2. 「チェックリスト」セクションを確認
3. 「正しい実装フロー」に従って実装
4. 「既存の正しい実装」と比較

### コードレビュー時
1. 「危険信号」セクションで問題パターンを検索
2. 「間違い例」と比較
3. 「修正例」を参照して指摘

### リファクタリング時
1. 「よくある間違い」で該当箇所を特定
2. 「正しい設計」を参照
3. 「修正チェックリスト」で確認

---

## 🎯 今後の対策

### 1. Pull Request時の自動チェック

**チェック項目**:
```bash
# Gateway interfaceに技術用語が含まれていないかチェック
grep -r "load_from_file\|save_to_\|fetch_from_\|read_from_\|write_to_" \
  src/agrr_core/usecase/gateways/
```

### 2. AI Assistantへの指示

**コード生成時の指示**:
```
新しいGatewayを作成する際は：
1. 必ず既存のFieldGateway/CropProfileGatewayと同じパターンを使用
2. メソッド名に技術用語（file, database, api）を含めない
3. get(), get_all(), get_by_id()などの抽象的な名前のみ使用
4. docstringに"configured source"と明記
5. CLEAN_ARCHITECTURE_GATEWAY_GUIDELINES.mdを参照
```

### 3. アーキテクチャレビュー定期実施

**月次レビュー項目**:
- Gateway interfaceの命名規則チェック
- Interactorの技術非依存性チェック
- 新規コンポーネントのアーキテクチャ準拠確認

---

## 📚 参考資料

### Clean Architecture原典
- Robert C. Martin著 "Clean Architecture"
- Chapter 22: The Clean Architecture

### プロジェクト内資料
- `ARCHITECTURE.md` - アーキテクチャ設計
- `usecase/gateways/*.py` - Gateway Interface定義集
- `adapter/gateways/*.py` - Gateway実装集

---

## ✅ このガイドラインの適用範囲

### 対象
- ✅ Gateway Interface（UseCase層）
- ✅ Gateway Implementation（Adapter層）
- ✅ Interactor（UseCase層）

### 対象外
- Framework層のService（技術詳細OK）
  - `FileService.read()` ← これはOK
  - `HttpClient.post()` ← これもOK
- Adapter層のMapper
- Presenter

---

## 🎊 まとめ

### 黄金ルール

> **Gateway Interfaceは技術を知らない。**  
> **技術詳細は全てGateway Implementationに隠蔽する。**

### 簡単チェック

新しいGatewayメソッドを作成したら、次の質問に答える：

**Q**: このメソッド名から、データソースがファイル/DB/APIのどれか推測できるか？  
**A**: Yesなら ❌ 間違い、Noなら ✅ 正しい

**Q**: Interactorがこのメソッドを呼ぶとき、技術的なことを意識するか？  
**A**: Yesなら ❌ 間違い、Noなら ✅ 正しい

---

**このガイドラインに従うことで、Clean Architectureの原則を守り、保守性・テスト性・拡張性の高いコードを実現できます。**

