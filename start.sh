#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# Load breathing exercises
python manage.py load_breathing_exercises

# Create superuser
export DJANGO_SUPERUSER_USERNAME=admin2
export DJANGO_SUPERUSER_EMAIL=admin2@example.com
export DJANGO_SUPERUSER_PASSWORD=Admin@123
python manage.py createsuperuser --noinput

# Set default port if not provided
if [ -z "$PORT" ]; then
    PORT=8000
fi

# Validate port is a number
if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
    echo "Error: PORT must be a number"
    exit 1
fi

# Start gunicorn with the correct WSGI application
exec gunicorn mental_wellness.wsgi:application \
    --bind "0.0.0.0:${PORT}" \
    --workers 1 \
    --threads 2 \
    --timeout 120 \
    --max-requests 1000 \
    --max-requests-jitter 50 