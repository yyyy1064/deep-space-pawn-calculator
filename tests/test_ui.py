"""梦尘页面交互测试（离屏渲染）。"""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from app.pages.dream_dust import DreamDustPage  # noqa: E402
from app.theme import APP_STYLESHEET  # noqa: E402


class DreamDustPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyleSheet(APP_STYLESHEET)

    def setUp(self) -> None:
        self.page = DreamDustPage()
        self.page.concentration_spin.setValue(70.0)
        self.page.multiplier_spin.setValue(3.1)
        self.page.paste_spin.setValue(61.6)

    def tearDown(self) -> None:
        self.page.deleteLater()
        self.app.processEvents()

    def test_reference_example_shows_expected_values(self) -> None:
        self.assertEqual(self.page.result_value.text(), "272.8")
        self.assertEqual(self.page.pure_value.text(), "191.0")
        self.assertIn("190.96", self.page.formula_label.text())

    def test_multiplier_spin_updates_slider(self) -> None:
        self.page.multiplier_spin.setValue(4.7)
        self.assertEqual(self.page.multiplier_slider.value(), 47)

    def test_slider_updates_multiplier_spin(self) -> None:
        self.page.multiplier_slider.setValue(52)
        self.assertAlmostEqual(self.page.multiplier_spin.value(), 5.2, places=6)

    def test_slider_min_and_max(self) -> None:
        self.page.multiplier_slider.setValue(30)
        self.assertEqual(self.page.multiplier_spin.value(), 3.0)
        self.page.multiplier_slider.setValue(60)
        self.assertEqual(self.page.multiplier_spin.value(), 6.0)

    def test_spinbox_clamps_to_game_range(self) -> None:
        self.page.multiplier_spin.setValue(1.0)
        self.assertEqual(self.page.multiplier_spin.value(), 3.0)
        self.assertEqual(self.page.multiplier_slider.value(), 30)

        self.page.multiplier_spin.setValue(9.0)
        self.assertEqual(self.page.multiplier_spin.value(), 6.0)
        self.assertEqual(self.page.multiplier_slider.value(), 60)

    def test_typed_out_of_range_is_clamped(self) -> None:
        line_edit = self.page.multiplier_spin.lineEdit()
        line_edit.setText("9.0")
        self.page.multiplier_spin.interpretText()
        self.app.processEvents()
        self.assertEqual(self.page.multiplier_spin.value(), 6.0)
        self.assertEqual(self.page.multiplier_slider.value(), 60)

    def test_concentration_change_updates_result(self) -> None:
        self.page.concentration_spin.setValue(100.0)
        self.assertEqual(self.page.result_value.text(), "191.0")

    def test_live_update_after_dose_change(self) -> None:
        self.page.paste_spin.setValue(100.0)
        self.assertEqual(self.page.result_value.text(), "442.9")


if __name__ == "__main__":
    unittest.main()
