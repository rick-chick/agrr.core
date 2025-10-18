# クリーンアーキテクチャ設計

## 概要

このプロジェクトはクリーンアーキテクチャに基づいて設計されており、以下の4つの主要層で構成されます：

1. **Entity Layer** (エンティティ層)
2. **UseCase Layer** (ユースケース層) 
3. **Adapter Layer** (アダプター層)
4. **Framework Layer** (フレームワーク層)

## 依存関係の方向

```
Framework Layer → Adapter Layer → UseCase Layer → Entity Layer
```

- **Entity Layer**: 他の層に依存しない（最内層）
- **UseCase Layer**: Entity Layerのみに依存
- **Adapter Layer**: UseCase Layerのみに依存
- **Framework Layer**: Adapter Layerのみに依存

### 依存関係の制約
1. **直接依存の禁止**: 隣接しない層への直接依存は禁止
2. **依存性逆転**: インターフェースを通じてのみ依存
3. **単一責任**: 各層は一つの内側層のみを参照

## 層別構成要素

### 1. Entity Layer (エンティティ層)
**責任**: ビジネスロジックとエンティティの定義

#### 構成要素:
- **Entity** - ビジネスエンティティ（IDを持つオブジェクト）
  - User, Task, Project, Organization
- **Entity Exception** - エンティティ例外
  - UserNotFoundError, TaskNotFoundError, BusinessRuleViolationError

#### ディレクトリ構造:
```
src/agrr.core/entity/
├── entities/           # エンティティ
├── exceptions/       # エンティティ例外
└── __init__.py
```

### 2. UseCase Layer (ユースケース層)
**責任**: アプリケーション固有のビジネスルールとユースケースの実装

#### 構成要素:
- **Interactor** - ユースケースの実装
  - CreateUserInteractor, UpdateUserInteractor, DeleteUserInteractor, GetUserInteractor
  - CreateTaskInteractor, AssignTaskInteractor, CompleteTaskInteractor
- **Input Port** - 入力ポート（Interactorのインターフェース）
  - UserInputPort, TaskInputPort, ProjectInputPort
- **Output Port** - 出力ポート（Presenterのインターフェース）
  - UserOutputPort, TaskOutputPort, NotificationOutputPort
- **Gateway** - ゲートウェイインターフェース（外部システムとの接続）
  - WeatherDataGateway, PredictionServiceGateway, UserRepositoryGateway
- **DTO** - データ転送オブジェクト
  - CreateUserDTO, UpdateUserDTO, UserResponseDTO, CreateTaskDTO, TaskResponseDTO
- **UseCase Exception** - ユースケース例外
  - UserCreationFailedError, TaskAssignmentFailedError, ValidationError

#### ディレクトリ構造:
```
src/agrr.core/usecase/
├── interactors/       # ユースケースの実装
├── ports/            # 入力・出力ポート
│   ├── input/        # 入力ポート（Interactorのインターフェース）
│   └── output/       # 出力ポート（Presenterのインターフェース）
├── gateways/         # ゲートウェイインターフェース
├── dto/              # データ転送オブジェクト
├── exceptions/       # ユースケース例外
└── __init__.py
```

### 3. Adapter Layer (アダプター層 / Interface Adapters)
**責任**: UseCase層とFramework層の間のインターフェース変換

#### 構成要素:
- **Gateway** - ゲートウェイ実装（UseCase層のGatewayインターフェースの実装）
  - WeatherGatewayImpl, PredictionGatewayImpl, CropProfileGatewayImpl
  - Framework層のServicesを注入してUseCaseに提供
- **Presenter** - プレゼンター（Output Portの実装）
  - WeatherPresenter, PredictionPresenter, CropProfilePresenter
  - UseCaseの出力を外部形式（JSON, Table等）に変換
- **Controller** - コントローラー（Input Portの実装）
  - WeatherCliController, PredictionCliController
  - 外部からの入力をUseCaseのDTOに変換
- **Mapper** - データマッパー
  - WeatherMapper, EntityToDtoMapper
  - Entity ↔ DTO変換
- **Interfaces** - Framework層向けインターフェース定義（役割別に分類）
  - **Clients**: HttpClientInterface, LLMClientInterface
  - **I/O Services**: FileServiceInterface, CsvServiceInterface, HtmlTableServiceInterface
  - **ML Services**: PredictionServiceInterface, TimeSeriesServiceInterface
  - **Structures**: HtmlTable, TableRow（共通データ構造）
- **Services** - ドメインサービス（UseCase層との橋渡し）
  - WeatherLinearInterpolator - 天気データ補間
- **Adapter Exception** - アダプター例外
  - ExternalServiceError, DataMappingError

#### ディレクトリ構造:
```
src/agrr.core/adapter/
├── gateways/         # ゲートウェイ実装
├── presenters/       # プレゼンター（Output Portの実装）
├── controllers/      # コントローラー（Input Portの実装）
├── mappers/          # データマッパー
├── interfaces/       # Framework層向けインターフェース定義（役割別）
│   ├── clients/      # 外部接続クライアントのインターフェース
│   ├── io/           # I/Oサービスのインターフェース
│   ├── ml/           # ML/予測サービスのインターフェース
│   └── structures/   # 共通データ構造
├── services/         # ドメインサービス
├── exceptions/       # アダプター例外
└── __init__.py
```


### 4. Framework Layer (フレームワーク層 / Frameworks & Drivers)
**責任**: 外部システムとの直接的な通信、技術的実装詳細、外部ライブラリの使用

