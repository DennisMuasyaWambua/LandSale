#!/bin/bash
# Startup script for Digital Ocean deployment
# Make executable with: chmod +x start_server.sh

set -e  # Exit on error

echo "=== Land Sale API - Production Startup ==="

# Set environment variables (override as needed)
export PORT=${PORT:-8080}
export DJANGO_SETTINGS_MODULE=land_sale.settings
export GUNICORN_WORKERS=${GUNICORN_WORKERS:-4}
export GUNICORN_THREADS=${GUNICORN_THREADS:-2}

# Run migrations
echo "Running database migrations..."
python3 manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python3 manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting Gunicorn on port $PORT with $GUNICORN_WORKERS workers..."

# Option 1: Using gunicorn.conf.py (recommended)
exec gunicorn land_sale.wsgi:application -c gunicorn.conf.py

# Option 2: Inline configuration (uncomment to use instead)
# exec gunicorn land_sale.wsgi:application \
#     --bind 0.0.0.0:$PORT \
#     --workers $GUNICORN_WORKERS \
#     --threads $GUNICORN_THREADS \
#     --worker-class gthread \
#     --timeout 120 \
#     --max-requests 1000 \
#     --max-requests-jitter 50 \
#     --access-logfile - \
#     --error-logfile - \
#     --log-level info \
#     --preload
