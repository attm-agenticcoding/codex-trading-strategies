"""Indicators with explicit warm-up values represented by ``None``."""

from typing import Sequence


def ema(values: Sequence[float], period: int) -> list[float | None]:
    if period < 1:
        raise ValueError("period must be positive")
    result: list[float | None] = [None] * len(values)
    if len(values) < period:
        return result
    seed = sum(values[:period]) / period
    result[period - 1] = seed
    alpha = 2 / (period + 1)
    for i in range(period, len(values)):
        seed = alpha * values[i] + (1 - alpha) * seed
        result[i] = seed
    return result


def atr(high: Sequence[float], low: Sequence[float], close: Sequence[float], period: int) -> list[float | None]:
    if not (len(high) == len(low) == len(close)):
        raise ValueError("price arrays must have equal length")
    true_ranges = [high[0] - low[0]] if high else []
    for i in range(1, len(close)):
        true_ranges.append(max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1])))
    return ema(true_ranges, period)
