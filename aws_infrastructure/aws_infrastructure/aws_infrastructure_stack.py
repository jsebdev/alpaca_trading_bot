import os
from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
)
from constructs import Construct


class TradingBotStack(Stack):
    """
    CDK Stack for Alpaca Trading Bot deployed to AWS Lambda.

    This stack creates:
    - Lambda Function with trading bot code (dependencies bundled automatically via Docker)
    - EventBridge Rules for scheduled execution
    - CloudWatch Logs integration
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Validate Alpaca credentials are provided
        alpaca_key = os.environ.get("ALPACA_API_KEY")
        alpaca_secret = os.environ.get("ALPACA_API_SECRET")

        if not alpaca_key or not alpaca_secret:
            raise ValueError(
                "ALPACA_API_KEY and ALPACA_API_SECRET environment variables must be set. "
                "Export them before running 'cdk deploy'."
            )

        # Define Lambda function with automatic dependency bundling
        trading_bot_function = _lambda.Function(
            self,
            "AlpacaTradingBot",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda.handler.lambda_handler",
            code=_lambda.Code.from_asset(
                "../src/",
                bundling={
                    "image": _lambda.Runtime.PYTHON_3_12.bundling_image,
                    "command": [
                        "bash", "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ],
                }
            ),
            architecture=_lambda.Architecture.ARM_64,  # Use ARM64 (Graviton2) - 20% cheaper and matches Mac builds
            timeout=Duration.seconds(60),
            memory_size=512,
            environment={
                # Alpaca Credentials
                "ALPACA_API_KEY": alpaca_key,
                "ALPACA_API_SECRET": alpaca_secret,
                "PAPER_TRADING": "true",
                # Trading Parameters
                "CASH_ALLOCATION_PERCENT": os.environ.get(
                    "CASH_ALLOCATION_PERCENT", "0.05"
                ),
                "LOOKBACK_DAYS": os.environ.get("LOOKBACK_DAYS", "5"),
                # Bot Control
                "DRY_RUN": os.environ.get("DRY_RUN", "true"),
                "WATCHLIST": os.environ.get(
                    "WATCHLIST", ""
                ),
            },
            description="Alpaca paper trading bot with gap-down strategy",
        )

        # Create EventBridge rule for scheduling (9:30 AM EST, Mon-Fri)
        # EST (winter): 9:30 AM EST = 14:30 UTC
        rule_est = events.Rule(
            self,
            "TradingBotScheduleEST",
            schedule=events.Schedule.cron(
                minute="30",
                hour="14",  # 9:30 AM EST = 14:30 UTC
                month="1,2,3,11,12",  # EST months (Nov-Mar)
                week_day="MON-FRI",
            ),
            description="Trigger trading bot at 9:30 AM EST (Nov-Mar)",
        )
        rule_est.add_target(targets.LambdaFunction(trading_bot_function))

        # Create EventBridge rule for scheduling (9:30 AM EDT, Mon-Fri)
        # EDT (summer): 9:30 AM EDT = 13:30 UTC
        rule_edt = events.Rule(
            self,
            "TradingBotScheduleEDT",
            schedule=events.Schedule.cron(
                minute="30",
                hour="13",  # 9:30 AM EDT = 13:30 UTC
                month="4-10",  # EDT months (Apr-Oct)
                week_day="MON-FRI",
            ),
            description="Trigger trading bot at 9:30 AM EDT (Apr-Oct)",
        )
        rule_edt.add_target(targets.LambdaFunction(trading_bot_function))

        # CloudFormation outputs
        CfnOutput(
            self,
            "TradingBotFunctionName",
            value=trading_bot_function.function_name,
            description="Lambda function name for the trading bot",
        )

        CfnOutput(
            self,
            "TradingBotFunctionArn",
            value=trading_bot_function.function_arn,
            description="Lambda function ARN",
        )

        CfnOutput(
            self,
            "LogGroup",
            value=f"/aws/lambda/{trading_bot_function.function_name}",
            description="CloudWatch Logs group name for viewing bot execution logs",
        )
