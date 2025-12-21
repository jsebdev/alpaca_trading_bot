# Trading Bot Architecture

## System Overview

```mermaid
graph TB
    subgraph "Entry Point"
        CLI[day_bot.py CLI]
    end

    subgraph "Configuration Layer"
        Config[Config<br/>- Load .env<br/>- Validate settings<br/>- Watchlist]
        Logger[Logger<br/>- Console output<br/>- File logging]
    end

    subgraph "Core Bot"
        Bot[DayTradingBot<br/>- Orchestrates workflow<br/>- Manages execution]
    end

    subgraph "Strategy Layer"
        BaseStrategy[BaseStrategy<br/>Abstract Interface]
        SimpleStrategy[SimpleGapDownStrategy<br/>- Gap down detection<br/>- 5% cash allocation<br/>- TP/SL calculation]
        CustomStrategy[Custom Strategies<br/>Easily injectable]

        BaseStrategy -.-> SimpleStrategy
        BaseStrategy -.-> CustomStrategy
    end

    subgraph "Alpaca Integration"
        AlpacaWrapper[AlpacaClientWrapper<br/>- TradingClient<br/>- DataClient<br/>- Account management]
    end

    subgraph "Utilities"
        MarketData[MarketDataFetcher<br/>- Historical bars<br/>- Gap analysis<br/>- Candle size calculation]
        OrderMgr[OrderManager<br/>- Bracket orders<br/>- Market orders<br/>- Order tracking]
    end

    subgraph "External Services"
        Alpaca[(Alpaca API<br/>- Trading<br/>- Market Data)]
    end

    CLI --> Config
    CLI --> Logger
    CLI --> Bot

    Bot --> SimpleStrategy
    Bot --> AlpacaWrapper
    Bot --> MarketData
    Bot --> OrderMgr

    SimpleStrategy --> MarketData

    AlpacaWrapper --> Alpaca
    MarketData --> Alpaca
    OrderMgr --> Alpaca

    Config -.provides config.-> Bot
    Logger -.logs to.-> Bot
    Logger -.logs to.-> SimpleStrategy
    Logger -.logs to.-> AlpacaWrapper
    Logger -.logs to.-> MarketData
    Logger -.logs to.-> OrderMgr
```

## Workflow Sequence

```mermaid
sequenceDiagram
    participant User
    participant CLI as day_bot.py
    participant Bot as DayTradingBot
    participant Alpaca as AlpacaClientWrapper
    participant Strategy as SimpleGapDownStrategy
    participant Market as MarketDataFetcher
    participant Orders as OrderManager
    participant API as Alpaca API

    User->>CLI: python day_bot.py --dry-run
    CLI->>CLI: Load config from .env
    CLI->>Strategy: Initialize strategy
    CLI->>Bot: Initialize bot with strategy

    Bot->>Alpaca: get_account_summary()
    Alpaca->>API: GET /v2/account
    API-->>Alpaca: Account data
    Alpaca-->>Bot: buying_power: $200,000

    Bot->>Bot: Check if tradeable

    loop For each symbol in watchlist
        Bot->>Strategy: evaluate(symbol, cash, market_data_fetcher)

        Strategy->>Market: get_gap_info(symbol)
        Market->>API: GET /v2/stocks/bars
        API-->>Market: Historical bars
        Market-->>Strategy: prev_close, current_open, gap%

        alt Gap down detected
            Strategy->>Market: calculate_average_candle_size(symbol, 5 days)
            Market->>API: GET /v2/stocks/bars
            API-->>Market: 5 days of bars
            Market-->>Strategy: avg_candle_size

            Strategy->>Strategy: Calculate TP/SL prices
            Strategy-->>Bot: TradeSignal(should_trade=True, notional, TP, SL)

            Bot->>Orders: place_bracket_order(symbol, notional, TP, SL)

            alt Not dry-run
                Orders->>API: POST /v2/orders (bracket)
                API-->>Orders: Order confirmation
            else Dry-run mode
                Orders->>Orders: Log order (not placed)
            end

        else No gap down
            Strategy-->>Bot: TradeSignal(should_trade=False, reason)
        end
    end

    Bot->>Bot: Summarize results
    Bot-->>User: Signals: 2 trades, 3 skips
```

