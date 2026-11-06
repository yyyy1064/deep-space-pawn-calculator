"""深空当铺 · 便携计算终端入口。"""

from __future__ import annotations

import ctypes
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from app.theme import APP_STYLESHEET


def _set_windows_app_id() -> None:
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "DeepSpacePawn.Calculator.0.1"
        )
    except Exception:
        pass


def main() -> int:
    _set_windows_app_id()

    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("深空当铺计算器")
    app.setApplicationDisplayName("深空当铺 · 便携计算终端")
    app.setOrganizationName("DeepSpacePawn")
    app.setStyle("Fusion")

    font = QFont("Microsoft YaHei UI")
    font.setPixelSize(14)
    app.setFont(font)
    app.setStyleSheet(APP_STYLESHEET)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
