# Railway Dockerfile - Ultra Simple
FROM python:3.11-slim

WORKDIR /app

# Copy files
COPY api_simple.py .
COPY requirements-railway.txt requirements.txt

# Install
RUN pip install -r requirements.txt

# Run
EXPOSE 8000
CMD ["python", "api_simple.py"]