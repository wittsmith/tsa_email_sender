#!/bin/bash

# Simple AWS ECS Deployment Script for TSA Report
# This script automatically sets up everything needed to run your TSA scheduler on AWS

set -e

# Configuration
PROJECT_NAME="tsa-passenger-report"
AWS_REGION="us-east-1"
ECR_REPOSITORY_NAME="tsa-passenger-report"
CLUSTER_NAME="tsa-report-cluster"
SERVICE_NAME="tsa-report-service"
TASK_DEFINITION_NAME="tsa-report-task"

echo "🚀 Simple AWS Deployment for TSA Passenger Report..."

# Check prerequisites
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install it first."
    exit 1
fi

# Check if environment variables are set
if [ -z "$SENDER_EMAIL" ] || [ -z "$APP_PASSWORD" ] || [ -z "$RECIPIENT_EMAIL" ]; then
    echo "❌ Environment variables not set. Please run: source setup_aws_env.sh"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}"

echo "🏗️ Setting up AWS infrastructure..."

# Create VPC and networking (if not exists)
echo "Creating VPC and networking..."
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=tsa-report-vpc" --query 'Vpcs[0].VpcId' --output text 2>/dev/null || echo "none")

if [ "$VPC_ID" = "none" ] || [ "$VPC_ID" = "None" ]; then
    echo "Creating new VPC..."
    VPC_ID=$(aws ec2 create-vpc --cidr-block 10.0.0.0/16 --query 'Vpc.VpcId' --output text)
    aws ec2 create-tags --resources $VPC_ID --tags Key=Name,Value=tsa-report-vpc
    
    # Create internet gateway
    IGW_ID=$(aws ec2 create-internet-gateway --query 'InternetGateway.InternetGatewayId' --output text)
    aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID
    
    # Create route table
    ROUTE_TABLE_ID=$(aws ec2 create-route-table --vpc-id $VPC_ID --query 'RouteTable.RouteTableId' --output text)
    aws ec2 create-route --route-table-id $ROUTE_TABLE_ID --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID
fi

# Create subnet (if not exists)
SUBNET_ID=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=tsa-report-subnet" --query 'Subnets[0].SubnetId' --output text 2>/dev/null || echo "none")

if [ "$SUBNET_ID" = "none" ] || [ "$SUBNET_ID" = "None" ]; then
    echo "Creating subnet..."
    SUBNET_ID=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.1.0/24 --query 'Subnet.SubnetId' --output text)
    aws ec2 create-tags --resources $SUBNET_ID --tags Key=Name,Value=tsa-report-subnet
    aws ec2 associate-route-table --subnet-id $SUBNET_ID --route-table-id $ROUTE_TABLE_ID
fi

# Create security group (if not exists)
SG_ID=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=tsa-report-sg" --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null || echo "none")

if [ "$SG_ID" = "none" ] || [ "$SG_ID" = "None" ]; then
    echo "Creating security group..."
    SG_ID=$(aws ec2 create-security-group --group-name tsa-report-sg --description "TSA Report Security Group" --vpc-id $VPC_ID --query 'GroupId' --output text)
    aws ec2 authorize-security-group-egress --group-id $SG_ID --protocol -1 --port -1 --cidr 0.0.0.0/0
else
    echo "Security group already exists, ensuring outbound rule..."
    # Try to add outbound rule, ignore if it already exists
    aws ec2 authorize-security-group-egress --group-id $SG_ID --protocol -1 --port -1 --cidr 0.0.0.0/0 2>/dev/null || true
fi

echo "✅ Infrastructure ready: VPC=$VPC_ID, Subnet=$SUBNET_ID, SG=$SG_ID"

