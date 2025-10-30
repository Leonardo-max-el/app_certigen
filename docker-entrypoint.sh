#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Creating admin..."
python manage.py create_admin

echo "Starting Gunicorn..."
exec gunicorn Admin_Upla.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --timeout 120 \
    --workers 2 \
    --log-level info \
    --access-logfile - \
    --error-logfile -