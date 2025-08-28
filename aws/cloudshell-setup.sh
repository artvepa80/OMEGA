#!/bin/bash

# AWS CloudShell Setup Script for OMEGA AI ECS Deployment
# Run this script in AWS CloudShell to deploy OMEGA AI to ECS

set -e

echo "🌩️ OMEGA AI AWS CloudShell Deployment"
echo "======================================"
echo ""

# Check if we're in CloudShell
if [[ ! -f /opt/aws/cloudshell/.cs-release ]]; then
    echo "⚠️  This script is optimized for AWS CloudShell"
    echo "   You can still run it, but some features might not work"
fi

# Set default region if not set
export AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1}
echo "Using AWS Region: $AWS_DEFAULT_REGION"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install required tools if not present
echo "🔧 Checking required tools..."

if ! command_exists git; then
    echo "Installing git..."
    sudo yum install -y git
fi

if ! command_exists docker; then
    echo "Installing docker..."
    sudo yum install -y docker
    sudo service docker start
    sudo usermod -a -G docker $(whoami)
fi

if ! command_exists jq; then
    echo "Installing jq..."
    sudo yum install -y jq
fi

# Clone or update repository
echo "📥 Setting up OMEGA AI repository..."
if [[ -d "OMEGA" ]]; then
    echo "Repository exists, updating..."
    cd OMEGA
    git pull origin main || git pull origin master
else
    echo "Cloning repository..."
    git clone https://github.com/artvepa80/OMEGA.git
    cd OMEGA
fi

# Check if we're in the right directory
if [[ ! -f "omega_unified_main.py" ]]; then
    echo "❌ omega_unified_main.py not found. Are you in the right directory?"
    exit 1
fi

echo "✅ Repository ready!"

# Make scripts executable
chmod +x aws/deploy-ecs.sh
chmod +x aws/setup-codebuild.sh

# Run the ECS deployment
echo ""
echo "🚀 Starting ECS infrastructure deployment..."
./aws/deploy-ecs.sh

# Set up CodeBuild
echo ""
echo "🏗️ Setting up CodeBuild..."
./aws/setup-codebuild.sh

# Build and push initial Docker image
echo ""
echo "🐳 Building and pushing initial Docker image..."

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/omega-pro-ai"

# Login to ECR
echo "Logging into ECR..."
aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $ECR_REPO

# Build image
echo "Building Docker image..."
docker build -f Dockerfile.aws -t omega-pro-ai:latest .

# Tag and push
echo "Tagging and pushing image..."
docker tag omega-pro-ai:latest $ECR_REPO:latest
docker push $ECR_REPO:latest

# Update ECS service to use new image
echo "Updating ECS service..."
aws ecs update-service \
    --cluster omega-cluster \
    --service omega-service \
    --force-new-deployment \
    --region $AWS_DEFAULT_REGION

# Get service information
echo ""
echo "📊 Getting deployment status..."
CLUSTER_NAME="omega-cluster"
SERVICE_NAME="omega-service"

# Wait for service to stabilize
echo "Waiting for service deployment to complete..."
aws ecs wait services-stable --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_DEFAULT_REGION

# Get load balancer URL
ALB_ARN=$(aws elbv2 describe-load-balancers --names omega-alb --query 'LoadBalancers[0].LoadBalancerArn' --output text)
ALB_DNS=$(aws elbv2 describe-load-balancers --load-balancer-arns $ALB_ARN --query 'LoadBalancers[0].DNSName' --output text)

echo ""
echo "🎉 OMEGA AI deployment completed successfully!"
echo "======================================"
echo ""
echo "🔗 Application URL: http://$ALB_DNS"
echo "📊 ECS Console: https://console.aws.amazon.com/ecs/home?region=$AWS_DEFAULT_REGION#/clusters/$CLUSTER_NAME"
echo "🏗️ CodeBuild: https://console.aws.amazon.com/codesuite/codebuild/projects/omega-build-project/history?region=$AWS_DEFAULT_REGION"
echo "📦 ECR Repository: https://console.aws.amazon.com/ecr/repositories/omega-pro-ai?region=$AWS_DEFAULT_REGION"
echo ""
echo "⏱️  Wait 2-3 minutes for the load balancer to become ready"
echo ""
echo "Test endpoints:"
echo "curl http://$ALB_DNS/health"
echo "curl -X POST http://$ALB_DNS/predict -H 'Content-Type: application/json' -d '{\"predictions\": 5}'"
echo ""
echo "To view logs:"
echo "aws logs tail /ecs/omega-pro-ai --follow --region $AWS_DEFAULT_REGION"