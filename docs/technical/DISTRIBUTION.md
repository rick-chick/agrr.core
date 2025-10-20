# 配布方法ガイド

## 概要

`agrr`の配布方法は、ターゲット環境に応じて5つの選択肢があります。

## 配布方法の選択

| 方法 | Python環境 | サイズ | 推奨用途 |
|------|-----------|--------|---------|
| Wheelパッケージ | 必要 | 90KB | 一般ユーザー（最推奨） |
| ネイティブバイナリ | 不要 | 125-353MB | Python環境がない環境 |
| Docker | 不要 | 中 | 環境の完全隔離が必要な場合 |
| システムパッケージ | 必要 | 小 | OS標準パッケージマネージャー使用 |
| PyPI公開 | 必要 | 小 | 最も簡単（公開後） |

---

## 1. Wheelパッケージ配布 ⭐️ 推奨

Python環境があれば最も軽量で簡単な方法です。

### ビルド

```bash
python3 -m build
```

### 配布・インストール

```bash
# 配布ファイル: dist/agrr_core-0.1.0-py3-none-any.whl

# ユーザー側でインストール
pip install agrr_core-0.1.0-py3-none-any.whl
agrr --help
```

### メリット
- ✅ 軽量（90KB）
- ✅ 依存関係が自動インストール
- ✅ クロスプラットフォーム対応
- ✅ Python 3.8以上で動作

---

## 2. ネイティブバイナリ（PyInstaller）

Python環境が不要で、単体で実行可能なバイナリを配布します。

### 前提条件

```bash
# Python 3.12（共有ライブラリ付き）のインストール
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
env PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.12.8
pyenv local 3.12.8

# 依存関係のインストール
pip install -r requirements.txt
pip install -e .
```

### ビルド

#### onedir形式（推奨：高速起動）

```bash
./build_standalone.sh --onedir
```

- **起動時間**: 約2秒
- **サイズ**: 353MB
- **出力**: `dist/agrr/` ディレクトリ、`dist/agrr-YYYYMMDD.tar.gz`

#### onefile形式（コンパクト）

```bash
./build_standalone.sh --onefile
```

- **起動時間**: 約6秒
- **サイズ**: 125MB
- **出力**: `dist/agrr` 単一ファイル

### 配布

#### onedir形式

```bash
# 配布
dist/agrr-YYYYMMDD.tar.gz をユーザーに配布

# ユーザー側での使用
tar -xzf agrr-YYYYMMDD.tar.gz
./agrr-YYYYMMDD/agrr --help
```

#### onefile形式

```bash
# 配布
dist/agrr をユーザーに配布

# ユーザー側での使用
chmod +x agrr
./agrr --help
```

### システムワイドインストール

```bash
sudo tar -xzf agrr-YYYYMMDD.tar.gz -C /opt/
sudo ln -s /opt/agrr-YYYYMMDD/agrr /usr/local/bin/agrr

# どこからでも使用可能
agrr --help
```

### システム要件
- Linux (Ubuntu 18.04+, Debian, WSL2等)
- x86_64アーキテクチャ
- Python環境不要
- 依存関係不要（全て含まれています）

### 依存関係の追加方法

新しいPythonパッケージを追加する場合：

1. `requirements.txt`に追加
2. `agrr.spec`に追加（hiddenimportsとcollect_all）
3. `build_standalone.sh`に追加（--hidden-importと--collect-all）
4. 再ビルド

詳細は各ファイルの既存パッケージを参考にしてください。

### トラブルシューティング

#### ModuleNotFoundError / ImportError

```bash
# 症状
ModuleNotFoundError: No module named 'pandas'
ImportError: numpy.core._multiarray_umath
```

**解決策**: `agrr.spec`と`build_standalone.sh`に該当パッケージを追加して再ビルド

#### Python 3.12 with shared library support not found

**解決策**: 
```bash
env PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.12.8
pyenv local 3.12.8
```

---

## 3. Docker

環境を完全に隔離して配布します。

### ビルドと実行

```bash
# イメージをビルド
docker build -t agrr .

# 実行
docker run --rm agrr --help
docker run --rm agrr weather --location 35.6762,139.6503 --days 7

# エイリアスを作成（便利）
alias agrr='docker run --rm agrr'
```

### 配布

```bash
# イメージを保存
docker save agrr > agrr-docker.tar

# ユーザー側で読み込み
docker load < agrr-docker.tar
```

### メリット
- ✅ Python環境不要
- ✅ 完全に隔離された環境
- ✅ 依存関係の問題なし
- ✅ クロスプラットフォーム

---

## 4. システムパッケージ（.deb/.rpm）

OS標準のパッケージマネージャーで管理できます。

### Ubuntu/Debian

```bash
# fpmをインストール
gem install fpm

# .debパッケージを作成
fpm -s python -t deb \
    --python-pip /usr/bin/pip3 \
    --python-package-name-prefix python3 \
    agrr_core
```

---

## 5. PyPI公開

最も簡単で標準的な配布方法です。

```bash
# 公開後、どこからでもインストール可能
pip install agrr-core
agrr --help
```

---

## 推奨配布方法まとめ

### 一般ユーザー向け
1. **PyPI公開** - `pip install agrr-core`で完結
2. **Wheelパッケージ** - オフライン環境でも使用可能

### Python環境がない場合
1. **Docker** - 環境の完全な隔離、クロスプラットフォーム
2. **ネイティブバイナリ** - 単体実行可能

### 企業/エンタープライズ向け
1. **Docker** - コンテナ環境で標準化
2. **システムパッケージ** - OS標準のパッケージマネージャーで管理
