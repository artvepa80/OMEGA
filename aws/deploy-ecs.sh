#!/bin/bash

# AWS ECS Deployment Script for OMEGA AI
# This script sets up complete ECS infrastructure using CloudShell

set -e

# Configuration
AWS_REGION="us-east-1"
CLUSTER_NAME="omega-cluster"
SERVICE_NAME="omega-service" 
TASK_FAMILY="omega-pro-ai"
ECR_REPO_NAME="omega-pro-ai"
CODEBUILD_PROJECT="omega-build-project"

echo "🚀 Starting OMEGA AI ECS Deployment..."

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "AWS Account ID: $AWS_ACCOUNT_ID"

# Create ECR Repository
echo "📦 Creating ECR Repository..."
aws ecr describe-repositories --repository-names $ECR_REPO_NAME --region $AWS_REGION || \
aws ecr create-repository --repository-name $ECR_REPO_NAME --region $AWS_REGION

# Create ECS Cluster
echo "🏗️ Creating ECS Cluster..."
aws ecs describe-clusters --clusters $CLUSTER_NAME --region $AWS_REGION || \
aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $AWS_REGION

# Create IAM roles if they don't exist
echo "🔐 Setting up IAM roles..."

# ECS Task Execution Role
aws iam get-role --role-name ecsTaskExecutionRole || {
    echo "Creating ecsTaskExecutionRole..."
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
    aws iam attach-role-policy --role-name ecsTaskExecutionRole --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
}

# ECS Task Role
aws iam get-role --role-name ecsTaskRole || {
    echo "Creating ecsTaskRole..."
    aws iam create-role --role-name ecsTaskRole --assume-role-policy-document '{
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
}

# CodeBuild Service Role
aws iam get-role --role-name CodeBuildServiceRole || {
    echo "Creating CodeBuildServiceRole..."
    aws iam create-role --role-name CodeBuildServiceRole --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "codebuild.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }'
    
    # Attach policies to CodeBuild role
    aws iam attach-role-policy --role-name CodeBuildServiceRole --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser
    aws iam attach-role-policy --role-name CodeBuildServiceRole --policy-arn arn:aws:iam::aws:policy/AmazonECS_FullAccess
    
    # Custom policy for CloudWatch Logs
    aws iam put-role-policy --role-name CodeBuildServiceRole --policy-name CloudWatchLogsPolicy --policy-document '{
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
    }'
}

# Create CloudWatch Log Group
echo "📝 Creating CloudWatch Log Group..."
aws logs describe-log-groups --log-group-name-prefix "/ecs/omega-pro-ai" --region $AWS_REGION || \
aws logs create-log-group --log-group-name "/ecs/omega-pro-ai" --region $AWS_REGION

# Update task definition with correct ARNs
echo "📋 Updating task definition..."
sed "s/YOUR_ACCOUNT_ID/$AWS_ACCOUNT_ID/g" aws/task-definition.json > aws/task-definition-updated.json

# Register task definition
echo "📝 Registering task definition..."
aws ecs register-task-definition --cli-input-json file://aws/task-definition-updated.json --region $AWS_REGION

# Create Application Load Balancer and Target Group
echo "🔄 Setting up Load Balancer..."

# Get default VPC and subnets
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text)
SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[*].SubnetId" --output text)
SUBNET_ARRAY=(${SUBNET_IDS})

# Create security group for ALB
ALB_SG_ID=$(aws ec2 create-security-group \
    --group-name omega-alb-sg \
    --description "Security group for OMEGA ALB" \
    --vpc-id $VPC_ID \
    --query 'GroupId' --output text 2>/dev/null || \
    aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=omega-alb-sg" \
    --query 'SecurityGroups[0].GroupId' --output text)

# Allow HTTP traffic to ALB
aws ec2 authorize-security-group-ingress \
    --group-id $ALB_SG_ID \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0 2>/dev/null || true

# Create security group for ECS tasks
ECS_SG_ID=$(aws ec2 create-security-group \
    --group-name omega-ecs-sg \
    --description "Security group for OMEGA ECS tasks" \
    --vpc-id $VPC_ID \
    --query 'GroupId' --output text 2>/dev/null || \
    aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=omega-ecs-sg" \
    --query 'SecurityGroups[0].GroupId' --output text)

# Allow traffic from ALB to ECS tasks
aws ec2 authorize-security-group-ingress \
    --group-id $ECS_SG_ID \
    --protocol tcp \
    --port 4000 \
    --source-group $ALB_SG_ID 2>/dev/null || true

# Create Application Load Balancer
ALB_ARN=$(aws elbv2 create-load-balancer \
    --name omega-alb \
    --subnets ${SUBNET_ARRAY[0]} ${SUBNET_ARRAY[1]} \
    --security-groups $ALB_SG_ID \
    --query 'LoadBalancers[0].LoadBalancerArn' --output text 2>/dev/null || \
    aws elbv2 describe-load-balancers \
    --names omega-alb \
    --query 'LoadBalancers[0].LoadBalancerArn' --output text)

# Create target group
TARGET_GROUP_ARN=$(aws elbv2 create-target-group \
    --name omega-targets \
    --protocol HTTP \
    --port 4000 \
    --vpc-id $VPC_ID \
    --target-type ip \
    --health-check-path /health \
    --health-check-interval-seconds 30 \
    --health-check-timeout-seconds 10 \
    --healthy-threshold-count 2 \
    --unhealthy-threshold-count 5 \
    --query 'TargetGroups[0].TargetGroupArn' --output text 2>/dev/null || \
    aws elbv2 describe-target-groups \
    --names omega-targets \
    --query 'TargetGroups[0].TargetGroupArn' --output text)

# Create listener
aws elbv2 create-listener \
    --load-balancer-arn $ALB_ARN \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn=$TARGET_GROUP_ARN 2>/dev/null || true

# Create ECS Service
echo "🚀 Creating ECS Service..."
cat > aws/service-definition.json << EOF
{
    "serviceName": "$SERVICE_NAME",
    "cluster": "$CLUSTER_NAME",
    "taskDefinition": "$TASK_FAMILY",
    "desiredCount": 1,
    "launchType": "FARGATE",
    "networkConfiguration": {
        "awsvpcConfiguration": {
            "subnets": ["${SUBNET_ARRAY[0]}", "${SUBNET_ARRAY[1]}"],
            "securityGroups": ["$ECS_SG_ID"],
            "assignPublicIp": "ENABLED"
        }
    },
    "loadBalancers": [
        {
            "targetGroupArn": "$TARGET_GROUP_ARN",
            "containerName": "omega-container",
            "containerPort": 4000
        }
    ]
}
EOF

# Check if service exists, if not create it
aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION || \
aws ecs create-service --cli-input-json file://aws/service-definition.json --region $AWS_REGION

# Get ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers --load-balancer-arns $ALB_ARN --query 'LoadBalancers[0].DNSName' --output text)

echo "✅ ECS Infrastructure setup complete!"
echo ""
echo "🔗 Load Balancer URL: http://$ALB_DNS"
echo "📊 ECS Console: https://console.aws.amazon.com/ecs/home?region=$AWS_REGION#/clusters/$CLUSTER_NAME"
echo "📦 ECR Repository: https://console.aws.amazon.com/ecr/repositories/omega-pro-ai?region=$AWS_REGION"
echo ""
echo "Next steps:"
echo "1. Set up CodeBuild project: ./setup-codebuild.sh"
echo "2. Push code to trigger first build"
echo "3. Monitor deployment in ECS console"