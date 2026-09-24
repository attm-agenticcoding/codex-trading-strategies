"""Small, dependency-free signal and backtest engine.

Orders generated from bar *t* are filled at the next bar's open.  This timing is
deliberate: using the same close that generated a signal would introduce
look-ahead bias.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import IntEnum
from typing import Protocol, Sequence


@dataclass(frozen=True)
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        if min(self.open, self.high, self.low, self.close) <= 0:
            raise ValueError("OHLC prices must be positive")
        if self.volume < 0 or self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("invalid OHLCV bar")


class Signal(IntEnum):
    SHORT = -1
    FLAT = 0
    LONG = 1


class Strategy(Protocol):
    def signals(self, bars: Sequence[Bar]) -> list[Signal]: ...


@dataclass(frozen=True)
class Trade:
    entry_time: datetime
    exit_time: datetime
    direction: Signal
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float


@dataclass(frozen=True)
class StrategyResult:
    initial_equity: float
    final_equity: float
    total_return: float
    max_drawdown: float
    trades: tuple[Trade, ...]
    equity_curve: tuple[float, ...]


def backtest(
    bars: Sequence[Bar],
    strategy: Strategy,
    *,
    initial_equity: float = 10_000.0,
    allocation: float = 1.0,
    fee_bps: float = 6.0,
    slippage_bps: float = 2.0,
) -> StrategyResult:
    """Backtest target-position signals with next-open fills.

    ``allocation`` is the fraction of current equity placed at risk notionally.
    Positions are marked to each close. A final open position is liquidated at
    the last close so results always include realized transaction costs.
    """
    if len(bars) < 2:
        raise ValueError("at least two bars are required")
    if initial_equity <= 0 or not 0 < allocation <= 1 or fee_bps < 0 or slippage_bps < 0:
        raise ValueError("invalid backtest parameters")
    if any(bars[i].timestamp >= bars[i + 1].timestamp for i in range(len(bars) - 1)):
        raise ValueError("bars must be strictly chronological")

    signals = strategy.signals(bars)
    if len(signals) != len(bars):
        raise ValueError("strategy must return one signal per bar")

    cash = initial_equity
    quantity = 0.0
    direction = Signal.FLAT
    entry_price = 0.0
    entry_time = bars[0].timestamp
    trades: list[Trade] = []
    curve = [initial_equity]
    cost_rate = (fee_bps + slippage_bps) / 10_000

    for i in range(1, len(bars)):
        bar = bars[i]
        target = signals[i - 1]
        if target != direction:
            if direction != Signal.FLAT:
                exit_price = bar.open * (1 - cost_rate * int(direction))
                pnl = quantity * int(direction) * (exit_price - entry_price)
                cash += pnl
                trades.append(Trade(entry_time, bar.timestamp, direction, entry_price, exit_price, quantity, pnl))
                quantity = 0.0
            if target != Signal.FLAT:
                entry_price = bar.open * (1 + cost_rate * int(target))
                quantity = cash * allocation / entry_price
                direction = target
                entry_time = bar.timestamp
            else:
                direction = Signal.FLAT

        marked = cash if direction == Signal.FLAT else cash + quantity * int(direction) * (bar.close - entry_price)
        curve.append(marked)

    if direction != Signal.FLAT:
        bar = bars[-1]
        exit_price = bar.close * (1 - cost_rate * int(direction))
        pnl = quantity * int(direction) * (exit_price - entry_price)
        cash += pnl
        trades.append(Trade(entry_time, bar.timestamp, direction, entry_price, exit_price, quantity, pnl))
        curve[-1] = cash

    peak = curve[0]
    max_drawdown = 0.0
    for equity in curve:
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, (peak - equity) / peak)
    return StrategyResult(
        initial_equity,
        cash,
        cash / initial_equity - 1,
        max_drawdown,
        tuple(trades),
        tuple(curve),
    )


def utc_timestamp(value: str) -> datetime:
    """Parse an ISO-8601 or Unix-seconds timestamp as an aware UTC datetime."""
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    except ValueError:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.replace(tzinfo=parsed.tzinfo or timezone.utc).astimezone(timezone.utc)
