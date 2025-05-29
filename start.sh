#!/usr/bin/env bash
python manage.py collectstatic --noinput
gunicorn moneyloop.wsgi:application --bind 0.0.0.0:$PORT
