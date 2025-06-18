# AWS ECS Deployment Guide

## Overview
This guide deploys your TSA report to AWS ECS Fargate, which will run 24/7 at minimal cost (~$10-15/month).

## Prerequisites

### 1. Install Required Tools
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Install Docker Desktop
# Download from https://www.docker.com/products/docker-desktop/

# Verify installations
aws --version
docker --version
```

### 2. Configure AWS CLI
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter your default region (e.g., us-east-1)
# Enter your output format (json)
```

## Quick Deployment (10 minutes)

### 1. Set Environment Variables
```bash
export SENDER_EMAIL="your_gmail@gmail.com"
export APP_PASSWORD="your_gmail_app_password"
export RECIPIENT_EMAIL="recipient@example.com"
```

### 2. Create Required AWS Resources

#### Create VPC and Subnet (if you don't have one):
```bash
# Create VPC
VPC_ID=$(aws ec2 create-vpc --cidr-block 10.0.0.0/16 --query 'Vpc.VpcId' --output text)
echo "VPC ID: $VPC_ID"

# Create subnet
SUBNET_ID=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.1.0/24 --query 'Subnet.SubnetId' --output text)
echo "Subnet ID: $SUBNET_ID"

# Create security group
SG_ID=$(aws ec2 create-security-group --group-name tsa-report-sg --description "TSA Report Security Group" --vpc-id $VPC_ID --query 'GroupId' --output text)
echo "Security Group ID: $SG_ID"

# Allow outbound traffic
aws ec2 authorize-security-group-egress --group-id $SG_ID --protocol -1 --port -1 --cidr 0.0.0.0/0
```

#### Create ECS Task Execution Role:
```bash
# Create role
aws iam create-role --role-name ecsTaskExecutionRole --assume-role-policy-document '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}'

# Attach required policies
aws iam attach-role-policy --role-name ecsTaskExecutionRole --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
```

### 3. Update Deployment Script
Edit `aws-deploy.sh` and replace the placeholder subnet and security group IDs:
```bash
# Find this line in aws-deploy.sh:
--network-configuration "awsvpcConfiguration={subnets=[subnet-12345678],securityGroups=[sg-12345678],assignPublicIp=ENABLED}" \

# Replace with your actual IDs:
--network-configuration "awsvpcConfiguration={subnets=[$SUBNET_ID],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
```

### 4. Deploy
```bash
chmod +x aws-deploy.sh
./aws-deploy.sh
```

## What You Get

✅ **24/7 Operation** - Runs continuously on AWS servers  
✅ **Automatic Restarts** - ECS restarts if the script crashes  
✅ **Cost Effective** - ~$10-15/month for Fargate  
✅ **Scalable** - Can easily scale up if needed  
✅ **Monitored** - CloudWatch logs and metrics  
✅ **Secure** - Runs in isolated containers  

## Monitoring

### View Logs
```bash
# Get log group name
aws logs describe-log-groups --log-group-name-prefix "/ecs/tsa-passenger-report"

# View recent logs
aws logs tail /ecs/tsa-passenger-report --follow
```

### Monitor Service
- **ECS Console**: https://console.aws.amazon.com/ecs/
- **CloudWatch**: https://console.aws.amazon.com/cloudwatch/

## Cost Breakdown

- **ECS Fargate**: ~$10-15/month (256 CPU units, 512MB RAM)
- **ECR**: ~$0.10/month (image storage)
- **CloudWatch Logs**: ~$0.50/month
- **Total**: ~$10-16/month

## Troubleshooting

### Common Issues

**"No space left on device"**
- Increase memory in task definition (512MB → 1024MB)

**"Permission denied"**
- Check IAM roles and policies
- Ensure ecsTaskExecutionRole exists

**"Container failed to start"**
- Check CloudWatch logs
- Verify environment variables are set

**"Network timeout"**
- Check security group rules
- Ensure subnet has internet access

### Useful Commands

```bash
# Check service status
aws ecs describe-services --cluster tsa-report-cluster --services tsa-report-service

# View task logs
aws logs tail /ecs/tsa-passenger-report --follow

# Stop service
aws ecs update-service --cluster tsa-report-cluster --service tsa-report-service --desired-count 0

# Start service
aws ecs update-service --cluster tsa-report-cluster --service tsa-report-service --desired-count 1
```

## Alternative: AWS Lambda (Even Cheaper)

If you want to save money, consider AWS Lambda with EventBridge:
- **Cost**: ~$1-2/month
- **Limitations**: 15-minute timeout, no persistent storage
- **Setup**: More complex but very cost-effective

Would you like me to create a Lambda version as well? 