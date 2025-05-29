# celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab  # Needed if using app.conf.beat_schedule
from django.conf import settings

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MoneyLoop.settings')

app = Celery('MoneyLoop')

# Optional: disable UTC and use Django timezone
app.conf.enable_utc = False
app.conf.update(timezone=settings.TIME_ZONE)

# Load custom config from Django settings with CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks in all installed apps
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'process-monthly-payouts': {
        'task': 'core.tasks.process_monthly_payouts',
        'schedule': crontab(day_of_month='1', hour=6, minute=0),
        'options': {'expires': 60 * 60 * 24}
    },
    'send-daily-notifications': {
        'task': 'core.tasks.send_daily_notifications',
        'schedule': crontab(hour=9, minute=0),
    },
    'dummy_task': {
        'task': 'core.tasks.dummy_task',
        'schedule': crontab(minute='*'),  # every minute
    }
}


# Debugging task
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
