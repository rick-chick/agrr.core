#!/usr/bin/env python3
"""Build script to create a standalone executable for agrr CLI."""

import os
import shutil
import sys
import zipapp
from pathlib import Path

def build_executable():
    """Build a standalone executable using zipapp."""
    
    # プロジェクトのルートディレクトリ
    project_root = Path(__file__).parent
    
    # ビルド用の一時ディレクトリ
    build_dir = project_root / "build_temp"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir()
    
    # src/agrr_core を build_temp/agrr_core にコピー
    src_dir = project_root / "src" / "agrr_core"
    dest_dir = build_dir / "agrr_core"
    shutil.copytree(src_dir, dest_dir)
    
    # __main__.py を作成（エントリーポイント）
    main_content = """#!/usr/bin/env python3
from agrr_core.cli import main

if __name__ == "__main__":
    main()
"""
    
    with open(build_dir / "__main__.py", "w") as f:
        f.write(main_content)
    
    # distディレクトリを作成
    dist_dir = project_root / "dist"
    dist_dir.mkdir(exist_ok=True)
    
    # zipappで実行可能ファイルを作成
    output_file = dist_dir / "agrr"
    
    print(f"Building executable: {output_file}")
    zipapp.create_archive(
        build_dir,
        target=output_file,
        interpreter="/usr/bin/env python3",
        compressed=True
    )
    
    # 実行権限を付与
    os.chmod(output_file, 0o755)
    
    # 一時ディレクトリを削除
    shutil.rmtree(build_dir)
    
    print(f"✓ Successfully built executable: {output_file}")
    print(f"✓ File size: {output_file.stat().st_size / 1024:.1f} KB")
    print(f"\nUsage:")
    print(f"  {output_file} --help")
    print(f"  {output_file} weather --help")
    print(f"  {output_file} crop --help")
    print(f"\nNote: This requires Python and dependencies to be installed on the target system.")

if __name__ == "__main__":
    build_executable()

