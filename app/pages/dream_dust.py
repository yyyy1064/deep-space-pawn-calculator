"""梦尘浓度计算页。"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QValidator
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from app.calculators.dream_dust import (
    CalculationError,
    calculate_dream_dust,
    format_plain,
    round_half_up,
)


class _NumberField(QDoubleSpinBox):
    """支持越界输入后自动夹取，并按 0.1 精度四舍五入。"""

    _NUMBER_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.setGroupSeparatorShown(False)
        self.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.setKeyboardTracking(True)

    def _clean_text(self, text: str) -> str:
        suffix = self.suffix()
        if suffix and text.endswith(suffix):
            text = text[: -len(suffix)]
        return text.strip().replace(",", "")

    def validate(self, text: str, pos: int):  # noqa: N802
        cleaned = self._clean_text(text)
        if cleaned in {"", "+", "-", ".", "+.", "-."}:
            return QValidator.State.Intermediate, text, pos
        if self._NUMBER_RE.match(cleaned):
            # 越界数字允许输入，由 valueFromText 夹取到上下限。
            return QValidator.State.Acceptable, text, pos
        return super().validate(text, pos)

    def valueFromText(self, text: str):  # noqa: N802
        cleaned = self._clean_text(text)
        try:
            value = Decimal(cleaned)
        except (InvalidOperation, ValueError):
            return self.value()
        # 先把用户输入四舍五入到当前精度，再由 QDoubleSpinBox 夹取范围。
        return float(round_half_up(value, self.decimals()))

    def wheelEvent(self, event) -> None:  # noqa: N802
        # 未聚焦时把滚轮留给页面滚动，避免误改数值。
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()

    def focusInEvent(self, event) -> None:  # noqa: N802
        super().focusInEvent(event)
        QTimer.singleShot(0, self._select_all)

    def _select_all(self) -> None:
        line_edit = self.lineEdit()
        if line_edit is not None:
            line_edit.selectAll()


class DreamDustPage(QWidget):
    """梦尘：输入原料剂量、酒精浓度、萃取倍率，输出所需溶液体积。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Page")
        self._syncing_multiplier = False
        self._build_ui()
        self._connect_signals()
        self._recalculate()

    # ------------------------------------------------------------------ UI

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        root.addWidget(scroll)

        body = QWidget()
        body.setObjectName("PageBody")
        scroll.setWidget(body)

        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 6, 0)
        layout.setSpacing(16)

        layout.addWidget(self._build_header())
        layout.addLayout(self._build_cards(), 1)

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("HeaderBox")
        box = QVBoxLayout(header)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(7)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(12)

        title = QLabel("梦尘浓度计算")
        title.setObjectName("PageTitle")
        title_row.addWidget(title, 0, Qt.AlignmentFlag.AlignVCenter)

        badge = QLabel("制药 · 浓度换算")
        badge.setObjectName("HeaderBadge")
        title_row.addWidget(badge, 0, Qt.AlignmentFlag.AlignVCenter)
        title_row.addStretch(1)

        box.addLayout(title_row)

        subtitle = QLabel(
            "输入梦帽菇糊剂量与萃取倍率，换算需要量取的酒精溶液体积。"
        )
        subtitle.setObjectName("PageSubtitle")
        box.addWidget(subtitle)
        return header

    def _build_cards(self) -> QHBoxLayout:
        cards = QHBoxLayout()
        cards.setContentsMargins(0, 0, 0, 0)
        cards.setSpacing(22)

        input_card = self._build_input_card()
        input_card.setMinimumWidth(400)
        input_card.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )

        result_card = self._build_result_card()
        result_card.setMinimumWidth(320)
        result_card.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        cards.addWidget(input_card, 11)
        cards.addWidget(result_card, 9)
        return cards

    def _build_input_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Panel")
        box = QVBoxLayout(card)
        box.setContentsMargins(26, 20, 26, 14)
        box.setSpacing(0)

        box.addWidget(self._card_header("输入参数", "01 / INPUT"))
        box.addSpacing(16)

        self.paste_spin = _NumberField()
        self.paste_spin.setDecimals(1)
        self.paste_spin.setRange(0.0, 999999.9)
        self.paste_spin.setSingleStep(0.1)
        self.paste_spin.setSuffix(" ml")
        self.paste_spin.setValue(0.0)
        self.paste_spin.setToolTip("梦帽菇糊的实际体积，精度 0.1 ml")

        box.addWidget(
            self._field(
                "梦帽菇糊剂量",
                "精度 0.1",
                self.paste_spin,
                "输入用于萃取的梦帽菇糊体积。",
            )
        )
        box.addSpacing(15)

        self.concentration_spin = _NumberField()
        self.concentration_spin.setDecimals(1)
        self.concentration_spin.setRange(0.1, 100.0)
        self.concentration_spin.setSingleStep(0.1)
        self.concentration_spin.setSuffix(" %")
        self.concentration_spin.setValue(70.0)
        self.concentration_spin.setToolTip("酒精体积浓度，例如 70% 即每 100 ml 含 70 ml 酒精")

        box.addWidget(
            self._field(
                "酒精浓度",
                "体积浓度",
                self.concentration_spin,
                "70% 表示每 100 ml 溶液含 70 ml 酒精、30 ml 水。",
            )
        )
        box.addSpacing(15)

        self.multiplier_spin = _NumberField()
        self.multiplier_spin.setDecimals(1)
        self.multiplier_spin.setRange(3.0, 6.0)
        self.multiplier_spin.setSingleStep(0.1)
        self.multiplier_spin.setSuffix(" ×")
        self.multiplier_spin.setValue(3.0)
        self.multiplier_spin.setToolTip("游戏要求酒精为原料的 3.0–6.0 倍")

        self.multiplier_slider = QSlider(Qt.Orientation.Horizontal)
        self.multiplier_slider.setRange(30, 60)
        self.multiplier_slider.setSingleStep(1)
        self.multiplier_slider.setPageStep(5)
        self.multiplier_slider.setValue(30)
        self.multiplier_slider.setToolTip("拖动调整倍率，精度 0.1")

        box.addWidget(
            self._field(
                "萃取用酒精倍率",
                "范围 3.0–6.0",
                self.multiplier_spin,
                "超出范围会自动修正到 3.0 或 6.0，滑块与输入框实时同步。",
                extra=self._build_slider_block(),
            )
        )

        box.addStretch(1)
        box.addSpacing(8)
        note, _ = self._note(
            "◇",
            "换算链路：原料体积 × 倍率 = 纯酒精；纯酒精 ÷ 浓度 = 酒精溶液体积。",
        )
        box.addWidget(note)
        return card

    def _build_slider_block(self) -> QWidget:
        block = QWidget()
        block.setObjectName("FieldBox")
        box = QVBoxLayout(block)
        box.setContentsMargins(1, 3, 1, 0)
        box.setSpacing(2)
        box.addWidget(self.multiplier_slider)

        ends = QHBoxLayout()
        ends.setContentsMargins(1, 0, 1, 0)
        left = QLabel("3.0×")
        left.setObjectName("SliderEnd")
        right = QLabel("6.0×")
        right.setObjectName("SliderEnd")
        ends.addWidget(left)
        ends.addStretch(1)
        ends.addWidget(right)
        box.addLayout(ends)
        return block

    def _field(
        self,
        title: str,
        badge: str,
        control: QWidget,
        hint: str,
        extra: Optional[QWidget] = None,
    ) -> QWidget:
        field = QWidget()
        field.setObjectName("FieldBox")
        box = QVBoxLayout(field)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(6)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        label = QLabel(title)
        label.setObjectName("FieldLabel")
        row.addWidget(label)

        badge_label = QLabel(badge)
        badge_label.setObjectName("FieldBadge")
        row.addWidget(badge_label, 0, Qt.AlignmentFlag.AlignVCenter)
        row.addStretch(1)
        box.addLayout(row)

        box.addWidget(control)

        if extra is not None:
            box.addWidget(extra)

        hint_label = QLabel(hint)
        hint_label.setObjectName("FieldHint")
        hint_label.setWordWrap(True)
        box.addWidget(hint_label)
        return field

    def _build_result_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Panel")
        box = QVBoxLayout(card)
        box.setContentsMargins(26, 18, 26, 14)
        box.setSpacing(0)

        box.addWidget(self._card_header("计算结果", "02 / RESULT"))
        box.addSpacing(16)

        caption = QLabel("所需酒精溶液")
        caption.setObjectName("ResultCaption")
        box.addWidget(caption)
        box.addSpacing(4)

        value_row = QHBoxLayout()
        value_row.setContentsMargins(0, 0, 0, 0)
        value_row.setSpacing(8)

        self.result_value = QLabel("0.0")
        self.result_value.setObjectName("ResultValue")
        self.result_value.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        value_row.addWidget(self.result_value, 0, Qt.AlignmentFlag.AlignBottom)

        unit = QLabel("ml")
        unit.setObjectName("ResultUnit")
        unit.setContentsMargins(0, 0, 0, 12)
        value_row.addWidget(unit, 0, Qt.AlignmentFlag.AlignBottom)
        value_row.addStretch(1)
        box.addLayout(value_row)

        self.result_hint = QLabel("按 70.0% 酒精折算")
        self.result_hint.setObjectName("ResultHint")
        box.addWidget(self.result_hint)

        box.addSpacing(10)
        divider = QFrame()
        divider.setObjectName("Divider")
        box.addWidget(divider)
        box.addSpacing(10)

        stats = QHBoxLayout()
        stats.setContentsMargins(0, 0, 0, 0)
        stats.setSpacing(10)

        pure_box, self.pure_value = self._stat_box("纯酒精用量", "ml")
        self.pure_sub = QLabel("精确 0 ml")
        self.pure_sub.setObjectName("StatSub")
        pure_layout = pure_box.layout()
        if pure_layout is not None:
            pure_layout.addWidget(self.pure_sub)

        conc_box, self.conc_value = self._stat_box("配制浓度", "%")
        conc_sub = QLabel("体积浓度")
        conc_sub.setObjectName("StatSub")
        conc_layout = conc_box.layout()
        if conc_layout is not None:
            conc_layout.addWidget(conc_sub)

        stats.addWidget(pure_box, 1)
        stats.addWidget(conc_box, 1)
        box.addLayout(stats)

        box.addSpacing(10)
        formula_box = QFrame()
        formula_box.setObjectName("FormulaBox")
        formula_layout = QVBoxLayout(formula_box)
        formula_layout.setContentsMargins(15, 11, 15, 11)
        formula_layout.setSpacing(7)

        formula_title = QLabel("计算明细")
        formula_title.setObjectName("FormulaTitle")
        formula_layout.addWidget(formula_title)

        self.formula_label = QLabel("")
        self.formula_label.setObjectName("Formula")
        self.formula_label.setWordWrap(True)
        self.formula_label.setTextFormat(Qt.TextFormat.RichText)
        self.formula_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        formula_layout.addWidget(self.formula_label)
        box.addWidget(formula_box)

        box.addSpacing(12)
        measure_note, self.measure_label = self._note(
            "◈",
            "量取 0.0 ml 的 70.0% 酒精溶液。",
        )
        box.addWidget(measure_note)

        box.addStretch(1)
        box.addSpacing(16)

        footnote = QLabel(
            "取整规则：四舍五入（ROUND_HALF_UP）保留 1 位小数；\n"
            "连续计算使用未取整值，避免中间误差累积。"
        )
        footnote.setObjectName("Footnote")
        footnote.setWordWrap(True)
        box.addWidget(footnote)
        return card

    def _stat_box(self, label_text: str, unit_text: str) -> tuple[QFrame, QLabel]:
        frame = QFrame()
        frame.setObjectName("InnerBox")
        box = QVBoxLayout(frame)
        box.setContentsMargins(13, 9, 13, 8)
        box.setSpacing(4)

        label = QLabel(label_text)
        label.setObjectName("StatLabel")
        box.addWidget(label)

        value_row = QHBoxLayout()
        value_row.setContentsMargins(0, 0, 0, 0)
        value_row.setSpacing(4)

        value = QLabel("0.0")
        value.setObjectName("StatValue")
        value.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        value_row.addWidget(value, 0, Qt.AlignmentFlag.AlignBottom)

        unit = QLabel(unit_text)
        unit.setObjectName("StatUnit")
        unit.setContentsMargins(0, 0, 0, 3)
        value_row.addWidget(unit, 0, Qt.AlignmentFlag.AlignBottom)
        value_row.addStretch(1)
        box.addLayout(value_row)
        return frame, value

    def _card_header(self, title_text: str, tag_text: str) -> QWidget:
        header = QWidget()
        header.setObjectName("HeaderBox")
        row = QHBoxLayout(header)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        title = QLabel(title_text)
        title.setObjectName("CardTitle")
        row.addWidget(title)
        row.addStretch(1)

        tag = QLabel(tag_text)
        tag.setObjectName("CardTag")
        row.addWidget(tag, 0, Qt.AlignmentFlag.AlignVCenter)
        return header

    def _note(self, icon_text: str, text: str) -> tuple[QFrame, QLabel]:
        note = QFrame()
        note.setObjectName("NoteBox")
        row = QHBoxLayout(note)
        row.setContentsMargins(12, 9, 12, 9)
        row.setSpacing(8)

        icon = QLabel(icon_text)
        icon.setObjectName("NoteIcon")
        icon.setAlignment(Qt.AlignmentFlag.AlignTop)
        row.addWidget(icon)

        label = QLabel(text)
        label.setObjectName("NoteText")
        label.setWordWrap(True)
        row.addWidget(label, 1)
        return note, label

    # ------------------------------------------------------------- behavior

    def _connect_signals(self) -> None:
        self.paste_spin.valueChanged.connect(self._recalculate)
        self.concentration_spin.valueChanged.connect(self._recalculate)
        self.multiplier_spin.valueChanged.connect(self._on_multiplier_changed)
        self.multiplier_slider.valueChanged.connect(self._on_slider_changed)
        self.multiplier_spin.editingFinished.connect(self._normalize_multiplier)

    def _on_multiplier_changed(self, value: float) -> None:
        if self._syncing_multiplier:
            return
        self._syncing_multiplier = True
        self.multiplier_slider.setValue(int(round(value * 10)))
        self._syncing_multiplier = False
        self._recalculate()

    def _on_slider_changed(self, value: int) -> None:
        if self._syncing_multiplier:
            return
        self._syncing_multiplier = True
        self.multiplier_spin.setValue(value / 10.0)
        self._syncing_multiplier = False
        self._recalculate()

    def _normalize_multiplier(self) -> None:
        value = min(6.0, max(3.0, self.multiplier_spin.value()))
        value = float(round_half_up(Decimal(str(value)), 1))
        if abs(value - self.multiplier_spin.value()) > 1e-9:
            self.multiplier_spin.setValue(value)

    def _recalculate(self, *_args) -> None:
        try:
            result = calculate_dream_dust(
                Decimal(str(self.paste_spin.value())),
                Decimal(str(self.concentration_spin.value())),
                Decimal(str(self.multiplier_spin.value())),
            )
        except CalculationError as exc:
            self.result_value.setText("—")
            self.result_hint.setText(str(exc))
            self.pure_value.setText("—")
            self.conc_value.setText(f"{self.concentration_spin.value():.1f}")
            self.measure_label.setText("请检查输入参数。")
            self.formula_label.setText(
                '<span style="color:#D98B7A;">请检查输入参数。</span>'
            )
            return

        self.result_value.setText(f"{result.solution_ml:.1f}")
        self.result_hint.setText(f"按 {result.alcohol_percent:.1f}% 酒精折算")

        self.pure_value.setText(f"{result.pure_alcohol_ml:.1f}")
        self.pure_sub.setText(f"精确 {format_plain(result.exact_pure_alcohol_ml)} ml")

        self.conc_value.setText(f"{result.alcohol_percent:.1f}")

        paste = format_plain(result.paste_ml)
        multiplier = f"{result.multiplier:.1f}"
        exact = format_plain(result.exact_pure_alcohol_ml)
        percent = f"{result.alcohol_percent:.1f}"
        solution = f"{result.solution_ml:.1f}"
        pure = f"{result.pure_alcohol_ml:.1f}"

        self.measure_label.setText(
            f"量取 {solution} ml 的 {percent}% 酒精溶液；"
            f"其中纯酒精 {pure} ml。"
        )

        self.formula_label.setText(
            '<div style="color:#AEB9C9;">'
            '<p style="margin:0 0 5px 0;">'
            '<span style="color:#66758A;">01</span>&nbsp;&nbsp;'
            f"{paste} ml × {multiplier} = "
            f'<span style="color:#EBC783;">{exact} ml</span> 纯酒精</p>'
            '<p style="margin:0 0 5px 0;">'
            '<span style="color:#66758A;">02</span>&nbsp;&nbsp;'
            f"{exact} ml ÷ {percent}% = "
            f'<span style="color:#EBC783;">{solution} ml</span> 溶液</p>'
            '<p style="margin:0;">'
            '<span style="color:#66758A;">03</span>&nbsp;&nbsp;'
            f"纯酒精显示值 {pure} ml，溶液结果按 0.1 ml 取整</p>"
            "</div>"
        )

    # 供测试与后续模块读取当前状态
    def current_values(self) -> tuple[float, float, float]:
        return (
            self.paste_spin.value(),
            self.concentration_spin.value(),
            self.multiplier_spin.value(),
        )
