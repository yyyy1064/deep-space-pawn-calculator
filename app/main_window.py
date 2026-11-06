"""主窗口：侧栏分类 + 页面容器。"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app import __version__
from app.pages.dream_dust import DreamDustPage
from app.resources import resource_path
from app.widgets.starfield import Starfield


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("深空当铺 · 便携计算终端")
        self.resize(1240, 820)
        self.setMinimumSize(1080, 700)

        icon_path = resource_path("assets/app.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._build_ui()

    # ------------------------------------------------------------------ UI

    def _build_ui(self) -> None:
        shell = Starfield()
        shell.setObjectName("Content")
        self.setCentralWidget(shell)

        root = QHBoxLayout(shell)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        main_area = QWidget()
        main_area.setObjectName("Content")
        main_layout = QVBoxLayout(main_area)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(self._build_topbar())

        line = QFrame()
        line.setObjectName("TopBarLine")
        main_layout.addWidget(line)

        content = QWidget()
        content.setObjectName("Content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(34, 18, 34, 10)
        content_layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.dream_dust_page = DreamDustPage()
        self.stack.addWidget(self.dream_dust_page)
        content_layout.addWidget(self.stack)

        main_layout.addWidget(content, 1)
        root.addWidget(main_area, 1)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(254)

        box = QVBoxLayout(sidebar)
        box.setContentsMargins(20, 24, 20, 20)
        box.setSpacing(0)

        box.addLayout(self._build_brand())
        box.addSpacing(34)

        section = QLabel("制药   /   PHARMACY")
        section.setObjectName("SectionLabel")
        section.setContentsMargins(4, 0, 0, 0)
        box.addWidget(section)
        box.addSpacing(10)

        self.dream_dust_nav = QPushButton("◈    梦尘")
        self.dream_dust_nav.setObjectName("NavItem")
        self.dream_dust_nav.setCheckable(True)
        self.dream_dust_nav.setChecked(True)
        self.dream_dust_nav.setCursor(Qt.CursorShape.PointingHandCursor)
        self.dream_dust_nav.setToolTip("梦尘浓度计算")
        self.dream_dust_nav.clicked.connect(self._show_dream_dust)
        box.addWidget(self.dream_dust_nav)

        hint = QLabel("梦尘浓度换算")
        hint.setObjectName("NavHint")
        hint.setContentsMargins(37, 7, 0, 0)
        box.addWidget(hint)

        box.addStretch(1)

        divider = QFrame()
        divider.setObjectName("Divider")
        box.addWidget(divider)
        box.addSpacing(14)

        footer_top = QLabel("更多制药子项目将在此接入")
        footer_top.setObjectName("SidebarFooter")
        box.addWidget(footer_top)
        box.addSpacing(5)

        footer = QLabel(f"本地离线计算  ·  v{__version__}")
        footer.setObjectName("SidebarFooter")
        box.addWidget(footer)
        return sidebar

    def _build_brand(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(11)

        mark = QLabel("◆")
        mark.setObjectName("LogoMark")
        mark.setFixedSize(42, 42)
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(mark)

        text_box = QVBoxLayout()
        text_box.setContentsMargins(0, 0, 0, 0)
        text_box.setSpacing(2)

        title = QLabel("深空当铺")
        title.setObjectName("BrandTitle")
        text_box.addWidget(title)

        sub = QLabel("DEEP SPACE PAWN")
        sub.setObjectName("BrandSub")
        sub_font = QFont(sub.font())
        sub_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.4)
        sub.setFont(sub_font)
        text_box.addWidget(sub)

        row.addLayout(text_box)
        row.addStretch(1)
        return row

    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(58)

        row = QHBoxLayout(bar)
        row.setContentsMargins(34, 0, 34, 0)
        row.setSpacing(14)

        breadcrumb = QLabel("计算终端   /   制药   /   梦尘")
        breadcrumb.setObjectName("Breadcrumb")
        row.addWidget(breadcrumb)
        row.addStretch(1)

        status = QLabel("●  实时计算")
        status.setObjectName("StatusPill")
        row.addWidget(status)

        version = QLabel(f"v{__version__}")
        version.setObjectName("VersionLabel")
        row.addWidget(version)
        return bar

    # ------------------------------------------------------------- behavior

    def _show_dream_dust(self) -> None:
        self.stack.setCurrentWidget(self.dream_dust_page)
        self.dream_dust_nav.setChecked(True)
