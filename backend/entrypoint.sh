#!/bin/sh

chown -R nginx:nginx /app/backend_static

echo 'Applying migrations'

python manage.py migrate

echo 'Collecting static'

python manage.py collectstatic --noinput

exec '$@'
