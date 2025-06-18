#!/bin/bash

# Setup IAM Role for Lambda Execution

echo "🔐 Setting up IAM role for Lambda..."

# Create Lambda execution role
aws iam create-role \
    --role-name lambda-execution-role \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }' 2>/dev/null || echo "Role already exists"

# Attach basic Lambda execution policy
aws iam attach-role-policy \
    --role-name lambda-execution-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole 2>/dev/null || echo "Policy already attached"

# Create custom policy for additional permissions (if needed)
aws iam create-policy \
    --policy-name lambda-tsa-report-policy \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "arn:aws:logs:*:*:*"
            }
        ]
    }' 2>/dev/null || echo "Policy already exists"

# Attach custom policy
aws iam attach-role-policy \
    --role-name lambda-execution-role \
    --policy-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/lambda-tsa-report-policy 2>/dev/null || echo "Custom policy already attached"

echo "✅ IAM role setup complete!"
echo "Role ARN: arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/lambda-execution-role" 