#!/bin/bash

# AWS ECS Deployment Script for TSA Report
# This script deploys the TSA report to AWS ECS Fargate

set -e

# Configuration
PROJECT_NAME="tsa-passenger-report"
AWS_REGION="us-east-1"
ECR_REPOSITORY_NAME="tsa-passenger-report"
CLUSTER_NAME="tsa-report-cluster"
SERVICE_NAME="tsa-report-service"
TASK_DEFINITION_NAME="tsa-report-task"

echo "🚀 Deploying TSA Passenger Report to AWS ECS..."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install it first."
    exit 1
fi

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}"

echo "📦 Building Docker image..."

# Build Docker image
docker build -t ${ECR_REPOSITORY_NAME} .

echo "🔐 Logging into ECR..."

# Login to ECR
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_URI}

echo "🏗️ Creating ECR repository if it doesn't exist..."

# Create ECR repository if it doesn't exist
aws ecr describe-repositories --repository-names ${ECR_REPOSITORY_NAME} --region ${AWS_REGION} 2>/dev/null || \
aws ecr create-repository --repository-name ${ECR_REPOSITORY_NAME} --region ${AWS_REGION}

echo "📤 Pushing image to ECR..."

# Tag and push image
docker tag ${ECR_REPOSITORY_NAME}:latest ${ECR_URI}:latest
docker push ${ECR_URI}:latest

echo "🏗️ Creating ECS cluster if it doesn't exist..."

# Create ECS cluster if it doesn't exist
aws ecs describe-clusters --clusters ${CLUSTER_NAME} --region ${AWS_REGION} 2>/dev/null || \
aws ecs create-cluster --cluster-name ${CLUSTER_NAME} --region ${AWS_REGION}

echo "📋 Creating task definition..."

# Create task definition JSON
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
                {
                    "name": "SENDER_EMAIL",
                    "value": "${SENDER_EMAIL}"
                },
                {
                    "name": "APP_PASSWORD",
                    "value": "${APP_PASSWORD}"
                },
                {
                    "name": "RECIPIENT_EMAIL",
                    "value": "${RECIPIENT_EMAIL}"
                }
            ]
        }
    ]
}
EOF

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json --region ${AWS_REGION}

echo "🔧 Creating CloudWatch log group..."

# Create CloudWatch log group
aws logs create-log-group --log-group-name "/ecs/${PROJECT_NAME}" --region ${AWS_REGION} 2>/dev/null || true

echo "🚀 Creating ECS service..."

# Create ECS service
aws ecs create-service \
    --cluster ${CLUSTER_NAME} \
    --service-name ${SERVICE_NAME} \
    --task-definition ${TASK_DEFINITION_NAME} \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-12345678],securityGroups=[sg-12345678],assignPublicIp=ENABLED}" \
    --region ${AWS_REGION} 2>/dev/null || \
aws ecs update-service \
    --cluster ${CLUSTER_NAME} \
    --service ${SERVICE_NAME} \
    --task-definition ${TASK_DEFINITION_NAME} \
    --region ${AWS_REGION}

echo "✅ Deployment complete!"
echo "📊 Monitor your service at: https://console.aws.amazon.com/ecs/home?region=${AWS_REGION}#/clusters/${CLUSTER_NAME}/services/${SERVICE_NAME}"
echo "📝 View logs at: https://console.aws.amazon.com/cloudwatch/home?region=${AWS_REGION}#logsV2:log-groups/log-group/%2Fecs%2F${PROJECT_NAME}"

# Clean up
rm -f task-definition.json 