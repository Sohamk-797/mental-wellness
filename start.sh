#!/usr/bin/env bash
set -x
# exit on error
set -o errexit

# Print Python version and environment
echo "Python version:"
python --version
echo "Python path:"
python -c "import sys; print('\n'.join(sys.path))"
echo "Environment variables:"
env

# Install dependencies
echo "Installing dependencies..."
pip install --no-cache-dir -r requirements.txt

# Apply database migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start gunicorn with the correct WSGI application
echo "Starting gunicorn..."
exec gunicorn mental_wellness.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --threads 2 \
    --timeout 120 \
    --log-level debug 