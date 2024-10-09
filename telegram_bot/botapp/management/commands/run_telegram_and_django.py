import threading
from django.core.management.base import BaseCommand
import os

class Command(BaseCommand):
    help = 'Runs both Django server and Telegram bot'

    def handle(self, *args, **kwargs):
        def run_django():
            os.system('python manage.py runserver 0.0.0.0:8000')

        def run_bot():
            os.system('python manage.py run_telegram_bot')

        django_thread = threading.Thread(target=run_django)
        django_thread.start()

        run_bot()
