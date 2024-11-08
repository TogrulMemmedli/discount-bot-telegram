from django.core.management.base import BaseCommand
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import logging
from botapp.bot import (start, register, feedback_command, 
                        help_command, languages_command, discounts_command, 
                        delete_me, profile_command, handle_location, 
                        text_message_handler, handle_feedback, language_selection, filter_search_handler,
                        specific_filter_handler, command_restriction, 
                        button_handler, 
                        display_by_brand, display_by_category, 
                        run_async_send_scheduled_messages, save_product,
                        my_saved_products, add_brand_favorite,
                        merchant_role_func, handle_merchant_selection, remove_product,
                        toggle_favorite_category, discount_percentage_options,
                        notification_time, skip_store_recommendation,
                        add_category_favorite, edit_favorite_category,
                        edit_favorite_category_fin, display_by_store,
                        edit_profile_options, edit_user_birthdate, edit_user_location, edit_user_gender,
                        handle_user_response, process_add_product,
                        show_merchant_users, edit_merchant_name, remove_merchant_user,
                        confirm_leave_merchant, cancel_leave_merchant
                        )

from dotenv import load_dotenv
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
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
        app.add_handler(CommandHandler("saved", my_saved_products))
        app.add_handler(CommandHandler('Merchant', merchant_role_func))

        app.add_handler(MessageHandler(filters.LOCATION, handle_location))  
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))  
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_feedback))

        app.add_handler(CallbackQueryHandler(button_handler, pattern='^(male|female|other)$'))
        app.add_handler(CallbackQueryHandler(language_selection, pattern='^(az|en|tr|ru)$'))
        app.add_handler(CallbackQueryHandler(filter_search_handler, pattern='^(all|filter|search|saved|profile)$'))
        app.add_handler(CallbackQueryHandler(specific_filter_handler, pattern='^(filter_brand|filter_category|filter_stores|filter_time|filter_favoritebrands|filter_favoritecategories)$'))
        app.add_handler(CallbackQueryHandler(display_by_brand, pattern=r'^brand_\d+$'))
        app.add_handler(CallbackQueryHandler(display_by_store, pattern=r'^store_\d+$'))
        app.add_handler(CallbackQueryHandler(add_brand_favorite, pattern=r'^favbrand_\d+$'))
        app.add_handler(CallbackQueryHandler(add_category_favorite, pattern=r'^favcategory_\d+$'))
        app.add_handler(CallbackQueryHandler(display_by_category, pattern=r'^category_\d+$'))
        app.add_handler(CallbackQueryHandler(process_add_product, pattern=r'^merchant_brand_\d+$'))
        app.add_handler(CallbackQueryHandler(process_add_product, pattern=r'^merchant_category_\d+$'))
        app.add_handler(CallbackQueryHandler(edit_favorite_category, pattern=r'^category_edit_\d+$'))
        app.add_handler(CallbackQueryHandler(toggle_favorite_category, pattern=r'^fav_category_\d+$'))
        app.add_handler(CallbackQueryHandler(edit_favorite_category_fin, pattern=r'^favorite_category_edit_\d+$'))
        app.add_handler(CallbackQueryHandler(save_product, pattern=r'^save_\d+$'))
        app.add_handler(CallbackQueryHandler(remove_product, pattern=r'^remove_merchant_product_\d+$'))
        app.add_handler(CallbackQueryHandler(remove_merchant_user, pattern=r'^remove_merchant_\d+$'))
        app.add_handler(CallbackQueryHandler(discount_percentage_options, pattern=r'^discount_percentage_\d+_\d+$'))
        app.add_handler(CallbackQueryHandler(notification_time, pattern=r'^notification_time_\d+_\d+$'))
        app.add_handler(CallbackQueryHandler(skip_store_recommendation, pattern='skip_store_recommendation'))
        
        app.add_handler(CallbackQueryHandler(edit_profile_options, pattern='^(edit_profile)$'))
        app.add_handler(CallbackQueryHandler(edit_user_birthdate, pattern='^(edit_user_birthdate)$'))
        app.add_handler(CallbackQueryHandler(edit_user_location, pattern='^(edit_user_location)$'))
        app.add_handler(CallbackQueryHandler(edit_user_gender, pattern='^(edit_user_gender)$'))

        app.add_handler(CallbackQueryHandler(handle_user_response, pattern='^(gender_male)$'))
        app.add_handler(CallbackQueryHandler(handle_user_response, pattern='^(gender_female)$'))
        app.add_handler(CallbackQueryHandler(handle_user_response, pattern='^(gender_other)$'))

        app.add_handler(CallbackQueryHandler(handle_merchant_selection, pattern='^(edit_merchant)$'))
        app.add_handler(CallbackQueryHandler(handle_merchant_selection, pattern='^(leave_merchant)$'))
        app.add_handler(CallbackQueryHandler(handle_merchant_selection, pattern='^(add_product)$'))
        app.add_handler(CallbackQueryHandler(handle_merchant_selection, pattern='^(all_products)$'))
        
        app.add_handler(CallbackQueryHandler(show_merchant_users, pattern='^(show_merchant_users)$'))
        app.add_handler(CallbackQueryHandler(edit_merchant_name, pattern='^(edit_merchant_name)$'))
        app.add_handler(CallbackQueryHandler(confirm_leave_merchant, pattern='^(confirm_leave_merchant)$'))
        app.add_handler(CallbackQueryHandler(cancel_leave_merchant, pattern='^(cancel_leave_merchant)$'))
        app.add_handler(MessageHandler(filters.COMMAND, command_restriction))

        current_time = datetime.now()
        scheduled_time = current_time + timedelta(minutes=1)

        scheduler = BackgroundScheduler()
        scheduler.add_job(
            run_async_send_scheduled_messages,
            trigger=CronTrigger(hour=21, minute=25),
            args=[app],
            name='send_scheduled_messages',
            replace_existing=True
        )
        
        scheduler.start()
        try:
            logging.info("Bot started...")
            app.run_polling()
        except KeyboardInterrupt:
            logging.info("Bot stopped...")
        finally:
            scheduler.shutdown()