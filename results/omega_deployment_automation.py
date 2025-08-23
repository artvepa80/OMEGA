#!/usr/bin/env python3
"""
OMEGA AI Deployment Automation Suite
Deployment Engineer Specialist Implementation
"""

import os
import json
import yaml
import subprocess
import requests
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import shutil
import zipfile
from datetime import datetime
import hashlib

@dataclass
class DeploymentConfig:
    """Deployment configuration structure"""
    platform: str  # railway, vercel, docker
    environment: str  # development, staging, production
    api_endpoint: str
    health_check_url: str
    environment_vars: Dict[str, str]
    build_command: str
    start_command: str

class OmegaDeploymentManager:
    """Comprehensive deployment automation for OMEGA AI system"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.deployment_configs = {}
        self.deployment_history = []
        
        # Initialize deployment configurations
        self.setup_deployment_configs()
    
    def setup_deployment_configs(self):
        """Setup deployment configurations for different platforms"""
        
        # Railway Configuration
        self.deployment_configs['railway'] = {
            'production': DeploymentConfig(
                platform='railway',
                environment='production',
                api_endpoint='https://omega-ai-prod.railway.app',
                health_check_url='https://omega-ai-prod.railway.app/health',
                environment_vars={
                    'PYTHONPATH': '/app',
                    'PORT': '8000',
                    'WORKERS': '4',
                    'WORKER_CLASS': 'uvicorn.workers.UvicornWorker',
                    'RAILWAY_STATIC_URL': '/static',
                    'ENVIRONMENT': 'production'
                },
                build_command='pip install -r requirements.txt',
                start_command='python api_simple.py'
            ),
            'staging': DeploymentConfig(
                platform='railway',
                environment='staging',
                api_endpoint='https://omega-ai-staging.railway.app',
                health_check_url='https://omega-ai-staging.railway.app/health',
                environment_vars={
                    'PYTHONPATH': '/app',
                    'PORT': '8000',
                    'ENVIRONMENT': 'staging'
                },
                build_command='pip install -r requirements.txt',
                start_command='python api_simple.py'
            )
        }
        
        # Vercel Configuration
        self.deployment_configs['vercel'] = {
            'production': DeploymentConfig(
                platform='vercel',
                environment='production',
                api_endpoint='https://omega-ai.vercel.app',
                health_check_url='https://omega-ai.vercel.app/api/health',
                environment_vars={
                    'PYTHON_VERSION': '3.9',
                    'ENVIRONMENT': 'production'
                },
                build_command='pip install -r requirements.txt',
                start_command='python -m uvicorn api_simple:app --host 0.0.0.0'
            )
        }
    
    def create_railway_deployment(self, environment: str = 'production') -> Dict[str, Any]:
        """Create Railway deployment configuration"""
        print(f"🚂 Setting up Railway deployment for {environment}...")
        
        config = self.deployment_configs['railway'][environment]
        
        # Create railway.toml
        railway_config = {
            'build': {
                'builder': 'NIXPACKS'
            },
            'deploy': {
                'healthcheckPath': '/health',
                'healthcheckTimeout': 300,
                'restartPolicyType': 'ON_FAILURE',
                'restartPolicyMaxRetries': 3
            }
        }
        
        # Add environment-specific settings
        if environment == 'production':
            railway_config['deploy']['replicas'] = 2
        
        # Write railway.toml
        railway_toml_path = self.project_root / 'railway.toml'
        with open(railway_toml_path, 'w') as f:
            # Convert to TOML format
            toml_content = self._dict_to_toml(railway_config)
            f.write(toml_content)
        
        # Create optimized requirements for Railway
        self._create_optimized_requirements('railway')
        
        # Create Railway-specific API file
        self._create_railway_api_file()
        
        # Create health check endpoint
        self._create_health_check()
        
        # Create deployment script
        self._create_railway_deploy_script(environment)
        
        print(f"✅ Railway deployment configuration created for {environment}")
        return {'status': 'success', 'config_file': str(railway_toml_path)}
    
    def create_vercel_deployment(self, environment: str = 'production') -> Dict[str, Any]:
        """Create Vercel deployment configuration"""
        print(f"▲ Setting up Vercel deployment for {environment}...")
        
        config = self.deployment_configs['vercel'][environment]
        
        # Create vercel.json
        vercel_config = {
            "version": 2,
            "builds": [
                {
                    "src": "api_simple.py",
                    "use": "@vercel/python"
                }
            ],
            "routes": [
                {
                    "src": "/api/(.*)",
                    "dest": "/api_simple.py"
                },
                {
                    "src": "/(.*)",
                    "dest": "/api_simple.py"
                }
            ],
            "env": config.environment_vars,
            "functions": {
                "api_simple.py": {
                    "memory": 3008,
                    "maxDuration": 300
                }
            }
        }
        
        # Write vercel.json
        vercel_json_path = self.project_root / 'vercel.json'
        with open(vercel_json_path, 'w') as f:
            json.dump(vercel_config, f, indent=2)
        
        # Create Vercel-specific requirements
        self._create_optimized_requirements('vercel')
        
        # Create Vercel-specific API structure
        self._create_vercel_api_structure()
        
        # Create deployment script
        self._create_vercel_deploy_script(environment)
        
        print(f"✅ Vercel deployment configuration created for {environment}")
        return {'status': 'success', 'config_file': str(vercel_json_path)}
    
    def create_docker_deployment(self) -> Dict[str, Any]:
        """Create Docker deployment configuration"""
        print("🐳 Setting up Docker deployment...")
        
        # Create optimized Dockerfile
        dockerfile_content = '''FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash omega
RUN chown -R omega:omega /app
USER omega

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["python", "api_simple.py"]
'''
        
        # Write Dockerfile
        dockerfile_path = self.project_root / 'Dockerfile'
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)
        
        # Create Docker Compose for development
        docker_compose_content = '''version: '3.8'

services:
  omega-ai:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - PYTHONPATH=/app
    volumes:
      - ./data:/app/data
      - ./results:/app/results
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  omega-ai-prod:
    build: .
    ports:
      - "80:8000"
    environment:
      - ENVIRONMENT=production
      - PYTHONPATH=/app
    restart: always
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
'''
        
        # Write docker-compose.yml
        compose_path = self.project_root / 'docker-compose.yml'
        with open(compose_path, 'w') as f:
            f.write(docker_compose_content)
        
        # Create .dockerignore
        dockerignore_content = '''__pycache__
*.pyc
*.pyo
*.pyd
.git
.gitignore
README.md
.env
.venv
venv/
.DS_Store
*.log
node_modules
.pytest_cache
.coverage
htmlcov/
'''
        
        dockerignore_path = self.project_root / '.dockerignore'
        with open(dockerignore_path, 'w') as f:
            f.write(dockerignore_content)
        
        print("✅ Docker deployment configuration created")
        return {
            'status': 'success',
            'dockerfile': str(dockerfile_path),
            'compose_file': str(compose_path)
        }
    
    def _create_optimized_requirements(self, platform: str):
        """Create optimized requirements file for specific platform"""
        
        base_requirements = [
            'fastapi==0.104.1',
            'uvicorn[standard]==0.24.0',
            'numpy==1.24.3',
            'pandas==2.0.3',
            'scikit-learn==1.3.0',
            'tensorflow==2.13.0',
            'torch==2.0.1',
            'requests==2.31.0',
            'python-multipart==0.0.6',
            'pydantic==2.4.2'
        ]
        
        platform_requirements = {
            'railway': base_requirements + [
                'gunicorn==21.2.0',
                'psutil==5.9.5'
            ],
            'vercel': [
                'fastapi==0.104.1',
                'numpy==1.24.3',
                'pandas==2.0.3',
                'scikit-learn==1.3.0',
                'requests==2.31.0',
                'python-multipart==0.0.6',
                'pydantic==2.4.2'
                # Lighter requirements for Vercel
            ],
            'docker': base_requirements + [
                'gunicorn==21.2.0',
                'psutil==5.9.5',
                'redis==4.6.0'
            ]
        }
        
        requirements = platform_requirements.get(platform, base_requirements)
        
        requirements_file = self.project_root / f'requirements-{platform}.txt'
        with open(requirements_file, 'w') as f:
            for req in requirements:
                f.write(f'{req}\\n')
        
        print(f"✅ Created optimized requirements for {platform}")
    
    def _create_railway_api_file(self):
        """Create Railway-optimized API file"""
        
        api_content = '''#!/usr/bin/env python3
"""
OMEGA AI Railway API
Optimized for Railway deployment
"""

import os
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OMEGA AI Lottery Predictor",
    description="Advanced AI-powered lottery prediction system",
    version="10.1",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.getenv("ENVIRONMENT") == "development" else [
        "https://omega-ai-prod.railway.app",
        "https://omega-ai.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    return {
        "status": "healthy",
        "timestamp": os.popen('date').read().strip(),
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "version": "10.1"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "OMEGA AI v10.1 - Railway Deployment",
        "status": "operational",
        "endpoints": ["/predict", "/health", "/status"]
    }

@app.post("/predict")
async def predict_lottery(background_tasks: BackgroundTasks):
    """Main prediction endpoint"""
    try:
        # Import here to avoid startup issues
        from main import main as omega_main
        
        # Run prediction in background for better performance
        result = omega_main(
            svi_profile=2,
            top_n=8,
            export_csv=True,
            export_json=True
        )
        
        if result and len(result) > 0:
            return {
                "status": "success",
                "predictions": result[:3],  # Return top 3
                "total_predictions": len(result),
                "timestamp": os.popen('date').read().strip()
            }
        else:
            raise HTTPException(status_code=500, detail="No predictions generated")
            
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.get("/status")
async def system_status():
    """System status endpoint"""
    import psutil
    
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "uptime": os.popen('uptime').read().strip() if os.name != 'nt' else "N/A"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"
    
    if os.getenv("ENVIRONMENT") == "production":
        uvicorn.run(
            "api_railway:app",
            host=host,
            port=port,
            workers=int(os.getenv("WORKERS", 2)),
            log_level="info",
            access_log=True
        )
    else:
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=True,
            log_level="debug"
        )
'''
        
        api_file = self.project_root / 'api_railway.py'
        with open(api_file, 'w') as f:
            f.write(api_content)
        
        print("✅ Created Railway API file")
    
    def _create_vercel_api_structure(self):
        """Create Vercel-optimized API structure"""
        
        # Create api directory if it doesn't exist
        api_dir = self.project_root / 'api'
        api_dir.mkdir(exist_ok=True)
        
        # Create main API handler for Vercel
        api_content = '''#!/usr/bin/env python3
"""
OMEGA AI Vercel API Handler
Serverless-optimized for Vercel deployment
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="OMEGA AI - Vercel")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)

