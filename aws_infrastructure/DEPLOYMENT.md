# AWS Lambda Deployment Guide

This guide walks you through deploying the Alpaca trading bot to AWS Lambda with scheduled execution.

## Architecture Overview

- **Lambda Function**: Python 3.12 runtime hosting your trading bot
- **Lambda Layer**: Dependencies (alpaca-py, pandas, numpy, python-dotenv)
- **EventBridge Rules**: Triggers Lambda at 9:30 AM ET, Monday-Friday
- **CloudWatch Logs**: Automatic logging of all bot executions

## Prerequisites

### 1. Install CDK CLI

```bash
npm install -g aws-cdk
```

### 2. Configure AWS Credentials

```bash
aws configure
```

Or export environment variables:
```bash
export AWS_ACCESS_KEY_ID="your_aws_access_key"
export AWS_SECRET_ACCESS_KEY="your_aws_secret_key"
export AWS_DEFAULT_REGION="us-east-1"
```

### 3. Set Alpaca Credentials

```bash
export ALPACA_API_KEY="your_alpaca_key"
export ALPACA_API_SECRET="your_alpaca_secret"
```

### 4. Install Docker

Docker is required to build the Lambda layer with correct binary dependencies.

```bash
# Verify Docker is running
docker --version
```

### 5. Bootstrap CDK (First Time Only)

```bash
cd aws_infrastructure
cdk bootstrap aws://YOUR_ACCOUNT_ID/us-east-1
```

Replace `YOUR_ACCOUNT_ID` with your AWS account ID (can find with `aws sts get-caller-identity`).

## Build and Deploy

### Step 1: Build Lambda Layer

```bash
cd aws_infrastructure
./build_layer.sh
```

This creates `layers/python/lib/python3.12/site-packages/` with all dependencies (~150 MB).

**Expected output**:
```
Building Lambda Layer for trading bot dependencies...
Installing dependencies using Docker...
Lambda layer built successfully!
Total layer size: 150M
```

### Step 2: Prepare Bot Code

```bash
./prepare_lambda.sh
```

This copies `bots/`, `strategies/`, and `utils/` to `lambda/bot_package/`.

**Expected output**:
```
Preparing bot code for Lambda deployment...
Total Python files copied: 11
Bot package prepared successfully!
```

### Step 3: Synthesize CDK Stack

```bash
cdk synth
```

This generates CloudFormation template in `cdk.out/`.

### Step 4: Preview Changes

```bash
cdk diff
```

This shows what will be created/modified/deleted.

### Step 5: Deploy to AWS

```bash
cdk deploy
```

Or with auto-approval (for CI/CD):
```bash
cdk deploy --require-approval never
```

**Expected output**:
```
AwsInfrastructureStack

Outputs:
AwsInfrastructureStack.TradingBotFunctionName = AwsInfrastructureStack-AlpacaTradingBot...
AwsInfrastructureStack.TradingBotFunctionArn = arn:aws:lambda:us-east-1:...
AwsInfrastructureStack.LogGroup = /aws/lambda/AwsInfrastructureStack-AlpacaTradingBot...
```

## Testing

### Test Lambda Function Manually

```bash
# Get function name from deploy output
FUNCTION_NAME="AwsInfrastructureStack-AlpacaTradingBot..."

# Invoke with test payload
aws lambda invoke \
  --function-name $FUNCTION_NAME \
  --payload '{"dry_run": true, "watchlist": ["AAPL", "TSLA"]}' \
  --cli-binary-format raw-in-base64-out \
  response.json

# View response
cat response.json | jq .
```

**Expected response**:
```json
{
  "statusCode": 200,
  "body": {
    "execution_time": "2025-12-21T14:30:00Z",
    "dry_run": true,
    "signals": [...],
    "summary": {
      "total_symbols": 2,
      "trades": 1,
      "skips": 1
    }
  }
}
```

### View CloudWatch Logs

```bash
# Get log group from deploy output
LOG_GROUP="/aws/lambda/AwsInfrastructureStack-AlpacaTradingBot..."

# Tail logs in real-time
aws logs tail $LOG_GROUP --follow

# Or view recent logs
aws logs tail $LOG_GROUP --since 1h
```

### Test Scheduled Execution

The bot will automatically run at **9:30 AM ET every weekday**. Check CloudWatch Logs the day after deployment to verify.

## Configuration

### Environment Variables

All bot configuration is done via Lambda environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ALPACA_API_KEY` | Yes | - | Alpaca API key |
| `ALPACA_API_SECRET` | Yes | - | Alpaca API secret |
| `PAPER_TRADING` | No | `"true"` | Use paper trading account |
| `DRY_RUN` | No | `"true"` | Log signals without placing orders |
| `CASH_ALLOCATION_PERCENT` | No | `"0.05"` | Percentage of cash per trade (5%) |
| `LOOKBACK_DAYS` | No | `"5"` | Days of historical data to analyze |
| `WATCHLIST` | No | `"AAPL,MSFT,GOOGL,AMZN,TSLA"` | Comma-separated symbols |

### Update Environment Variables

**Option 1: AWS Console**
1. Navigate to Lambda → Functions → [Your Function]
2. Configuration → Environment variables → Edit
3. Update values and Save

**Option 2: AWS CLI**
```bash
aws lambda update-function-configuration \
  --function-name $FUNCTION_NAME \
  --environment "Variables={
    ALPACA_API_KEY=your_key,
    ALPACA_API_SECRET=your_secret,
    DRY_RUN=false,
    WATCHLIST=AAPL,NVDA,AMD,TSLA
  }"
