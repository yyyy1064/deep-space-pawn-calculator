"""深空当铺 · 界面主题。

所有颜色与控件样式集中在这里，后续新增计算页时可以直接复用。
"""

from __future__ import annotations

from PySide6.QtGui import QColor

# 调色板：深空底色 + 旧金色 + 冷青色
INK = "#070A10"
PANEL = "#0D1420"
PANEL_RAISED = "#111A29"
LINE = "#1D2A3E"
TEXT = "#E9E2D3"
TEXT_STRONG = "#F6EEDC"
MUTED = "#8A97AA"
DIM = "#66758A"
GOLD = "#E3B566"
GOLD_BRIGHT = "#F4CE8C"
CYAN = "#6FD6C8"

COLORS = {
    "ink": QColor(INK),
    "panel": QColor(PANEL),
    "line": QColor(LINE),
    "text": QColor(TEXT),
    "muted": QColor(MUTED),
    "gold": QColor(GOLD),
    "gold_bright": QColor(GOLD_BRIGHT),
    "cyan": QColor(CYAN),
}


APP_STYLESHEET = """
* {
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI";
    outline: none;
}

QMainWindow, QWidget {
    color: #E9E2D3;
    font-size: 14px;
}

QWidget#Content, QWidget#Page, QWidget#PageBody, QWidget#FieldBox,
QWidget#HeaderBox, QWidget#TopBar, QStackedWidget {
    background: transparent;
}

QLabel {
    background: transparent;
}

QToolTip {
    background-color: #111A29;
    color: #F0E7D6;
    border: 1px solid #3A4A63;
    border-radius: 6px;
    padding: 6px 8px;
    font-size: 12px;
}

/* ---------- 框架 ---------- */

QFrame#Sidebar {
    background-color: rgba(7, 11, 18, 238);
    border: none;
    border-right: 1px solid #172235;
}

QFrame#TopBarLine {
    background-color: #162033;
    border: none;
    min-height: 1px;
    max-height: 1px;
}

QFrame#Panel {
    background-color: rgba(13, 20, 32, 244);
    border: 1px solid #1D2A3E;
    border-radius: 16px;
}

QFrame#InnerBox {
    background-color: #0A111C;
    border: 1px solid #1A2638;
    border-radius: 12px;
}

QFrame#FormulaBox {
    background-color: #0A101A;
    border: 1px solid #1A2537;
    border-radius: 12px;
}

QFrame#NoteBox {
    background-color: rgba(29, 38, 49, 150);
    border: 1px solid #263346;
    border-radius: 10px;
}

QFrame#Divider {
    background-color: #1D293B;
    border: none;
    min-height: 1px;
    max-height: 1px;
}

/* ---------- 侧栏 ---------- */

QLabel#LogoMark {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #F3D79F, stop:1 #B98232);
    color: #161006;
    border-radius: 12px;
    font-size: 22px;
    font-weight: 700;
}

QLabel#BrandTitle {
    color: #F5E9D3;
    font-size: 20px;
    font-weight: 600;
}

QLabel#BrandSub {
    color: #6D7B8F;
    font-size: 9px;
}

QLabel#SectionLabel {
    color: #66758A;
    font-size: 11px;
    font-weight: 600;
}

QPushButton#NavItem {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 9px;
    color: #9EABBE;
    text-align: left;
    padding: 10px 13px;
    font-size: 15px;
}

QPushButton#NavItem:hover {
    background-color: #111A29;
    color: #E9E2D3;
}

QPushButton#NavItem:checked {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(73, 55, 28, 230), stop:1 rgba(23, 32, 46, 230));
    border: 1px solid #4B3B21;
    color: #F5D79B;
    font-weight: 600;
}

QLabel#NavHint {
    color: #4F5D71;
    font-size: 11px;
}

QLabel#SidebarFooter {
    color: #4F5D71;
    font-size: 11px;
}

QLabel#DotGold {
    color: #B98A43;
    font-size: 12px;
}

/* ---------- 顶栏与页头 ---------- */

QLabel#Breadcrumb {
    color: #7E8CA1;
    font-size: 12px;
}

QLabel#StatusPill {
    background-color: rgba(36, 78, 71, 130);
    border: 1px solid #244D48;
    border-radius: 11px;
    color: #7FE0D1;
    padding: 4px 10px;
    font-size: 11px;
}

QLabel#VersionLabel {
    color: #536176;
    font-size: 11px;
}

QLabel#PageTitle {
    color: #F6EEDC;
    font-size: 31px;
    font-weight: 600;
}

QLabel#HeaderBadge {
    background-color: #141F2E;
    border: 1px solid #2A3A52;
    border-radius: 9px;
    color: #C9B68E;
    padding: 4px 9px;
    font-size: 11px;
}

QLabel#PageSubtitle {
    color: #8A97AA;
    font-size: 13px;
}

/* ---------- 卡片 ---------- */

QLabel#CardTitle {
    color: #F0E8D8;
    font-size: 17px;
    font-weight: 600;
}

QLabel#CardTag {
    color: #C89D55;
    font-size: 10px;
    font-weight: 600;
}

QLabel#FieldLabel {
    color: #DCE3EE;
    font-size: 14px;
    font-weight: 500;
}

QLabel#FieldHint {
    color: #6F7E93;
    font-size: 11px;
}

QLabel#FieldBadge {
    background-color: #141E2C;
    border: 1px solid #253248;
    border-radius: 7px;
    color: #A38A61;
    padding: 2px 7px;
    font-size: 10px;
}

/* ---------- 输入 ---------- */

QDoubleSpinBox {
    background-color: #0A111C;
    border: 1px solid #22304A;
    border-radius: 10px;
    padding: 9px 14px;
    color: #F5EEDF;
    font-family: "Bahnschrift", "Microsoft YaHei UI";
    font-size: 22px;
    min-height: 30px;
    selection-background-color: #7D5B26;
    selection-color: #FFF7E8;
}

QDoubleSpinBox:hover {
    border-color: #2E405D;
}

QDoubleSpinBox:focus {
    border: 1px solid #D9A84E;
    background-color: #0C1521;
}

QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    width: 0px;
    border: none;
    background: transparent;
}

QSlider {
    min-height: 20px;
}

QSlider::groove:horizontal {
    height: 4px;
    background: #1B2739;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7A5524, stop:1 #EAC170);
    border-radius: 2px;
}

QSlider::add-page:horizontal {
    background: #1B2739;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #F6D08A;
    border: 3px solid #101724;
    width: 14px;
    height: 14px;
    margin: -8px 0;
    border-radius: 10px;
}

QSlider::handle:horizontal:hover {
    background: #FFE1A8;
    border-color: #D9A84E;
}

QLabel#SliderEnd {
    color: #66758A;
    font-size: 11px;
}

/* ---------- 结果 ---------- */

QLabel#ResultCaption {
    color: #8D9AAE;
    font-size: 12px;
}

QLabel#ResultValue {
    color: #F3CE8D;
    font-family: "Bahnschrift", "Microsoft YaHei UI";
    font-size: 56px;
    font-weight: 600;
}

QLabel#ResultUnit {
    color: #A7B3C4;
    font-size: 15px;
}

QLabel#ResultHint {
    color: #6D7B90;
    font-size: 11px;
}

QLabel#StatLabel {
    color: #7D8A9E;
    font-size: 11px;
}

QLabel#StatValue {
    color: #E9E3D7;
    font-family: "Bahnschrift", "Microsoft YaHei UI";
    font-size: 21px;
    font-weight: 500;
}

QLabel#StatUnit {
    color: #78869A;
    font-size: 11px;
}

QLabel#StatSub {
    color: #59677C;
    font-size: 10px;
}

QLabel#FormulaTitle {
    color: #7E8CA1;
    font-size: 10px;
    font-weight: 600;
}

QLabel#Formula {
    color: #B6C1D0;
    font-size: 13px;
}

QLabel#Footnote {
    color: #66758A;
    font-size: 11px;
}

QLabel#NoteText {
    color: #8A97AA;
    font-size: 11px;
}

QLabel#NoteIcon {
    color: #C89D55;
    font-size: 12px;
}

/* ---------- 滚动条 ---------- */

QScrollArea {
    border: none;
    background: transparent;
}

QScrollArea > QWidget > QWidget {
    background: transparent;
}

QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background: #253248;
    border-radius: 4px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background: #344762;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}

QScrollBar:horizontal {
    height: 0px;
}
"""
