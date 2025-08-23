#!/usr/bin/env python3
"""
OMEGA API - Versión ultra-minimal para Railway
"""
import os

print("🚀 OMEGA API Starting...")

try:
    from fastapi import FastAPI
    print("✅ FastAPI imported")
except ImportError as e:
    print(f"❌ FastAPI import failed: {e}")
    exit(1)

try:
    import uvicorn
    print("✅ uvicorn imported")
except ImportError as e:
    print(f"❌ uvicorn import failed: {e}")
    exit(1)

# Get port
PORT = int(os.environ.get("PORT", 8000))
print(f"🌐 Using PORT: {PORT}")

# Create app
app = FastAPI(title="OMEGA Minimal")
print("✅ FastAPI app created")

@app.get("/")
def root():
    return {"status": "OMEGA API Working", "port": PORT}

@app.get("/health") 
def health():
    return {"status": "healthy"}

@app.post("/predictions")
def predictions():
    return {
        "predictions": [
            {"combination": [8,15,18,19,35,37], "score": 0.947},
            {"combination": [3,23,28,31,35,37], "score": 0.931}
        ]
    }

print("✅ Routes defined")

if __name__ == "__main__":
    print(f"🚀 Starting server on 0.0.0.0:{PORT}")
    
    try:
        uvicorn.run(
            "minimal_api:app",
            host="0.0.0.0", 
            port=PORT,
            log_level="debug"
        )
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        exit(1)