## Component Details

```mermaid
classDiagram
    class Config {
        +alpaca_api_key: str
        +alpaca_api_secret: str
        +paper_trading: bool
        +watchlist: List[str]
        +cash_allocation_percent: float
        +lookback_days: int
        +from_env() Config
        +validate() void
    }

    class AlpacaClientWrapper {
        +trading_client: TradingClient
        +data_client: StockHistoricalDataClient
        +get_account() TradeAccount
        +get_buying_power() float
        +is_tradeable() bool
        +get_account_summary() Dict
    }

    class MarketDataFetcher {
        +get_historical_bars(symbol, days) List[CandleData]
        +calculate_average_candle_size(symbol, days) float
        +get_previous_close(symbol) float
        +get_current_price(symbol) float
        +get_gap_info(symbol) Tuple
    }

    class OrderManager {
        +place_bracket_order(params, dry_run) Order
        +place_market_order(symbol, notional) Order
        +get_order_status(order_id) Order
        +cancel_order(order_id) bool
    }

    class BaseStrategy {
        <<abstract>>
        +evaluate(symbol, cash, market_data_fetcher) TradeSignal*
        +get_name() str*
        +get_description() str*
        +evaluate_watchlist(symbols, cash) List[TradeSignal]
    }

    class SimpleGapDownStrategy {
        +cash_allocation_percent: float
        +lookback_days: int
        +evaluate(symbol, cash, market_data_fetcher) TradeSignal
        +get_name() str
        +get_description() str
    }

    class TradeSignal {
        +symbol: str
        +should_trade: bool
        +notional: float
        +take_profit_price: float
        +stop_loss_price: float
        +reason: str
    }

    class DayTradingBot {
        +config: Config
        +strategy: BaseStrategy
        +alpaca_client: AlpacaClientWrapper
        +market_data_fetcher: MarketDataFetcher
        +order_manager: OrderManager
        +run() List[TradeSignal]
    }

    BaseStrategy <|-- SimpleGapDownStrategy
    DayTradingBot o-- Config
    DayTradingBot o-- BaseStrategy
    DayTradingBot o-- AlpacaClientWrapper
    DayTradingBot o-- MarketDataFetcher
    DayTradingBot o-- OrderManager
    BaseStrategy ..> TradeSignal : creates
    BaseStrategy ..> MarketDataFetcher : uses
```

## Strategy Pattern Flow

```mermaid
flowchart TD
    Start([Bot Starts]) --> LoadConfig[Load Configuration]
    LoadConfig --> InitStrategy{Choose Strategy}

    InitStrategy -->|Default| GapDown[SimpleGapDownStrategy]
    InitStrategy -->|Custom| Custom[Custom Strategy]

    GapDown --> Inject[Inject into DayTradingBot]
    Custom --> Inject

    Inject --> GetCash[Get Available Cash]
    GetCash --> Loop{For Each Symbol}

    Loop -->|Next Symbol| Evaluate[strategy.evaluate<br/>symbol, cash, market_data]

    Evaluate --> StrategyLogic[Strategy-Specific Logic:<br/>- Fetch market data<br/>- Apply criteria<br/>- Calculate TP/SL]

    StrategyLogic --> Decision{Should Trade?}

    Decision -->|Yes| CreateSignal[TradeSignal<br/>should_trade=True<br/>+ notional, TP, SL]
    Decision -->|No| SkipSignal[TradeSignal<br/>should_trade=False<br/>+ reason]

    CreateSignal --> PlaceOrder[Place Bracket Order]
    SkipSignal --> UpdateCash
    PlaceOrder --> UpdateCash[Update Remaining Cash]

    UpdateCash --> Loop
    Loop -->|Done| Summary[Generate Summary]
    Summary --> End([Bot Complete])
```

## Data Flow: Gap-Down Strategy

