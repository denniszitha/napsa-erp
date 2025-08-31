# FastAPI Backend Dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir uvicorn[standard] && \
    pip install --no-cache-dir pydantic-settings

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/uploads /app/logs /app/static

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port (internal container port)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

# Run with uvicorn for production
CMD ["uvicorn", "app.main_live:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--log-level", "info", "--access-log", "--proxy-headers", "--forwarded-allow-ips", "*"]