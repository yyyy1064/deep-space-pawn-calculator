"""离屏截取主界面，用于开发阶段检查布局。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtGui import QFont  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from app.main_window import MainWindow  # noqa: E402
from app.theme import APP_STYLESHEET  # noqa: E402


def main() -> int:
    app = QApplication(sys.argv[:1])
    app.setStyle("Fusion")
    font = QFont("Microsoft YaHei UI")
    font.setPixelSize(14)
    app.setFont(font)
    app.setStyleSheet(APP_STYLESHEET)

    width = int(os.environ.get("CAPTURE_WIDTH", "1240"))
    height = int(os.environ.get("CAPTURE_HEIGHT", "820"))

    window = MainWindow()
    window.resize(width, height)
    window.show()
    app.processEvents()

    page = window.dream_dust_page
    page.paste_spin.setValue(61.6)
    page.concentration_spin.setValue(70.0)
    page.multiplier_spin.setValue(3.1)
    page.protein_spin.setValue(5.0)
    page.agent_combo.setCurrentIndex(0)
    page.agent_concentration_spin.setValue(97.0)
    page.neutralizer_concentration_spin.setValue(98.0)
    app.processEvents()

    output = Path(__file__).resolve().parent.parent / "preview" / "main.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    pixmap = window.grab()
    if not pixmap.save(str(output), "PNG"):
        print("failed to save screenshot", file=sys.stderr)
        return 1
    print(f"wrote {output} ({pixmap.width()}x{pixmap.height()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
