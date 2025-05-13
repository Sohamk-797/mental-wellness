FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV TRANSFORMERS_CACHE=/tmp/transformers_cache
ENV HF_HOME=/tmp/huggingface
ENV HF_DATASETS_CACHE=/tmp/huggingface/datasets
ENV HF_METRICS_CACHE=/tmp/huggingface/metrics
ENV HF_MODULES_CACHE=/tmp/huggingface/modules
ENV PYTORCH_NO_CUDA=1
ENV TRANSFORMERS_OFFLINE=1
ENV PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128

# Create cache directories
RUN mkdir -p /tmp/transformers_cache /tmp/huggingface/datasets /tmp/huggingface/metrics /tmp/huggingface/modules

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV TRANSFORMERS_CACHE=/tmp/transformers_cache
ENV HF_HOME=/tmp/huggingface
ENV HF_DATASETS_CACHE=/tmp/huggingface/datasets
ENV HF_METRICS_CACHE=/tmp/huggingface/metrics
ENV HF_MODULES_CACHE=/tmp/huggingface/modules
ENV PYTORCH_NO_CUDA=1
ENV TRANSFORMERS_OFFLINE=1
ENV PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128

# Create cache directories
RUN mkdir -p /tmp/transformers_cache /tmp/huggingface/datasets /tmp/huggingface/metrics /tmp/huggingface/modules

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy application code
COPY . .

# Create startup script
RUN echo '#!/bin/bash\n\
python manage.py migrate\n\
python manage.py load_breathing_exercises\n\
python manage.py collectstatic --noinput\n\
DJANGO_SUPERUSER_USERNAME=admin2 DJANGO_SUPERUSER_EMAIL=admin2@example.com DJANGO_SUPERUSER_PASSWORD=Admin@123 python manage.py createsuperuser --noinput\n\
exec gunicorn mental_wellness.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 1 \
    --threads 1 \
    --timeout 120 \
    --max-requests 1 \
    --max-requests-jitter 0' > /app/start.sh && \
    chmod +x /app/start.sh

# Use the startup script
CMD ["/app/start.sh"] 