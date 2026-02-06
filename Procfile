release: python3 manage.py migrate --noinput && python3 manage.py collectstatic --noinput
web: gunicorn land_sale.wsgi:application --bind 0.0.0.0:8080 --workers 4 --threads 2 --worker-class gthread --timeout 120 --max-requests 1000 --max-requests-jitter 50 --access-logfile - --error-logfile - --log-level info --preload
