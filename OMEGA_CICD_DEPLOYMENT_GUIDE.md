# 🚀 OMEGA PRO AI v10.1 - Automatic Deployment Guide

Complete CI/CD pipeline for automatic deployment from Mac to Akash Network via GitHub Actions.

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Usage](#usage)
- [Monitoring & Troubleshooting](#monitoring--troubleshooting)
- [Advanced Configuration](#advanced-configuration)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

This system provides automatic deployment of OMEGA PRO AI from your Mac to Akash Network using:

- **GitHub Actions**: Automated CI/CD pipeline
- **Docker Hub**: Container registry for versioned deployments
- **Akash Network**: Decentralized cloud deployment
- **Mac Scripts**: Local automation tools

### Architecture

```
Mac Local Development
        ↓ (git push)
GitHub Actions CI/CD
        ↓ (docker build/push)
Docker Hub Registry
        ↓ (deploy)
Akash Network
        ↓ (health check)
Production OMEGA API
```

## ⚡ Quick Start

### 1. One-Command Setup (Mac)

```bash
# Navigate to your OMEGA directory
cd /Users/user/Documents/OMEGA_PRO_AI_v10.1

# Run Mac deployment automation
./scripts/omega-deploy-mac.sh --setup
```

### 2. Make Your First Change

```bash
# Edit any file in your project
echo "# Updated $(date)" >> README.md

# Deploy automatically
./scripts/omega-deploy-mac.sh
```

That's it! Your changes will automatically deploy to Akash Network.

## 📋 Prerequisites

### Required Accounts

1. **Docker Hub Account**
   - Sign up at: https://hub.docker.com
   - Create access token: Settings → Security → New Access Token

2. **Akash Network Wallet**
   - Install Akash CLI
   - Create wallet with AKT tokens for deployments
   - Export your key for deployment

3. **GitHub Repository** (Already configured)
   - Your code is already in: https://github.com/artvepa80/-omega-pro-ai.git

### Required Software (Mac)

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install git docker-desktop
```

## 🔧 Initial Setup

### Step 1: Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
code .env  # or nano .env
```

**Required Variables:**
```bash
# Docker Hub
DOCKERHUB_USERNAME=your_dockerhub_username
DOCKERHUB_TOKEN=dckr_pat_your_access_token

# Akash Network
AKASH_FROM=your_wallet_key_name
AKASH_NODE=https://rpc.akashnet.net:443
AKASH_CHAIN_ID=akashnet-2

# Optional: Existing Deployment (for updates)
AKASH_URI=https://your-deployment.akash-node.com
```

### Step 2: GitHub Secrets Configuration

Add these secrets to your GitHub repository at:
`https://github.com/artvepa80/-omega-pro-ai/settings/secrets/actions`

**Required Secrets:**
```bash
DOCKERHUB_USERNAME          # Your Docker Hub username
DOCKERHUB_TOKEN            # Your Docker Hub access token
AKASH_KEY_SECRET           # Base64 encoded Akash wallet key
AKASH_NODE                 # https://rpc.akashnet.net:443
AKASH_CHAIN_ID             # akashnet-2
```

**Optional Secrets (for existing deployments):**
```bash
AKASH_DSEQ                 # Deployment sequence number
AKASH_GSEQ                 # Group sequence number
AKASH_OSEQ                 # Order sequence number
AKASH_PROVIDER             # Provider address
AKASH_URI                  # Public deployment URL
```

### Step 3: Verify Setup

```bash
# Check all prerequisites
./scripts/omega-deploy-mac.sh --check

# Test Docker build locally
./scripts/omega-deploy-mac.sh --local-test
```

## 🚀 Usage

### Basic Deployment Workflow

1. **Make Changes**: Edit any files in your project
2. **Deploy**: Run the deployment script
3. **Monitor**: Check GitHub Actions and Akash deployment

```bash
# Full deployment with testing
./scripts/omega-deploy-mac.sh

# Quick deployment (skip local Docker test)
./scripts/omega-deploy-mac.sh --quick
```

### Manual Git Operations

If you prefer manual git control:

```bash
# Commit your changes
git add .
git commit -m "Your commit message"
git push origin main

# GitHub Actions will automatically deploy
```

### Monitoring Deployment

```bash
# Monitor GitHub Actions
./scripts/omega-deploy-mac.sh --monitor

# Check deployment health
./scripts/omega-monitor.sh health

# Continuous monitoring (1 hour)
./scripts/omega-monitor.sh monitor 3600
```

## 📊 Monitoring & Troubleshooting

### Health Monitoring

```bash
# Single health check
./scripts/omega-monitor.sh health

# Continuous monitoring
./scripts/omega-monitor.sh monitor

# View monitoring logs
./scripts/omega-monitor.sh logs
```

### Deployment Status

```bash
# Check Akash deployment status
./scripts/omega-monitor.sh status

# View GitHub Actions
open https://github.com/artvepa80/-omega-pro-ai/actions
```

### Rollback if Needed

```bash
# Automated rollback
./scripts/omega-monitor.sh rollback

# Manual rollback via GitHub
gh workflow run "OMEGA PRO AI - Akash CI/CD Pipeline" --field rollback=true
```

## ⚙️ Advanced Configuration

### Custom Deployment Manifests

Edit deployment configurations:
```bash
# Main deployment manifest
nano deploy/omega-cicd-deployment.yaml

# Akash-specific settings
nano deploy/omega-simple.yaml
```

### Docker Build Customization

```bash
# Custom Docker build
docker build -f Dockerfile.cicd -t omegaproai/omega-pro-ai:custom .

# Push custom version
docker push omegaproai/omega-pro-ai:custom
```

### GitHub Actions Customization

Edit the workflow:
```bash
nano .github/workflows/akash-cicd.yml
```

### Resource Allocation

Modify resources in deployment manifest:
```yaml
resources:
  cpu:
    units: 2.0      # Increase CPU
  memory:
    size: 8Gi       # Increase memory
  gpu:
    units: 1        # GPU units
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Docker Hub Authentication Failed
```bash
# Check Docker Hub token
docker login --username $DOCKERHUB_USERNAME

# Regenerate token if needed
# Go to: https://hub.docker.com/settings/security
```

#### 2. Akash Deployment Failed
```bash
# Check Akash wallet balance
akash query bank balances $AKASH_ADDRESS

# Verify network connectivity
akash query deployment list --owner $AKASH_FROM
```

#### 3. GitHub Actions Failed
```bash
# Check GitHub secrets
gh secret list

# View detailed logs
gh run view --log
```

#### 4. Health Checks Failing
```bash
# Check deployment logs
./scripts/omega-monitor.sh logs 100

# Test endpoints manually
curl https://your-deployment.akash-node.com/health
```

### Debug Mode

Enable debug mode for detailed logging:
```bash
# Set debug in environment
export DEBUG_MODE=true

# Run with verbose output
./scripts/omega-deploy-mac.sh --verbose
```

### Log Files

Important log locations:
```bash
# Monitoring logs
tail -f logs/monitoring.log

# Deployment logs
tail -f logs/deployment.log

# GitHub Actions logs
gh run view --log
```

## 📁 File Structure

```
/Users/user/Documents/OMEGA_PRO_AI_v10.1/
├── scripts/
│   ├── omega-deploy-mac.sh      # Main Mac deployment script
│   ├── deploy-to-akash.sh       # Advanced Akash deployment
│   └── omega-monitor.sh         # Monitoring and health checks
├── .github/workflows/
│   └── akash-cicd.yml          # GitHub Actions CI/CD
├── deploy/
│   ├── omega-cicd-deployment.yaml  # Main deployment manifest
│   └── omega-simple.yaml          # Simple deployment config
├── Dockerfile.cicd             # Optimized production Dockerfile
├── .env.example                 # Environment template
└── omega_unified_main.py        # Main application entry point
```

## 🔐 Security Notes

1. **Never commit .env file** - Contains sensitive credentials
2. **Use GitHub Secrets** - For CI/CD credentials
3. **Rotate tokens regularly** - Docker Hub and GitHub tokens
4. **Monitor access logs** - Check for unauthorized access
5. **Use HTTPS only** - All endpoints should use SSL

## 📞 Support

### Get Help

```bash
# Show help for any script
./scripts/omega-deploy-mac.sh --help
./scripts/omega-monitor.sh --help

# Check system status
./scripts/omega-deploy-mac.sh --check
```

### Resources

- **Akash Network**: https://akash.network/docs/
- **Docker Hub**: https://docs.docker.com/docker-hub/
- **GitHub Actions**: https://docs.github.com/en/actions
- **OMEGA Pro AI**: https://github.com/artvepa80/-omega-pro-ai

## 🎉 Success!

Once setup is complete, you have:

✅ **Automatic Deployment**: Push code → Auto-deploy to Akash  
✅ **Health Monitoring**: Continuous deployment health checks  
✅ **Rollback Capability**: Quick rollback if issues occur  
✅ **Version Control**: All deployments are versioned and tracked  
✅ **Zero Downtime**: Seamless updates to your OMEGA API  

Your OMEGA PRO AI system is now ready for production use on Akash Network!

---

*🤖 Generated with [Claude Code](https://claude.ai/code)*

*Co-Authored-By: Claude <noreply@anthropic.com>*