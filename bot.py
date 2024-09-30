import os
from dotenv import load_dotenv
import logging
import psycopg2

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext, ContextTypes

from datetime import datetime
from decimal import Decimal

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
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# Dil
languages = {
    'en': {
        'greeting': "Hello, {name}! Welcome to the bot.",
        'ask_birthday': "Please enter your birth date:",
        'ask_gender': "Please select your gender:",
        'registration_success': "Registration successful! You can now use other commands.",
        'error_invalid_birthday': "Invalid date format. Our bot still can't recognize all formats, please enter your birth date in a different format.",
        'not_registered': "You are not registered. Please use /register to register.",
        'already_registered': "You are already registered.",
        'ask_location': "Please share your location or type your region:",
        'thank_you_feedback': "Thank you for your feedback!",
        'feedback_error': "An error occurred while submitting your feedback. Please try again later.",
        'ask_store_recommendation': "Please recommend any markets or stores you think we should work with (optional):",
                "help_start": "Greet the user",
        "help_register": "Register if you haven't",
        "help_discounts": "Show available discounts",
        "help_languages": "Switch language",
        "available_commands": "Here are the available commands:",
        "not_registered_help": "You are not registered. You can't use /help without registration. Please use /register to register.",
         "profile_info": "Here is your profile information:",
        "profile_id": "Telegram ID",
        "profile_username": "Username",
        "profile_first_name": "First Name",
        "profile_last_name": "Last Name",
        "profile_birthdate": "Birthdate",
        "profile_gender": "Gender",
        "profile_language": "Language",
        "profile_location": "Location", 
        "profile_created_at": "Registration Date",
        "profile_not_found": "No profile found. Please register first.",
 
    },
    'tr': {
        'greeting': "Merhaba, {name}! Bota hoş geldiniz.",
        'ask_birthday': "Lütfen doğum tarihinizi girin:",
        'ask_gender': "Lütfen cinsiyetinizi seçin:",
        'registration_success': "Kayıt başarılı! Artık diğer komutları kullanabilirsiniz.",
        'error_invalid_birthday': "Geçersiz tarih formatı. Botumuz hala bütün formatları algılamıyor, lütfen daha farklı bir formatla doğum tarihinizi giriniz.",
        'not_registered': "Kayıtlı değilsiniz. Lütfen kayıt olmak için /register kullanın.",
        'already_registered': "Siz zaten kayıtlısınız.",
        'ask_location': "Lütfen konumunuzu paylaşın veya bölgenizi yazın:",
        'thank_you_feedback': "Geri bildiriminiz için teşekkür ederiz!",
        'feedback_error': "Geri bildiriminizi gönderirken bir hata oluştu. Lütfen tekrar deneyin.",
        'ask_store_recommendation': "Çalışmamız gereken marketleri veya mağazaları önerin (isteğe bağlı):",
                "help_start": "Kullanıcıyı selamla",
        "help_register": "Henüz kayıt olmadıysanız kayıt olun",
        "help_discounts": "Mevcut indirimleri göster",
        "help_languages": "Dili değiştir",
        "available_commands": "Mevcut komutlar:",
        "not_registered_help": "Kayıtlı değilsiniz. /help komutunu kullanabilmek için kayıt olmanız gerekir. Lütfen /register komutunu kullanarak kayıt olun.",
        "profile_info": "Profil bilgilerin aşağıda:",
        "profile_id": "Telegram ID",
        "profile_username": "Kullanıcı Adı",
        "profile_first_name": "Ad",
        "profile_last_name": "Soyad",
        "profile_birthdate": "Doğum Tarihi",
        "profile_gender": "Cinsiyet",
        "profile_language": "Dil",
        "profile_location": "Konum", 

        "profile_created_at": "Kayıt Tarihi",
        "profile_not_found": "Profil bulunamadı. Lütfen önce kayıt olun."

    },
    'az': {
        'greeting': "Salam, {name}! Bota xoş gəlmisiniz.",
        'ask_birthday': "Zəhmət olmasa doğum tarixinizi daxil edin:",
        'ask_gender': "Zəhmət olmasa cinsiyyətinizi seçin:",
        'registration_success': "Qeydiyyat uğurla tamamlandı! İndi digər komandaları istifadə edə bilərsiniz.",
        'error_invalid_birthday': "Yanlış tarix formatı. Botumuz hələ bütün formatları tanımır, xahiş edirik, doğum tarixini fərqli bir formatda daxil edin.",
        'not_registered': "Siz qeydiyyatdan keçməmisiniz. Zəhmət olmasa qeydiyyatdan keçmək üçün /register istifadə edin.",
        'already_registered': "Siz artıq qeydiyyatdasınız.",
        'ask_location': "Zəhmət olmasa konumunuzu paylaşın və ya bölgənizi yazın:",
        'thank_you_feedback': "Geri bildiriminiz üçün təşəkkür edirik!",
        'feedback_error': "Geri bildiriminizi göndərərkən bir xəta baş verdi. Zəhmət olmasa, yenidən cəhd edin.",
        'ask_store_recommendation': "İşlədiyimiz marketləri və ya dükanları tövsiyə edin (isteğe bağlı):",
        "help_start": "İstifadəçini salamla",
        "help_register": "Əgər qeydiyyatdan keçməmisinizsə, qeydiyyatdan keçin",
        "help_discounts": "Mövcud endirimləri göstər",
        "help_languages": "Dili dəyişdir",
        "available_commands": "Mövcud əmrlər:",
        "not_registered_help": "Qeydiyyatdan keçməmisiniz. /help əmrindən istifadə etmək üçün qeydiyyatdan keçməlisiniz. Xahiş edirik, /register istifadə edərək qeydiyyatdan keçin.",
        "profile_info": "Profil məlumatlarınız aşağıda:",
        "profile_id": "Telegram ID",
        "profile_username": "İstifadəçi adı",
        "profile_first_name": "Ad",
        "profile_last_name": "Soyad",
        "profile_birthdate": "Doğum tarixi",
        "profile_gender": "Cinsiyyət",
        "profile_language": "Dil",
        "profile_location": "Məkan", 
        "profile_created_at": "Qeydiyyat tarixi",
        "profile_not_found": "Profil tapılmadı. Zəhmət olmasa əvvəl qeydiyyatdan keçin."
    },
    'ru': {
        'greeting': "Здравствуйте, {name}! Добро пожаловать в бот.",
        'ask_birthday': "Пожалуйста, введите вашу дату рождения:",
        'ask_gender': "Пожалуйста, выберите ваш пол:",
        'registration_success': "Регистрация прошла успешно! Теперь вы можете использовать другие команды.",
        'error_invalid_birthday': "Неверный формат даты. Наш бот все еще не может распознать все форматы, пожалуйста, введите вашу дату рождения в другом формате.",
        'not_registered': "Вы не зарегистрированы. Пожалуйста, используйте /register для регистрации.",
        'already_registered': "Вы уже зарегистрированы.",
        'ask_location': "Пожалуйста, поделитесь своим местоположением или введите свой регион:",
        'thank_you_feedback': "Спасибо за ваш отзыв!",
        'feedback_error': "Произошла ошибка при отправке вашего отзыва. Пожалуйста, попробуйте еще раз.",
        'ask_store_recommendation': "Пожалуйста, рекомендуйте любые рынки или магазины, с которыми мы должны работать (по желанию):",
        "help_start": "Поздороваться с пользователем",
        "help_register": "Зарегистрируйтесь, если еще не зарегистрированы",
        "help_discounts": "Показать доступные скидки",
        "help_languages": "Сменить язык",
        "available_commands": "Доступные команды:",
        "not_registered_help": "Вы не зарегистрированы. Вы не можете использовать /help без регистрации. Пожалуйста, используйте /register для регистрации.",
        "profile_info": "Ваша информация о профиле:",
        "profile_id": "Телеграм ID",
        "profile_username": "Имя пользователя",
        "profile_first_name": "Имя",
        "profile_last_name": "Фамилия",
        "profile_birthdate": "Дата рождения",
        "profile_gender": "Пол",
        "profile_language": "Язык",
        "profile_location": "Местоположение",
        "profile_not_found": "Профиль не найден. Пожалуйста, сначала зарегистрируйтесь."
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
        cursor.execute("SELECT * FROM product_product WHERE end_date >= %s and start_date <= %s", (datetime.now(),datetime.now()))
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
    cursor.execute("SELECT * FROM product_brand")
    brands = cursor.fetchall()
    conn.close()
    return brands

def fetch_all_categories():
    print("Fetch categories")
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM product_category")
    categories = cursor.fetchall()
    conn.close()
    return categories

def fetch_products_by_brand(brand_id):
    print("FILTER BY BRANDS FETCH")
    logging.info(f"Fetching products for brand: {brand_id}")
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""SELECT * FROM product_product WHERE brand_id = %s AND end_date >= %s AND start_date <= %s""",
                   (brand_id, datetime.now(), datetime.now()))
    products = cursor.fetchall()
    conn.close()
    logging.info(f"Products found: {products}")
    return products

def fetch_products_by_category(category_id):
    print("FILTER BY CATEGORY FETCH")
    logging.info(f"Fetching products for category: {category_id}")
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""SELECT * FROM product_product WHERE category_id = %s AND end_date >= %s AND start_date <= %s""",
                   (category_id, datetime.now(), datetime.now()))
    products = cursor.fetchall()
    conn.close()
    logging.info(f"Products found: {products}")
    return products

def is_user_registered(telegram_id):
    conn = connect_db()
    if not conn:
        logging.error("Failed to connect to the database during registration check.")
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM account_user WHERE telegram_id = %s", (telegram_id,))
        result = cursor.fetchone()
    except Exception as e:
        logging.error(f"Error fetching user data: {e}")
        return False
    finally:
        conn.close()
    return result is not None


def delete_user_from_db(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        print(user_id)
        cursor.execute("DELETE FROM account_user WHERE telegram_id = %s", (user_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Hata: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def store_user_recommendation(description, user_id):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO account_recommendations (description, user_id)
            VALUES (%s, %s);
        """, (description, user_id))
        conn.commit()
    except Exception as e:
        logging.error(f"Error storing user recommendation data: {e}")
        return False
    finally:
        conn.close()
    return True


def store_user_data(user_id, username, first_name, last_name, birthday, gender, location, language):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO account_user (telegram_id, username, first_name, last_name, birthday, gender, location, language)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """, (user_id, username, first_name, last_name, birthday, gender, location, language))
        conn.commit()
    except Exception as e:
        logging.error(f"Error storing user data: {e}")
        return False
    finally:
        conn.close()
    return True

def profile_data(tg_id):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""select * from account_user where telegram_id= %s""", (tg_id, ))
        conn.commit()
    except Exception as e:
        logging.error(f"Error profile data: {e}")
        return False
    finally:
        conn.close()
    return cursor.fetchone()


def fetch_products_by_search(search_query: str):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, description, url, image_url, normal_price, discount_percentage
            FROM product_product
            WHERE (LOWER(title) LIKE LOWER(%s) OR LOWER(description) LIKE LOWER(%s)) AND end_date >= %s AND start_date <= %s
        """, (f"%{search_query}%", f"%{search_query}%", datetime.now(), datetime.now()))
        products = cursor.fetchall()
        conn.close()
        return products
    except Exception as e:
        logging.error(f"Error fetching products by search: {e}")
        return []
    

async def get_user_profile(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT id, telegram_id, username, first_name, last_name, birthday, gender, language, location FROM account_user WHERE telegram_id = %s",
            (user_id,)
        )
        user_data = cursor.fetchone()
        if user_data:
            return {
                "id": user_data[0],
                "telegram_id": user_data[1],
                "username": user_data[2],
                "first_name": user_data[3],
                "last_name": user_data[4],
                "birthday": user_data[5].strftime("%d-%m-%Y") if user_data[5] else "N/A",
                "gender": user_data[6],
                "language": user_data[7],
                "location": user_data[8] 
            }
        return None
    except Exception as e:
        print(f"Error retrieving profile: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


async def profile_command(update: Update, context):
    user = update.effective_user
    language = auto_language(context, user)

    user_profile = await get_user_profile(user.id)
    
    if user_profile:
        profile_info = (
            f"{languages[language]['profile_info']}\n"
            f"🆔 {languages[language]['profile_id']}: {user_profile['id']}\n" 
            f"👤 {languages[language]['profile_username']}: {user_profile['username']}\n"
            f"🧑 {languages[language]['profile_first_name']}: {user_profile['first_name']}\n"
            f"👨‍⚖️ {languages[language]['profile_last_name']}: {user_profile['last_name']}\n"
            f"🎂 {languages[language]['profile_birthdate']}: {user_profile['birthday']}\n"
            f"⚧️ {languages[language]['profile_gender']}: {user_profile['gender']}\n"
            f"🗣️ {languages[language]['profile_language']}: {user_profile['language']}\n"
            f"📍 {languages[language]['profile_location']}: {user_profile['location']}\n"
        )
        await update.message.reply_text(profile_info)
    else:
        await update.message.reply_text(languages[language]['profile_not_found'])



def update_user_language(telegram_id, language):
    try:
        update_query =  """UPDATE account_user SET language = %s WHERE telegram_id = %s"""
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(update_query, (language, telegram_id))
        conn.commit()
    except Exception as e:
        print(f"Error updating language: {e}")
    finally:
        cursor.close()
        conn.close()


async def change_language(update: Update, context: CallbackContext):
    query = update.callback_query
    selected_language = query.data
    telegram_id = query.from_user.id

    context.user_data['language'] = selected_language
    update_user_language(telegram_id, selected_language)

    await query.edit_message_text(text=languages[selected_language]['greeting'].format(name=query.from_user.first_name))

def auto_language(context, user):
    language = context.user_data.get('language', 'en')
    if user.language_code in ['en', 'tr', 'az', 'ru']:
        language = context.user_data.get('language', user.language_code)
    return language

# /start komandası
async def start(update: Update, context):
    print("START")
    user = update.effective_user
    language = context.user_data.get('language', 'en')
    language = auto_language(context, user)
    print(update.effective_user)
    await update.message.reply_text(languages[language]["greeting"].format(name=user.first_name))

async def active_user(update: Update, context):
    return profile_data(tg_id=update.effective_user.id)

async def delete_me(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    
    if delete_user_from_db(user_id):
        await update.message.reply_text("Başarıyla silindiniz.")
    else:
        await update.message.reply_text("Bir hata oluştu ya da kullanıcı bulunamadı.")


async def register(update: Update, context):
    user = update.effective_user
    language = auto_language(context, user)

    if is_user_registered(user.id):
        await update.message.reply_text(languages[language]['already_registered'])
        return

    await update.message.reply_text(languages[language]["ask_birthday"])
    context.user_data['step'] = 'ask_birthday'

def check_birthday(birthday_input):
    months = {
        'tr': {
            "ocak": "January", "şubat": "February", "mart": "March",
            "nisan": "April", "mayıs": "May", "haziran": "June",
            "temmuz": "July", "ağustos": "August", "eylül": "September",
            "ekim": "October", "kasım": "November", "aralık": "December"
        },
        'az': {
            "yanvar": "January", "fevral": "February", "mart": "March",
            "aprel": "April", "may": "May", "iyun": "June",
            "iyul": "July", "avqust": "August", "sentyabr": "September",
            "oktyabr": "October", "noyabr": "November", "dekabr": "December"
        },
        'ru': {
            "январь": "January", "февраль": "February", "март": "March",
            "апрель": "April", "май": "May", "июнь": "June",
            "июль": "July", "август": "August", "сентябрь": "September",
            "октябрь": "October", "ноябрь": "November", "декабрь": "December"
        }
    }

    replaced = False
    birthday_input_casefold = birthday_input.lower()
    print("Data:", birthday_input_casefold)
    for lang, month_dict in months.items():
        for turkish, english in month_dict.items():
            if turkish in birthday_input_casefold:  
                birthday_input = birthday_input_casefold.replace(turkish, english)
                replaced = True
                break
        if replaced:
            break

    date_formats = [
        "%d-%m-%Y",  
        "%d/%m/%Y",  
        "%Y.%m.%d",  
        "%d %B %Y",  
        "%d %b %Y",  
        "%Y-%m-%d",  
        "%m-%d-%Y",
        "%m/%d/%Y",
        "%Y/%m/%d",
        "%d.%m.%Y",  
        "%B %d, %Y",  
        "%b %d, %Y", 
        "%d %m %Y",  
        "%d %b %y",  
        "%d %B %y",  
        "%Y%m%d",      
        "%d %m %y"     
    ]        

    for date_format in date_formats:
        try:
            parsed_date = datetime.strptime(birthday_input, date_format)
            formatted_date = parsed_date.strftime("%d-%m-%Y") 
            return formatted_date 
        except ValueError:
            continue 

    return False

async def ask_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    language = auto_language(context, user)
    
    if context.user_data.get('step') == 'ask_birthday':
        birthday = update.message.text
        print(birthday)
        formatted_birthday = check_birthday(birthday)
        print(formatted_birthday)
        
        if not formatted_birthday: 
            await update.message.reply_text(languages[language]["error_invalid_birthday"])
            return  
        else:
            context.user_data['birthday'] = formatted_birthday

            keyboard = [
                [InlineKeyboardButton("👨 Male", callback_data='male')],
                [InlineKeyboardButton("👩 Female", callback_data='female')],
                [InlineKeyboardButton("🌈 Other", callback_data='other')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(languages[language]["ask_gender"], reply_markup=reply_markup)
            context.user_data['step'] = 'ask_gender'

async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user = query.from_user
    language = auto_language(context, user)
    
    if context.user_data.get('step') == 'ask_gender':
        selected_gender = query.data
        context.user_data['gender'] = selected_gender
        await query.answer()
        await query.edit_message_text(text=f"Gender selected: {selected_gender}")

        await query.message.reply_text(languages[language]["ask_location"], reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("Share Location", request_location=True)]], resize_keyboard=True, one_time_keyboard=True))
        context.user_data['step'] = 'ask_location'
        return
    
# /help komandası
async def help_command(update: Update, context):
    print("HELP COMMAND")
    user = update.effective_user
    language = auto_language(context, user)
    print(language)

    if is_user_registered(user.id):
        available_commands = f"/start - {languages[language]['help_start']}\n" \
                             f"/register - {languages[language]['help_register']}\n" \
                             f"/discounts - {languages[language]['help_discounts']}\n" \
                             f"/languages - {languages[language]['help_languages']}\n"
        
        await update.message.reply_text(languages[language]['available_commands'] + f"\n{available_commands}")
    else:
        await update.message.reply_text(languages[language]['not_registered_help'])

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
    print(context.user_data)

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

import re

def is_valid_url(url):
    regex = re.compile(
        r'^(https?:\/\/)?'
        r'([a-z0-9\-]+\.)+[a-z]{2,}'
        r'(:[0-9]{1,5})?'
        r'(\/.*)?$'
    )
    
    is_valid = re.match(regex, url) is not None
    print("IS VALID URL" if is_valid else "IS INVALID URL")
    return is_valid

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
            print(products[3])
            for product in products:
                photo_url = product[5]
                if is_valid_url(photo_url):
                    try:
                        price = Decimal(product[2])
                        discount = Decimal(product[3])
                        discounted_price = round(price * (Decimal(100) - discount) / Decimal(100), 2)
                        caption = (
                            f"Title: {product[1]}\n"
                            f"Description: {product[6]}\n"
                            f"Price: {discounted_price} ₼\n"
                            f"Discount: {discount}%\n"
                            f"Last Day: {product[8].strftime("%d %B %Y, %H:%M UTC")}\n"
                            f"Link: {product[9]}\n"
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
        for brand in brands:
            print(brand, "\n")
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
    print("WE ARE HERE")
    filter_type = data[0]
    print(filter_type)
    value = data[1]
    print(value)

    if filter_type == 'brand':
        products = fetch_products_by_brand(value)
        for i in products:
            print(i)
            print('\n')
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
            photo_url = product[5]
            if is_valid_url(photo_url):
                price = Decimal(product[2])
                discount = Decimal(product[3])
                discounted_price = round(price * (Decimal(100) - discount) / Decimal(100), 2)
                caption = (
                    f"Title: {product[1]}\n"
                    f"Price: {discounted_price} ₼\n"
                    f"Discount: {discount}%\n"
                    f"Link: {product[9]}"
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

async def location_handler(update: Update, context):
    print("LOCATION")
    language = auto_language(context, update.effective_user)
    if context.user_data['step'] == 'ask_location':
        if update.message.location:
            latitude = update.message.location.latitude
            longitude = update.message.location.longitude
            context.user_data['location'] = {'latitude': latitude, 'longtitude': longitude}
            
            recommendation_buttons = [
                ["Skip Recommendation"]
            ]
            reply_markup = ReplyKeyboardMarkup(recommendation_buttons, one_time_keyboard=True, resize_keyboard=True, )
        else:
            region = update.message.text
            context.user_data['location'] = {"region": region}
        context.user_data['step'] = 'ask_store_recommendation'
        await update.message.reply_text(languages[language]['ask_store_recommendation'])
    else:
        await update.message.reply_text("Thanks for your location data...but we can only use it in registration process")

async def store_recommendation_handler(update: Update, context):
    print("STORE RECOMENDATION")
    recommendation = update.message.text
    user = update.effective_user
    language = auto_language(context, user)
    if recommendation == "Skip Recommendation":
        context.user_data['store_recommendation'] = None
        await update.message.reply_text("Öneriniz alınmadı.", reply_markup=None)
    else:
        context.user_data['store_recommendation'] = recommendation
    location = context.user_data['location']
    if isinstance(location, dict):
        location_str = f"{location.get('region', 'Unknown')}, Latitude: {location.get('latitude', 'N/A')}, Longitude: {location.get('longitude', 'N/A')}"
    else:
        location_str = location

    success = store_user_data(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        birthday=context.user_data['birthday'],
        gender=context.user_data['gender'],
        location=location_str,
        language=auto_language(context, user),
    )
    # user_profile = await get_user_profile(user.id)
    # success_2 = store_user_recommendation(
    #     user_id=user_profile['id'],
    #     description=recommendation
    # )
    if success:
        recommendation_buttons = []
        reply_markup = ReplyKeyboardMarkup(keyboard=recommendation_buttons)
        await update.message.reply_text(languages[language]["registration_success"], reply_markup=None)
    else:
        recommendation_buttons = []
        reply_markup = ReplyKeyboardMarkup(keyboard=recommendation_buttons)
        await update.message.reply_text("An error occurred while saving your data. Please try again later.", reply_markup=None)

    context.user_data.clear()

async def feedback_command(update: Update, context: CallbackContext):
    language = context.user_data.get('language', 'en')
    await update.message.reply_text("Please provide your feedback:")
    context.user_data['step'] = 'feedback'

async def handle_feedback(update: Update, context: CallbackContext):
    if context.user_data.get('step') == 'feedback':
        feedback = update.message.text
        user_id = update.effective_user.id
        
        success = store_feedback(user_id, feedback)
        
        if success:
            await update.message.reply_text("Thank you for your feedback!")
        else:
            await update.message.reply_text("An error occurred while submitting your feedback. Please try again later.")
        
        context.user_data['step'] = None  

def store_feedback(user_id, feedback):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO feedback (user_id, description) VALUES (%s, %s);",
            (user_id, feedback)
        )
        conn.commit()
    except Exception as e:
        logging.error(f"Error storing feedback: {e}")
        return False
    finally:
        conn.close()
    return True


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



async def text_message_handler(update: Update, context: CallbackContext):
    step = context.user_data.get('step')
    print("step is, ", step)
    if step == 'ask_birthday':
        await ask_birthday(update, context)
    elif step == 'ask_store_recommendation':
        await store_recommendation_handler(update, context)
    elif step == 'ask_location':
        await location_handler(update, context)
    elif context.user_data['search_step']:
        await search_handler(update, context)
    else:
        await update.message.reply_text("I don't understand that command. Please follow the prompts.")


if __name__ == '__main__':
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_API")).build()

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
    app.add_handler(CallbackQueryHandler(button_handler, pattern='^(male|female|other)$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_feedback))
    app.add_handler(CallbackQueryHandler(language_selection, pattern='^(az|en|tr|ru)$'))
    app.add_handler(CallbackQueryHandler(filter_search_handler, pattern='^(all|filter|search|filter_brand|filter_category)$'))
    app.add_handler(CallbackQueryHandler(specific_filter_handler, pattern='^(brand_|category_)'))
    app.add_handler(MessageHandler(filters.COMMAND, command_restriction))

    app.run_polling()