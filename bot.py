import os
from dotenv import load_dotenv
import logging
import psycopg2

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext

from datetime import datetime
from decimal import Decimal

# Konfiqurasiyalar
load_dotenv()
def connect_db():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DATABASE_HOST"),
            database=os.getenv("DATABASE_NAME"),
            user=os.getenv("DATABASE_USER"),
            password=os.getenv("DATABASE_PASS"),
        )
        print("Connected to Database")
        return conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        return None
logging.basicConfig(level=logging.INFO)

# Dil
languages = {
    'en': {
        'greeting': "Hello, {name}! Welcome to the bot.",
        'ask_birthday': "Please enter your birthday in the format YYYY-MM-DD:",
        'ask_gender': "Please select your gender:",
        'registration_success': "Registration successful! You can now use other commands.",
        'error_invalid_birthday': "Invalid date format. Please enter your birthday as YYYY-MM-DD.",
        'not_registered': "You are not registered. Please use /register to register.",
        'already_register': "You are already registered."
    },
    'tr': {
        'greeting': "Merhaba, {name}! Bota hoş geldiniz.",
        'ask_birthday': "Lütfen doğum tarihinizi YYYY-AA-GG formatında girin:",
        'ask_gender': "Lütfen cinsiyetinizi seçin:",
        'registration_success': "Kayıt başarılı! Artık diğer komutları kullanabilirsiniz.",
        'error_invalid_birthday': "Geçersiz tarih formatı. Lütfen doğum tarihinizi YYYY-AA-GG olarak girin.",
        'not_registered': "Kayıtlı değilsiniz. Lütfen kayıt olmak için /register kullanın.",
                'already_register': "Siz zaten kayıtlısınız"

    },
    'az': {
        'greeting': "Salam, {name}! Bota xoş gəlmisiniz.",
        'ask_birthday': "Zəhmət olmasa doğum tarixinizi YYYY-AA-GG formatında daxil edin:",
        'ask_gender': "Zəhmət olmasa cinsiyyətinizi seçin:",
        'registration_success': "Qeydiyyat uğurla tamamlandı! İndi digər komandaları istifadə edə bilərsiniz.",
        'error_invalid_birthday': "Yanlış tarix formatı. Zəhmət olmasa doğum tarixinizi YYYY-AA-GG kimi daxil edin.",
        'not_registered': "Siz qeydiyyatdan keçməmisiniz. Zəhmət olmasa qeydiyyatdan keçmək üçün /register istifadə edin.",
        'already_register': "Siz artıq qeydiyyatdasınız."

    },
    'ru': {
        'greeting': "Здравствуйте, {name}! Добро пожаловать в бот.",
        'ask_birthday': "Пожалуйста, введите свою дату рождения в формате ГГГГ-ММ-ДД:",
        'ask_gender': "Пожалуйста, выберите ваш пол:",
        'registration_success': "Регистрация прошла успешно! Теперь вы можете использовать другие команды.",
        'error_invalid_birthday': "Неверный формат даты. Пожалуйста, введите дату рождения в формате ГГГГ-ММ-ДД.",
        'not_registered': "Вы не зарегистрированы. Пожалуйста, используйте /register для регистрации.",
        "already_register": "Вы уже зарегистрированы."
    }
}

# Databaza queryləri
def fetch_all_discounted_products():
    print("Fetch all discount products")
    try:
        conn = connect_db()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM discounted_products WHERE end_date >= %s", (datetime.now(),))
        products = cursor.fetchall()
        conn.close()
        return products
    except psycopg2.Error as e:
        logging.error(f"Error fetching products: {e}")
        return []

def fetch_all_brands():
    print("Fetch brands")
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, brand_name FROM brands")
    brands = cursor.fetchall()
    conn.close()
    return brands

def fetch_all_categories():
    print("Fetch categories")
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, category_name FROM categories")
    categories = cursor.fetchall()
    conn.close()
    return categories

def fetch_products_by_brand(brand_id):
    print("FILTER BY BRANDS FETCH")
    logging.info(f"Fetching products for brand: {brand_id}")
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""SELECT * FROM discounted_products WHERE brand_id = %s AND end_date >= %s""",
                   (brand_id, datetime.now()))
    products = cursor.fetchall()
    conn.close()
    logging.info(f"Products found: {products}")
    return products

def fetch_products_by_category(category_id):
    print("FILTER BY CATEGORY FETCH")
    logging.info(f"Fetching products for category: {category_id}")
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""SELECT * FROM discounted_products WHERE category_id = %s AND end_date >= %s""",
                   (category_id, datetime.now()))
    products = cursor.fetchall()
    conn.close()
    logging.info(f"Products found: {products}")
    return products

def is_user_registered(user_id):
    print("IS USER REGISTERED")
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def store_user_data(user_id, username, first_name, last_name, birthday, gender):
    print("STORE USER DATA")
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (telegram_id, username, first_name, last_name, birthday, gender)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (user_id, username, first_name, last_name, birthday, gender))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error storing user data: {e}")
        return False
    return True

