#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_infrastructure.aws_infrastructure_stack import AwsInfrastructureStack


app = cdk.App()
AwsInfrastructureStack(app, "AwsInfrastructureStack",
    env=cdk.Environment(account=os.getenv('AWS_ACCOUNT'), region=os.getenv('AWS_REGION')),
    )

app.synth()
