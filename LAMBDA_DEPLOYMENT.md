# AWS Lambda Deployment (No Docker Required)

## Overview
This guide deploys your TSA report to AWS Lambda, which is **much simpler and cheaper** than ECS. No Docker required!

## Benefits
- ✅ **No Docker required** - Just Python and AWS CLI
- ✅ **Much cheaper** - ~$1-2/month vs $10-15/month
- ✅ **Simpler deployment** - Just ZIP and upload
- ✅ **Automatic scaling** - AWS handles everything
- ✅ **Pay per execution** - Only pay when it runs

## Prerequisites

### 1. Install Required Tools
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Verify installation
aws --version
```

### 2. Configure AWS CLI
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter your default region (e.g., us-east-1)
# Enter your output format (json)
```

## Quick Deployment (5 minutes)

### Step 1: Set up environment variables
```bash
source setup_aws_env.sh
```

### Step 2: Set up IAM role
```bash
./setup_lambda_role.sh
```

### Step 3: Deploy to Lambda
```bash
./deploy_lambda.sh
```

## What You Get

✅ **Scheduled Execution** - Runs every weekday at 9:05 AM ET  
✅ **Automatic Email Reports** - Same functionality as before  
✅ **CloudWatch Logs** - Monitor execution and errors  
✅ **Cost Effective** - ~$1-2/month total  
✅ **No Server Management** - AWS handles everything  

## Monitoring

### View Logs
```bash
# View recent logs
aws logs tail /aws/lambda/tsa-daily-report --follow --region us-east-1
```

### Monitor Function
- **Lambda Console**: https://console.aws.amazon.com/lambda/
- **CloudWatch**: https://console.aws.amazon.com/cloudwatch/

## Cost Breakdown

- **Lambda**: ~$0.50/month (15 minutes daily execution)
- **EventBridge**: ~$0.50/month (scheduled triggers)
- **CloudWatch Logs**: ~$0.10/month
- **Total**: ~$1-2/month

## Management Commands

### Test the function manually
```bash
aws lambda invoke --function-name tsa-daily-report --region us-east-1 response.json
```

### Disable the schedule
```bash
aws events disable-rule --name tsa-daily-report-schedule --region us-east-1
```

### Enable the schedule
```bash
aws events enable-rule --name tsa-daily-report-schedule --region us-east-1
```

### Update the function
```bash
./deploy_lambda.sh
```

## Troubleshooting

### Common Issues

**"Role not found"**
- Run `./setup_lambda_role.sh` first

**"Timeout"**
- Function has 15-minute timeout (should be enough)

**"Memory limit"**
- Function has 1GB memory (should be enough)

**"Import error"**
- Check that all dependencies are in requirements.txt

### Useful Commands

```bash
# Check function status
aws lambda get-function --function-name tsa-daily-report --region us-east-1

# View function configuration
aws lambda get-function-configuration --function-name tsa-daily-report --region us-east-1

# Check EventBridge rule
aws events describe-rule --name tsa-daily-report-schedule --region us-east-1
```

## Comparison: Lambda vs ECS

| Feature | Lambda | ECS |
|---------|--------|-----|
| **Cost** | ~$1-2/month | ~$10-15/month |
| **Complexity** | Simple | Complex |
| **Docker** | Not required | Required |
| **Timeout** | 15 minutes | Unlimited |
| **Memory** | 10GB max | Configurable |
| **Cold Start** | Yes | No |
| **Scaling** | Automatic | Manual |

**Recommendation**: Use Lambda for this use case - it's simpler, cheaper, and perfect for scheduled tasks! 