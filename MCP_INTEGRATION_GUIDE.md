# 🔗 OMEGA AI MCP Integration Guide

**Multi-Channel Platform Integration for OMEGA AI v10.1**

This guide provides complete instructions for setting up and using the OMEGA AI Multi-Channel Platform (MCP) integration, which enables automated notifications, lottery data ingestion, and workflow automation.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Prerequisites](#prerequisites)
4. [Quick Start](#quick-start)
5. [Configuration](#configuration)
6. [Service Management](#service-management)
7. [Integration with Main System](#integration-with-main-system)
8. [Health Monitoring](#health-monitoring)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)
11. [Advanced Usage](#advanced-usage)

## 🎯 Overview

The OMEGA AI MCP Integration provides a comprehensive multi-channel platform that extends OMEGA AI's capabilities with:

- **🎰 Lottery Data Service**: Automated data ingestion from multiple sources
- **📱 Notification Service**: Multi-channel notifications (Email, WhatsApp, Telegram, Discord, Slack)
- **🤖 Workflow Automation**: Scheduled predictions and automated result processing
- **🔍 Health Monitoring**: Advanced system health checks and alerting
- **🔧 Service Orchestration**: Production-ready service management

## ✨ Features

### Core Services

- **Lottery Data MCP**: Multi-source lottery data ingestion with caching and validation
- **Notification MCP**: Multi-channel notification delivery with rate limiting and retry logic
- **Workflow Automation MCP**: Intelligent scheduling and workflow orchestration

### Integration Features

- **Seamless Main System Integration**: Direct integration with OMEGA AI prediction engine
- **Environment-based Configuration**: Flexible configuration via files or environment variables
- **Production-ready Scripts**: Complete service lifecycle management
- **Advanced Health Monitoring**: Comprehensive system health checks and alerting
- **Extensive Testing Framework**: Automated testing and validation

## 🔧 Prerequisites

### System Requirements

- **Python 3.9+** with asyncio support
- **OMEGA AI v10.1** base system
- **Required Python packages** (automatically installed)

### External Services (Optional)

- **Twilio Account** (for WhatsApp/SMS notifications)
- **Telegram Bot** (for Telegram notifications)
- **SMTP Server Access** (for email notifications)
- **Discord/Slack Webhooks** (for Discord/Slack notifications)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install MCP dependencies
pip install -r requirements.txt

# Verify installation
python scripts/test_mcp_integration.py
```

### 2. Basic Configuration

```bash
# Copy configuration templates
cp config/credentials.example.json config/credentials.json
cp config/user_preferences.example.json config/user_preferences.json
cp .env.mcp.template .env

# Edit credentials (at minimum, set up email)
nano config/credentials.json
```

### 3. Test Integration

```bash
# Run integration tests
python scripts/test_mcp_integration.py

# Test with main system
python main.py --enable-mcp --mcp-test
```

### 4. Start Services

```bash
# Start MCP services
./scripts/start_omega_mcp.sh

# Check status
python scripts/omega_mcp_service.py status
```

## ⚙️ Configuration

### Configuration Files

| File | Purpose | Required |
|------|---------|----------|
| `config/mcp_config.json` | Main MCP configuration | No (auto-created) |
| `config/credentials.json` | Service credentials | No (can use env vars) |
| `config/user_preferences.json` | User notification preferences | No (auto-created) |
| `.env` | Environment variables | No (optional) |

### Environment Variables

```bash
# Basic MCP Settings
OMEGA_MCP_ENABLED=true
OMEGA_MCP_AUTO_INIT=false

# Twilio (WhatsApp/SMS)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token

# Test contacts
TEST_EMAIL=test@example.com
TEST_WHATSAPP=+1234567890
TEST_TELEGRAM_CHAT_ID=123456789
```

### Service Configuration

Edit `config/mcp_config.json`:

```json
{
  "mcp_enabled": true,
  "auto_start": false,
  "services": {
    "lottery_data": {
      "enabled": true,
      "cache_enabled": true,
      "timeout_seconds": 30
    },
    "notifications": {
      "enabled": true,
      "channels": {
        "console": true,
        "email": true,
        "whatsapp": false,
        "telegram": false
      },
      "rate_limiting": {
        "max_per_minute": 10,
        "max_per_hour": 100
      }
    },
    "workflow_automation": {
      "enabled": true,
      "scheduler_timezone": "America/Lima",
      "monitoring_interval": 60
    }
  }
}
```

## 🔧 Service Management

### Using Shell Scripts (Recommended)

```bash
# Start services
./scripts/start_omega_mcp.sh

# Stop services
./scripts/stop_omega_mcp.sh

# Restart services
./scripts/restart_omega_mcp.sh

# Start with validation
./scripts/start_omega_mcp.sh --validate-only
```

### Using Python Service Manager

```bash
# Start service in daemon mode
python scripts/omega_mcp_service.py start --daemon

# Check service status
python scripts/omega_mcp_service.py status

# Run health check
python scripts/omega_mcp_service.py health

# Stop service
python scripts/omega_mcp_service.py stop
```

### Service Status Commands

```bash
# Detailed status with JSON output
python scripts/omega_mcp_service.py status --output json

# Health check with detailed results
python scripts/omega_mcp_service.py health --output json

# Test all MCP systems
python scripts/omega_mcp_service.py test
```

## 🎯 Integration with Main System

### Command Line Integration

The MCP integration adds several command-line options to the main OMEGA AI system:

```bash
# Enable MCP integration
python main.py --enable-mcp

# Enable with custom config
python main.py --enable-mcp --mcp-config config/my_mcp_config.json

# Enable with testing
python main.py --enable-mcp --mcp-test

# Enable with auto-start services
python main.py --enable-mcp --mcp-auto-start

# Enable with notifications
python main.py --enable-mcp --mcp-notify
```

### Programmatic Integration

```python
from omega_mcp_integration import get_omega_mcp_integration

# Get integration instance
integration = get_omega_mcp_integration()

# Initialize
await integration.initialize()

# Check if enabled
if integration.is_mcp_enabled():
    # Use MCP services
    status = integration.get_status()
    print(f"Services: {status['services_initialized']}")
```

### Prediction with Notifications

```bash
# Generate predictions and send notifications
python main.py --enable-mcp --mcp-notify

# This will:
# 1. Generate OMEGA AI predictions
# 2. Format results for notifications
# 3. Send via configured channels (email, WhatsApp, etc.)
# 4. Log delivery status
```

## 🔍 Health Monitoring

### Automated Health Checks

The MCP integration includes comprehensive health monitoring:

```bash
# Run health monitor
python scripts/omega_mcp_health_monitor.py --continuous

# Generate single health report
python scripts/omega_mcp_health_monitor.py --report

# Health check with JSON output
python scripts/omega_mcp_health_monitor.py --report --output json
```

### Health Check Services

| Service | Description |
|---------|-------------|
| MCP Integration | Overall integration health |
| Lottery Data Service | Data ingestion functionality |
| Notification Service | Multi-channel notifications |
| Workflow Automation | Scheduler and job management |
| System Resources | CPU, memory, disk usage |
| Process Health | OMEGA process monitoring |
| API Connectivity | External API health |
| Data Integrity | Critical file validation |

### Health Monitoring Features

- **Real-time Monitoring**: Continuous health checks with configurable intervals
- **Alert System**: Automated alerts for critical issues
- **Performance Metrics**: System resource monitoring
- **Historical Tracking**: Health history and trend analysis
- **Customizable Thresholds**: Configurable alert thresholds

## 🧪 Testing

### Comprehensive Test Suite

```bash
# Run full integration test suite
python scripts/test_mcp_integration.py

# Run with verbose output
python scripts/test_mcp_integration.py --verbose

# Save test report
python scripts/test_mcp_integration.py --save-report test_report.json

# JSON output
python scripts/test_mcp_integration.py --output json
```

### Unit Tests

```bash
# Run pytest-based unit tests
cd tests
python -m pytest test_mcp_integration.py -v

# Run specific test class
python -m pytest test_mcp_integration.py::TestOMEGAMCPIntegration -v
```

### Test Categories

1. **Availability Tests**: MCP module imports and dependencies
2. **Configuration Tests**: Config loading and validation
3. **Initialization Tests**: Service startup and connectivity
4. **Integration Tests**: Main system integration
5. **Health Check Tests**: Monitoring system functionality
6. **Service Tests**: Individual MCP service functionality

## 🔧 Troubleshooting

### Common Issues

#### 1. MCP Dependencies Missing

```bash
# Error: ImportError: No module named 'apscheduler'
# Solution:
pip install -r requirements.txt

# Verify:
python scripts/test_mcp_integration.py
```

#### 2. Permission Denied on Scripts

```bash
# Error: Permission denied: ./scripts/start_omega_mcp.sh
# Solution:
chmod +x scripts/*.sh
```

#### 3. Configuration Issues

```bash
# Error: MCP configuration not found
# Solution:
cp config/credentials.example.json config/credentials.json
# Edit config/credentials.json with your settings
```

#### 4. Service Won't Start

```bash
# Check logs
tail -f logs/omega_mcp_service.log

# Validate configuration
./scripts/start_omega_mcp.sh --validate-only

# Force restart
./scripts/restart_omega_mcp.sh --force
```

### Debugging Tools

```bash
# Enable debug logging
export OMEGA_DEBUG_ENABLED=true

# Test individual components
python scripts/omega_mcp_service.py test

# Health check with details
python scripts/omega_mcp_health_monitor.py --report --verbose

# Check system resources
python -c "import psutil; print(f'CPU: {psutil.cpu_percent()}%, Memory: {psutil.virtual_memory().percent}%')"
```

### Log Files

| Log File | Purpose |
|----------|---------|
| `logs/omega_mcp_integration.log` | Main integration logs |
| `logs/omega_mcp_service.log` | Service management logs |
| `logs/omega_mcp_daemon.log` | Daemon process logs |
| `logs/omega_mcp_health_monitor.log` | Health monitoring logs |

## 🚀 Advanced Usage

### Custom Workflows

Create custom prediction workflows:

```python
# Custom workflow example
from omega_mcp_integration import get_omega_mcp_integration

async def custom_prediction_workflow():
    integration = get_omega_mcp_integration()
    
    # Generate predictions using MCP
    results = await integration.predict_with_mcp(
        lottery_type="kabala_pe",
        count=5,
        analysis=True
    )
    
    return results
```

### Scheduling Custom Jobs

```python
from mcps.workflow_automation_mcp import ProductionWorkflowAutomationMCP

# Add custom scheduled job
workflow_mcp = ProductionWorkflowAutomationMCP(
    omega_api_base="http://localhost:8000",
    lottery_data_mcp=lottery_mcp,
    notification_mcp=notification_mcp
)

# Schedule daily predictions
workflow_mcp.scheduler.add_job(
    func=custom_prediction_workflow,
    trigger="cron",
    hour=20,  # 8 PM daily
    minute=0,
    id="daily_custom_predictions"
)
```

### Custom Notification Channels

Extend notification system:

```python
from mcps.notification_mcp import ProductionNotificationMCP

class CustomNotificationMCP(ProductionNotificationMCP):
    def __init__(self, credentials):
        super().__init__(credentials)
        # Add custom channels
    
    async def send_custom_channel(self, message, recipients):
        # Implement custom notification logic
        pass
```

### Performance Optimization

```json
{
  "performance": {
    "enable_profiling": false,
    "enable_metrics_collection": true,
    "memory_limit_mb": 1024,
    "cpu_limit_percent": 80,
    "connection_pool_size": 10,
    "request_timeout_seconds": 30
  }
}
```

## 📊 Production Deployment

### Docker Deployment

```dockerfile
# Dockerfile with MCP support
FROM python:3.9-slim

# Copy MCP integration files
COPY omega_mcp_integration.py /app/
COPY scripts/ /app/scripts/
COPY mcps/ /app/mcps/
COPY config/ /app/config/

# Install dependencies
RUN pip install -r requirements.txt

# Set up MCP services
CMD ["python", "scripts/omega_mcp_service.py", "start", "--daemon"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: omega-mcp-services
spec:
  replicas: 1
  selector:
    matchLabels:
      app: omega-mcp
  template:
    metadata:
      labels:
        app: omega-mcp
    spec:
      containers:
      - name: omega-mcp
        image: omega-ai:mcp-latest
        env:
        - name: OMEGA_MCP_ENABLED
          value: "true"
        - name: TWILIO_ACCOUNT_SID
          valueFrom:
            secretKeyRef:
              name: omega-secrets
              key: twilio-sid
```

### Environment Variables for Production

```bash
# Production settings
OMEGA_MCP_ENABLED=true
OMEGA_MCP_AUTO_INIT=true
OMEGA_HEALTH_CHECK_ENABLED=true
OMEGA_HEALTH_CHECK_INTERVAL=300

# Security settings
OMEGA_RATE_LIMIT_PER_MINUTE=10
OMEGA_DATA_RETENTION_DAYS=30
OMEGA_LOG_RETENTION_DAYS=7

# Performance settings
OMEGA_WORKFLOW_TIMEZONE=America/Lima
OMEGA_WORKFLOW_MONITORING_INTERVAL=60
```

## 📚 API Reference

### Integration Class

```python
class OMEGAMCPIntegration:
    async def initialize(credentials=None) -> bool
    async def start(user_preferences=None) -> bool
    async def stop() -> None
    async def shutdown() -> None
    def get_status() -> Dict[str, Any]
    def is_mcp_enabled() -> bool
    async def predict_with_mcp(lottery_type, **kwargs) -> Dict[str, Any]
```

### Service Manager

```python
class OMEGAMCPService:
    async def start_service(config_path=None, daemon_mode=False) -> bool
    async def stop_service() -> None
    async def restart_service(config_path=None) -> bool
    def get_service_status() -> Dict[str, Any]
    async def run_health_check() -> Dict[str, Any]
```

### Health Monitor

```python
class OMEGAMCPHealthMonitor:
    async def run_all_health_checks() -> Dict[str, HealthCheckResult]
    async def generate_health_report() -> Dict[str, Any]
    async def run_continuous_monitoring(interval_seconds=None) -> None
```

## 🤝 Support and Contributing

### Getting Help

1. **Check Logs**: Review log files in `logs/` directory
2. **Run Tests**: Use `python scripts/test_mcp_integration.py`
3. **Health Check**: Run `python scripts/omega_mcp_health_monitor.py --report`
4. **Configuration**: Validate with `./scripts/start_omega_mcp.sh --validate-only`

### Contributing

The MCP integration is designed to be extensible:

1. **Custom Services**: Add new MCP services in `mcps/` directory
2. **Additional Channels**: Extend notification channels
3. **Custom Workflows**: Create specialized prediction workflows
4. **Health Checks**: Add domain-specific health validations

---

## 📄 License and Credits

This MCP integration is part of the OMEGA AI v10.1 system and follows the same licensing terms.

**Generated with Claude Code** - Production-ready MCP integration for OMEGA AI.

---

*For technical support or questions about the MCP integration, please refer to the comprehensive logging and health monitoring systems provided.*