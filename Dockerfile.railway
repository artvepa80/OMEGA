# Dockerfile optimizado para Railway
FROM python:3.9-slim

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements (ya optimizado)
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Crear directorios necesarios
RUN mkdir -p logs data export model checkpoints results

# Railway maneja healthcheck automáticamente
# HEALTHCHECK removido temporalmente

# Exponer puerto (Railway asigna automáticamente)
EXPOSE $PORT

# Comando ultra-simple que funciona garantizado
CMD python3 api_simple.py
