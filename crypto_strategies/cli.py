"""Command-line interface for reproducible CSV backtests."""

import argparse
import csv
import json
from pathlib import Path

from .engine import Bar, backtest, utc_timestamp
from .strategies import BreakoutStrategy, TrendStrategy


def load_csv(path: Path) -> list[Bar]:
    with path.open(newline="", encoding="utf-8") as source:
        rows = csv.DictReader(source)
        required = {"timestamp", "open", "high", "low", "close", "volume"}
        if not rows.fieldnames or not required.issubset(rows.fieldnames):
            raise ValueError(f"CSV must contain columns: {', '.join(sorted(required))}")
        return [Bar(utc_timestamp(row["timestamp"]), *(float(row[key]) for key in ("open", "high", "low", "close", "volume"))) for row in rows]


def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest crypto-major strategies on OHLCV CSV data")
    parser.add_argument("csv", type=Path)
    parser.add_argument("--strategy", choices=("trend", "breakout"), default="trend")
    parser.add_argument("--fee-bps", type=float, default=6.0)
    parser.add_argument("--slippage-bps", type=float, default=2.0)
    parser.add_argument("--initial-equity", type=float, default=10_000.0)
    args = parser.parse_args()
    strategy = TrendStrategy() if args.strategy == "trend" else BreakoutStrategy()
    result = backtest(load_csv(args.csv), strategy, initial_equity=args.initial_equity, fee_bps=args.fee_bps, slippage_bps=args.slippage_bps)
    print(json.dumps({
        "strategy": args.strategy,
        "initial_equity": result.initial_equity,
        "final_equity": round(result.final_equity, 2),
        "total_return": round(result.total_return, 6),
        "max_drawdown": round(result.max_drawdown, 6),
        "trades": len(result.trades),
    }, indent=2))


if __name__ == "__main__":
    main()