```

**Option 3: Re-deploy with CDK**
```bash
# Update environment variables in your shell
export DRY_RUN="false"
export WATCHLIST="AAPL,NVDA,AMD"

# Re-deploy
cdk deploy
```

### Switch from Dry-Run to Live Trading

**⚠️ Warning**: Only do this after thoroughly testing in dry-run mode!

```bash
aws lambda update-function-configuration \
  --function-name $FUNCTION_NAME \
  --environment "Variables={...,DRY_RUN=false}"
```

## Monitoring

### CloudWatch Dashboard

View metrics in AWS Console:
- Navigate to CloudWatch → Dashboards
- Metrics → Lambda → By Function Name → [Your Function]

Key metrics:
- **Invocations**: Should be 1/day on weekdays
- **Errors**: Should be 0
- **Duration**: Typically 5-15 seconds
- **Throttles**: Should be 0

### CloudWatch Alarms (Optional)

Set up alerts for failures:

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name trading-bot-errors \
  --alarm-description "Alert on trading bot errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --dimensions Name=FunctionName,Value=$FUNCTION_NAME
```

## Scheduling

### Current Schedule

- **9:30 AM EST** (Nov-Mar): Monday-Friday
- **9:30 AM EDT** (Apr-Oct): Monday-Friday

The bot uses two EventBridge rules to handle timezone changes automatically.

### Modify Schedule

Edit `aws_infrastructure/aws_infrastructure/aws_infrastructure_stack.py`:

```python
# Example: Change to 10:00 AM ET
rule_est = events.Rule(
    self, "TradingBotScheduleEST",
    schedule=events.Schedule.cron(
        minute="0",   # Changed from 30
        hour="15",    # 10:00 AM EST = 15:00 UTC
        month="1,2,3,11,12",
        week_day="MON-FRI",
    ),
)
```

Then re-deploy:
```bash
cdk deploy
```

### Disable Scheduled Execution

```bash
# List rules
aws events list-rules --query 'Rules[?contains(Name, `TradingBot`)].Name'

# Disable rules
aws events disable-rule --name AwsInfrastructureStack-TradingBotScheduleEST...
aws events disable-rule --name AwsInfrastructureStack-TradingBotScheduleEDT...

# Re-enable later
aws events enable-rule --name AwsInfrastructureStack-TradingBotScheduleEST...
aws events enable-rule --name AwsInfrastructureStack-TradingBotScheduleEDT...
```

## Updating the Bot Code

When you modify the bot logic in `bots/`, `strategies/`, or `utils/`:

```bash
cd aws_infrastructure

# Re-prepare bot code
./prepare_lambda.sh

# Re-deploy (dependencies layer not rebuilt)
cdk deploy
```

This is fast (~30 seconds) because the Lambda layer doesn't need to be rebuilt.

## Cost Estimate

- **Lambda Function**: $0.00 (free tier: 1M requests/month)
- **Lambda Layer Storage**: ~$0.02/month
- **EventBridge**: $0.00 (free tier: 1M events/month)
- **CloudWatch Logs**: ~$0.03/month

**Total**: ~$0.05/month (essentially free)

## Troubleshooting

### Import Errors

```
ERROR: ModuleNotFoundError: No module named 'bots'
```

**Solution**: Run `./prepare_lambda.sh` to copy bot code.

### Missing Dependencies

```
ERROR: No module named 'alpaca'
```

**Solution**: Run `./build_layer.sh` to rebuild the Lambda layer.

### Alpaca API Errors

```
ERROR: API credentials invalid
```

**Solution**: Verify environment variables:
```bash
aws lambda get-function-configuration \
  --function-name $FUNCTION_NAME \
  --query 'Environment.Variables'
```

### Docker Not Available

If Docker is not available for building the layer, use pip with --platform:

```bash
mkdir -p layers/python/lib/python3.12/site-packages

pip install \
  alpaca-py==0.43.2 \
  python-dotenv==1.1.0 \
  pandas==2.3.3 \
  numpy==2.3.5 \
  sseclient-py==1.8.0 \
  websockets==15.0.1 \
  --platform manylinux2014_x86_64 \
  --only-binary=:all: \
  -t layers/python/lib/python3.12/site-packages
```

Note: This may not work for all dependencies (numpy, pandas) on some systems.

### Timeout Errors

```
ERROR: Task timed out after 60 seconds
```

**Solution**: Increase timeout in `aws_infrastructure_stack.py`:
```python
timeout=Duration.seconds(120),  # Increase from 60
```

## Cleanup

To remove all AWS resources:

```bash
cd aws_infrastructure
cdk destroy
```

This deletes:
- Lambda function
- Lambda layer
- EventBridge rules
- IAM roles

CloudWatch Logs are retained by default. To delete:
```bash
aws logs delete-log-group --log-group-name $LOG_GROUP
```

## Next Steps

1. **Test in dry-run mode** for a few days to ensure signals are reasonable
2. **Monitor CloudWatch Logs** to verify execution at 9:30 AM ET
3. **Review trade signals** before switching to live mode
4. **Set up CloudWatch Alarms** for error notifications
5. **Switch to live trading** when confident (update `DRY_RUN` to `false`)

## Support

For issues or questions:
- Check CloudWatch Logs for detailed error messages
- Review the CDK stack in AWS Console → CloudFormation
- Verify environment variables in Lambda console
- Test locally first: `python bots/day_bot.py --dry-run`
