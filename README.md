# Crypto Major Trading Strategies

A dependency-free Python research toolkit for testing systematic strategies on
liquid crypto majors such as BTC and ETH. It includes realistic next-bar order
timing, explicit fees and slippage, short support, drawdown reporting, and two
strategy families that can be evaluated across different market regimes.

> **Research use only.** These examples are not investment advice. Backtest
> results do not represent live performance. Validate data, liquidity, funding,
> borrow availability, exchange outages, taxes, and execution assumptions before
> risking capital.

## Included strategies

### EMA trend + ATR stop

`TrendStrategy` follows the direction of a fast/slow exponential moving-average
pair. A trailing Average True Range stop responds to changing crypto volatility.
Defaults (20/80 EMA, 14 ATR, 3 ATR stop) are intended as a starting hypothesis,
not optimized parameters.

### Donchian breakout

`BreakoutStrategy` enters when a close exceeds the previous 55-bar high or low,
then exits on a shorter 20-bar channel. Current-bar prices are excluded from all
channel calculations to prevent leakage.

Both strategies are long/short. If using spot-only markets, treat `SHORT` as
`FLAT`, or use a carefully managed derivatives implementation.

## Data and usage

Supply an ascending CSV with this header:

```csv
timestamp,open,high,low,close,volume
2025-01-01T00:00:00Z,93425,95000,92500,94410,1234.5
```

Timestamps may be ISO-8601 values or Unix seconds. Run either backtest:

```bash
python -m crypto_strategies.cli btc-usd-1d.csv --strategy trend
python -m crypto_strategies.cli eth-usd-1d.csv --strategy breakout --fee-bps 8 --slippage-bps 3
```

Example output:

```json
{
  "strategy": "trend",
  "initial_equity": 10000.0,
  "final_equity": 11234.56,
  "total_return": 0.123456,
  "max_drawdown": 0.084321,
  "trades": 12
}
```

Signals calculated at a bar's close fill at the **next bar's open**. The final
position is liquidated at the last close. Fees and adverse slippage are charged
on both entry and exit. Equity is allocated notionally rather than compounded
with leverage; default allocation is 100%.

## Research workflow

1. Use survivorship-free, gap-aware OHLCV data from the intended venue.
2. Reserve a genuinely unseen period for out-of-sample evaluation.
3. Test several bar sizes and BTC/ETH independently; avoid selecting only the
   best instrument or parameters.
4. Stress costs, including derivatives funding, and simulate delayed fills.
5. Prefer stable parameter regions over a single sharp optimum.
6. Paper trade through volatile and quiet regimes before considering deployment.

Run the test suite with:

```bash
python -m unittest discover -s tests -v
```
