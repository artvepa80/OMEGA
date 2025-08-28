#!/bin/bash

# CodeBuild Setup Script for OMEGA AI
# This script creates a CodeBuild project for automated deployments

set -e

# Configuration
AWS_REGION="us-east-1"
PROJECT_NAME="omega-build-project"
ECR_REPO_NAME="omega-pro-ai"

echo "🏗️ Setting up CodeBuild project..."

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "AWS Account ID: $AWS_ACCOUNT_ID"

# Create CodeBuild project
cat > aws/codebuild-project.json << EOF
{
    "name": "$PROJECT_NAME",
    "description": "Build project for OMEGA AI",
    "source": {
        "type": "GITHUB",
        "location": "https://github.com/artvepa80/OMEGA.git",
        "buildspec": "aws/buildspec.yml"
    },
    "artifacts": {
        "type": "NO_ARTIFACTS"
    },
    "environment": {
        "type": "LINUX_CONTAINER",
        "image": "aws/codebuild/amazonlinux2-x86_64-standard:3.0",
        "computeType": "BUILD_GENERAL1_MEDIUM",
        "privilegedMode": true,
        "environmentVariables": [
            {
                "name": "AWS_DEFAULT_REGION",
                "value": "$AWS_REGION"
            },
            {
                "name": "AWS_ACCOUNT_ID",
                "value": "$AWS_ACCOUNT_ID"
            },
            {
                "name": "IMAGE_REPO_NAME",
                "value": "$ECR_REPO_NAME"
            }
        ]
    },
    "serviceRole": "arn:aws:iam::$AWS_ACCOUNT_ID:role/CodeBuildServiceRole"
}
EOF

# Create the CodeBuild project
aws codebuild create-project --cli-input-json file://aws/codebuild-project.json --region $AWS_REGION || {
    echo "⚠️  CodeBuild project might already exist. Updating..."
    aws codebuild update-project --cli-input-json file://aws/codebuild-project.json --region $AWS_REGION
}

echo "✅ CodeBuild project created successfully!"
echo ""
echo "🔗 CodeBuild Console: https://console.aws.amazon.com/codesuite/codebuild/projects/$PROJECT_NAME/history?region=$AWS_REGION"
echo ""
echo "Next steps:"
echo "1. Update the GitHub repository URL in aws/codebuild-project.json"
echo "2. Set up GitHub webhook or manual triggers"
echo "3. Trigger first build to deploy OMEGA AI"
echo ""
echo "To start a manual build:"
echo "aws codebuild start-build --project-name $PROJECT_NAME --region $AWS_REGION"