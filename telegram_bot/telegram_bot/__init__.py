# telegram_bot/telegram_bot/__init__.py
import threading
from django.core.management import call_command

def start_bot():
    try:
        call_command('run_telegram_bot')
    except Exception as e:
        print(f"Failed to start bot: {e}")

def start():
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.daemon = True
    bot_thread.start()
