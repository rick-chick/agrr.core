# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('prompts', 'prompts')]
binaries = []
hiddenimports = ['agrr_core.daemon', 'agrr_core.daemon.server', 'agrr_core.daemon.client', 'agrr_core.daemon.manager', 'pandas', 'numpy', 'numpy.core._multiarray_umath', 'requests', 'pydantic', 'pydantic_core', 'aiohttp', 'beautifulsoup4', 'bs4', 'lxml', 'lxml.etree', 'scipy', 'scipy.special._ufuncs_cxx', 'statsmodels', 'lightgbm', 'sklearn', 'openai', 'dotenv']

# agrr_core: バイナリとhiddenimportsのみ収集、ソースコード（.py）は除外
tmp_ret = collect_all('agrr_core')
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]
# datas += tmp_ret[0]  # ソースコードを含めない（バイトコードのみ）
tmp_ret = collect_all('pandas')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('numpy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('pydantic')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('pydantic_core')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('scipy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('lightgbm')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('sklearn')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['src/agrr_core/__main__.py'],
    pathex=['src'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'pytest', 'pygments', 'py'],
    noarchive=False,
    optimize=2,  # バイトコード最適化（.pyファイルを完全にバイトコード化）
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='agrr',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='agrr',
)
