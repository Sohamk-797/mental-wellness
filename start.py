import os
import subprocess
import sys

def main():
    # Run migrations
    subprocess.run([sys.executable, 'manage.py', 'migrate'], check=True)
    
    # Load breathing exercises
    subprocess.run([sys.executable, 'manage.py', 'load_breathing_exercises'], check=True)
    
    # Collect static files
    subprocess.run([sys.executable, 'manage.py', 'collectstatic', '--noinput'], check=True)
    
    # Create superuser
    os.environ['DJANGO_SUPERUSER_USERNAME'] = 'admin2'
    os.environ['DJANGO_SUPERUSER_EMAIL'] = 'admin2@example.com'
    os.environ['DJANGO_SUPERUSER_PASSWORD'] = 'Admin@123'
    subprocess.run([sys.executable, 'manage.py', 'createsuperuser', '--noinput'], check=True)
    
    # Get port from environment variable or use default
    port = os.getenv('PORT', '8000')
    
    # Start Gunicorn
    gunicorn_cmd = [
        'gunicorn',
        'mental_wellness.wsgi:application',
        f'--bind=0.0.0.0:{port}',
        '--workers=1',
        '--threads=2',
        '--timeout=120',
        '--max-requests=1000',
        '--max-requests-jitter=50'
    ]
    
    os.execvp('gunicorn', gunicorn_cmd)

if __name__ == '__main__':
    main() 