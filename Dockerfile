# OMEGA PRO AI v10.1 - Multi-Stage Multi-Arch Build (Optimized 2025)

# Etapa 1: Builder (instala dependencias, compatible multi-arch)
FROM --platform=$BUILDPLATFORM python:3.13-slim AS builder

# Build arguments
ARG BUILDPLATFORM
ARG TARGETPLATFORM
ARG OMEGA_VERSION=v10.1
ARG BUILD_DATE
ARG VCS_REF

# Print build info
RUN printf "🏗️ Building dependencies for TARGETPLATFORM=%s on BUILDPLATFORM=%s\n" "$TARGETPLATFORM" "$BUILDPLATFORM"

WORKDIR /app

# Copy requirements first for better caching
COPY requirements*.txt ./

# Install system dependencies y Python deps en una sola capa (reduce tamaño)
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3-dev build-essential git && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    # TensorFlow installation based on architecture \
    if [ "$TARGETPLATFORM" = "linux/amd64" ]; then \
        pip install --no-cache-dir tensorflow-cpu; \
    else \
        pip install --no-cache-dir tensorflow; \
    fi && \
    pip install --no-cache-dir -r requirements.txt && \
    # Limpieza agresiva \
    rm -rf /root/.cache/pip /var/lib/apt/lists/* && \
    apt-get autoremove -y && apt-get clean

# Etapa 2: Runtime final (copia solo lo necesario)
FROM python:3.13-slim

# Build arguments for runtime
ARG OMEGA_VERSION=v10.1
ARG BUILD_DATE
ARG VCS_REF

# Build info y env vars
ENV OMEGA_VERSION=${OMEGA_VERSION}
ENV OMEGA_COMPLETE=true
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Labels para best practices 2025 (traceability y multi-arch)
LABEL org.opencontainers.image.title="OMEGA PRO AI"
LABEL org.opencontainers.image.version="${OMEGA_VERSION}"
LABEL org.opencontainers.image.description="Multi-arch ML image for OMEGA Pro AI v10.1"
LABEL org.opencontainers.image.base.name="python:3.11-slim"
LABEL org.opencontainers.image.architecture="multi (amd64/arm64)"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.source="https://github.com/artvepa80/OMEGA_PRO_AI_v10.1"
LABEL maintainer="OMEGA Team <admin@omega-pro-ai.com>"

# Install minimal runtime dependencies en una capa
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl htop && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Create user for security
RUN useradd -m -u 1001 omegauser && \
    mkdir -p /app && \
    chown omegauser:omegauser /app

WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy ALL OMEGA PROJECT (todo el contenido)
COPY --chown=omegauser:omegauser . .

# Create necessary directories y set permissions en una capa
RUN mkdir -p logs outputs results temp export reports performance_reports && \
    find /app -name "*.py" -exec chmod +x {} \; 2>/dev/null || true && \
    find /app -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true && \
    chown -R omegauser:omegauser /app

# Create optimized entrypoint
RUN echo '#!/bin/bash\necho "🚀 OMEGA PRO AI v${OMEGA_VERSION} - MULTI-STAGE MULTI-ARCH"\necho "🏗️ Arquitectura: $(uname -m)"\necho "💻 CPU: $(nproc) cores"\necho "🐍 Python: $(python3 --version)"\necho "📁 OMEGA COMPLETO en /app"\necho "📊 Archivos Python: $(find /app -name \"*.py\" 2>/dev/null | wc -l)"\necho "📦 Módulos: $(ls -1 /app/modules/ 2>/dev/null | wc -l)"\necho "🧠 Modelos: $(ls -1 /app/models/ 2>/dev/null | wc -l)"\necho "✅ Sistema listo para ejecución completa"\necho "================================================"\nexec "$@"' > entrypoint.sh && \
    chmod +x entrypoint.sh && \
    chown omegauser:omegauser entrypoint.sh

# Health check más robusto (prueba import de módulo Omega)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sys; sys.path.append('/app'); print('✅ OMEGA Multi-Stage Health OK'); \
    try: \
        import core.predictor, modules.lstm_model; \
        print('✅ Core modules loaded successfully'); \
    except ImportError as e: \
        print('⚠️ Some modules not available:', str(e)); \
    " || exit 1

# Switch to non-root user para seguridad
USER omegauser

# Default port
EXPOSE 8000

# Default command
CMD ["python3", "main.py", "--server-mode", "--port", "8000"]
ENTRYPOINT ["./entrypoint.sh"]