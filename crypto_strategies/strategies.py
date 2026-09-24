"""Systematic strategies suited to continuously traded, liquid crypto majors."""

from dataclasses import dataclass
from typing import Sequence

from .engine import Bar, Signal
from .indicators import atr, ema


@dataclass(frozen=True)
class TrendStrategy:
    """EMA trend filter with an ATR trailing exit.

    The strategy is long/short and remains flat during indicator warm-up. A
    close across the slow EMA flips direction; a volatility-scaled trailing
    stop exits a position before the next possible entry.
    """

    fast_period: int = 20
    slow_period: int = 80
    atr_period: int = 14
    stop_atr: float = 3.0

    def signals(self, bars: Sequence[Bar]) -> list[Signal]:
        if not (1 <= self.fast_period < self.slow_period and self.atr_period >= 1 and self.stop_atr > 0):
            raise ValueError("invalid trend strategy parameters")
        closes = [bar.close for bar in bars]
        fast = ema(closes, self.fast_period)
        slow = ema(closes, self.slow_period)
        volatility = atr([b.high for b in bars], [b.low for b in bars], closes, self.atr_period)
        output = [Signal.FLAT] * len(bars)
        position = Signal.FLAT
        extreme = 0.0
        for i, close in enumerate(closes):
            if fast[i] is None or slow[i] is None or volatility[i] is None:
                continue
            desired = Signal.LONG if fast[i] > slow[i] else Signal.SHORT
            if position == Signal.LONG:
                extreme = max(extreme, bars[i].high)
                if close < extreme - self.stop_atr * volatility[i]:
                    position = Signal.FLAT
                    output[i] = position
                    continue
            elif position == Signal.SHORT:
                extreme = min(extreme, bars[i].low)
                if close > extreme + self.stop_atr * volatility[i]:
                    position = Signal.FLAT
                    output[i] = position
                    continue
            if position == Signal.FLAT or desired != position:
                position = desired
                extreme = bars[i].high if position == Signal.LONG else bars[i].low
            output[i] = position
        return output


@dataclass(frozen=True)
class BreakoutStrategy:
    """Donchian breakout with separate, shorter exit channels."""

    entry_period: int = 55
    exit_period: int = 20

    def signals(self, bars: Sequence[Bar]) -> list[Signal]:
        if self.entry_period <= self.exit_period or self.exit_period < 1:
            raise ValueError("entry_period must exceed a positive exit_period")
        output = [Signal.FLAT] * len(bars)
        position = Signal.FLAT
        for i, bar in enumerate(bars):
            if i < self.entry_period:
                continue
            # Channels deliberately exclude the current bar.
            entry_high = max(b.high for b in bars[i - self.entry_period : i])
            entry_low = min(b.low for b in bars[i - self.entry_period : i])
            exit_high = max(b.high for b in bars[i - self.exit_period : i])
            exit_low = min(b.low for b in bars[i - self.exit_period : i])
            if position == Signal.LONG and bar.close < exit_low:
                position = Signal.FLAT
            elif position == Signal.SHORT and bar.close > exit_high:
                position = Signal.FLAT
            if bar.close > entry_high:
                position = Signal.LONG
            elif bar.close < entry_low:
                position = Signal.SHORT
            output[i] = position
        return output
