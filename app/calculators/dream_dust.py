"""梦尘：梦帽菇糊 / 酒精浓度 / 萃取倍率计算。

计算链路：
    纯酒精体积 = 梦帽菇糊剂量 × 萃取倍率
    酒精溶液体积 = 纯酒精体积 ÷ 酒精浓度

取整口径：
    所有对外显示的数值四舍五入（ROUND_HALF_UP）保留 1 位小数；
    连续计算使用未取整的精确值，避免中间取整造成误差累积。
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from typing import Union

Number = Union[int, float, str, Decimal]


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


def round_half_up(value: Number, places: int = 1) -> Decimal:
    """标准四舍五入（不是 Python 内置的银行家舍入）。"""

    decimal_value = to_decimal(value)
    quantum = Decimal(1).scaleb(-places)
    with localcontext() as ctx:
        ctx.prec = 40
        return decimal_value.quantize(quantum, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class DreamDustResult:
    paste_ml: Decimal
    alcohol_percent: Decimal
    multiplier: Decimal
    exact_pure_alcohol_ml: Decimal
    pure_alcohol_ml: Decimal
    solution_ml: Decimal


def calculate_dream_dust(
    paste_ml: Number,
    alcohol_percent: Number,
    multiplier: Number,
) -> DreamDustResult:
    """按未取整的中间值计算，结果统一四舍五入到 1 位小数。"""

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
        pure_alcohol_ml=round_half_up(exact_pure, 1),
        solution_ml=round_half_up(exact_solution, 1),
    )


def format_plain(value: Number) -> str:
    """去掉无意义的尾零，用于展示精确中间值。"""

    decimal_value = to_decimal(value)
    text = format(decimal_value.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"
