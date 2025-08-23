#!/bin/bash
# OMEGA PRO AI Deployment Script

set -e

echo "🚀 OMEGA PRO AI Deployment Script v4.0"
echo "======================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
mkdir -p data logs checkpoints ssl

echo "📋 Deployment Options:"
echo "1. Full Stack (API + Sports + Asian + Monitoring)"
echo "2. API Only"
echo "3. Asian Markets Only"
echo "4. Development Mode"

read -p "Select deployment option (1-4): " option

case $option in
    1)
        echo "🚀 Deploying Full Stack..."
        docker-compose -f deploy/docker-compose.yml up -d
        ;;
    2)
        echo "🚀 Deploying API Only..."
        docker-compose -f deploy/docker-compose.yml up -d omega-api redis postgres
        ;;
    3)
        echo "🚀 Deploying Asian Markets Only..."
        docker-compose -f deploy/docker-compose.asian.yml up -d
        ;;
    4)
        echo "🚀 Starting Development Mode..."
        docker-compose -f deploy/docker-compose.yml -f deploy/docker-compose.dev.yml up -d
        ;;
    *)
        echo "❌ Invalid option selected."
        exit 1
        ;;
esac

echo "⏳ Waiting for services to start..."
sleep 30

# Health check
echo "🔍 Performing health checks..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Main API is healthy"
else
    echo "❌ Main API health check failed"
fi

if [ "$option" = "1" ] || [ "$option" = "3" ]; then
    if curl -f http://localhost:8001/health > /dev/null 2>&1; then
        echo "✅ Asian Markets API is healthy"
    else
        echo "❌ Asian Markets API health check failed"
    fi
fi

echo "🎉 Deployment complete!"
echo ""
echo "📊 Service URLs:"
echo "  - Main API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Health: http://localhost:8000/health"

if [ "$option" = "1" ]; then
    echo "  - Asian Markets: http://localhost:8001"
    echo "  - Grafana: http://localhost:3000 (admin/admin123)"
    echo "  - Prometheus: http://localhost:9090"
fi

echo ""
echo "📝 Next steps:"
echo "  1. Configure your .env file with API keys"
echo "  2. Test the APIs using the documentation"
echo "  3. Monitor logs: docker-compose logs -f"
echo ""
echo "🔧 Management commands:"
echo "  - Stop: docker-compose down"
echo "  - Restart: docker-compose restart"
echo "  - Logs: docker-compose logs -f [service]"
echo "  - Update: docker-compose pull && docker-compose up -d"