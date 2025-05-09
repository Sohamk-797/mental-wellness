#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# Start gunicorn
gunicorn mental_wellness.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120 