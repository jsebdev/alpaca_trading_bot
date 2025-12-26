# Trading Bot - Automated Stock Trading System

A modular, production-ready trading bot for Alpaca paper trading with injectable strategy pattern.

## Quick Visual Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION                          │
│  python src/bots/day_bot.py --dry-run --symbols AAPL MSFT GOOGL │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DAY TRADING BOT                             │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│  │   Config     │   │   Logger     │   │  Strategy    │       │
│  │   (.env)     │   │  (console/   │   │  (Injectable)│       │
│  │              │   │   file)      │   │              │       │
│  └──────────────┘   └──────────────┘   └──────────────┘       │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
    ┌───────────────┐ ┌──────────────┐ ┌──────────────┐
    │   Alpaca      │ │ Market Data  │ │    Order     │
    │   Client      │ │   Fetcher    │ │   Manager    │
    │               │ │              │ │              │
    │ • Account     │ │ • Bars       │ │ • Bracket    │
    │ • Positions   │ │ • Gap Info   │ │ • Market     │
    │ • Status      │ │ • Candle Avg │ │ • Tracking   │
    └───────┬───────┘ └──────┬───────┘ └──────┬───────┘
            │                │                │
            └────────────────┼────────────────┘
                             ▼
                    ┌────────────────┐
                    │  ALPACA API    │
                    │  (Paper Trade) │
                    └────────────────┘
```

## Architecture at a Glance

```
src/                                     # All source code
├── LAYER 1: Entry Point
│   └── bots/day_bot.py ................. Main bot orchestration & CLI
│
├── LAYER 2: Business Logic
│   └── strategies/
│       ├── base_strategy.py ............ Abstract strategy interface
│       └── simple_strategy.py .......... Gap-down strategy
│
├── LAYER 3: Utilities
│   └── utils/
│       ├── config.py ................... Environment & configuration
│       ├── logger.py ................... Logging setup
│       ├── alpaca_client.py ............ Alpaca API wrapper
│       ├── market_data.py .............. Market data operations
│       └── order_manager.py ............ Order placement & tracking
│
├── LAYER 4: Lambda Handler
│   └── lambda/handler.py ............... AWS Lambda entry point
│
└── requirements.txt .................... Python dependencies

example_custom_strategy.py .............. Custom strategy examples (project root)
```

## How It Works: Simple Gap-Down Strategy

```
STEP 1: Get Available Cash
   └─> Account: $200,000 buying power

STEP 2: Scan Watchlist [AAPL, MSFT, GOOGL, AMZN, TSLA]
   │
   ├─> AAPL
   │   ├─ Previous Close: $272.19
   │   ├─ Current Open:   $272.14
   │   ├─ Gap: -0.02% ✓ (Gap Down!)
   │   ├─ Avg 5-day candle: $5.38
   │   ├─ Position: 5% × $200,000 = $10,000
   │   ├─ Take Profit: $272.14 + $5.38 = $277.53
   │   ├─ Stop Loss:   $272.14 - $5.38 = $266.76
   │   └─> TRADE! ✓
   │
   ├─> MSFT
   │   ├─ Previous Close: $483.98
   │   ├─ Current Open:   $487.36
   │   ├─ Gap: +0.70% ✗ (Gap Up - Skip)
   │   └─> SKIP
   │
   └─> GOOGL
       ├─ Previous Close: $302.46
       ├─ Current Open:   $301.73
       ├─ Gap: -0.24% ✓ (Gap Down!)
       ├─ Position: 5% × $190,000 = $9,500
       └─> TRADE! ✓

STEP 3: Execute Trades
   ├─> Place bracket order: AAPL $10,000
   └─> Place bracket order: GOOGL $9,500

RESULT: 2 trades, 3 skips
```

## Strategy Pattern: Swap Strategies Easily

```python
# Option 1: Use default gap-down strategy
strategy = SimpleGapDownStrategy(
    cash_allocation_percent=0.05,
    lookback_days=5,
    logger=logger
)

# Option 2: Create your own strategy
class MyStrategy(BaseStrategy):
    def evaluate(self, symbol, cash, market_data_fetcher):
        # Your custom logic here
        return TradeSignal(...)

strategy = MyStrategy(logger=logger)

# Option 3: Use momentum strategy
strategy = MomentumStrategy(
    lookback_days=10,
    min_gain_percent=5.0,
    logger=logger
)

# Inject into bot - no other code changes needed!
bot = DayTradingBot(config, strategy, logger)
```

## Usage

### Run in Dry-Run Mode (Recommended)
```bash
python src/bots/day_bot.py --dry-run
```

### Run with Live Paper Trading
```bash
python src/bots/day_bot.py
```

### Custom Watchlist
```bash
python src/bots/day_bot.py --dry-run --symbols AAPL TSLA NVDA AMD
```

## Output Example

```
2025-12-20 23:21:03 - INFO - Initialized DayTradingBot with Simple Gap-Down Strategy
2025-12-20 23:21:03 - INFO - Watchlist: AAPL, MSFT, GOOGL, AMZN, TSLA
2025-12-20 23:21:04 - INFO - Available buying power: $200,000.00
2025-12-20 23:21:04 - INFO - Evaluating 5 symbols...

