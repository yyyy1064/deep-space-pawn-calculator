"""梦尘计算核心测试。"""

from __future__ import annotations

import unittest
from decimal import Decimal

from app.calculators.dream_dust import (
    CalculationError,
    calculate_dream_dust,
    format_plain,
    round_half_up,
)


class RoundHalfUpTests(unittest.TestCase):
    def test_half_up_not_bankers_rounding(self) -> None:
        self.assertEqual(round_half_up("2.25", 1), Decimal("2.3"))
        self.assertEqual(round_half_up("2.35", 1), Decimal("2.4"))
        self.assertEqual(round_half_up("2.44", 1), Decimal("2.4"))
        self.assertEqual(round_half_up("2.45", 1), Decimal("2.5"))

    def test_format_plain_removes_trailing_zeroes(self) -> None:
        self.assertEqual(format_plain(Decimal("190.9600")), "190.96")
        self.assertEqual(format_plain(Decimal("3.0")), "3")
        self.assertEqual(format_plain(Decimal("0.0")), "0")


class DreamDustCalculationTests(unittest.TestCase):
    def test_reference_example(self) -> None:
        result = calculate_dream_dust("61.6", "70", "3.1")
        self.assertEqual(result.exact_pure_alcohol_ml, Decimal("190.96"))
        self.assertEqual(result.pure_alcohol_ml, Decimal("191.0"))
        self.assertEqual(result.solution_ml, Decimal("272.8"))

    def test_solution_uses_unrounded_intermediate(self) -> None:
        result = calculate_dream_dust("61.6", "70", "3.1")
        # 若先把纯酒精取整成 191.0，会得到 272.9；这里应采用 190.96。
        self.assertNotEqual(result.solution_ml, Decimal("272.9"))
        self.assertEqual(result.solution_ml, Decimal("272.8"))

    def test_full_concentration(self) -> None:
        result = calculate_dream_dust("10", "100", "3")
        self.assertEqual(result.pure_alcohol_ml, Decimal("30.0"))
        self.assertEqual(result.solution_ml, Decimal("30.0"))

    def test_small_values(self) -> None:
        result = calculate_dream_dust("0.1", "70", "3")
        self.assertEqual(result.exact_pure_alcohol_ml, Decimal("0.3"))
        self.assertEqual(result.solution_ml, Decimal("0.4"))

    def test_zero_dose(self) -> None:
        result = calculate_dream_dust("0", "70", "3")
        self.assertEqual(result.solution_ml, Decimal("0.0"))

    def test_invalid_concentration(self) -> None:
        with self.assertRaises(CalculationError):
            calculate_dream_dust("10", "0", "3")
        with self.assertRaises(CalculationError):
            calculate_dream_dust("10", "101", "3")

    def test_invalid_multiplier(self) -> None:
        with self.assertRaises(CalculationError):
            calculate_dream_dust("10", "70", "2.9")
        with self.assertRaises(CalculationError):
            calculate_dream_dust("10", "70", "6.1")

    def test_invalid_dose(self) -> None:
        with self.assertRaises(CalculationError):
            calculate_dream_dust("-1", "70", "3")


if __name__ == "__main__":
    unittest.main()