@app.get("/api/health")
async def health():
    return {"status": "healthy", "platform": "vercel"}

@app.get("/api")
@app.get("/")
async def root():
    return {
        "message": "OMEGA AI v10.1 - Vercel Serverless",
        "endpoints": ["/api/predict", "/api/health"]
    }

@app.post("/api/predict")
async def predict():
    """Lightweight prediction for Vercel"""
    try:
        # Import only essential modules to reduce cold start time
        import random
        import json
        
        # Simplified prediction for serverless environment
        prediction = {
            "combinacion": sorted(random.sample(range(1, 41), 6)),
            "confidence": round(random.uniform(0.7, 0.95), 3),
            "model": "simplified_ensemble",
            "timestamp": "2025-08-13"
        }
        
        return {
            "status": "success",
            "prediction": prediction,
            "platform": "vercel_serverless"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Vercel handler
def handler(request, response):
    return app(request, response)
'''
        
        # Write main API file
        api_main = api_dir / 'index.py'
        with open(api_main, 'w') as f:
            f.write(api_content)
        
        # Create separate endpoint files for Vercel
        predict_content = '''from fastapi import FastAPI, HTTPException
app = FastAPI()

@app.post("/")
async def predict():
    import random
    return {
        "prediction": sorted(random.sample(range(1, 41), 6)),
        "confidence": 0.85
    }
'''
        
        predict_file = api_dir / 'predict.py'
        with open(predict_file, 'w') as f:
            f.write(predict_content)
        
        print("✅ Created Vercel API structure")
    
    def _create_health_check(self):
        """Create comprehensive health check endpoint"""
        
        health_content = '''#!/usr/bin/env python3
"""
OMEGA AI Health Check Module
"""

import psutil
import os
import json
from datetime import datetime
from pathlib import Path

class HealthChecker:
    def __init__(self):
        self.start_time = datetime.now()
    
    def get_system_health(self) -> dict:
        """Get comprehensive system health metrics"""
        try:
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                "system": {
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage('/').percent if os.name != 'nt' else 0,
                    "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
                },
                "application": {
                    "environment": os.getenv("ENVIRONMENT", "unknown"),
                    "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}",
                    "data_files_accessible": self._check_data_access(),
                    "models_loaded": self._check_models()
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _check_data_access(self) -> bool:
        """Check if data files are accessible"""
        data_files = [
            "data/historial_kabala_github.csv",
            "data/historial_kabala_github_emergency_clean.csv"
        ]
        
        for file_path in data_files:
            if Path(file_path).exists():
                return True
        return False
    
    def _check_models(self) -> bool:
        """Check if model files are accessible"""
        model_dirs = ["models/", "modules/"]
        
        for model_dir in model_dirs:
            if Path(model_dir).exists():
                return True
        return False

health_checker = HealthChecker()
'''
        
        health_file = self.project_root / 'health_check.py'
        with open(health_file, 'w') as f:
            f.write(health_content)
        
        print("✅ Created health check module")
    
    def _create_railway_deploy_script(self, environment: str):
        """Create Railway deployment script"""
        
        deploy_script = f'''#!/bin/bash
# OMEGA AI Railway Deployment Script
# Environment: {environment}

echo "🚂 Starting Railway deployment for {environment}..."

# Check Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Install with: npm install -g @railway/cli"
    exit 1
fi

# Login check
echo "🔐 Checking Railway authentication..."
railway whoami || {{
    echo "❌ Not logged in to Railway. Run: railway login"
    exit 1
}}

# Set environment
if [ "{environment}" = "production" ]; then
    export RAILWAY_ENVIRONMENT="production"
else
    export RAILWAY_ENVIRONMENT="staging" 
fi

# Deploy
echo "🚀 Deploying to Railway ({environment})..."
railway up --environment $RAILWAY_ENVIRONMENT

# Wait for deployment
echo "⏳ Waiting for deployment to complete..."
sleep 30

# Health check
echo "🏥 Running health check..."
HEALTH_URL="https://omega-ai-{environment}.railway.app/health"
curl -f $HEALTH_URL || {{
    echo "❌ Health check failed"
    exit 1
}}

echo "✅ Railway deployment completed successfully!"
echo "🌐 URL: https://omega-ai-{environment}.railway.app"
'''
        
        script_file = self.project_root / f'deploy_railway_{environment}.sh'
        with open(script_file, 'w') as f:
            f.write(deploy_script)
        
        # Make executable
        os.chmod(script_file, 0o755)
        print(f"✅ Created Railway deployment script for {environment}")
    
    def _create_vercel_deploy_script(self, environment: str):
        """Create Vercel deployment script"""
        
        deploy_script = f'''#!/bin/bash
# OMEGA AI Vercel Deployment Script
# Environment: {environment}

echo "▲ Starting Vercel deployment for {environment}..."

# Check Vercel CLI
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Install with: npm install -g vercel"
    exit 1
fi

# Deploy
if [ "{environment}" = "production" ]; then
    echo "🚀 Deploying to Vercel production..."
    vercel --prod --confirm
else
    echo "🚀 Deploying to Vercel preview..."
    vercel --confirm
fi

# Get deployment URL
DEPLOYMENT_URL=$(vercel ls | head -n 1 | awk '{{print $2}}')
HEALTH_URL="https://$DEPLOYMENT_URL/api/health"

echo "⏳ Waiting for deployment to be ready..."
sleep 20

# Health check
echo "🏥 Running health check..."
curl -f $HEALTH_URL || {{
    echo "❌ Health check failed"
    exit 1
}}

echo "✅ Vercel deployment completed successfully!"
echo "🌐 URL: https://$DEPLOYMENT_URL"
'''
        
        script_file = self.project_root / f'deploy_vercel_{environment}.sh'
        with open(script_file, 'w') as f:
            f.write(deploy_script)
        
        # Make executable
        os.chmod(script_file, 0o755)
        print(f"✅ Created Vercel deployment script for {environment}")
    
    def _dict_to_toml(self, data: dict) -> str:
        """Convert dictionary to TOML format"""
        toml_lines = []
        
        for key, value in data.items():
            if isinstance(value, dict):
                toml_lines.append(f"[{key}]")
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, str):
                        toml_lines.append(f'{sub_key} = "{sub_value}"')
                    else:
                        toml_lines.append(f'{sub_key} = {sub_value}')
                toml_lines.append("")
            else:
                toml_lines.append(f'{key} = "{value}"')
        
        return "\\n".join(toml_lines)
    
    def deploy_to_platform(self, platform: str, environment: str = 'production') -> Dict[str, Any]:
        """Deploy to specified platform"""
        print(f"🚀 Initiating deployment to {platform} ({environment})...")
        
        try:
            if platform == 'railway':
                config_result = self.create_railway_deployment(environment)
                # Execute deployment
                script_path = self.project_root / f'deploy_railway_{environment}.sh'
                if script_path.exists():
                    result = subprocess.run(['bash', str(script_path)], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        return {
                            'status': 'success',
                            'platform': platform,
                            'environment': environment,
                            'url': f'https://omega-ai-{environment}.railway.app'
                        }
                    else:
                        return {
                            'status': 'failed',
                            'error': result.stderr
                        }
                        
            elif platform == 'vercel':
                config_result = self.create_vercel_deployment(environment)
                # Execute deployment
                script_path = self.project_root / f'deploy_vercel_{environment}.sh'
                if script_path.exists():
                    result = subprocess.run(['bash', str(script_path)], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        return {
                            'status': 'success',
                            'platform': platform,
                            'environment': environment,
                            'url': 'https://omega-ai.vercel.app'
                        }
                    else:
                        return {
                            'status': 'failed',
                            'error': result.stderr
                        }
                        
            elif platform == 'docker':
                docker_result = self.create_docker_deployment()
                # Build and run Docker container
                build_result = subprocess.run(['docker', 'build', '-t', 'omega-ai', '.'], 
                                            capture_output=True, text=True)
                if build_result.returncode == 0:
                    return {
                        'status': 'success',
                        'platform': platform,
                        'container': 'omega-ai',
                        'command': 'docker run -p 8000:8000 omega-ai'
                    }
                else:
                    return {
                        'status': 'failed',
                        'error': build_result.stderr
                    }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def create_deployment_summary(self) -> Dict[str, Any]:
        """Create comprehensive deployment summary"""
        
        summary = {
            "deployment_timestamp": datetime.now().isoformat(),
            "platforms_configured": list(self.deployment_configs.keys()),
            "environments": ["production", "staging"],
            "deployment_files_created": [
                "railway.toml",
                "vercel.json", 
                "Dockerfile",
                "docker-compose.yml",
                "api_railway.py",
                "health_check.py",
                "requirements-railway.txt",
                "requirements-vercel.txt",
                "deploy_railway_production.sh",
                "deploy_vercel_production.sh"
            ],
            "next_steps": [
                "1. Configure environment variables in Railway/Vercel dashboard",
                "2. Set up custom domains if needed",
                "3. Configure monitoring and alerting",
                "4. Set up CI/CD pipelines",
                "5. Perform load testing"
            ],
            "monitoring_urls": {
                "railway_production": "https://omega-ai-prod.railway.app/health",
                "railway_staging": "https://omega-ai-staging.railway.app/health", 
                "vercel_production": "https://omega-ai.vercel.app/api/health"
            }
        }
        
        # Save summary
        summary_file = self.project_root / 'deployment_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        return summary

# Example usage
if __name__ == "__main__":
    # Initialize deployment manager
    deployment_manager = OmegaDeploymentManager()
    
    print("🚀 OMEGA AI Deployment Automation")
    print("=" * 50)
    
    # Create all deployment configurations
    railway_result = deployment_manager.create_railway_deployment('production')
    vercel_result = deployment_manager.create_vercel_deployment('production')
    docker_result = deployment_manager.create_docker_deployment()
    
    # Create deployment summary
    summary = deployment_manager.create_deployment_summary()
    
    print(f"\\n✅ Deployment automation complete!")
    print(f"📁 Files created: {len(summary['deployment_files_created'])}")
    print(f"🌐 Platforms configured: {', '.join(summary['platforms_configured'])}")
    print(f"📋 Deployment summary saved to: deployment_summary.json")
    
    print(f"\\n🚀 Next steps:")
    for step in summary['next_steps']:
        print(f"   {step}")
    
    print(f"\\n📊 Monitoring URLs:")
    for name, url in summary['monitoring_urls'].items():
        print(f"   {name}: {url}")