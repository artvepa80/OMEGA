# 🚀 OMEGA PRO AI v10.1 - Complete CI/CD Pipeline Guide

## Overview

This guide provides complete instructions for the automated CI/CD pipeline that deploys OMEGA PRO AI to Akash Network using GitHub Pro features. The system automatically syncs from local development to cloud deployment with comprehensive monitoring and security.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Initial Setup](#initial-setup)
3. [GitHub Configuration](#github-configuration)
4. [Docker Hub Setup](#docker-hub-setup)
5. [Akash Network Configuration](#akash-network-configuration)
6. [Local Development](#local-development)
7. [Deployment Process](#deployment-process)
8. [Monitoring & Management](#monitoring--management)
9. [Security Features](#security-features)
10. [Troubleshooting](#troubleshooting)
11. [Advanced Usage](#advanced-usage)

---

## 🚀 Quick Start

### One-Command Setup (macOS)
```bash
# Run the complete setup script
./scripts/omega-dev-setup.sh

# Test the entire pipeline
./scripts/test-pipeline.sh

# Deploy to Akash Network
./scripts/deploy-to-akash.sh
```

### Manual Deployment
```bash
# Build and push to Docker Hub
docker build -f Dockerfile.production -t omegaproai/omega-ai:latest .
docker push omegaproai/omega-ai:latest

# Deploy to Akash
./scripts/deploy-to-akash.sh
```

---

## 🛠️ Initial Setup

### 1. Prerequisites

**Required Software:**
- macOS (script optimized for Mac)
- Homebrew
- Docker Desktop
- Git
- Python 3.11+

**Accounts Needed:**
- GitHub Pro account
- Docker Hub account
- Akash Network wallet

### 2. Environment Configuration

Copy the environment template:
```bash
cp .env.example .env
```

Update `.env` with your actual values:
```bash
# Essential variables
AKASH_ACCOUNT_ADDRESS=your_akash_address
AKASH_DSEQ=22849193
AKASH_PROVIDER=provider.akash.win
DOCKERHUB_USERNAME=your_docker_username
DOCKERHUB_TOKEN=your_docker_token
GITHUB_TOKEN=your_github_token
```

---

## 🐙 GitHub Configuration

### 1. Repository Setup

Initialize and configure the repository:
```bash
git init
git add .
git commit -m "🚀 Initial OMEGA PRO AI v10.1 setup"
git branch -M main
git remote add origin https://github.com/yourusername/omega-pro-ai.git
git push -u origin main
```

### 2. GitHub Pro Features Setup

**Branch Protection Rules:**
- Go to Settings > Branches
- Add rule for `main` branch:
  - Require pull request reviews
  - Require status checks to pass
  - Require up-to-date branches
  - Include administrators

**GitHub Secrets:**
Add these secrets in Settings > Secrets and variables > Actions:

```bash
# Docker Hub
DOCKERHUB_USERNAME=your_username
DOCKERHUB_TOKEN=your_access_token

# Akash Network
AKASH_NODE=https://rpc.akashnet.net:443
AKASH_CHAIN_ID=akashnet-2
AKASH_ACCOUNT_ADDRESS=your_address
AKASH_DSEQ=22849193
AKASH_PROVIDER=provider.akash.win
AKASH_WALLET_MNEMONIC="your twelve word mnemonic"

# Monitoring (Optional)
SLACK_WEBHOOK=your_slack_webhook_url
```

### 3. GitHub Actions Workflows

The pipeline includes these workflows:

- **Main CI/CD Pipeline** (`.github/workflows/cicd-pipeline.yml`)
  - Security analysis
  - Automated testing
  - Docker build and scan
  - Akash deployment
  - Health monitoring

- **Dependency Updates** (`.github/workflows/dependency-updates.yml`)
  - Weekly dependency updates
  - Security vulnerability checks
  - Automated pull requests

- **Dependabot** (`.github/dependabot.yml`)
  - Python, Docker, and GitHub Actions updates
  - Automated dependency management

---

## 🐳 Docker Hub Setup

### 1. Create Docker Hub Account
1. Sign up at [hub.docker.com](https://hub.docker.com)
2. Create repository: `omegaproai/omega-ai`
3. Generate access token in Account Settings > Security

### 2. Test Docker Integration
```bash
# Login to Docker Hub
docker login -u your_username

# Build and test image
docker build -f Dockerfile.production -t omegaproai/omega-ai:test .
docker run --rm -p 8000:8000 omegaproai/omega-ai:test

# Push image
docker push omegaproai/omega-ai:test
```

---

## ☁️ Akash Network Configuration

### 1. Wallet Setup

Install Akash CLI:
```bash
curl -sSfL https://raw.githubusercontent.com/akash-network/node/master/install.sh | sh
sudo mv ./bin/akash /usr/local/bin/
```

Create or import wallet:
```bash
# Create new wallet
akash keys add main

# Or import existing wallet
akash keys recover main --recover-key
```

Fund your wallet with AKT tokens from an exchange.

### 2. Current Deployment Info

Your existing deployment:
- **DSEQ:** 22849193
- **Provider:** provider.akash.win
- **URL:** https://f4o5gi3c0tfmvblt4avi2l6o08.ingress.akash.win
- **Cost:** $0.73/month

### 3. Deployment Management

Update existing deployment:
```bash
# Update with new image
./scripts/deploy-to-akash.sh
```

Monitor deployment:
```bash
# Real-time monitoring
./scripts/monitor-akash.sh

# Check deployment status
akash query deployment get --owner $AKASH_ACCOUNT_ADDRESS --dseq 22849193
```

---

## 💻 Local Development

### Development Environment

Set up local development:
```bash
# Run setup script
./scripts/omega-dev-setup.sh

# Activate virtual environment
source venv/bin/activate

# Start local development
./run-local.sh
```

### Development Commands

```bash
# Run OMEGA locally
./run-local.sh

# Run test suite
./run-tests.sh

# Run in Docker (development)
./run-docker-dev.sh

# Deploy to Akash
./scripts/deploy-to-akash.sh

# Monitor Akash deployment
./scripts/monitor-akash.sh
```

### Pre-commit Hooks

The setup script installs pre-commit hooks for:
- Code formatting (Black)
- Import sorting (isort)
- Linting (flake8)
- Security scanning (bandit)
- YAML validation

---

## 🚀 Deployment Process

### Automatic Deployment

The CI/CD pipeline triggers on:
- Push to `main` branch
- Pull request to `main`
- Manual trigger via GitHub Actions

### Pipeline Stages

1. **Security Analysis**
   - Bandit security scan
   - Safety vulnerability check
   - Semgrep code analysis

2. **Testing**
   - Unit tests across Python versions
   - Integration tests
   - Coverage reporting

3. **Docker Build**
   - Multi-architecture build
   - Security scanning with Trivy
   - Registry push

4. **Akash Deployment**
   - Manifest creation
   - Deployment update
   - Health verification

5. **Monitoring**
   - Health checks
   - Performance monitoring
   - Alert notifications

### Manual Deployment

For immediate deployment:
```bash
# Quick deployment
./scripts/deploy-to-akash.sh

# With custom image
DOCKER_IMAGE="omegaproai/omega-ai:custom" ./scripts/deploy-to-akash.sh
```

---

## 📊 Monitoring & Management

### Health Monitoring

Continuous monitoring with:
```bash
# Start monitoring dashboard
./scripts/monitor-akash.sh
```

### Monitoring Features

- **Real-time Health Checks:** Every 60 seconds
- **API Endpoint Validation:** Multiple endpoints
- **Response Time Tracking:** Performance metrics
- **Alert System:** Slack notifications
- **Failure Threshold:** 3 consecutive failures

### Dashboard Information

The monitoring dashboard shows:
- Deployment URL and status
- Response times and health checks
- Akash deployment details
- Issue tracking and alerts
- System uptime and statistics

### Log Files

Monitor logs at:
- `logs/akash-deployment.log` - Deployment logs
- `logs/akash-monitor.log` - Monitoring logs
- `logs/pipeline-test.log` - Test results

---

## 🔐 Security Features

### GitHub Pro Security Features

- **Secret Scanning:** Automatic detection of secrets
- **Dependency Review:** Security analysis of dependencies
- **CodeQL Analysis:** Semantic code analysis
- **Security Advisories:** Vulnerability tracking

### Pipeline Security

- **Container Scanning:** Trivy vulnerability scanning
- **Code Analysis:** Multiple security tools
- **Secret Management:** GitHub secrets for sensitive data
- **Access Control:** Branch protection and reviews

### Best Practices

1. **Never commit secrets** to the repository
2. **Use `.env` files** for local configuration
3. **Rotate tokens regularly** in GitHub secrets
4. **Monitor security alerts** in GitHub
5. **Keep dependencies updated** via Dependabot

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Docker Build Failures
```bash
# Check Docker daemon
docker info

# Clean Docker cache
docker system prune -f

# Rebuild from scratch
docker build --no-cache -f Dockerfile.production -t omegaproai/omega-ai .
```

#### 2. Akash Deployment Issues
```bash
# Check wallet balance
akash query bank balances $AKASH_ACCOUNT_ADDRESS

# Check deployment status
akash query deployment get --owner $AKASH_ACCOUNT_ADDRESS --dseq $AKASH_DSEQ

# Check provider connectivity
akash provider status --provider $AKASH_PROVIDER
```

#### 3. GitHub Actions Failures
- Check GitHub secrets configuration
- Verify branch protection rules
- Review workflow logs in Actions tab
- Ensure Docker Hub credentials are correct

#### 4. Monitoring Issues
```bash
# Test connectivity manually
curl -f https://f4o5gi3c0tfmvblt4avi2l6o08.ingress.akash.win/health

# Check DNS resolution
nslookup f4o5gi3c0tfmvblt4avi2l6o08.ingress.akash.win

# Restart monitoring
./scripts/monitor-akash.sh
```

### Emergency Procedures

#### Rollback Deployment
```bash
# Rollback to previous image
docker pull omegaproai/omega-ai:previous
docker tag omegaproai/omega-ai:previous omegaproai/omega-ai:latest
docker push omegaproai/omega-ai:latest

# Redeploy
./scripts/deploy-to-akash.sh
```

#### Service Recovery
```bash
# Close and recreate deployment
akash tx deployment close --owner $AKASH_ACCOUNT_ADDRESS --dseq $AKASH_DSEQ --from main --yes

# Create new deployment
./scripts/deploy-to-akash.sh
```

---

## 🚀 Advanced Usage

### Custom Deployment Configurations

Override default settings:
```bash
# Custom monitoring intervals
MONITOR_INTERVAL=30 ./scripts/monitor-akash.sh

# Custom Docker image
DOCKER_IMAGE="omegaproai/omega-ai:experimental" ./scripts/deploy-to-akash.sh

# Skip Docker build
SKIP_BUILD=true ./scripts/deploy-to-akash.sh
```

### GitHub Actions Customization

Trigger specific workflows:
```bash
# Manual deployment trigger
gh workflow run cicd-pipeline.yml -f deploy_to_akash=true -f force_rebuild=true

# Check workflow status
gh run list --workflow=cicd-pipeline.yml
```

### Multi-Environment Deployment

Set up staging and production:
```bash
# Staging environment
cp .env.example .env.staging
# Configure staging values

# Production environment
cp .env.example .env.production
# Configure production values

# Deploy to staging
ENV_FILE=.env.staging ./scripts/deploy-to-akash.sh
```

### Custom Health Checks

Add custom health checks:
```python
# In api_server.py
@app.get("/custom-health")
async def custom_health():
    # Your custom health logic
    return {"status": "healthy", "custom_checks": results}
```

---

## 📚 Additional Resources

### Documentation
- [Akash Network Documentation](https://docs.akash.network/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)

### Support
- OMEGA PRO AI Issues: Create GitHub issue
- Akash Network: [Discord](https://discord.akash.network/)
- GitHub Support: GitHub Pro support

### Monitoring URLs
- **Live Deployment:** https://f4o5gi3c0tfmvblt4avi2l6o08.ingress.akash.win
- **Health Check:** https://f4o5gi3c0tfmvblt4avi2l6o08.ingress.akash.win/health
- **API Documentation:** https://f4o5gi3c0tfmvblt4avi2l6o08.ingress.akash.win/docs

---

## 🎉 Success! 

Your OMEGA PRO AI v10.1 is now equipped with:

✅ **Complete CI/CD Pipeline** - Automated from code to cloud  
✅ **GitHub Pro Integration** - Enterprise-grade security and features  
✅ **Docker Hub Automation** - Automated builds and security scanning  
✅ **Akash Network Deployment** - Decentralized cloud deployment  
✅ **Real-time Monitoring** - 24/7 health checks and alerts  
✅ **Security Best Practices** - Multiple layers of protection  
✅ **One-Command Deployment** - Simple `./scripts/deploy-to-akash.sh`  

**Your deployment is live at:** https://f4o5gi3c0tfmvblt4avi2l6o08.ingress.akash.win

Happy deploying! 🚀