#### 構成要素:
- **Services（技術的サービス実装）** - 役割別に分類
  - **Clients** - 外部システム接続クライアント
    - HttpClient - HTTP通信（requestsライブラリ使用）
    - LLMClient - LLM API通信（OpenAI等）
  - **I/O Services** - ファイル・データI/O処理
    - FileService - ファイルI/O基本実装
    - CsvService - CSV処理
    - HtmlTableService - HTMLパース（BeautifulSoup使用）
  - **ML Services** - 機械学習・予測サービス
    - ARIMAPredictionService - 時系列予測（statsmodels使用）
    - TimeSeriesARIMAService - ARIMA実装
    - LightGBMPredictionService - 機械学習予測（lightgbm使用）
    - FeatureEngineeringService - 特徴量エンジニアリング
  - **Utils** - 共通ユーティリティ
    - InterpolationService - 線形補間処理

- **Configuration** - 設定管理とDI
  - AgrrCoreContainer - 依存性注入コンテナ
  - Environment Config, Logging Config
  
- **Framework Exception** - フレームワーク例外
  - ConfigurationError, InfrastructureError

#### ディレクトリ構造:
```
src/agrr.core/framework/
├── services/         # 技術的サービス実装（役割別）
│   ├── clients/      # 外部接続クライアント（HTTP, LLM等）
│   ├── io/           # I/O処理サービス（File, CSV, HTML等）
│   ├── ml/           # 機械学習サービス（ARIMA, LightGBM等）
│   └── utils/        # 共通ユーティリティ（補間等）
├── config/           # 設定管理、DIコンテナ
├── exceptions/       # フレームワーク例外
└── __init__.py
```


## データフロー

### 標準的なフロー
1. **入力**: Framework Layer → Adapter Layer (Controller) → UseCase Layer (Interactor)
2. **処理**: UseCase Layer (Interactor) → Entity Layer (Entity)
3. **外部システムアクセス**: UseCase Layer (Interactor) → UseCase Layer (Gatewayインターフェース) → Adapter Layer (Gateway実装) → Framework Layer (Services)
4. **出力**: UseCase Layer (Interactor) → UseCase Layer (Output Port) → Adapter Layer (Presenter) → Framework Layer

### 依存関係の実現方法
- **UseCase → Entity**: UseCase層がEntity層を直接使用
- **Adapter → UseCase**: Adapter層がUseCase層のGatewayインターフェース、Input Port、Output Portを実装
- **Framework → Adapter**: Framework層がAdapter層のインターフェースを使用

### インターフェース分離の原則
- 各層は隣接する内側層のインターフェースのみを知る
- 具体的な実装は外側層で行う
- 依存性注入により結合度を下げる

### Gateway設計の原則

**黄金ルール**: Gateway Interface（UseCase層）は技術詳細を知らない

#### ✅ 正しい設計
```python
# UseCase層 - Gateway Interface
class EntityGateway(ABC):
    @abstractmethod
    async def get(self) -> Optional[Entity]:
        """Get entity from configured source."""  # ← "configured source"
        pass
    
    @abstractmethod
    async def get_all(self) -> List[Entity]:
        """Get all entities from configured source."""
        pass
```

#### ❌ 禁止パターン
```python
# ❌ メソッド名に技術用語を含めない
async def load_from_file(self):      # file, database, api等は禁止
async def save_to_database(self):
async def fetch_from_api(self):
```

#### 実装のポイント
1. **データソース設定は初期化時に注入**
   ```python
   gateway = EntityFileGateway(file_service, file_path)  # ← 初期化時
   result = await gateway.get()  # ← 呼び出し時はデータソース不問
   ```

2. **技術詳細はAdapter層の実装内に隠蔽**
   ```python
   # Adapter層 - Gateway Implementation
   class EntityFileGateway(EntityGateway):
       async def get(self):
           # ← この中でファイル読み込み（技術詳細）
           content = await self.file_repository.read(self.file_path)
           return self._parse(content)
   ```

3. **推奨メソッド名**: `get()`, `get_all()`, `get_by_id()`, `save()`, `delete()`

4. **参考実装**: `FieldGateway`, `CropProfileGateway`, `WeatherGateway`

詳細: `docs/CLEAN_ARCHITECTURE_GATEWAY_GUIDELINES.md`

## 例外処理の流れ

各層で適切な例外を定義し、上位層でキャッチして処理：

1. **Entity Exception** → UseCase Layer でキャッチ
2. **UseCase Exception** → Adapter Layer でキャッチ  
3. **Adapter Exception** → Framework Layer でキャッチ
4. **Framework Exception** → 最終的なエラーレスポンス

## テスト戦略

- **Unit Tests**: 各層の個別テスト
- **Integration Tests**: 層間の結合テスト
- **E2E Tests**: Framework Layer から全体のテスト

各層でモックを使用して依存関係を分離し、テストの独立性を保つ。

---

## 命名規則

### インターフェースと実装
- **インターフェース**: 必ず`*Interface`サフィックス
  - 例: `HttpClientInterface`, `FileServiceInterface`, `PredictionServiceInterface`
  
- **実装**: サフィックスなし、役割に応じて命名
  - 例: `HttpClient`, `FileService`, `ARIMAPredictionService`

### Client vs Service
- **Client**: 外部システムへの接続・通信
  - 例: `HttpClient`, `LLMClient`
  
- **Service**: データ処理・変換・機能提供
  - 例: `FileService`, `CsvService`, `PredictionService`, `InterpolationService`

---
