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
  - Framework層のRepositoryを注入してUseCaseに提供
- **Presenter** - プレゼンター（Output Portの実装）
  - WeatherPresenter, PredictionPresenter, CropProfilePresenter
  - UseCaseの出力を外部形式（JSON, Table等）に変換
- **Controller** - コントローラー（Input Portの実装）
  - WeatherCliController, PredictionCliController
  - 外部からの入力をUseCaseのDTOに変換
- **Mapper** - データマッパー
  - WeatherMapper, EntityToDtoMapper
  - Entity ↔ DTO変換
- **Interfaces** - インターフェース定義
  - PredictionServiceInterface, HttpServiceInterface, FileRepositoryInterface
  - Framework層が実装すべきインターフェースを定義
- **Adapter Exception** - アダプター例外
  - ExternalServiceError, DataMappingError

#### ディレクトリ構造:
```
src/agrr.core/adapter/
├── gateways/         # ゲートウェイ実装（Framework層のRepositoryを抽象化）
├── presenters/       # プレゼンター（Output Portの実装）
├── controllers/      # コントローラー（Input Portの実装）
├── mappers/          # データマッパー
├── interfaces/       # Framework層向けインターフェース定義
├── exceptions/       # アダプター例外
└── __init__.py
```


### 4. Framework Layer (フレームワーク層 / Frameworks & Drivers)
**責任**: 外部システムとの直接的な通信、技術的実装詳細、外部ライブラリの使用

#### 構成要素:
- **Repository実装** - 外部システムとの直接通信（データアクセス層）
  - WeatherAPIOpenMeteoRepository - Open-Meteo API通信
  - WeatherJMARepository - JMA API通信
  - WeatherFileRepository - ファイルベースの天気データ
  - CropProfileFileRepository - 作物プロファイルファイル
  - 外部API、データベース、ファイルシステムとの直接I/O
  - Adapter層のインターフェースを実装
- **Technical Services** - 技術的サービス実装
  - HttpClient - HTTP通信（requestsライブラリ使用）
  - FileRepository - ファイルI/O基本実装
  - HtmlTableFetcher - HTMLパース（BeautifulSoup使用）
  - ARIMAPredictionService - 時系列予測（statsmodels使用）
  - LightGBMPredictionService - 機械学習予測（lightgbm使用）
  - TimeSeriesARIMAService - ARIMA実装
  - FeatureEngineeringService - 特徴量エンジニアリング
- **InMemory Repositories** - テスト用メモリ実装
  - InMemoryCropProfileRepository
  - InMemoryFieldRepository
  - InMemoryOptimizationResultRepository
- **Configuration** - 設定管理とDI
  - AgrrCoreContainer - 依存性注入コンテナ
  - Environment Config, Logging Config
- **Framework Exception** - フレームワーク例外
  - ConfigurationError, InfrastructureError

#### ディレクトリ構造:
```
src/agrr.core/framework/
├── repositories/     # Repository実装（外部システムとの直接通信）
├── services/         # 技術的サービス実装（ML、HTTP、File等）
├── config/           # 設定管理、DIコンテナ
├── exceptions/       # フレームワーク例外
└── __init__.py
```


## データフロー

### 標準的なフロー
1. **入力**: Framework Layer → Adapter Layer (Controller) → UseCase Layer (Interactor)
2. **処理**: UseCase Layer (Interactor) → Entity Layer (Entity)
3. **外部システムアクセス**: UseCase Layer (Interactor) → UseCase Layer (Gatewayインターフェース) → Adapter Layer (Gateway実装) → Adapter Layer (Service)
4. **出力**: UseCase Layer (Interactor) → UseCase Layer (Output Port) → Adapter Layer (Presenter) → Framework Layer

### 依存関係の実現方法
- **UseCase → Entity**: UseCase層がEntity層を直接使用
- **Adapter → UseCase**: Adapter層がUseCase層のGatewayインターフェース、Input Port、Output Portを実装
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

---

## 補足: Repository実装の配置

✅ **2025-10-14 更新:** すべてのRepository実装を標準的なClean Architectureに従い`framework/repositories/`に配置しました。

**配置されているRepository実装:**
- WeatherAPIOpenMeteoRepository - Open-Meteo API通信
- WeatherJMARepository - JMA API通信
- WeatherFileRepository - ファイルベースの天気データ
- CropProfileFileRepository - 作物プロファイルファイル
- CropProfileLLMRepository - LLMベースの作物プロファイル
- FieldFileRepository - 圃場ファイル
- InteractionRuleFileRepository - 相互作用ルールファイル
- PredictionStorageRepository - 予測結果ストレージ
- InMemory*Repository - テスト用メモリ実装

これにより、標準的なClean Architectureの定義に完全準拠しました。

---