def fetch_products_by_search(search_query: str):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, description, url, image_url, normal_price, discount_percentage
            FROM discounted_products
            WHERE (LOWER(title) LIKE LOWER(%s) OR LOWER(description) LIKE LOWER(%s)) AND end_date >= %s
        """, (f"%{search_query}%", f"%{search_query}%", datetime.now()))
        products = cursor.fetchall()
        conn.close()
        return products
    except Exception as e:
        logging.error(f"Error fetching products by search: {e}")
        return []
    
# /start komandası
async def start(update: Update, context):
    print("START")
    user = update.effective_user
    language = context.user_data.get('language', 'en')
    await update.message.reply_text(languages[language]["greeting"].format(name=user.first_name))

async def register(update: Update, context):
    print("REGISTER")
    user = update.effective_user
    language = context.user_data.get('language', 'en')

    if is_user_registered(user.id):
        await update.message.reply_text(languages[language]['already_register'])
        return

    await update.message.reply_text(languages[language]["ask_birthday"])
    context.user_data['step'] = 'ask_birthday'


async def ask_birthday(update: Update, context):
    print("ASK BIRTHDAY")
    language = context.user_data.get('language', 'en')

    if context.user_data.get('step') == 'ask_birthday':
        try:
            birthday = update.message.text
            datetime.strptime(birthday, '%Y-%m-%d') 
            context.user_data['birthday'] = birthday

            keyboard = [
                [InlineKeyboardButton("Male", callback_data='male')],
                [InlineKeyboardButton("Female", callback_data='female')],
                [InlineKeyboardButton("Other", callback_data='other')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(languages[language]["ask_gender"], reply_markup=reply_markup)
            context.user_data['step'] = 'ask_gender'  
        except ValueError:
            await update.message.reply_text(languages[language]["error_invalid_birthday"])


async def button_handler(update: Update, context):
    print("Button Handler")
    query = update.callback_query
    gender = query.data
    user = query.from_user
    language = context.user_data.get('language', 'en')

    if context.user_data.get('step') == 'ask_gender':
        success = store_user_data(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            birthday=context.user_data.get('birthday'),
            gender=gender
        )

        if success:
            await query.edit_message_text(languages[language]["registration_success"])
        else:
            await query.edit_message_text("An error occurred while saving your data. Please try again later.")

        context.user_data.clear()  



# /help komandası
async def help_command(update: Update, context):
    print("HELP COMMAND")
    user = update.effective_user
    language = context.user_data.get('language', 'en')

    if is_user_registered(user.id):
        available_commands = "/start - Greet the user\n" \
                             "/register - Register if you haven't\n" \
                             "/discounts - Show available discounts\n" \
                             "/languages - Switch language\n"
        await update.message.reply_text(f"Here are the available commands:\n{available_commands}")
    else:
        await update.message.reply_text(f"You are not registered. You can't use /help without registration. Please use /register to register.")

# /languages komandası
async def languages_command(update: Update, context):
    print("LANGUAGE COMMAND")
    keyboard = [
        [InlineKeyboardButton("🇦🇿 Azerbaijani", callback_data='az')],
        [InlineKeyboardButton("🇬🇧 English", callback_data='en')],
        [InlineKeyboardButton("🇹🇷 Turkish", callback_data='tr')],
        [InlineKeyboardButton("🇷🇺 Russian", callback_data='ru')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("Please select your language:", reply_markup=reply_markup)

async def language_selection(update: Update, context):
    print("LANGUAGE SELECTION")
    query = update.callback_query
    selected_language = query.data

    context.user_data['language'] = selected_language

    languages_change_message = {
        'en': "Language changed to English.",
        'tr': "Dil Türkçe olarak değiştirildi.",
        'az': "Dil Azərbaycan dilinə dəyişdirildi.",
        'ru': "Язык изменен на русский."
    }
    await query.edit_message_text(text=languages_change_message[selected_language])

# /discounts komandası
async def discounts_command(update: Update, context):
    print("DISCOUNT COMMAND")
    user = update.effective_user
    language = context.user_data.get('language', 'en')

    if not is_user_registered(user.id):
        await update.message.reply_text(languages[language]["not_registered"])
        return

    keyboard = [
        [InlineKeyboardButton("All Discounted Products", callback_data='all')],
        [InlineKeyboardButton("Filter Discounts", callback_data='filter')],
        [InlineKeyboardButton("Search", callback_data='search')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose an option:", reply_markup=reply_markup)

def is_valid_url(url):
    print("IS VALID URL")
    return url.startswith('http://') or url.startswith('https://')

async def filter_search_handler(update: Update, context):
    print("Filter Search Handler")
    query = update.callback_query
    choice = query.data
    language = context.user_data.get('language', 'en')
    
    if choice == 'all':
        products = fetch_all_discounted_products()
        if not products:
            await query.message.reply_text("No discounted products found.")
        else:
            for product in products:
                photo_url = product[4]
                if is_valid_url(photo_url):
                    try:
                        price = Decimal(product[5])
                        discount = Decimal(product[6])
                        discounted_price = round(price * (Decimal(100) - discount) / Decimal(100), 2)
                        caption = (
                            f"Title: {product[1]}\n"
                            f"Description: {product[2]}\n"
                            f"Price: {discounted_price} ₼\n"
                            f"Discount: {discount}%\n"
                            f"Link: {product[3]}"
                        )
                        await query.message.reply_photo(photo=photo_url, caption=caption)
                    except Exception as e:
                        logging.error(f"Failed to send photo for product {product[0]}: {e}")
                else:
                    logging.error(f"Invalid photo URL: {photo_url}")
    
    
    elif choice == 'filter':
        keyboard = [
            [InlineKeyboardButton("Filter by Brand", callback_data='filter_brand')],
            [InlineKeyboardButton("Filter by Category", callback_data='filter_category')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Select filter type:", reply_markup=reply_markup)

    elif choice == 'filter_brand':
        brands = fetch_all_brands()
        keyboard = [
            [InlineKeyboardButton(brand[1], callback_data=f'brand_{brand[0]}')] for brand in brands
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Select a brand:", reply_markup=reply_markup)

    elif choice == 'filter_category':
        categories = fetch_all_categories()
        keyboard = [
            [InlineKeyboardButton(category[1], callback_data=f'category_{category[0]}')] for category in categories
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Select a category:", reply_markup=reply_markup)

    elif choice == 'search':
        print("SEARCH")
        await query.message.reply_text("Please enter the product name to search for:")
        context.user_data['search_step'] = True
        return

async def specific_filter_handler(update: Update, context):
    print("Specific Filter Handler")
    query = update.callback_query
    data = query.data.split('_', 1)
    
    if len(data) != 2:
        await query.message.reply_text("Invalid filter selection.")
        return
    
    filter_type = data[0]
    value = data[1]

    if filter_type == 'brand':
        products = fetch_products_by_brand(value)
    elif filter_type == 'category':
        products = fetch_products_by_category(value)
    else:
        await query.message.reply_text("Unknown filter type.")
        return

    if not products:
        await query.message.reply_text(f"No products found for the selected {filter_type}.")
        return

    for product in products:
        try:
            photo_url = product[4]
            if is_valid_url(photo_url):
                price = Decimal(product[5])
                discount = Decimal(product[6])
                discounted_price = round(price * (Decimal(100) - discount) / Decimal(100), 2)
                caption = (
                    f"Title: {product[1]}\n"
                    f"Price: {discounted_price} ₼\n"
                    f"Discount: {discount}%\n"
                    f"Link: {product[3]}"
                )
                await query.message.reply_photo(photo=photo_url, caption=caption)
            else:
                logging.warning(f"Invalid photo URL for product: {product[1]}")
        except Exception as e:
            logging.error(f"Failed to send photo for product {product[1]}: {e}")

async def search_handler(update: Update, context: CallbackContext):
    if context.user_data.get('search_step'):
        query_text = update.message.text
        products = fetch_products_by_search(query_text)

        if not products:
            await update.message.reply_text("No products found matching the search query.")
            return

        for product in products:
            try:
                photo_url = product[4]  
                if photo_url:
                    await update.message.reply_photo(
                        photo=photo_url,
                        caption=f"Title: {product[1]}\nDescription: {product[2]}\nPrice: {product[5]}\nDiscount: {product[6]}%"
                    )
                else:
                    logging.warning(f"No image URL provided for product: {product[1]}")
            except Exception as e:
                logging.error(f"Failed to send photo for product {product[1]}: {e}")

        context.user_data['search_step'] = False

async def command_restriction(update: Update, context):
    print("Command Restriction")
    user = update.effective_user
    language = context.user_data.get('language', 'en')

    if not is_user_registered(user.id):
        if update.message.text.startswith('/discounts'):
            await update.message.reply_text(languages[language]["not_registered"])
        return

    if update.message.text == '/discounts':
        await discounts_command(update, context)

if __name__ == '__main__':
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_API")).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("register", register))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("languages", languages_command))
    app.add_handler(CommandHandler("discounts", discounts_command))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ask_birthday))  
    app.add_handler(CallbackQueryHandler(button_handler, pattern='^(male|female|other)$'))  

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler))  

    app.add_handler(CallbackQueryHandler(language_selection, pattern='^(az|en|tr|ru)$'))
    app.add_handler(CallbackQueryHandler(filter_search_handler, pattern='^(all|filter|search|filter_brand|filter_category)$'))
    app.add_handler(CallbackQueryHandler(specific_filter_handler, pattern='^(brand_|category_)'))

    app.add_handler(MessageHandler(filters.COMMAND, command_restriction))

    app.run_polling()
