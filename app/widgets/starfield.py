"""静态深空背景：渐变、星云与细小星点。"""

from __future__ import annotations

import random

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
    QRadialGradient,
)
from PySide6.QtWidgets import QWidget


class Starfield(QWidget):
    """轻量背景控件，不拦截鼠标事件，也不影响布局。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Starfield")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMouseTracking(False)

        rng = random.Random(20261106)
        self._stars: list[tuple[float, float, float, int, QColor]] = []
        for _ in range(190):
            x = rng.random()
            y = rng.random()
            radius = rng.choice([0.55, 0.7, 0.8, 0.95, 1.2, 1.5])
            alpha = rng.randint(16, 100)
            if rng.random() < 0.12:
                color = QColor(239, 205, 150)
            elif rng.random() < 0.35:
                color = QColor(159, 218, 219)
            else:
                color = QColor(206, 219, 242)
            self._stars.append((x, y, radius, alpha, color))

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt 命名
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = QRectF(self.rect())
        width = max(rect.width(), 1.0)
        height = max(rect.height(), 1.0)

        base = QLinearGradient(0, 0, width, height)
        base.setColorAt(0.0, QColor("#070A10"))
        base.setColorAt(0.48, QColor("#090E18"))
        base.setColorAt(1.0, QColor("#0B1220"))
        painter.fillRect(rect, QBrush(base))

        # 右上角冷色星云
        nebula = QRadialGradient(QPointF(width * 0.84, height * 0.08), width * 0.52)
        nebula.setColorAt(0.0, QColor(55, 128, 132, 46))
        nebula.setColorAt(0.45, QColor(35, 77, 93, 18))
        nebula.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(rect, QBrush(nebula))

        # 左下角暖色尘雾
        dust = QRadialGradient(QPointF(width * 0.06, height * 0.95), width * 0.46)
        dust.setColorAt(0.0, QColor(131, 91, 42, 34))
        dust.setColorAt(0.55, QColor(80, 57, 33, 12))
        dust.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(rect, QBrush(dust))

        painter.setPen(Qt.PenStyle.NoPen)
        for x, y, radius, alpha, color in self._stars:
            star = QColor(color)
            star.setAlpha(alpha)
            painter.setBrush(star)
            painter.drawEllipse(
                QPointF(x * width, y * height),
                radius,
                radius,
            )

        # 一条极淡的地平线光带
        horizon = QLinearGradient(0, height - 130, 0, height)
        horizon.setColorAt(0.0, QColor(63, 105, 117, 0))
        horizon.setColorAt(1.0, QColor(63, 105, 117, 18))
        painter.fillRect(QRectF(0, height - 130, width, 130), QBrush(horizon))

        painter.end()
