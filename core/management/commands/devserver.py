import subprocess
from django.core.management.commands.runserver import Command as RunserverCommand

class Command(RunserverCommand):
    def handle(self, *args, **options):
        subprocess.Popen(['celery', '-A', 'MoneyLoop', 'worker', '--loglevel=info'])
        subprocess.Popen(['celery', '-A', 'MoneyLoop', 'beat', '--loglevel=info'])
        super().handle(*args, **options)
