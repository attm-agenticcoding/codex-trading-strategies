import unittest
from datetime import datetime, timedelta, timezone

from crypto_strategies.engine import Bar, Signal, backtest
from crypto_strategies.strategies import BreakoutStrategy, TrendStrategy


def bars(prices: list[float]) -> list[Bar]:
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return [
        Bar(start + timedelta(days=i), price, price + 1, price - 1, price, 1000)
        for i, price in enumerate(prices)
    ]


class FixedStrategy:
    def __init__(self, values: list[Signal]):
        self.values = values

    def signals(self, _: list[Bar]) -> list[Signal]:
        return self.values


class BacktestTests(unittest.TestCase):
    def test_signal_is_filled_at_next_open(self) -> None:
        data = bars([100, 110, 120])
        result = backtest(data, FixedStrategy([Signal.LONG, Signal.LONG, Signal.FLAT]), fee_bps=0, slippage_bps=0)
        self.assertEqual(result.trades[0].entry_price, 110)
        self.assertEqual(result.trades[0].exit_price, 120)
        self.assertAlmostEqual(result.total_return, 10 / 110)

    def test_costs_reduce_flat_price_trade(self) -> None:
        data = bars([100, 100])
        result = backtest(data, FixedStrategy([Signal.LONG, Signal.LONG]), fee_bps=10, slippage_bps=0)
        self.assertLess(result.final_equity, result.initial_equity)

    def test_bad_bar_and_ordering_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Bar(datetime.now(timezone.utc), 100, 90, 80, 100, 1)
        data = list(reversed(bars([100, 101])))
        with self.assertRaises(ValueError):
            backtest(data, FixedStrategy([Signal.FLAT, Signal.FLAT]))


class StrategyTests(unittest.TestCase):
    def test_trend_warms_up_then_goes_long(self) -> None:
        signals = TrendStrategy(fast_period=2, slow_period=4, atr_period=2).signals(bars([100, 101, 102, 103, 104]))
        self.assertEqual(signals[:3], [Signal.FLAT] * 3)
        self.assertEqual(signals[3:], [Signal.LONG, Signal.LONG])

    def test_trend_stop_can_exit_before_reentry(self) -> None:
        data = bars([100, 102, 104, 106, 108, 100, 101])
        signals = TrendStrategy(fast_period=2, slow_period=4, atr_period=2, stop_atr=1).signals(data)
        self.assertEqual(signals[4], Signal.LONG)
        self.assertEqual(signals[5], Signal.FLAT)

    def test_breakout_uses_prior_channel(self) -> None:
        strategy = BreakoutStrategy(entry_period=3, exit_period=2)
        signals = strategy.signals(bars([100, 101, 102, 104, 103]))
        self.assertEqual(signals[2], Signal.FLAT)
        self.assertEqual(signals[3], Signal.LONG)
        self.assertEqual(signals[4], Signal.LONG)


if __name__ == "__main__":
    unittest.main()
