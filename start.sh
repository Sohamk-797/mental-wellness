#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Apply database migrations
echo "Running migrations..."
python manage.py makemigrations auth
python manage.py makemigrations sessions
python manage.py makemigrations admin
python manage.py makemigrations chatbot
python manage.py migrate auth
python manage.py migrate sessions
python manage.py migrate admin
python manage.py migrate chatbot
python manage.py migrate

# Load breathing exercises
echo "Loading breathing exercises..."
python manage.py load_breathing_exercises

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input

# Create superuser if it doesn't exist
echo "Creating superuser..."
DJANGO_SUPERUSER_USERNAME=admin2 \
DJANGO_SUPERUSER_EMAIL=admin2@example.com \
DJANGO_SUPERUSER_PASSWORD=Admin@123 \
python manage.py createsuperuser --noinput || true

# Start gunicorn with the correct WSGI application
echo "Starting gunicorn..."
exec gunicorn mental_wellness.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 1 \
    --threads 1 \
    --timeout 120 \
    --max-requests 1 \
    --max-requests-jitter 0 \
    --log-level debug 