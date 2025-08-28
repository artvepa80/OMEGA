# OMEGA AI AWS ECS Deployment Guide

## 🚀 Complete Production Deployment on AWS ECS with CodeBuild

This guide provides step-by-step instructions for deploying OMEGA AI to AWS ECS using CloudShell and CodeBuild for automated CI/CD.

## 📋 Prerequisites

- AWS Account with appropriate permissions
- GitHub repository with OMEGA AI code
- Basic knowledge of AWS services (ECS, ECR, CodeBuild, ALB)

## 🏗️ Architecture Overview

```
GitHub → CodeBuild → ECR → ECS Fargate → Application Load Balancer → Internet
```

**Components:**
- **ECS Fargate**: Serverless container hosting
- **Application Load Balancer**: HTTP traffic distribution
- **ECR**: Docker image registry  
- **CodeBuild**: Automated CI/CD pipeline
- **CloudWatch**: Logging and monitoring

## 🚀 Quick Start (CloudShell)

### Step 1: Access AWS CloudShell
1. Log into AWS Console
2. Click the CloudShell icon (terminal symbol) in the top navigation
3. Wait for CloudShell to initialize

### Step 2: Run Automated Setup
```bash
# Download and run the setup script
curl -O https://raw.githubusercontent.com/YOUR_USERNAME/OMEGA_PRO_AI_v10.1/main/aws/cloudshell-setup.sh
chmod +x cloudshell-setup.sh
./cloudshell-setup.sh
```

**The script will:**
- Clone your repository
- Set up ECS cluster and services
- Create load balancer and security groups
- Configure CodeBuild project
- Build and deploy initial Docker image
- Run validation tests

### Step 3: Test Deployment
```bash
# Get your load balancer URL from the output, then test:
python3 aws/test-deployment.py http://YOUR-ALB-DNS-NAME
```

## 🔧 Manual Setup (Detailed Steps)

If you prefer manual control, follow these detailed steps:

### Phase 1: Infrastructure Setup

#### 1. Create ECR Repository
```bash
aws ecr create-repository --repository-name omega-pro-ai --region us-east-1
```

#### 2. Set up ECS Cluster
```bash
aws ecs create-cluster --cluster-name omega-cluster --region us-east-1
```

#### 3. Create IAM Roles
```bash
# ECS Task Execution Role (managed by AWS)
aws iam create-role --role-name ecsTaskExecutionRole --assume-role-policy-document file://aws/trust-policy.json
aws iam attach-role-policy --role-name ecsTaskExecutionRole --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# CodeBuild Service Role
aws iam create-role --role-name CodeBuildServiceRole --assume-role-policy-document file://aws/codebuild-trust-policy.json
```

#### 4. Set up Load Balancer
```bash
# The deploy-ecs.sh script handles this automatically
./aws/deploy-ecs.sh
```

### Phase 2: Application Deployment

#### 1. Register Task Definition
```bash
# Update task-definition.json with your account ID
sed "s/YOUR_ACCOUNT_ID/$(aws sts get-caller-identity --query Account --output text)/g" aws/task-definition.json > aws/task-definition-updated.json

aws ecs register-task-definition --cli-input-json file://aws/task-definition-updated.json
```

#### 2. Create ECS Service
```bash
aws ecs create-service \
  --cluster omega-cluster \
  --service-name omega-service \
  --task-definition omega-pro-ai \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration file://aws/network-config.json
```

### Phase 3: CI/CD Pipeline

#### 1. Set up CodeBuild
```bash
./aws/setup-codebuild.sh
```

#### 2. Build Initial Image
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -f Dockerfile.aws -t omega-pro-ai:latest .
docker tag omega-pro-ai:latest $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com/omega-pro-ai:latest
docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com/omega-pro-ai:latest
```

## 🔍 Configuration Files

### Key Files Created:
- `aws/task-definition.json` - ECS task configuration
- `aws/buildspec.yml` - CodeBuild instructions
- `aws/deploy-ecs.sh` - Infrastructure setup script
- `aws/setup-codebuild.sh` - CI/CD pipeline setup
- `aws/cloudshell-setup.sh` - Complete automated deployment
- `aws/test-deployment.py` - Validation and testing
- `Dockerfile.aws` - Optimized container image

### Environment Variables:
- `OMEGA_VERSION=v10.1`
- `PYTHONUNBUFFERED=1`
- `PORT=4000`

## 📊 Monitoring and Management

### View Logs
```bash
# Real-time log streaming
aws logs tail /ecs/omega-pro-ai --follow --region us-east-1

