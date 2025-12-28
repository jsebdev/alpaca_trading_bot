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


class ToyStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        alpaca_key = os.environ.get("ALPACA_API_KEY")
        alpaca_secret = os.environ.get("ALPACA_API_SECRET")

        if not alpaca_key or not alpaca_secret:
            raise ValueError(
                "ALPACA_API_KEY and ALPACA_API_SECRET environment variables must be set. "
                "Export them before running 'cdk deploy'."
            )

        toy_lambda_function = _lambda.Function(
            self,
            "ToyLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda.toy_handler.toy_handler",
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
                    "WATCHLIST", "AAPL,MSFT,GOOGL,AMZN,TSLA"
                ),
                "TEST_VARIABLE": os.environ.get("TEST_VARIABLE", "paila"),
            },
            description="Alpaca paper trading bot with gap-down strategy",
        )

        # CloudFormation outputs
        CfnOutput(
            self,
            "ToyLambdaFunctionName",
            value=toy_lambda_function.function_name,
            description="Lambda function name",
        )

        CfnOutput(
            self,
            "ToyLambdaFunctionARN",
            value=toy_lambda_function.function_arn,
            description="Lambda function ARN",
        )

        CfnOutput(
            self,
            "LogGroup",
            value=f"/aws/lambda/{toy_lambda_function.function_name}",
            description="CloudWatch Log Group Name",
        )