2025-12-20 23:21:04 - INFO - AAPL: TRADE
  └─ Gap down -0.02% (open=$272.14, prev_close=$272.19)
  └─ TP=$277.53, SL=$266.76, allocating $10,000.00

2025-12-20 23:21:04 - INFO - MSFT: SKIP
  └─ No gap down (open=$487.36 >= prev_close=$483.98)

2025-12-20 23:21:04 - INFO - GOOGL: TRADE
  └─ Gap down -0.24% (open=$301.73, prev_close=$302.46)
  └─ TP=$309.27, SL=$294.19, allocating $9,500.00

2025-12-20 23:21:05 - INFO - Signals: 2 trades, 3 skips
```

## Configuration

Create or edit `.env`:
```bash
ALPACA_API_KEY=your_key_here
ALPACA_API_SECRET=your_secret_here
PAPER_TRADING=true
CASH_ALLOCATION_PERCENT=0.05
LOOKBACK_DAYS=5
```

## Key Features

✅ **Modular Architecture** - Clean separation of concerns
✅ **Injectable Strategies** - Swap strategies without changing bot code
✅ **Bracket Orders** - Automatic take profit & stop loss
✅ **Fractional Shares** - Uses notional amounts
✅ **Dry-Run Mode** - Test without placing real orders
✅ **Comprehensive Logging** - Track every decision
✅ **Error Handling** - Graceful failure recovery
✅ **Paper Trading** - Safe testing environment
✅ **Production-Ready** - Senior-level code quality

## AWS Lambda Deployment (Optional)

```
┌─────────────────────────────────────────┐
│        AWS EventBridge                  │
│    Schedule: cron(30 13 ? * MON-FRI *)  │  # 9:30 AM ET
└────────────┬────────────────────────────┘
             │ Trigger
             ▼
┌─────────────────────────────────────────┐
│         AWS Lambda Function             │
│  • Runtime: Python 3.12                 │
│  • Timeout: 5 minutes                   │
│  • Memory: 512 MB                       │
│  • Handler: lambda_handler              │
│  • Env Vars: ALPACA_API_KEY/SECRET      │
└────────────┬────────────────────────────┘
             │ Execute
             ▼
┌─────────────────────────────────────────┐
│          day_bot.py                     │
│  1. Scan watchlist                      │
│  2. Generate signals                    │
│  3. Place trades                        │
└────────────┬────────────────────────────┘
             │ Log
             ▼
┌─────────────────────────────────────────┐
│       CloudWatch Logs                   │
│  • Execution logs                       │
│  • Trade decisions                      │
│  • Error tracking                       │
└─────────────────────────────────────────┘
```

## Creating Custom Strategies

See `example_custom_strategy.py` for complete examples. Basic structure:

```python
from src.strategies import BaseStrategy, TradeSignal

class MyCustomStrategy(BaseStrategy):
    def get_name(self) -> str:
        return "My Custom Strategy"

    def get_description(self) -> str:
        return "Description of what this strategy does"

    def evaluate(self, symbol, available_cash, market_data_fetcher):
        # 1. Fetch market data
        bars = market_data_fetcher.get_historical_bars(symbol, 10)

        # 2. Apply your logic
        if your_condition_met:
            return TradeSignal(
                symbol=symbol,
                should_trade=True,
                notional=available_cash * 0.05,
                take_profit_price=calculated_tp,
                stop_loss_price=calculated_sl,
                reason="Why you're trading"
            )

        # 3. Or skip
        return TradeSignal(
            symbol=symbol,
            should_trade=False,
            reason="Why you're skipping"
        )
```

## Documentation

- **ARCHITECTURE.md** - Detailed system architecture with diagrams
- **example_custom_strategy.py** - Strategy creation examples
- **day_bot.log** - Execution logs

## Safety Features

🛡️ **Paper Trading by Default** - No real money at risk
🛡️ **Dry-Run Mode** - Test without any API calls
🛡️ **Position Limits** - 5% cash allocation prevents over-exposure
🛡️ **Automatic Exits** - Bracket orders include TP & SL
🛡️ **Error Recovery** - Continues processing if one symbol fails
🛡️ **Comprehensive Logging** - Audit trail of all decisions

## Next Steps

1. ✅ Test in dry-run mode
2. ✅ Review logs and signals
3. ✅ Test with live paper trading
4. ⏳ Create custom strategies
5. ⏳ Deploy to AWS Lambda
6. ⏳ Monitor performance
7. ⏳ Backtest strategies
8. ⏳ Add alerting (SNS/email)

---

**Note**: This bot is designed for paper trading and educational purposes. Always test thoroughly before using real money. Trading involves risk of loss.
