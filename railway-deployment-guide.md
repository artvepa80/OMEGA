# 🚂 OMEGA Railway Deployment Guide

## Pre-deployment Checklist

### 1. Essential Files
- [ ] `requirements.txt` with all dependencies
- [ ] `Procfile` for Railway startup command
- [ ] `.gitignore` excluding large files
- [ ] Environment variables configured

### 2. Recommended Railway Configuration

```bash
# Procfile
web: gunicorn app:app --bind 0.0.0.0:$PORT

# or for Flask app
web: python main.py
```

### 3. Environment Variables to Set in Railway
```bash
PYTHONPATH=/app
OMEGA_ENV=production
PORT=8000
```

### 4. Memory Optimization
```python
# Add to main script
import os
import gc

# Force garbage collection
gc.collect()

# Limit memory usage for models
os.environ['OMP_NUM_THREADS'] = '2'
```

### 5. Large Files Strategy
Since Railway has size limits:
- Move large CSV files to Railway volumes or external storage
- Use compressed models (.pkl.gz instead of .pkl)
- Implement lazy loading for heavy components

### 6. API Endpoint Structure
```python
from flask import Flask, jsonify, request
from omega_integrated_system import run_omega_integrated_system

app = Flask(__name__)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get parameters from request
        n_predictions = request.json.get('n_predictions', 8)
        
        # Run OMEGA with optimal weights
        system = run_omega_integrated_system(
            historical_path="data/historial_kabala_github_emergency_clean.csv",
            jackpot_path="data/jackpots_omega.csv", 
            n_predictions=n_predictions
        )
        
        return jsonify({
            'predictions': system.final_predictions,
            'confidence': system.system_confidence,
            'weights_used': 'OMEGA_OPTIMAL_WEIGHTS'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
```

### 7. Performance Tips for Railway
- Use Railway's built-in caching
- Implement request rate limiting
- Add health check endpoint
- Monitor memory usage

### 8. Post-deployment Testing
```bash
# Test API endpoint
curl -X POST https://your-app.railway.app/predict \
  -H "Content-Type: application/json" \
  -d '{"n_predictions": 5}'
```