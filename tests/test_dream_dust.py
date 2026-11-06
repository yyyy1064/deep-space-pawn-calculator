"""梦尘计算核心测试。"""

from __future__ import annotations

import unittest
from decimal import Decimal

from app.calculators.dream_dust import (
    CalculationError,
    calculate_dream_dust,
    calculate_protein_treatment,
    ceil_ml,
    format_plain,
    round_half_up,
)


class RoundHalfUpTests(unittest.TestCase):
    def test_half_up_not_bankers_rounding(self) -> None:
        self.assertEqual(round_half_up("2.25", 1), Decimal("2.3"))
        self.assertEqual(round_half_up("2.35", 1), Decimal("2.4"))
        self.assertEqual(round_half_up("2.44", 1), Decimal("2.4"))
        self.assertEqual(round_half_up("2.45", 1), Decimal("2.5"))

    def test_default_precision_is_two_places(self) -> None:
        self.assertEqual(round_half_up("2.255"), Decimal("2.26"))
        self.assertEqual(round_half_up("2.254"), Decimal("2.25"))

    def test_ceil_ml(self) -> None:
        self.assertEqual(ceil_ml("5.1546"), 6)
        self.assertEqual(ceil_ml("5.00"), 5)
        self.assertEqual(ceil_ml("0.01"), 1)
        self.assertEqual(ceil_ml("0"), 0)

    def test_format_plain_removes_trailing_zeroes(self) -> None:
        self.assertEqual(format_plain(Decimal("190.9600")), "190.96")
        self.assertEqual(format_plain(Decimal("3.0")), "3")
        self.assertEqual(format_plain(Decimal("0.0")), "0")


class DreamDustCalculationTests(unittest.TestCase):
    def test_reference_example(self) -> None:
        result = calculate_dream_dust("61.6", "70", "3.1")
        self.assertEqual(result.exact_pure_alcohol_ml, Decimal("190.96"))
        self.assertEqual(result.pure_alcohol_ml, Decimal("190.96"))
        self.assertEqual(result.solution_ml, Decimal("272.80"))

    def test_solution_uses_unrounded_intermediate(self) -> None:
        result = calculate_dream_dust("61.6", "70", "3.1")
        # 若先把纯酒精取整成 191.0，会得到 272.9；这里应采用 190.96。
        self.assertNotEqual(result.solution_ml, Decimal("272.9"))
        self.assertEqual(result.solution_ml, Decimal("272.80"))

    def test_full_concentration(self) -> None:
        result = calculate_dream_dust("10", "100", "3")
        self.assertEqual(result.pure_alcohol_ml, Decimal("30.00"))
        self.assertEqual(result.solution_ml, Decimal("30.00"))

    def test_small_values(self) -> None:
        result = calculate_dream_dust("0.1", "70", "3")
        self.assertEqual(result.exact_pure_alcohol_ml, Decimal("0.3"))
        self.assertEqual(result.solution_ml, Decimal("0.43"))

    def test_zero_dose(self) -> None:
        result = calculate_dream_dust("0", "70", "3")
        self.assertEqual(result.solution_ml, Decimal("0.00"))

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


class ProteinTreatmentTests(unittest.TestCase):
    def test_reference_example(self) -> None:
        result = calculate_protein_treatment("5", "base", "97", "98")
        self.assertEqual(result.agent_dose_ml, 6)
        self.assertEqual(result.agent_pure_ml, Decimal("5.82"))
        self.assertEqual(result.residual_ml, Decimal("0.82"))
        self.assertEqual(result.neutralizer, "acid")
        self.assertEqual(result.neutralizer_dose_ml, 1)
        self.assertEqual(result.target_percent, Decimal("82.00"))
        self.assertEqual(result.stock_agent_ml, 41)
        self.assertEqual(result.stock_water_ml, 8)
        self.assertEqual(result.stock_total_ml, 49)
        self.assertTrue(result.diluted)

    def test_exact_reaction_needs_no_neutralization(self) -> None:
        result = calculate_protein_treatment("9.7", "base", "97", "98")
        self.assertEqual(result.agent_dose_ml, 10)
        self.assertEqual(result.agent_pure_ml, Decimal("9.7"))
        self.assertEqual(result.residual_ml, Decimal("0"))
        self.assertEqual(result.neutralizer_dose_ml, 0)
        self.assertFalse(result.diluted)

    def test_acid_agent_uses_base_neutralizer(self) -> None:
        result = calculate_protein_treatment("5", "acid", "98", "97")
        self.assertEqual(result.agent_dose_ml, 6)
        self.assertEqual(result.agent_pure_ml, Decimal("5.88"))
        self.assertEqual(result.residual_ml, Decimal("0.88"))
        self.assertEqual(result.neutralizer, "base")
        self.assertEqual(result.target_percent, Decimal("88.00"))
        self.assertEqual(result.stock_agent_ml, 88)
        self.assertEqual(result.stock_water_ml, 9)
        self.assertEqual(result.stock_total_ml, 97)

    def test_zero_protein_skips_treatment(self) -> None:
        result = calculate_protein_treatment("0", "base", "97", "98")
        self.assertEqual(result.agent_dose_ml, 0)
        self.assertEqual(result.residual_ml, Decimal("0"))
        self.assertEqual(result.neutralizer_dose_ml, 0)
        self.assertEqual(result.stock_total_ml, 0)

    def test_minimum_one_ml_for_tiny_protein(self) -> None:
        result = calculate_protein_treatment("0.01", "base", "97", "98")
        self.assertEqual(result.agent_dose_ml, 1)
        self.assertEqual(result.agent_pure_ml, Decimal("0.97"))
        self.assertEqual(result.residual_ml, Decimal("0.96"))
        self.assertEqual(result.target_percent, Decimal("96.00"))
        self.assertEqual(result.stock_agent_ml, 48)
        self.assertEqual(result.stock_water_ml, 1)

    def test_invalid_inputs(self) -> None:
        with self.assertRaises(CalculationError):
            calculate_protein_treatment("-1", "base", "97", "98")
        with self.assertRaises(CalculationError):
            calculate_protein_treatment("5", "water", "97", "98")
        with self.assertRaises(CalculationError):
            calculate_protein_treatment("5", "base", "0", "98")
        with self.assertRaises(CalculationError):
            calculate_protein_treatment("5", "base", "97", "101")


if __name__ == "__main__":
    unittest.main()
