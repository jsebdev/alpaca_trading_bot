"""
AWS Lambda handler for Alpaca trading bot.

This handler wraps the day trading bot and provides Lambda-compatible
entry point with environment variable configuration.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import asdict


# Add bot_package to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import bot after path modification
from bots.day_bot import main as run_bot
from strategies.base_strategy import TradeSignal
from utils.setup_logging import setup_logging


setup_logging()
logger = logging.getLogger(__name__)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    execution_time = datetime.utcnow().isoformat() + "Z"

    logger.info("=" * 60)
    logger.info(f"Lambda execution started at {execution_time}")
    logger.info(f"Event: {json.dumps(event)}")
    logger.info("=" * 60)

    try:
        # Parse configuration from environment and event
        dry_run = _parse_dry_run(event)
        watchlist = _parse_watchlist(event)

        logger.info(f"Configuration: dry_run={dry_run}, watchlist={watchlist}")

        # Run the trading bot
        signals: List[TradeSignal] = run_bot(watchlist=watchlist, dry_run=dry_run)

        # Convert TradeSignal dataclasses to dicts
        signals_dict = [asdict(signal) for signal in signals]

        # Calculate summary
        trade_signals = [s for s in signals if s.should_trade]
        summary = {
            "total_symbols": len(signals),
            "trades": len(trade_signals),
            "skips": len(signals) - len(trade_signals),
        }

        logger.info(f"Execution completed: {summary}")
        logger.info("=" * 60 + "\n\n")

        response = {
            "statusCode": 200,
            "body": {
                "execution_time": execution_time,
                "dry_run": dry_run,
                "signals": signals_dict,
                "summary": summary,
            }
        }

    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}", exc_info=True)
        logger.error("=" * 60)

        response = {
            "statusCode": 500,
            "body": {
                "execution_time": execution_time,
                "error": str(e),
                "error_type": type(e).__name__,
            }
        }
    logger.info("final response:")
    logger.info(response)
    return response


def _parse_dry_run(event: Dict[str, Any]) -> bool:
    """
    Parse dry_run flag from event or environment.

    Event takes precedence over environment variable.
    """
    # Event takes precedence over environment
    if "dry_run" in event:
        return bool(event["dry_run"])
    return False

    # Fall back to environment variable
    return os.environ.get("DRY_RUN", "true").lower() == "true"


def _parse_watchlist(event: Dict[str, Any]) -> Optional[List[str]]:
    """
    Parse watchlist from event or environment.

    Event takes precedence. Returns None to use Config default.
    """
    # Event takes precedence
    if "watchlist" in event:
        watchlist = event["watchlist"]
        if isinstance(watchlist, list):
            return watchlist
        elif isinstance(watchlist, str):
            return [s.strip() for s in watchlist.split(",")]

    # Fall back to environment variable
    watchlist_env = os.environ.get("WATCHLIST", "")
    if watchlist_env:
        return [s.strip() for s in watchlist_env.split(",") if s.strip()]

    # Return None to use Config default
    return None

if __name__ == "__main__":
    # For local testing
    test_event = {
        "dry_run": False,
        "watchlist": ["AAPL"]
    }
    response = lambda_handler(test_event, None)
    logger.info('>>>>> handler.py:171 "response"')
    logger.info(response)
