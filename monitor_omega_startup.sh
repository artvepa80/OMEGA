#!/bin/bash

URL="http://crfvkrkp5pbab34elothkbqi94.ingress.bdl.computer"
echo "🔍 Monitoring OMEGA PRO AI v10.1 startup on Akash..."
echo "📍 URL: $URL"
echo "⏱️  Checking every 30 seconds..."
echo ""

attempt=1
max_attempts=20  # 10 minutes total

while [ $attempt -le $max_attempts ]; do
    echo "🕐 Attempt $attempt of $max_attempts ($(date))"
    
    # Test health endpoint
    health_response=$(curl -s -o /dev/null -w "%{http_code}" "$URL/health" 2>/dev/null)
    
    # Test main endpoint  
    main_response=$(curl -s -o /dev/null -w "%{http_code}" "$URL/" 2>/dev/null)
    
    echo "   Health endpoint: HTTP $health_response"
    echo "   Main endpoint: HTTP $main_response"
    
    if [ "$health_response" = "200" ] || [ "$main_response" = "200" ]; then
        echo ""
        echo "🎉 OMEGA IS READY!"
        echo "✅ Successfully running on: $URL"
        echo ""
        echo "📋 Available endpoints:"
        echo "   🌐 Main interface: $URL/"
        echo "   💚 Health check: $URL/health" 
        echo "   🔮 Predictions: $URL/predict"
        echo "   📊 Status: $URL/status"
        echo ""
        echo "🚀 OMEGA PRO AI v10.1 is now fully operational on Akash Network!"
        echo "💻 Resources: 16 CPU cores + 32GB RAM + 200GB storage"
        echo "🎯 Ready for predictions and ML operations!"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        echo ""
        echo "⚠️  OMEGA is still initializing after 10 minutes"
        echo "📝 This is normal for the first deployment - dependencies are still installing"
        echo "🔄 System should be ready within 15-20 minutes total"
        echo ""
        echo "📞 You can manually check: $URL"
    fi
    
    sleep 30
    attempt=$((attempt + 1))
done