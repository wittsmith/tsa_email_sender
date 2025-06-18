#!/bin/bash

# Simple AWS Lambda Deployment Script for TSA Report
# Uses Lambda layers for heavy dependencies

set -e

# Configuration
FUNCTION_NAME="tsa-daily-report"
AWS_REGION="us-east-1"
RUNTIME="python3.9"
HANDLER="lambda_tsa_report_simple.lambda_handler"
TIMEOUT=900  # 15 minutes
MEMORY_SIZE=1024

echo "🚀 Simple Lambda Deployment for TSA Report..."

# Check prerequisites
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install it first."
    exit 1
fi

# Check if environment variables are set
if [ -z "$SENDER_EMAIL" ] || [ -z "$APP_PASSWORD" ] || [ -z "$RECIPIENT_EMAIL" ]; then
    echo "❌ Environment variables not set. Please run: source setup_aws_env.sh"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Create lightweight deployment package (just your code)
echo "📦 Creating lightweight deployment package..."

# Create temporary directory
TEMP_DIR=$(mktemp -d)
echo "Using temp directory: $TEMP_DIR"

# Copy only your code files
cp lambda_tsa_report_simple.py "$TEMP_DIR/"
cp tsa_scraper.py "$TEMP_DIR/"

# Create ZIP file
cd "$TEMP_DIR"
zip -r tsa-lambda-deployment.zip .
cd - > /dev/null

# Move ZIP file to current directory
mv "$TEMP_DIR/tsa-lambda-deployment.zip" .

echo "✅ Lightweight deployment package created: tsa-lambda-deployment.zip"
echo "📏 Package size: $(du -h tsa-lambda-deployment.zip | cut -f1)"

# Create Lambda function
echo "🏗️ Creating Lambda function..."

# Check if function exists
if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$AWS_REGION" >/dev/null 2>&1; then
    echo "Updating existing function..."
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file fileb://tsa-lambda-deployment.zip \
        --region "$AWS_REGION"
    
    aws lambda update-function-configuration \
        --function-name "$FUNCTION_NAME" \
        --timeout "$TIMEOUT" \
        --memory-size "$MEMORY_SIZE" \
        --environment "Variables={SENDER_EMAIL=$SENDER_EMAIL,APP_PASSWORD=$APP_PASSWORD,RECIPIENT_EMAIL=$RECIPIENT_EMAIL}" \
        --region "$AWS_REGION"
else
    echo "Creating new function..."
    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --runtime "$RUNTIME" \
        --role "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/lambda-execution-role" \
        --handler "$HANDLER" \
        --zip-file fileb://tsa-lambda-deployment.zip \
        --timeout "$TIMEOUT" \
        --memory-size "$MEMORY_SIZE" \
        --environment "Variables={SENDER_EMAIL=$SENDER_EMAIL,APP_PASSWORD=$APP_PASSWORD,RECIPIENT_EMAIL=$RECIPIENT_EMAIL}" \
        --region "$AWS_REGION"
fi

# Create EventBridge rule for scheduling (weekdays at 9:05 AM ET)
echo "⏰ Setting up EventBridge schedule..."

RULE_NAME="tsa-daily-report-schedule"
TARGET_NAME="tsa-daily-report-target"

# Create EventBridge rule
aws events put-rule \
    --name "$RULE_NAME" \
    --schedule-expression "cron(5 9 ? * MON-FRI *)" \
    --description "Trigger TSA daily report every weekday at 9:05 AM ET" \
    --region "$AWS_REGION" 2>/dev/null || true

# Add Lambda permission for EventBridge
aws lambda add-permission \
    --function-name "$FUNCTION_NAME" \
    --statement-id "EventBridgeInvoke" \
    --action "lambda:InvokeFunction" \
    --principal "events.amazonaws.com" \
    --source-arn "arn:aws:events:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):rule/$RULE_NAME" \
    --region "$AWS_REGION" 2>/dev/null || true

# Create EventBridge target
aws events put-targets \
    --rule "$RULE_NAME" \
    --targets "Id=$TARGET_NAME,Arn=arn:aws:lambda:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):function:$FUNCTION_NAME" \
    --region "$AWS_REGION" 2>/dev/null || true

# Clean up
rm -rf "$TEMP_DIR"
rm -f tsa-lambda-deployment.zip

echo "✅ Lambda deployment complete!"
echo ""
echo "📊 Monitor your function:"
echo "   Lambda Console: https://console.aws.amazon.com/lambda/home?region=$AWS_REGION#/functions/$FUNCTION_NAME"
echo "   CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/home?region=$AWS_REGION#logsV2:log-groups/log-group/%2Faws%2Flambda%2F$FUNCTION_NAME"
echo ""
echo "💰 Estimated cost: ~$1-2/month"
echo ""
echo "🧪 Test the function:"
echo "   aws lambda invoke --function-name $FUNCTION_NAME --region $AWS_REGION response.json"
echo ""
echo "🛑 To disable the schedule:"
echo "   aws events disable-rule --name $RULE_NAME --region $AWS_REGION"
echo ""
echo "▶️  To enable the schedule:"
echo "   aws events enable-rule --name $RULE_NAME --region $AWS_REGION"
echo ""
echo "⚠️  Note: This deployment uses Lambda's built-in libraries. If you need additional packages,"
echo "   you'll need to create Lambda layers or use a container image." 