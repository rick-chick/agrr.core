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
- **Input Port** - 入力ポート（インターフェース）
  - UserInputPort, TaskInputPort, ProjectInputPort
- **Output Port** - 出力ポート（Repository Interfaceの役割）
  - UserOutputPort, TaskOutputPort, NotificationOutputPort
- **DTO** - データ転送オブジェクト
  - CreateUserDTO, UpdateUserDTO, UserResponseDTO, CreateTaskDTO, TaskResponseDTO
- **UseCase Exception** - ユースケース例外
  - UserCreationFailedError, TaskAssignmentFailedError, ValidationError

#### ディレクトリ構造:
```
src/agrr.core/usecase/
├── interactors/       # ユースケースの実装
├── ports/            # 入力・出力ポート
│   ├── input/        # 入力ポート
│   └── output/       # 出力ポート（Repository Interface）
├── dto/              # データ転送オブジェクト
├── exceptions/       # ユースケース例外
└── __init__.py
```

### 3. Adapter Layer (アダプター層)
**責任**: 外部システムとの接続とデータ変換

#### 構成要素:
- **Repository** - リポジトリの実装（Output Portの実装）
  - SqlUserRepository, MongoUserRepository, InMemoryUserRepository, SqlTaskRepository
- **Gateway** - 外部システムとのゲートウェイ
  - EmailGateway, NotificationGateway, FileStorageGateway, ExternalApiGateway
- **Presenter** - プレゼンター（出力の整形）
  - UserPresenter, TaskPresenter, ErrorPresenter, JsonPresenter
- **Controller** - コントローラー（入力の受け取り）
  - UserController, TaskController, HealthController
- **Mapper** - データマッパー
  - UserMapper, TaskMapper, EntityToDtoMapper, DtoToEntityMapper
- **Adapter Exception** - アダプター例外
  - DatabaseConnectionError, ExternalServiceError, DataMappingError

#### ディレクトリ構造:
```
src/agrr.core/adapter/
├── repositories/     # リポジトリ実装（Output Portの実装）
├── gateways/         # 外部システムゲートウェイ
├── presenters/       # プレゼンター
├── controllers/      # コントローラー
├── mappers/          # データマッパー
├── exceptions/       # アダプター例外
└── __init__.py
```

### 4. Framework Layer (フレームワーク層)
**責任**: 外部フレームワークとの統合

#### 構成要素:
- **Web Framework** - Webフレームワーク
  - FastAPI Router, Middleware, Authentication, Rate Limiting
- **Database** - データベース設定・接続
  - Database Connection, Migration, Connection Pool, Transaction Manager
- **External APIs** - 外部API統合
  - HTTP Client, API Client, Retry Logic, Circuit Breaker
- **Message Queue** - メッセージキュー
  - Producer, Consumer, Message Handler, Dead Letter Queue
- **Configuration** - 設定管理
  - Environment Config, Secret Management, Feature Flags, Logging Config
- **Framework Exception** - フレームワーク例外
  - ConfigurationError, InfrastructureError, TimeoutError

#### ディレクトリ構造:
```
src/agrr.core/framework/
├── web/              # Webフレームワーク
├── database/         # データベース設定
├── external/         # 外部API
├── messaging/        # メッセージキュー
├── config/           # 設定管理
├── exceptions/       # フレームワーク例外
└── __init__.py
```

## データフロー

### 標準的なフロー
1. **入力**: Framework Layer → Adapter Layer (Controller) → UseCase Layer (Input Port)
2. **処理**: UseCase Layer (Interactor) → Entity Layer (Entity)
3. **出力**: UseCase Layer (Output Port) → Adapter Layer (Presenter) → Framework Layer

### 依存関係の実現方法
- **UseCase → Entity**: UseCase層がEntity層を直接使用
- **Adapter → UseCase**: Adapter層がUseCase層のOutput Portを実装
- **Framework → Adapter**: Framework層がAdapter層のインターフェースを使用

### インターフェース分離の原則
- 各層は隣接する内側層のインターフェースのみを知る
- 具体的な実装は外側層で行う
- 依存性注入により結合度を下げる

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
