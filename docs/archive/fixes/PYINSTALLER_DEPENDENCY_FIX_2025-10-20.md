# PyInstallerバイナリの依存関係問題の修正

## 問題の概要

agrrバイナリ（PyInstallerでビルド）が依存関係（Pandas、Numpy等）を正しくロードできず、実行時にエラーが発生していた。

## 原因

PyInstallerの`--collect-all agrr_core`オプションのみでビルドしていたため、agrr_core自体のコードしか収集されず、requirements.txtに定義されている外部依存関係（pandas、numpy、requests、pydantic等）が含まれていなかった。

## 影響範囲

- agrrバイナリから天気データ取得コマンド実行時にエラー
- Railsアプリケーションの`FetchWeatherDataJob`が失敗
- 回避策として、バイナリの代わりにPythonから直接`agrr_core.cli`を実行する必要があった

## 修正内容

### 1. agrr.spec の修正

以下の依存関係を明示的に追加：

```python
hiddenimports = [
    'agrr_core.daemon', 
    'agrr_core.daemon.server', 
    'agrr_core.daemon.client', 
    'agrr_core.daemon.manager',
    # External dependencies from requirements.txt
    'pandas', 'numpy', 'requests', 'pydantic', 'pydantic_core',
    'aiohttp', 'beautifulsoup4', 'bs4', 'lxml', 'scipy',
    'statsmodels', 'lightgbm', 'sklearn', 'openai', 'dotenv'
]

# Collect all from critical dependencies
for package in ['pandas', 'numpy', 'pydantic', 'pydantic_core', 'scipy', 'lightgbm', 'sklearn']:
    try:
        tmp_ret = collect_all(package)
        datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
    except:
        pass
```

### 2. build_standalone.sh の修正

以下のオプションを追加：

```bash
--collect-all pandas \
--collect-all numpy \
--collect-all pydantic \
--collect-all pydantic_core \
--collect-all scipy \
--collect-all lightgbm \
--collect-all sklearn \
--hidden-import pandas \
--hidden-import numpy \
--hidden-import numpy.core._multiarray_umath \
--hidden-import requests \
--hidden-import pydantic \
--hidden-import pydantic_core \
--hidden-import aiohttp \
--hidden-import beautifulsoup4 \
--hidden-import bs4 \
--hidden-import lxml \
--hidden-import lxml.etree \
--hidden-import scipy \
--hidden-import scipy.special._ufuncs_cxx \
--hidden-import statsmodels \
--hidden-import lightgbm \
--hidden-import sklearn \
--hidden-import openai \
--hidden-import dotenv
```

### 3. ドキュメントの更新

- `docs/technical/DISTRIBUTION.md` - トラブルシューティングセクションを追加
- `README.md` - PyInstallerの注意事項を追加

## 動作確認

修正後のバイナリで以下を確認：

```bash
# バイナリのビルド
./build_standalone.sh --onedir

# 動作確認
./dist/agrr/agrr weather --location 35.6762,139.6503 --days 7 --data-source openmeteo --json

# 依存関係のロードを確認
./dist/agrr/agrr --help
```

## 今後の対策

### 新しい依存関係を追加する場合

1. `requirements.txt`に追加
2. `agrr.spec`の`hiddenimports`リストに追加
3. C拡張を含むパッケージの場合、`collect_all`のループにも追加
4. `build_standalone.sh`の両方のビルドコマンド（onefile/onedir）に追加
   - `--collect-all <package>` (C拡張を含む場合)
   - `--hidden-import <package>`

### 検証方法

バイナリをビルドした後、必ず以下を確認：

```bash
# 1. 基本動作確認
./dist/agrr/agrr --help

# 2. 天気データ取得確認
./dist/agrr/agrr weather --location 35.6762,139.6503 --days 1 --data-source openmeteo

# 3. 依存関係のインポート確認
./dist/agrr/agrr --version  # (バージョン確認コマンドがあれば)
```

## 参考情報

- PyInstallerドキュメント: https://pyinstaller.org/en/stable/
- PyInstaller Hooks: https://pyinstaller.org/en/stable/hooks.html
- `docs/technical/DISTRIBUTION.md` - 配布方法ガイド

## 修正日時

2025年10月20日

## 影響するファイル

- `agrr.spec`
- `build_standalone.sh`
- `docs/technical/DISTRIBUTION.md`
- `README.md`

