#!/usr/bin/env python3
import os
from dotenv import load_dotenv

from aws_infrastructure.toy_stack import ToyStack
load_dotenv()

import aws_cdk as cdk

from aws_infrastructure.aws_infrastructure_stack import TradingBotStack


app = cdk.App()
TradingBotStack(app, "TradingBotStack",
    env=cdk.Environment(account=os.getenv('AWS_ACCOUNT'), region=os.getenv('AWS_REGION')),
    )

ToyStack(app, "ToyStack",
    env=cdk.Environment(account=os.getenv('AWS_ACCOUNT'), region=os.getenv('AWS_REGION')),
    )

app.synth()
