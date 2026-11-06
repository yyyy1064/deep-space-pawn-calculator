"""梦尘：梦帽菇糊 / 酒精浓度 / 萃取倍率 / 蛋白质处理计算。

计算链路：
    纯酒精体积 = 梦帽菇糊剂量 × 萃取倍率
    酒精溶液体积 = 纯酒精体积 ÷ 酒精浓度

    处理剂剂量 = ceil(蛋白质体积 ÷ 处理剂浓度)，最低 1 ml
    处理剂实际有效量 = 剂量 × 浓度
    剩余酸碱 = 实际有效量 − 蛋白质体积

    中和剂剂量 = ceil(剩余酸碱 ÷ 中和剂浓度)，最低 1 ml
    中和目标浓度 = 剩余酸碱 ÷ 中和剂剂量 × 100%
    若中和剂浓度高于目标浓度，按整数 ml 配比稀释后取用。

取整口径：
    对外显示的普通数值四舍五入（ROUND_HALF_UP）保留 2 位小数；
    酸碱剂量向上取整到整数 ml；
    连续计算使用未取整的精确值，避免中间取整造成误差累积。
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_HALF_UP, localcontext
from fractions import Fraction
from typing import Union

Number = Union[int, float, str, Decimal]

AGENT_NAMES = {"acid": "酸", "base": "碱"}
VALID_AGENTS = frozenset(AGENT_NAMES)


class CalculationError(ValueError):
    """输入不满足计算条件。"""


def to_decimal(value: Number) -> Decimal:
    """把界面上的 float 安全地转成 Decimal，避免二进制浮点误差。"""

    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise CalculationError(f"无法识别的数值：{value!r}") from exc


def round_half_up(value: Number, places: int = 2) -> Decimal:
    """标准四舍五入（不是 Python 内置的银行家舍入）。"""

    decimal_value = to_decimal(value)
    quantum = Decimal(1).scaleb(-places)
    with localcontext() as ctx:
        ctx.prec = 40
        return decimal_value.quantize(quantum, rounding=ROUND_HALF_UP)


def ceil_ml(value: Number) -> int:
    """把体积向上取整到整数 ml。"""

    decimal_value = to_decimal(value)
    if decimal_value < 0:
        raise CalculationError("体积不能小于 0")
    return int(decimal_value.to_integral_value(rounding=ROUND_CEILING))


def _opposite_agent(agent: str) -> str:
    return "acid" if agent == "base" else "base"


@dataclass(frozen=True)
class DreamDustResult:
    paste_ml: Decimal
    alcohol_percent: Decimal
    multiplier: Decimal
    exact_pure_alcohol_ml: Decimal
    pure_alcohol_ml: Decimal
    solution_ml: Decimal


@dataclass(frozen=True)
class ProteinTreatmentResult:
    protein_ml: Decimal
    agent: str
    agent_percent: Decimal
    agent_raw_dose_ml: Decimal
    agent_dose_ml: int
    agent_pure_ml: Decimal
    residual_ml: Decimal
    neutralizer: str
    neutralizer_percent: Decimal
    neutralizer_raw_dose_ml: Decimal
    neutralizer_dose_ml: int
    target_percent: Decimal
    stock_agent_ml: int
    stock_water_ml: int
    stock_total_ml: int
    diluted: bool


def calculate_dream_dust(
    paste_ml: Number,
    alcohol_percent: Number,
    multiplier: Number,
) -> DreamDustResult:
    """按未取整的中间值计算，结果统一四舍五入到 2 位小数。"""

    paste = to_decimal(paste_ml)
    percent = to_decimal(alcohol_percent)
    factor = to_decimal(multiplier)

    if paste < 0:
        raise CalculationError("梦帽菇糊剂量不能小于 0")
    if percent <= 0 or percent > 100:
        raise CalculationError("酒精浓度必须在 0 到 100% 之间")
    if factor < 3 or factor > 6:
        raise CalculationError("萃取用酒精倍率必须在 3.0 到 6.0 之间")

    with localcontext() as ctx:
        ctx.prec = 40
        exact_pure = paste * factor
        exact_solution = exact_pure / (percent / Decimal(100))

    return DreamDustResult(
        paste_ml=paste,
        alcohol_percent=percent,
        multiplier=factor,
        exact_pure_alcohol_ml=exact_pure,
        pure_alcohol_ml=round_half_up(exact_pure, 2),
        solution_ml=round_half_up(exact_solution, 2),
    )


def calculate_protein_treatment(
    protein_ml: Number,
    agent: str,
    agent_percent: Number,
    neutralizer_percent: Number,
) -> ProteinTreatmentResult:
    """计算蛋白质处理剂剂量、剩余酸碱，以及中和所需稀释配比。

    ``agent`` 是用于沉淀蛋白质的试剂，``neutralizer`` 是用于中和剩余
    酸碱的相反试剂。所有试剂剂量按整数 ml 向上取整。
    """

    protein = to_decimal(protein_ml)
    agent_key = str(agent).strip().lower()
    agent_conc = to_decimal(agent_percent)
    neutralizer_conc = to_decimal(neutralizer_percent)

    if protein < 0:
        raise CalculationError("蛋白质含量不能小于 0")
    if agent_key not in VALID_AGENTS:
        raise CalculationError("处理剂必须选择酸或碱")
    if agent_conc <= 0 or agent_conc > 100:
        raise CalculationError("处理剂浓度必须在 0 到 100% 之间")
    if neutralizer_conc <= 0 or neutralizer_conc > 100:
        raise CalculationError("中和剂浓度必须在 0 到 100% 之间")

    neutralizer_key = _opposite_agent(agent_key)

    with localcontext() as ctx:
        ctx.prec = 40

        if protein == 0:
            agent_raw = Decimal(0)
            agent_dose = 0
            agent_pure = Decimal(0)
            residual = Decimal(0)
        else:
            agent_raw = protein / (agent_conc / Decimal(100))
            agent_dose = max(1, ceil_ml(agent_raw))
            agent_pure = Decimal(agent_dose) * agent_conc / Decimal(100)
            residual = max(agent_pure - protein, Decimal(0))

        if residual == 0:
            return ProteinTreatmentResult(
                protein_ml=protein,
                agent=agent_key,
                agent_percent=agent_conc,
                agent_raw_dose_ml=agent_raw,
                agent_dose_ml=agent_dose,
                agent_pure_ml=agent_pure,
                residual_ml=Decimal(0),
                neutralizer=neutralizer_key,
                neutralizer_percent=neutralizer_conc,
                neutralizer_raw_dose_ml=Decimal(0),
                neutralizer_dose_ml=0,
                target_percent=Decimal(0),
                stock_agent_ml=0,
                stock_water_ml=0,
                stock_total_ml=0,
                diluted=False,
            )

        neutralizer_raw = residual / (neutralizer_conc / Decimal(100))
        neutralizer_dose = max(1, ceil_ml(neutralizer_raw))
        target_exact = residual / Decimal(neutralizer_dose) * Decimal(100)
        target = min(round_half_up(target_exact, 2), neutralizer_conc)

        if target >= neutralizer_conc:
            stock_agent = neutralizer_dose
            stock_water = 0
            stock_total = neutralizer_dose
            diluted = False
        else:
            # 98% 稀释到 82%：98A = 82(A + W) -> A:W = 82:16 = 41:8。
            ratio = Fraction(target) / (Fraction(neutralizer_conc) - Fraction(target))
            stock_agent = ratio.numerator
            stock_water = ratio.denominator
            stock_total = stock_agent + stock_water

            # 储备液至少要有足够体积，供本次取用。
            if stock_total < neutralizer_dose:
                scale = ceil_ml(
                    Decimal(neutralizer_dose) / Decimal(stock_total)
                )
                stock_agent *= scale
                stock_water *= scale
                stock_total = stock_agent + stock_water
            diluted = True

    return ProteinTreatmentResult(
        protein_ml=protein,
        agent=agent_key,
        agent_percent=agent_conc,
        agent_raw_dose_ml=agent_raw,
        agent_dose_ml=agent_dose,
        agent_pure_ml=agent_pure,
        residual_ml=residual,
        neutralizer=neutralizer_key,
        neutralizer_percent=neutralizer_conc,
        neutralizer_raw_dose_ml=neutralizer_raw,
        neutralizer_dose_ml=neutralizer_dose,
        target_percent=target,
        stock_agent_ml=stock_agent,
        stock_water_ml=stock_water,
        stock_total_ml=stock_total,
        diluted=diluted,
    )


def format_plain(value: Number) -> str:
    """去掉无意义的尾零，用于展示精确中间值。"""

    decimal_value = to_decimal(value)
    text = format(decimal_value.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"
