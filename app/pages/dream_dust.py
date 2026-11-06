"""梦尘浓度与蛋白质处理页。"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QValidator
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QComboBox,
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
    AGENT_NAMES,
    CalculationError,
    calculate_dream_dust,
    calculate_protein_treatment,
    format_plain,
    round_half_up,
)


class _NumberField(QDoubleSpinBox):
    """支持越界输入后自动夹取，并按当前 decimals 精度四舍五入。"""

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
    """梦尘：酒精萃取、蛋白质沉淀与剩余酸碱中和。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Page")
        self._syncing_multiplier = False
        self._current_agent = "base"
        self._build_ui()
        self._update_agent_labels()
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

        badge = QLabel("制药 · 萃取 / 提纯")
        badge.setObjectName("HeaderBadge")
        title_row.addWidget(badge, 0, Qt.AlignmentFlag.AlignVCenter)
        title_row.addStretch(1)

        box.addLayout(title_row)

        subtitle = QLabel(
            "输入梦帽菇糊、萃取参数与蛋白质含量，换算酒精溶液和中和液配比。"
        )
        subtitle.setObjectName("PageSubtitle")
        box.addWidget(subtitle)
        return header

    def _build_cards(self) -> QHBoxLayout:
        cards = QHBoxLayout()
        cards.setContentsMargins(0, 0, 0, 0)
        cards.setSpacing(22)

        input_card = self._build_input_card()
        input_card.setMinimumWidth(410)
        input_card.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )

        result_card = self._build_result_card()
        result_card.setMinimumWidth(330)
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
        box.setContentsMargins(24, 16, 24, 4)
        box.setSpacing(0)

        box.addWidget(self._card_header("输入参数", "01 / INPUT"))
        box.addSpacing(12)
        box.addWidget(self._section_title("01 萃取参数", "酒精 · 倍率"))
        box.addSpacing(8)

        self.paste_spin = _NumberField()
        self.paste_spin.setDecimals(2)
        self.paste_spin.setRange(0.0, 999999.99)
        self.paste_spin.setSingleStep(0.01)
        self.paste_spin.setSuffix(" ml")
        self.paste_spin.setValue(0.0)
        self.paste_spin.setToolTip("梦帽菇糊的实际体积，精度 0.01 ml")

        self.concentration_spin = _NumberField()
        self.concentration_spin.setDecimals(2)
        self.concentration_spin.setRange(0.01, 100.0)
        self.concentration_spin.setSingleStep(0.01)
        self.concentration_spin.setSuffix(" %")
        self.concentration_spin.setValue(70.0)
        self.concentration_spin.setToolTip(
            "酒精体积浓度，例如 70% 即每 100 ml 含 70 ml 酒精"
        )

        extract_row = QHBoxLayout()
        extract_row.setContentsMargins(0, 0, 0, 0)
        extract_row.setSpacing(12)
        extract_row.addWidget(
            self._field(
                "梦帽菇糊剂量",
                "0.01 ml",
                self.paste_spin,
                "用于萃取的梦帽菇糊体积。",
            ),
            1,
        )
        extract_row.addWidget(
            self._field(
                "酒精浓度",
                "体积浓度",
                self.concentration_spin,
                "70% = 每 100 ml 含 70 ml 酒精。",
            ),
            1,
        )
        box.addLayout(extract_row)
        box.addSpacing(12)

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
                "超出范围自动修正；滑块与输入框实时同步。",
                extra=self._build_slider_block(),
            )
        )
        box.addSpacing(12)

        divider = QFrame()
        divider.setObjectName("Divider")
        box.addWidget(divider)
        box.addSpacing(12)

        box.addWidget(self._section_title("02 蛋白质处理", "1 : 1 有效量"))
        box.addSpacing(8)

        self.protein_spin = _NumberField()
        self.protein_spin.setDecimals(2)
        self.protein_spin.setRange(0.0, 999999.99)
        self.protein_spin.setSingleStep(0.01)
        self.protein_spin.setSuffix(" ml")
        self.protein_spin.setValue(0.0)
        self.protein_spin.setToolTip("待清除的蛋白质体积，精度 0.01 ml")

        self.agent_combo = QComboBox()
        self.agent_combo.addItem("碱 · 沉淀蛋白质", "base")
        self.agent_combo.addItem("酸 · 沉淀蛋白质", "acid")
        self.agent_combo.setCurrentIndex(0)
        self.agent_combo.setToolTip("选择用于清除蛋白质的酸或碱")

        protein_row = QHBoxLayout()
        protein_row.setContentsMargins(0, 0, 0, 0)
        protein_row.setSpacing(12)
        protein_row.addWidget(
            self._field(
                "蛋白质含量",
                "0.01 ml",
                self.protein_spin,
                "",
            ),
            1,
        )
        protein_row.addWidget(
            self._field(
                "处理剂",
                "酸 / 碱",
                self.agent_combo,
                "",
            ),
            1,
        )
        box.addLayout(protein_row)
        box.addSpacing(12)

        self.agent_concentration_spin = _NumberField()
        self.agent_concentration_spin.setDecimals(2)
        self.agent_concentration_spin.setRange(0.01, 100.0)
        self.agent_concentration_spin.setSingleStep(0.01)
        self.agent_concentration_spin.setSuffix(" %")
        self.agent_concentration_spin.setValue(97.0)
        self.agent_concentration_spin.setToolTip("所选处理剂的体积浓度")

        self.neutralizer_concentration_spin = _NumberField()
        self.neutralizer_concentration_spin.setDecimals(2)
        self.neutralizer_concentration_spin.setRange(0.01, 100.0)
        self.neutralizer_concentration_spin.setSingleStep(0.01)
        self.neutralizer_concentration_spin.setSuffix(" %")
        self.neutralizer_concentration_spin.setValue(98.0)
        self.neutralizer_concentration_spin.setToolTip(
            "用于中和剩余酸碱的相反试剂浓度"
        )

        self.agent_conc_field = self._field(
            "碱浓度",
            "体积浓度",
            self.agent_concentration_spin,
            "",
        )
        self.neutralizer_field = self._field(
            "中和用酸浓度",
            "体积浓度",
            self.neutralizer_concentration_spin,
            "",
        )

        concentration_row = QHBoxLayout()
        concentration_row.setContentsMargins(0, 0, 0, 0)
        concentration_row.setSpacing(12)
        concentration_row.addWidget(self.agent_conc_field, 1)
        concentration_row.addWidget(self.neutralizer_field, 1)
        box.addLayout(concentration_row)

        box.addStretch(1)
        box.addSpacing(6)
        note, _ = self._note(
            "◇",
            "按有效量 1:1 加入酸/碱；最小 1 ml，向上取整；"
            "浓度过高时先按整数 ml 配比稀释。",
        )
        note.setMinimumHeight(50)
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

    def _section_title(self, title_text: str, tag_text: str) -> QWidget:
        header = QWidget()
        header.setObjectName("HeaderBox")
        row = QHBoxLayout(header)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        title = QLabel(title_text)
        title.setObjectName("SubSectionTitle")
        row.addWidget(title)
        row.addStretch(1)

        tag = QLabel(tag_text)
        tag.setObjectName("SubSectionTag")
        row.addWidget(tag, 0, Qt.AlignmentFlag.AlignVCenter)
        return header

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
        field.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        box = QVBoxLayout(field)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(5)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(7)

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

        hint_label = None
        if hint:
            hint_label = QLabel(hint)
            hint_label.setObjectName("FieldHint")
            hint_label.setWordWrap(True)
            box.addWidget(hint_label)

        # 供动态标题使用。
        field.title_label = label  # type: ignore[attr-defined]
        field.hint_label = hint_label  # type: ignore[attr-defined]
        return field

    def _build_result_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Panel")
        box = QVBoxLayout(card)
        box.setContentsMargins(24, 18, 24, 8)
        box.setSpacing(0)

        box.addWidget(self._card_header("计算结果", "02 / RESULT"))
        box.addSpacing(14)

        caption = QLabel("所需酒精溶液")
        caption.setObjectName("ResultCaption")
        box.addWidget(caption)
        box.addSpacing(3)

        value_row = QHBoxLayout()
        value_row.setContentsMargins(0, 0, 0, 0)
        value_row.setSpacing(8)

        self.result_value = QLabel("0.00")
        self.result_value.setObjectName("ResultValue")
        self.result_value.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        value_row.addWidget(self.result_value, 0, Qt.AlignmentFlag.AlignBottom)

        unit = QLabel("ml")
        unit.setObjectName("ResultUnit")
        unit.setContentsMargins(0, 0, 0, 10)
        value_row.addWidget(unit, 0, Qt.AlignmentFlag.AlignBottom)
        value_row.addStretch(1)
        box.addLayout(value_row)

        self.result_hint = QLabel("按 70.00% 酒精折算")
        self.result_hint.setObjectName("ResultHint")
        box.addWidget(self.result_hint)

        box.addSpacing(8)
        divider = QFrame()
        divider.setObjectName("Divider")
        box.addWidget(divider)
        box.addSpacing(9)

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

        box.addSpacing(8)
        box.addWidget(self._section_title("蛋白质处理", "03 / TREAT"))

        protein_stats = QHBoxLayout()
        protein_stats.setContentsMargins(0, 4, 0, 0)
        protein_stats.setSpacing(10)

        agent_box, self.agent_caption, self.agent_value, self.agent_sub = (
            self._result_stat("需加入碱", "ml", "实际 0.00 ml")
        )
        (
            neutralizer_box,
            self.neutralizer_caption,
            self.neutralizer_value,
            self.neutralizer_sub,
        ) = self._result_stat("中和用酸", "ml", "目标 0.00%")

        protein_stats.addWidget(agent_box, 1)
        protein_stats.addWidget(neutralizer_box, 1)
        box.addLayout(protein_stats)

        box.addSpacing(6)
        recipe_note, self.recipe_label = self._note(
            "◈",
            "蛋白质为 0，跳过酸碱处理。",
        )
        recipe_note.setMinimumHeight(44)
        box.addWidget(recipe_note)

        box.addSpacing(6)
        formula_box = QFrame()
        formula_box.setObjectName("FormulaBox")
        formula_layout = QVBoxLayout(formula_box)
        formula_layout.setContentsMargins(14, 10, 14, 10)
        formula_layout.setSpacing(6)

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
        formula_box.setMinimumHeight(190)
        box.addWidget(formula_box)

        box.addStretch(1)
        box.addSpacing(6)

        footnote = QLabel(
            "取整规则：普通数值四舍五入保留 2 位小数；\n"
            "酸碱剂量向上取整到 1 ml；连续计算使用未取整值。"
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
        box.setSpacing(3)

        label = QLabel(label_text)
        label.setObjectName("StatLabel")
        box.addWidget(label)

        value_row = QHBoxLayout()
        value_row.setContentsMargins(0, 0, 0, 0)
        value_row.setSpacing(4)

        value = QLabel("0.00")
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

    def _result_stat(
        self, caption_text: str, unit_text: str, sub_text: str
    ) -> tuple[QFrame, QLabel, QLabel, QLabel]:
        frame = QFrame()
        frame.setObjectName("InnerBox")
        box = QVBoxLayout(frame)
        box.setContentsMargins(13, 8, 13, 7)
        box.setSpacing(2)

        caption = QLabel(caption_text)
        caption.setObjectName("StatLabel")
        box.addWidget(caption)

        value_row = QHBoxLayout()
        value_row.setContentsMargins(0, 0, 0, 0)
        value_row.setSpacing(4)

        value = QLabel("0.00")
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

        sub = QLabel(sub_text)
        sub.setObjectName("StatSub")
        sub.setWordWrap(True)
        box.addWidget(sub)
        return frame, caption, value, sub

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
        row.setContentsMargins(12, 8, 12, 8)
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
        self.protein_spin.valueChanged.connect(self._recalculate)
        self.agent_concentration_spin.valueChanged.connect(self._recalculate)
        self.neutralizer_concentration_spin.valueChanged.connect(self._recalculate)
        self.multiplier_spin.valueChanged.connect(self._on_multiplier_changed)
        self.multiplier_slider.valueChanged.connect(self._on_slider_changed)
        self.multiplier_spin.editingFinished.connect(self._normalize_multiplier)
        self.agent_combo.currentIndexChanged.connect(self._on_agent_changed)

    def _on_agent_changed(self, _index: int) -> None:
        new_agent = self.agent_combo.currentData()
        if new_agent == self._current_agent:
            return

        old_agent = self._current_agent
        # 只在浓度仍是旧默认值时切换默认值，避免覆盖用户手填数据。
        if new_agent == "acid":
            if abs(self.agent_concentration_spin.value() - 97.0) < 1e-9:
                self.agent_concentration_spin.setValue(98.0)
            if abs(self.neutralizer_concentration_spin.value() - 98.0) < 1e-9:
                self.neutralizer_concentration_spin.setValue(97.0)
        else:
            if abs(self.agent_concentration_spin.value() - 98.0) < 1e-9:
                self.agent_concentration_spin.setValue(97.0)
            if abs(self.neutralizer_concentration_spin.value() - 97.0) < 1e-9:
                self.neutralizer_concentration_spin.setValue(98.0)

        self._current_agent = new_agent
        self._update_agent_labels()
        self._recalculate()
        self.agent_combo.setToolTip(f"当前处理剂：{AGENT_NAMES[new_agent]}")

    def _update_agent_labels(self) -> None:
        agent = self.agent_combo.currentData()
        agent_name = AGENT_NAMES[agent]
        neutralizer_name = AGENT_NAMES["acid" if agent == "base" else "base"]
        self.agent_conc_field.title_label.setText(f"{agent_name}浓度")
        self.neutralizer_field.title_label.setText(
            f"中和用{neutralizer_name}浓度"
        )

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
            treatment = calculate_protein_treatment(
                Decimal(str(self.protein_spin.value())),
                str(self.agent_combo.currentData()),
                Decimal(str(self.agent_concentration_spin.value())),
                Decimal(str(self.neutralizer_concentration_spin.value())),
            )
        except CalculationError as exc:
            self._show_error(str(exc))
            return

        self.result_value.setText(f"{result.solution_ml:.2f}")
        self.result_hint.setText(
            f"按 {result.alcohol_percent:.2f}% 酒精折算"
        )

        self.pure_value.setText(f"{result.pure_alcohol_ml:.2f}")
        self.pure_sub.setText(
            f"精确 {format_plain(result.exact_pure_alcohol_ml)} ml"
        )
        self.conc_value.setText(f"{result.alcohol_percent:.2f}")

        self._update_protein_result(treatment)
        self._update_formula(result, treatment)

    def _show_error(self, message: str) -> None:
        self.result_value.setText("—")
        self.result_hint.setText(message)
        self.pure_value.setText("—")
        self.conc_value.setText("—")
        self.agent_value.setText("—")
        self.neutralizer_value.setText("—")
        self.agent_sub.setText("请检查输入")
        self.neutralizer_sub.setText("请检查输入")
        self.recipe_label.setText("请检查输入参数。")
        self.formula_label.setText(
            '<span style="color:#D98B7A;">请检查输入参数。</span>'
        )

    def _update_protein_result(self, treatment) -> None:
        agent_name = AGENT_NAMES[treatment.agent]
        neutralizer_name = AGENT_NAMES[treatment.neutralizer]
        self.agent_caption.setText(f"需加入{agent_name}")
        self.neutralizer_caption.setText(f"中和用{neutralizer_name}")

        if treatment.protein_ml == 0:
            self.agent_value.setText("—")
            self.neutralizer_value.setText("—")
            self.agent_sub.setText("无需处理")
            self.neutralizer_sub.setText("无需中和")
            self.recipe_label.setText("蛋白质为 0，跳过酸碱处理。")
            return

        self.agent_value.setText(f"{treatment.agent_dose_ml:.2f}")
        self.agent_sub.setText(
            f"实际 {treatment.agent_pure_ml:.2f} ml · "
            f"剩余 {treatment.residual_ml:.2f} ml"
        )

        if treatment.residual_ml == 0:
            self.neutralizer_value.setText("—")
            self.neutralizer_sub.setText("无需中和")
            self.recipe_label.setText(
                f"{agent_name}刚好完全反应，无剩余，无需中和。"
            )
            return

        self.neutralizer_value.setText(
            f"{treatment.neutralizer_dose_ml:.2f}"
        )
        self.neutralizer_sub.setText(
            f"目标 {treatment.target_percent:.2f}%"
        )

        if treatment.diluted:
            self.recipe_label.setText(
                f"配 {treatment.stock_agent_ml} ml {neutralizer_name} + "
                f"{treatment.stock_water_ml} ml 水 → "
                f"{treatment.stock_total_ml} ml "
                f"{treatment.target_percent:.2f}% 储备液；"
                f"取 {treatment.neutralizer_dose_ml:.2f} ml 加入混合物。"
            )
        else:
            self.recipe_label.setText(
                f"直接取 {treatment.neutralizer_dose_ml:.2f} ml "
                f"{neutralizer_name}（{treatment.neutralizer_percent:.2f}%），"
                "无需加水。"
            )

    def _update_formula(self, result, treatment) -> None:
        paste = format_plain(result.paste_ml)
        multiplier = f"{result.multiplier:.1f}"
        exact = format_plain(result.exact_pure_alcohol_ml)
        percent = f"{result.alcohol_percent:.2f}"
        solution = f"{result.solution_ml:.2f}"
        pure = f"{result.pure_alcohol_ml:.2f}"

        lines = [
            (
                '<span style="color:#66758A;">01</span>&nbsp;&nbsp;'
                f"{paste} ml × {multiplier} = "
                f'<span style="color:#EBC783;">{exact} ml</span> 纯酒精'
            ),
            (
                '<span style="color:#66758A;">02</span>&nbsp;&nbsp;'
                f"{exact} ml ÷ {percent}% = "
                f'<span style="color:#EBC783;">{solution} ml</span> 溶液'
            ),
        ]

        if treatment.protein_ml == 0:
            lines.append(
                '<span style="color:#66758A;">03</span>&nbsp;&nbsp;'
                "蛋白质为 0，跳过酸碱处理"
            )
        else:
            agent_name = AGENT_NAMES[treatment.agent]
            neutralizer_name = AGENT_NAMES[treatment.neutralizer]
            raw_agent = format_plain(
                round_half_up(treatment.agent_raw_dose_ml, 2)
            )
            lines.append(
                '<span style="color:#66758A;">03</span>&nbsp;&nbsp;'
                f"{format_plain(treatment.protein_ml)} ml ÷ "
                f"{treatment.agent_percent:.2f}% ≈ {raw_agent} ml → "
                f"向上取整 <span style=\"color:#EBC783;\">"
                f"{treatment.agent_dose_ml:.2f} ml</span> {agent_name}"
            )
            lines.append(
                '<span style="color:#66758A;">04</span>&nbsp;&nbsp;'
                f"实际 {treatment.agent_dose_ml:.2f} × "
                f"{treatment.agent_percent:.2f}% = "
                f"{treatment.agent_pure_ml:.2f} ml；剩余 "
                f"{treatment.residual_ml:.2f} ml {agent_name}"
            )

            if treatment.residual_ml == 0:
                lines.append(
                    '<span style="color:#66758A;">05</span>&nbsp;&nbsp;'
                    "无剩余酸碱，无需中和"
                )
            else:
                raw_neutralizer = format_plain(
                    round_half_up(treatment.neutralizer_raw_dose_ml, 2)
                )
                lines.append(
                    '<span style="color:#66758A;">05</span>&nbsp;&nbsp;'
                    f"{treatment.residual_ml:.2f} ml ÷ "
                    f"{treatment.neutralizer_percent:.2f}% ≈ "
                    f"{raw_neutralizer} ml → 取 "
                    f"<span style=\"color:#EBC783;\">"
                    f"{treatment.neutralizer_dose_ml:.2f} ml</span>；"
                    f"目标 {treatment.target_percent:.2f}%"
                )
                if treatment.diluted:
                    lines.append(
                        '<span style="color:#66758A;">06</span>&nbsp;&nbsp;'
                        f"{treatment.stock_agent_ml} ml {neutralizer_name} + "
                        f"{treatment.stock_water_ml} ml 水 = "
                        f"{treatment.stock_total_ml} ml "
                        f"{treatment.target_percent:.2f}% 储备液"
                    )
                else:
                    lines.append(
                        '<span style="color:#66758A;">06</span>&nbsp;&nbsp;'
                        f"直接取 {treatment.neutralizer_dose_ml:.2f} ml "
                        f"{neutralizer_name}，无需加水"
                    )

        body = "".join(
            f'<p style="margin:0 0 5px 0;">{line}</p>' for line in lines
        )
        self.formula_label.setText(
            f'<div style="color:#AEB9C9;">{body}</div>'
        )

    # 供测试与后续模块读取当前状态
    def current_values(self) -> tuple[float, float, float]:
        return (
            self.paste_spin.value(),
            self.concentration_spin.value(),
            self.multiplier_spin.value(),
        )

    def current_protein_values(self) -> tuple[float, str, float, float]:
        return (
            self.protein_spin.value(),
            str(self.agent_combo.currentData()),
            self.agent_concentration_spin.value(),
            self.neutralizer_concentration_spin.value(),
        )
