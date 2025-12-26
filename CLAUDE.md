# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Alpaca paper trading bot with a modular, strategy-injectable architecture. The bot evaluates stocks against custom strategies and places bracket orders (entry + take profit + stop loss) automatically. The default implementation uses a gap-down strategy.

## Environment Setup

This project uses conda. To activate the environment:

```bash
conda activate alpaca
```

The environment is defined in `environment.yml` with core dependencies:
- `alpaca-py` (via pip) - Alpaca trading API
- `python-dotenv` - Environment variable management
- Standard data libraries (pandas, numpy, matplotlib)

## Running the Bot

### Dry-run mode (logs signals without placing orders):
```bash
python src/bots/day_bot.py --dry-run
```

### Live paper trading:
```bash
python src/bots/day_bot.py
```

### Custom watchlist:
```bash
python src/bots/day_bot.py --dry-run --symbols AAPL TSLA NVDA AMD
```

## Configuration

The bot requires a `.env` file in the project root with:
- `ALPACA_API_KEY` - Your Alpaca API key
- `ALPACA_API_SECRET` - Your Alpaca API secret
- `PAPER_TRADING` - Set to "true" for paper trading
- `CASH_ALLOCATION_PERCENT` - Percentage of cash per trade (default: 0.05 = 5%)
- `LOOKBACK_DAYS` - Days of historical data to analyze (default: 5)

## Core Architecture

The system follows a **Strategy Pattern** design where trading strategies are injected into the bot:

### Entry Point
- `src/bots/day_bot.py` - Main orchestration & CLI. Contains `DayTradingBot` class that coordinates all components.

### Strategy Layer (Business Logic)
- `src/strategies/base_strategy.py` - Abstract `BaseStrategy` class defining the interface all strategies must implement
- `src/strategies/simple_strategy.py` - Concrete `SimpleGapDownStrategy` implementation

**Key pattern**: Strategies return `TradeSignal` objects that encapsulate whether to trade, position size, and bracket order prices (TP/SL). The bot executes these signals without knowing the strategy logic.

### Utilities Layer
- `src/utils/config.py` - Loads and validates configuration from `.env`
- `src/utils/alpaca_client.py` - `AlpacaClientWrapper` facade for Alpaca API (trading & data clients)
- `src/utils/market_data.py` - `MarketDataFetcher` for historical bars, gap analysis, candle calculations
- `src/utils/order_manager.py` - `OrderManager` for bracket and market order placement
- `src/utils/logger.py` - Logging setup (console + file)

### Lambda Handler
- `src/lambda/handler.py` - AWS Lambda entry point for scheduled cloud execution

### Dependency Flow
```
DayTradingBot
├── Config (from .env)
├── Strategy (injected)
├── AlpacaClientWrapper
│   ├── TradingClient (alpaca-py)
│   └── DataClient (alpaca-py)
├── MarketDataFetcher (uses DataClient)
└── OrderManager (uses TradingClient)
```

## Bot Execution Flow

1. **Initialization**: Load config, create strategy, initialize Alpaca clients
2. **Account Check**: Verify account is tradeable and get available buying power
3. **Strategy Evaluation**: For each symbol in watchlist:
   - Call `strategy.evaluate(symbol, available_cash, market_data_fetcher)`
   - Strategy fetches market data and applies its logic
   - Returns `TradeSignal(should_trade, notional, take_profit_price, stop_loss_price, reason)`
   - If should_trade is True, deduct notional from remaining cash
4. **Order Execution**: For each positive signal, place bracket order via `OrderManager`
5. **Summary**: Log results (number of trades vs skips)

## Creating Custom Strategies

See `example_custom_strategy.py` for complete examples. All strategies must:

1. Inherit from `BaseStrategy`
2. Implement three methods:
   - `get_name()` - Return strategy name
   - `get_description()` - Return strategy description
   - `evaluate(symbol, available_cash, market_data_fetcher)` - Return `TradeSignal`

### Strategy Interface Contract
- Strategies receive `MarketDataFetcher` to query historical data
- Must handle data errors gracefully (return `TradeSignal(should_trade=False)`)
- Should deduct allocated cash from available_cash when returning positive signals
- Take profit and stop loss prices are optional but recommended for risk management

### Injecting a Custom Strategy
In `src/bots/day_bot.py` main() function (around line 192), replace:
```python
strategy = SimpleGapDownStrategy(...)
```
with:
```python
strategy = YourCustomStrategy(logger=logger, ...)
```

## Key Concepts

### Bracket Orders
The bot primarily uses bracket orders which include:
- Entry order (market order to enter position)
- Take profit limit order (exit at profit target)
- Stop loss order (exit to limit losses)

See `src/utils/order_manager.py:BracketOrderParams` for the data structure.

### Gap-Down Strategy Logic
The default `SimpleGapDownStrategy`:
1. Compares current open to previous close
2. If open < close (gap down), considers trading
3. Calculates average candle size over last 5 days
4. Sets TP = open + avg_candle, SL = open - avg_candle
5. Allocates 5% of available cash per trade

### Cash Management
The bot tracks remaining cash across the watchlist evaluation loop (`evaluate_watchlist` in `base_strategy.py`). Each positive signal deducts its notional amount from available cash to prevent over-allocation.

## Important Files to Read First

When modifying the system, read these in order:
1. `src/strategies/base_strategy.py` - Understand the strategy interface and `TradeSignal`
2. `src/bots/day_bot.py` - See how the bot orchestrates everything
3. `src/utils/market_data.py` - Understand data fetching capabilities
4. `src/strategies/simple_strategy.py` - See a complete strategy implementation

## Architectural Diagrams

The `ARCHITECTURE.md` file contains detailed Mermaid diagrams showing:
- System component relationships
- Workflow sequence diagrams
- Strategy pattern flow
- Class diagrams with all methods
- Data flow for gap-down strategy
- AWS Lambda deployment architecture

Refer to these diagrams when planning significant changes to understand the full system.

## Testing & Safety

- Always test new strategies in `--dry-run` mode first
- The bot defaults to paper trading (verify `PAPER_TRADING=true` in `.env`)
- Logs are written to `day_bot.log` for audit trail
- Each symbol evaluation is try-catch wrapped to prevent one failure from stopping the entire run

## AWS Lambda Deployment

The bot can be deployed to AWS Lambda for scheduled execution using AWS CDK:
1. All source code is in `src/` directory (including the Lambda handler at `src/lambda/handler.py`)
2. CDK automatically bundles dependencies from `src/requirements.txt` using Docker
3. EventBridge rules trigger execution at 9:30 AM ET on weekdays
4. See `aws_infrastructure/DEPLOYMENT.md` for complete deployment instructions

## Code Style Notes

- The codebase uses type hints extensively
- Dataclasses are used for structured data (`TradeSignal`, `BracketOrderParams`)
- Dependency injection throughout (strategy, config, logger passed to constructors)
- Single Responsibility Principle: each utility class has one clear purpose
- Facade pattern: `AlpacaClientWrapper` simplifies complex Alpaca API interaction