```mermaid
flowchart LR
    subgraph Input
        A1[Symbol: AAPL]
        A2[Available Cash: $200,000]
    end

    subgraph "Strategy Evaluation"
        B1[Fetch Historical Bars<br/>Last 2 days]
        B2{Open < Prev Close?}
        B3[Calculate 5-Day<br/>Avg Candle Size]
        B4[Calculate Position<br/>5% of Cash = $10,000]
        B5[Calculate TP/SL<br/>TP = open + avg<br/>SL = open - avg]
    end

    subgraph Output
        C1[TradeSignal<br/>Symbol: AAPL<br/>Notional: $10,000<br/>TP: $277.53<br/>SL: $266.76]
    end

    subgraph "Order Execution"
        D1[Bracket Order<br/>Entry: Market<br/>Take Profit: Limit<br/>Stop Loss: Stop]
    end

    A1 --> B1
    A2 --> B4
    B1 --> B2
    B2 -->|Yes, Gap Down| B3
    B2 -->|No| Skip[Skip Trade]
    B3 --> B5
    B4 --> B5
    B5 --> C1
    C1 --> D1
```

## File Structure

```
trading-bot/
│
├── bots/
│   ├── __init__.py
│   └── day_bot.py                    # Main orchestration & CLI
│
├── strategies/
│   ├── __init__.py
│   ├── base_strategy.py              # Abstract strategy interface
│   └── simple_strategy.py            # Gap-down implementation
│
├── utils/
│   ├── __init__.py
│   ├── config.py                     # Configuration management
│   ├── logger.py                     # Logging setup
│   ├── alpaca_client.py              # API client wrapper
│   ├── market_data.py                # Market data utilities
│   └── order_manager.py              # Order placement
│
├── example_custom_strategy.py        # Strategy examples
├── .env                              # API credentials
└── day_bot.log                       # Execution logs
```

## Key Design Patterns

### 1. Strategy Pattern
- **Intent**: Define a family of algorithms, encapsulate each one, and make them interchangeable
- **Implementation**: `BaseStrategy` abstract class, multiple concrete implementations
- **Benefits**: Easy to add new strategies without modifying bot code

### 2. Dependency Injection
- **Intent**: Inject dependencies rather than hard-coding them
- **Implementation**: Bot receives strategy, config, and utilities via constructor
- **Benefits**: Testable, flexible, maintainable

### 3. Facade Pattern
- **Intent**: Provide a simplified interface to complex subsystems
- **Implementation**: `AlpacaClientWrapper` simplifies Alpaca API interaction
- **Benefits**: Easier to use, centralized error handling

### 4. Single Responsibility Principle
- Each class has one reason to change:
  - `Config`: Configuration management only
  - `MarketDataFetcher`: Market data operations only
  - `OrderManager`: Order operations only
  - `Strategy`: Trading logic only
  - `Bot`: Orchestration only

## Deployment Architecture (AWS Lambda)

```mermaid
graph TB
    subgraph "AWS Cloud"
        EB[EventBridge<br/>Rule: 9:30 AM ET]
        Lambda[Lambda Function<br/>day_bot.py<br/>Timeout: 5 min]
        CW[CloudWatch Logs<br/>Execution logs]
        Secrets[Secrets Manager<br/>Optional: API keys]
    end

    subgraph "External"
        Alpaca[Alpaca API<br/>Trading & Data]
    end

    EB -->|Trigger| Lambda
    Lambda -->|Log| CW
    Lambda -.->|Get secrets| Secrets
    Lambda <-->|API calls| Alpaca
```

### Lambda Deployment Steps
1. Package code + dependencies
2. Create Lambda function
3. Set environment variables (API keys)
4. Create EventBridge rule (cron: 9:30 AM ET)
5. Monitor via CloudWatch Logs

### Lambda Handler
```python
def lambda_handler(event, context):
    from bots.day_bot import main
    signals = main(dry_run=False)
    return {
        'statusCode': 200,
        'body': f'{len([s for s in signals if s.should_trade])} trades executed'
    }
```
