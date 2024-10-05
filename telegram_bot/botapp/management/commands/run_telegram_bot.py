from django.core.management.base import BaseCommand
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters

import logging
from django.conf import settings

from botapp.bot import start, register, feedback_command, help_command, languages_command, discounts_command, delete_me, profile_command, location_handler, text_message_handler, handle_feedback, language_selection, filter_search_handler, specific_filter_handler, command_restriction, button_handler, display_by_brand, display_by_category
from dotenv import load_dotenv
import os

load_dotenv()


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


class Command(BaseCommand):
    help = 'Runs the Telegram bot'

    def handle(self, *args, **kwargs):
        bot_token = os.getenv("TELEGRAM_BOT_API")
        if not bot_token:
            logging.error("TELEGRAM_BOT_TOKEN environment variable not set.")
            return
        app = ApplicationBuilder().token(bot_token).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("register", register))
        app.add_handler(CommandHandler("feedback", feedback_command))  
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("languages", languages_command))
        app.add_handler(CommandHandler("discounts", discounts_command))
        app.add_handler(CommandHandler('delete_me', delete_me))
        app.add_handler(CommandHandler("profile", profile_command))

        app.add_handler(MessageHandler(filters.LOCATION, location_handler))  
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))  
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_feedback))

        app.add_handler(CallbackQueryHandler(button_handler, pattern='^(male|female|other)$'))
        app.add_handler(CallbackQueryHandler(language_selection, pattern='^(az|en|tr|ru)$'))
        app.add_handler(CallbackQueryHandler(filter_search_handler, pattern='^(all|filter|search)$'))
        app.add_handler(CallbackQueryHandler(specific_filter_handler, pattern='^(filter_brand|filter_category)$'))
        app.add_handler(CallbackQueryHandler(display_by_brand, pattern=r'^brand_\d+$'))
        app.add_handler(CallbackQueryHandler(display_by_category, pattern=r'^category_\d+$'))
        app.add_handler(MessageHandler(filters.COMMAND, command_restriction))

        app.run_polling()
