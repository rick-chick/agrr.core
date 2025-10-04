# CLI Container API Reference

`CLIContainer`は、CLIアプリケーションの依存性注入を管理するFramework層のコンポーネントです。クリーンアーキテクチャに従って、各層の依存関係を適切に設定します。

## クラス概要

```python
class CLIContainer:
    """Dependency injection container for CLI application."""
```

**パス**: `src/agrr_core/framework/container.py`

## コンストラクタ

```python
def __init__(self, config: Dict[str, Any] = None) -> None
```

### パラメータ

| パラメータ | 型 | デフォルト | 説明 |
|---|---|---|---|
| `config` | `Dict[str, Any]` | `None` | 設定辞書 |

### 設定オプション

| キー | 型 | デフォルト | 説明 |
|---|---|---|---|
| `open_meteo_base_url` | `str` | `"https://archive-api.open-meteo.com/v1/archive"` | Open-Meteo APIのベースURL |

## 主要メソッド

### `get_weather_repository()`

天気データリポジトリのインスタンスを取得します。

```python
def get_weather_repository(self) -> OpenMeteoWeatherRepository
```

**戻り値**: `OpenMeteoWeatherRepository` - 天気データリポジトリ

**特徴**:
- シングルトンパターンでインスタンスを管理
- 設定されたベースURLを使用

**例**:
```python
container = CLIContainer({
    'open_meteo_base_url': 'https://test-api.open-meteo.com/v1/archive'
})

repository = container.get_weather_repository()
# repository.base_url = "https://test-api.open-meteo.com/v1/archive"
```

### `get_cli_presenter()`

CLIプレゼンターのインスタンスを取得します。

```python
def get_cli_presenter(self) -> CLIWeatherPresenter
```

**戻り値**: `CLIWeatherPresenter` - CLIプレゼンター

**特徴**:
- シングルトンパターンでインスタンスを管理
- デフォルトで`sys.stdout`を使用

**例**:
```python
presenter = container.get_cli_presenter()
presenter.display_success_message("Test message")
```

### `get_fetch_weather_interactor()`

天気データ取得インタラクターのインスタンスを取得します。

```python
def get_fetch_weather_interactor(self) -> FetchWeatherDataInteractor
```

**戻り値**: `FetchWeatherDataInteractor` - 天気データ取得インタラクター

**依存関係**:
- `weather_repository`: 天気データリポジトリ
- `cli_presenter`: CLIプレゼンター

**例**:
```python
interactor = container.get_fetch_weather_interactor()
# interactor.weather_data_input_port = repository
# interactor.weather_presenter_output_port = presenter
```

### `get_cli_controller()`

CLIコントローラーのインスタンスを取得します。

```python
def get_cli_controller(self) -> CLIWeatherController
```

**戻り値**: `CLIWeatherController` - CLIコントローラー

**依存関係**:
- `fetch_weather_interactor`: 天気データ取得インタラクター
- `cli_presenter`: CLIプレゼンター

**例**:
```python
controller = container.get_cli_controller()
# controller.fetch_weather_interactor = interactor
# controller.cli_presenter = presenter
```

### `run_cli()`

CLIアプリケーションを実行します。

```python
async def run_cli(self, args: list = None) -> None
```

**パラメータ**:
- `args` (list): コマンドライン引数リスト

**処理フロー**:
1. CLIコントローラーの取得
2. コントローラーの実行

**例**:
```python
await container.run_cli(['weather', '--location', '35.6762,139.6503', '--days', '7'])
```

## 依存関係グラフ

```
CLIContainer
    ├── get_cli_controller()
    │   ├── get_fetch_weather_interactor()
    │   │   ├── get_weather_repository()
    │   │   └── get_cli_presenter()
    │   └── get_cli_presenter()
    └── run_cli()
        └── get_cli_controller()
```

## 使用例

### 基本的な使用

```python
from agrr_core.framework.container import CLIContainer
import asyncio

# コンテナの作成
config = {
    'open_meteo_base_url': 'https://archive-api.open-meteo.com/v1/archive'
}
container = CLIContainer(config)

# CLIアプリケーションの実行
async def main():
    await container.run_cli(['weather', '--location', '35.6762,139.6503', '--days', '7'])

asyncio.run(main())
```

### カスタム設定

```python
# テスト用の設定
test_config = {
    'open_meteo_base_url': 'https://test-api.open-meteo.com/v1/archive'
}
test_container = CLIContainer(test_config)

# 個別コンポーネントの取得
repository = test_container.get_weather_repository()
presenter = test_container.get_cli_presenter()
interactor = test_container.get_fetch_weather_interactor()
controller = test_container.get_cli_controller()
```

### デフォルト設定

```python
# 設定なしでコンテナを作成
container = CLIContainer()

# デフォルト設定が使用される
repository = container.get_weather_repository()
# repository.base_url = "https://archive-api.open-meteo.com/v1/archive"
```

## シングルトンパターン

各コンポーネントはシングルトンパターンで管理され、同じインスタンスが再利用されます。

```python
container = CLIContainer()

# 同じインスタンスが返される
presenter1 = container.get_cli_presenter()
presenter2 = container.get_cli_presenter()
assert presenter1 is presenter2  # True

repository1 = container.get_weather_repository()
repository2 = container.get_weather_repository()
assert repository1 is repository2  # True
```

## エラーハンドリング

コンテナ自体はエラーハンドリングを行いませんが、各コンポーネントのエラーは適切に伝播されます。

```python
try:
    await container.run_cli(['weather', '--location', 'invalid,location'])
except Exception as e:
    print(f"CLI execution failed: {e}")
```

## テスト

```python
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from agrr_core.framework.container import CLIContainer

class TestCLIContainer:
    def setup_method(self):
        self.config = {
            'open_meteo_base_url': 'https://test-api.open-meteo.com/v1/archive'
        }
        self.container = CLIContainer(self.config)
    
    def test_get_weather_repository(self):
        """Test getting weather repository instance."""
        repo = self.container.get_weather_repository()
        
        assert repo is not None
        assert repo.base_url == 'https://test-api.open-meteo.com/v1/archive'
        
        # Test singleton behavior
        repo2 = self.container.get_weather_repository()
        assert repo is repo2
    
    def test_get_cli_presenter(self):
        """Test getting CLI presenter instance."""
        presenter = self.container.get_cli_presenter()
        
        assert presenter is not None
        
        # Test singleton behavior
        presenter2 = self.container.get_cli_presenter()
        assert presenter is presenter2
    
    @pytest.mark.asyncio
    async def test_run_cli(self):
        """Test running CLI application."""
        # Mock the controller's run method
        mock_controller = MagicMock()
        mock_controller.run = AsyncMock()
        
        with patch.object(self.container, 'get_cli_controller', return_value=mock_controller):
            await self.container.run_cli(['weather', '--location', '35.6762,139.6503'])
            
            mock_controller.run.assert_called_once_with(['weather', '--location', '35.6762,139.6503'])
```

## 拡張

新しいコンポーネントを追加する場合：

1. 対応するgetterメソッドを実装
2. シングルトンパターンを適用
3. 依存関係を適切に設定
4. テストケースを作成

```python
def get_new_component(self) -> NewComponent:
    """Get new component instance."""
    if 'new_component' not in self._instances:
        dependency = self.get_dependency()
        self._instances['new_component'] = NewComponent(dependency)
    return self._instances['new_component']
```