# Create ECS task execution role (if not exists)
echo "Setting up IAM roles..."
aws iam get-role --role-name ecsTaskExecutionRole 2>/dev/null || {
    echo "Creating ECS task execution role..."
    aws iam create-role --role-name ecsTaskExecutionRole --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Principal": {"Service": "ecs-tasks.amazonaws.com"}, "Action": "sts:AssumeRole"}]
    }'
    aws iam attach-role-policy --role-name ecsTaskExecutionRole --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
}

echo "📦 Building and pushing Docker image..."

# Build Docker image
docker build -t ${ECR_REPOSITORY_NAME} .

# Login to ECR
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_URI}

# Create ECR repository if it doesn't exist
aws ecr describe-repositories --repository-names ${ECR_REPOSITORY_NAME} --region ${AWS_REGION} 2>/dev/null || \
aws ecr create-repository --repository-name ${ECR_REPOSITORY_NAME} --region ${AWS_REGION}

# Tag and push image
docker tag ${ECR_REPOSITORY_NAME}:latest ${ECR_URI}:latest
docker push ${ECR_URI}:latest

echo "🏗️ Creating ECS resources..."

# Create ECS cluster if it doesn't exist
aws ecs describe-clusters --clusters ${CLUSTER_NAME} --region ${AWS_REGION} 2>/dev/null || \
aws ecs create-cluster --cluster-name ${CLUSTER_NAME} --region ${AWS_REGION}

# Create CloudWatch log group
aws logs create-log-group --log-group-name "/ecs/${PROJECT_NAME}" --region ${AWS_REGION} 2>/dev/null || true

# Create task definition
echo "Creating task definition..."
cat > task-definition.json << EOF
{
    "family": "${TASK_DEFINITION_NAME}",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "256",
    "memory": "512",
    "executionRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/ecsTaskExecutionRole",
    "containerDefinitions": [
        {
            "name": "${PROJECT_NAME}",
            "image": "${ECR_URI}:latest",
            "essential": true,
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/${PROJECT_NAME}",
                    "awslogs-region": "${AWS_REGION}",
                    "awslogs-stream-prefix": "ecs"
                }
            },
            "environment": [
                {"name": "SENDER_EMAIL", "value": "${SENDER_EMAIL}"},
                {"name": "APP_PASSWORD", "value": "${APP_PASSWORD}"},
                {"name": "RECIPIENT_EMAIL", "value": "${RECIPIENT_EMAIL}"}
            ]
        }
    ]
}
EOF

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json --region ${AWS_REGION}

# Create or update ECS service
echo "Creating ECS service..."
aws ecs create-service \
    --cluster ${CLUSTER_NAME} \
    --service-name ${SERVICE_NAME} \
    --task-definition ${TASK_DEFINITION_NAME} \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[${SUBNET_ID}],securityGroups=[${SG_ID}],assignPublicIp=ENABLED}" \
    --region ${AWS_REGION} 2>/dev/null || \
aws ecs update-service \
    --cluster ${CLUSTER_NAME} \
    --service ${SERVICE_NAME} \
    --task-definition ${TASK_DEFINITION_NAME} \
    --region ${AWS_REGION}

# Clean up
rm -f task-definition.json

echo "✅ Deployment complete!"
echo ""
echo "📊 Monitor your service:"
echo "   ECS Console: https://console.aws.amazon.com/ecs/home?region=${AWS_REGION}#/clusters/${CLUSTER_NAME}/services/${SERVICE_NAME}"
echo "   CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/home?region=${AWS_REGION}#logsV2:log-groups/log-group/%2Fecs%2F${PROJECT_NAME}"
echo ""
echo "💰 Estimated cost: ~$10-15/month"
echo ""
echo "🛑 To stop the service:"
echo "   aws ecs update-service --cluster ${CLUSTER_NAME} --service ${SERVICE_NAME} --desired-count 0 --region ${AWS_REGION}"
echo ""
echo "▶️  To start the service:"
echo "   aws ecs update-service --cluster ${CLUSTER_NAME} --service ${SERVICE_NAME} --desired-count 1 --region ${AWS_REGION}" 