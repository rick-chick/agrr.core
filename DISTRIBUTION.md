# 配布方法ガイド

## 概要

`agrr`の配布方法は、ターゲット環境に応じて複数の選択肢があります。

## 1. Wheelパッケージ配布 ⭐️ **最も推奨**

### メリット
- ✅ Python環境があれば動作（Python 3.8+）
- ✅ 依存関係が自動インストール
- ✅ 軽量（90KB）
- ✅ クロスプラットフォーム対応

### ビルド方法
```bash
python3 -m build
```

### 配布・インストール
```bash
# 配布ファイル
dist/agrr_core-0.1.0-py3-none-any.whl

# ユーザー側でインストール
pip install agrr_core-0.1.0-py3-none-any.whl
agrr --help
```

## 2. ネイティブバイナリ（PyInstaller）⚠️ **環境依存が強い**

### 制約
- ❌ libpython-dev が必要（システムパッケージ）
- ❌ ビルド環境とターゲット環境のOS/アーキテクチャが一致必要
- ❌ ファイルサイズが大きい（100MB+）
- ❌ C拡張（numpy, pandas, scipy）のバンドルが複雑

### ビルド方法（Linux）
```bash
# システムライブラリをインストール（要sudo）
sudo apt install libpython3.12-dev python3.12-dev

# ビルド
./build_standalone.sh
```

### 問題
WSL環境ではlibpythonのインストールに制限がある場合があります。

## 3. Docker 🐳 **真のスタンドアロン**

### メリット
- ✅ Python環境不要
- ✅ 完全に隔離された環境
- ✅ 依存関係の問題なし
- ✅ クロスプラットフォーム

### 使用方法
```bash
# イメージをビルド
docker build -t agrr .

# 実行
docker run --rm agrr --help
docker run --rm agrr weather --location 35.6762,139.6503 --days 7
docker run --rm agrr crop --query "トマト"

# エイリアスを作成（便利）
alias agrr='docker run --rm agrr'
agrr --help
```

### 配布方法
```bash
# Dockerイメージを保存
docker save agrr > agrr-docker.tar

# ユーザー側で読み込み
docker load < agrr-docker.tar
```

## 4. システムパッケージ（.deb/.rpm）

### Ubuntu/Debianの場合
```bash
# fpm をインストール
gem install fpm

# .debパッケージを作成
fpm -s python -t deb \
    --python-pip /usr/bin/pip3 \
    --python-package-name-prefix python3 \
    agrr_core
```

## 5. PyPI公開（最も簡単）

### 公開後
```bash
# どこからでもインストール可能
pip install agrr-core
agrr --help
```

## 推奨配布方法

### 一般ユーザー向け
1. **PyPI公開** - `pip install agrr-core`で完結
2. **Wheelパッケージ** - オフライン環境でも使用可能

### 企業/エンタープライズ向け
1. **Docker** - 環境の完全な隔離
2. **システムパッケージ** - OS標準のパッケージマネージャーで管理

### 技術者向け
1. **GitHubから直接** - `pip install git+https://github.com/...`
2. **Wheelパッケージ** - ローカルインストール

## 真のネイティブバイナリが難しい理由

Pythonアプリケーション（特にC拡張を含む）を真のネイティブバイナリにする場合：

1. **C拡張の問題**
   - numpy, pandas, scipyなどはCで書かれている
   - 動的リンクライブラリに依存
   - バンドルが非常に複雑

2. **環境依存**
   - libpython、libcなどのシステムライブラリが必要
   - ビルド環境とターゲット環境の一致が必須

3. **ファイルサイズ**
   - すべての依存関係を含めると100MB以上
   - Wheelパッケージ（90KB）の1000倍以上

4. **実用性**
   - Pythonエコシステムでは`pip install`が標準
   - ネイティブバイナリは例外的な使用例

## 結論

**Wheelパッケージ + pip installが最も実用的です。**

Python環境が不要な場合は**Docker**を使用してください。

