"""一键打包《深空当铺计算器》为单文件 exe。

用法：
    python build.py

依赖：PySide6、PyInstaller。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_NAME = "深空当铺计算器"
ICON = ROOT / "assets" / "app.ico"


def main() -> int:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("未安装 PyInstaller。请先运行：")
        print("  python -m pip install pyinstaller")
        return 1

    if not ICON.is_file():
        print(f"找不到图标：{ICON}")
        return 1

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--uac-admin",
        "--name",
        APP_NAME,
        "--icon",
        str(ICON),
        "--add-data",
        f"{ICON};assets",
        "--distpath",
        str(ROOT / "dist"),
        "--workpath",
        str(ROOT / "build" / "pyinstaller"),
        "--specpath",
        str(ROOT / "build"),
        str(ROOT / "main.py"),
    ]
    print("正在打包：", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)

    output = ROOT / "dist" / f"{APP_NAME}.exe"
    if not output.is_file():
        print("打包结束，但没有找到输出 exe。")
        return 1

    size_mb = output.stat().st_size / (1024 * 1024)
    print()
    print(f"已生成：{output}")
    print(f"大小：{size_mb:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