# Service status
aws ecs describe-services --cluster omega-cluster --services omega-service
```

### Scaling
```bash
# Update desired count
aws ecs update-service --cluster omega-cluster --service omega-service --desired-count 2
```

### Rolling Updates
```bash
# Force new deployment
aws ecs update-service --cluster omega-cluster --service omega-service --force-new-deployment
```

## 🔗 API Endpoints

Once deployed, your OMEGA AI will be accessible at:

### Health Check
```bash
curl http://YOUR-ALB-DNS/health
```

### Predictions
```bash
curl -X POST http://YOUR-ALB-DNS/predict \
  -H "Content-Type: application/json" \
  -d '{"predictions": 10, "ai_combinations": 25}'
```

### Response Format
```json
{
  "predictions": [
    {
      "numbers": [6, 10, 13, 30, 35, 37],
      "score": 0.734,
      "confidence": 0.89
    }
  ],
  "metadata": {
    "generation_time": 1.23,
    "version": "v10.1"
  }
}
```

## 💰 Cost Estimation

**Monthly costs (us-east-1):**
- ECS Fargate (1 task): ~$30
- Application Load Balancer: ~$18
- ECR storage (minimal): ~$1
- CloudWatch logs: ~$5
- **Total: ~$54/month**

**Cost optimization:**
- Use spot instances for development
- Set up auto-scaling based on demand
- Configure log retention policies

## 🔧 Troubleshooting

### Common Issues

#### Service fails to start
```bash
# Check service events
aws ecs describe-services --cluster omega-cluster --services omega-service --query 'services[0].events'

# Check task logs
aws logs tail /ecs/omega-pro-ai --since 10m
```

#### Load balancer health checks fail
- Verify container port 4000 is exposed
- Check security group rules
- Ensure /health endpoint works in container

#### Build failures
```bash
# Check CodeBuild logs
aws codebuild list-builds-for-project --project-name omega-build-project
aws codebuild batch-get-builds --ids BUILD_ID
```

### Performance Tuning

#### Optimize container resources
```json
{
  "cpu": "1024",
  "memory": "2048"
}
```

#### Enable auto-scaling
```bash
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/omega-cluster/omega-service \
  --min-capacity 1 \
  --max-capacity 10
```

## 🚀 Deployment Automation

### GitHub Actions Integration
```yaml
name: Deploy to ECS
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Trigger CodeBuild
        run: |
          aws codebuild start-build --project-name omega-build-project
```

### Automated Rollbacks
```bash
# Rollback to previous task definition
aws ecs update-service \
  --cluster omega-cluster \
  --service omega-service \
  --task-definition omega-pro-ai:PREVIOUS_REVISION
```

## ✅ Validation Checklist

After deployment, verify:
- [ ] Load balancer health checks pass
- [ ] /health endpoint returns 200
- [ ] /predict endpoint generates predictions
- [ ] Logs are flowing to CloudWatch
- [ ] Service scales correctly
- [ ] CodeBuild pipeline works
- [ ] Monitoring alerts configured

## 🎯 Next Steps

1. **Set up monitoring**: Configure CloudWatch dashboards and alarms
2. **Enable HTTPS**: Add SSL certificate to load balancer  
3. **Custom domain**: Route53 domain mapping
4. **Auto-scaling**: Configure based on CPU/memory metrics
5. **Backup strategy**: Database and configuration backups
6. **Security hardening**: WAF, VPC endpoints, secrets management

## 📚 Resources

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [CodeBuild User Guide](https://docs.aws.amazon.com/codebuild/)
- [ECR User Guide](https://docs.aws.amazon.com/ecr/)
- [Application Load Balancer Guide](https://docs.aws.amazon.com/elasticloadbalancing/)

---

**Support**: For issues or questions, check the troubleshooting section or review AWS CloudWatch logs for detailed error information.