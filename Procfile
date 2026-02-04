release: python manage.py collectstatic --noinput
web: gunicorn land_sale.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120
