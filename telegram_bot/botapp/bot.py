import os
from dotenv import load_dotenv
import logging
import psycopg2
from django.db import transaction
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext, ContextTypes
from datetime import datetime
from decimal import Decimal
from .models import Profile, Product, Brand, Category, Recommendations, Feedback, Stats
from django.db import models
from django.db.models import Q
from asgiref.sync import sync_to_async
from telegram.helpers import escape_markdown
import re
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone 

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



@sync_to_async
def fetch_all_discounted_products_sync():
    print("Fetch all discount products")
    return list(Product.objects.filter(
        discount_end_date__gte=datetime.now(),
        discount_start_date__lte=datetime.now()
    ).values())
async def fetch_all_discounted_products():
    return await fetch_all_discounted_products_sync()

@sync_to_async
def fetch_all_brands_sync():
    print("Fetch brands")
    return list(Brand.objects.all().values())

async def fetch_all_brands():
    return await fetch_all_brands_sync()

@sync_to_async
def fetch_all_categories_sync():
    print("Fetch categories")
    return list(Category.objects.all().values())

async def fetch_all_categories():
    return await fetch_all_categories_sync()

@sync_to_async
def fetch_products_by_brand_sync(brand_id):
    print("FILTER BY BRANDS FETCH")
    return list(Product.objects.filter(
        brand_id=brand_id,
        discount_end_date__gte=datetime.now(),
        discount_start_date__lte=datetime.now()
    ).values())

async def fetch_products_by_brand(brand_id):
    return await fetch_products_by_brand_sync(brand_id)
    
@sync_to_async
def fetch_products_by_category_sync(category_id):
    print("FILTER BY CATEGORY FETCH")
    return list(Product.objects.filter(
        category_id=category_id,
        discount_end_date__gte=datetime.now(),
        discount_start_date__lte=datetime.now()
    ).values())

async def fetch_products_by_category(category_id):
    return await fetch_products_by_category_sync(category_id)


@sync_to_async
def is_user_registered_sync(telegram_id):
    print(Profile.objects.all())
    return Profile.objects.filter(telegram_id=telegram_id).exists()

async def is_user_registered(telegram_id):
    return await is_user_registered_sync(telegram_id)

@sync_to_async
def delete_user_from_db_sync(user_id):
    try:
        profile = Profile.objects.get(telegram_id=user_id)
        profile.delete()
        return True
    except Profile.DoesNotExist:
        return False

async def delete_user_from_db(user_id):
    return await delete_user_from_db_sync(user_id)

@sync_to_async
def store_user_recommendation_sync(description, user_id):
    try:
        Recommendations.objects.create(description=description, user_id=user_id)
        return True
    except Exception as e:
        logging.error(f"Error storing user recommendation data: {e}")
        return False

async def store_user_recommendation(description, user_id):
    return await store_user_recommendation_sync(description, user_id)


@sync_to_async
def store_user_data_sync(user_data):
    try:
        birthday = user_data.get('birthday')
        if birthday:
            formatted_birthday = datetime.strptime(birthday, "%d-%m-%Y").strftime("%Y-%m-%d")
            user_data['birthday'] = formatted_birthday
        Profile.objects.create(**user_data)
        return True
    except Exception as e:
        logging.error(f"Error storing user data: {e}")
        return False

async def store_user_data(user_data):
    return await store_user_data_sync(user_data)

@sync_to_async
def profile_data_sync(tg_id):
    try:
        return Profile.objects.filter(telegram_id=tg_id).values().first()
    except Exception as e:
        logging.error(f"Error fetching profile data: {e}")
        return None

async def profile_data(tg_id):
    return await profile_data_sync(tg_id)
    
@sync_to_async
def fetch_products_by_search_sync(search_query: str):
    try:
        now = timezone.now()  
        
        return list(Product.objects.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query),
            discount_end_date__gte=now,
            discount_start_date__lte=now
        ).values())
    except Exception as e:
        logging.error(f"Error fetching products by search: {e}")
        return []

async def fetch_products_by_search(search_query: str):
    print("HERE")
    return await fetch_products_by_search_sync(search_query)


@sync_to_async
def get_user_profile_sync(user_id):
    try:
        user_data = Profile.objects.get(telegram_id=user_id)
        return {
            "id": user_data.id,
            "telegram_id": user_data.telegram_id,
            "username": user_data.username,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "birthday": user_data.birthday.strftime("%d-%m-%Y") if user_data.birthday else "N/A",
            "gender": user_data.gender,
            "language": user_data.language,
            "location": user_data.location
        }
    except Profile.DoesNotExist:
        logging.error(f"Profile with telegram_id {user_id} does not exist.")
        return None
    except Exception as e:
        print(f"Error retrieving profile: {e}")
        return None

async def get_user_profile(user_id):
    return await get_user_profile_sync(user_id)

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


@sync_to_async
def update_user_language_sync(telegram_id, language):
    try:
        profile = Profile.objects.get(telegram_id=telegram_id)
        profile.language = language
        profile.save()
    except Profile.DoesNotExist:
        print(f"User with telegram_id {telegram_id} does not exist.")
    except Exception as e:
        print(f"Error updating language: {e}")

async def update_user_language(telegram_id, language):
    await update_user_language_sync(telegram_id, language)
    

@sync_to_async
def update_user_language_sync(telegram_id, language):
    update_user_language(telegram_id, language) 

async def change_language(update: Update, context: CallbackContext):
    query = update.callback_query
    selected_language = query.data
    telegram_id = query.from_user.id

    context.user_data['language'] = selected_language
    await update_user_language_sync(telegram_id, selected_language)

    await query.edit_message_text(text=languages[selected_language]['greeting'].format(name=query.from_user.first_name))

def auto_language(context, user):
    language = context.user_data.get('language', 'en')
    if user.language_code in ['en', 'tr', 'az', 'ru']:
        language = context.user_data.get('language', user.language_code)
    return language

async def start(update: Update, context: CallbackContext):
    print("START")
    user = update.effective_user
    brands = await fetch_all_brands()
    print(brands)
    
    language = auto_language(context, user)

    print(user)
    await update.message.reply_text(languages[language]["greeting"].format(name=user.first_name))

async def active_user(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    return await profile_data(tg_id=user_id)

async def delete_me(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    
    if await sync_to_async(delete_user_from_db)(user_id):
        await update.message.reply_text(languages[auto_language(context, update.effective_user)]['delete_success'])
    else:
        await update.message.reply_text(languages[auto_language(context, update.effective_user)]['delete_failure'])

async def register(update: Update, context: CallbackContext):
    user = update.effective_user
    language = auto_language(context, user)

    if await is_user_registered(user.id):
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

    birthday_input_casefold = birthday_input.lower()
    print("Data:", birthday_input_casefold)
    
    for lang, month_dict in months.items():
        for turkish, english in month_dict.items():
            if turkish in birthday_input_casefold:
                birthday_input = birthday_input_casefold.replace(turkish, english)
                break

    date_formats = [
        "%d-%m-%Y", "%d/%m/%Y", "%Y.%m.%d", "%d %B %Y",
        "%d %b %Y", "%Y-%m-%d", "%m-%d-%Y", "%m/%d/%Y",
        "%Y/%m/%d", "%d.%m.%Y", "%B %d, %Y", "%b %d, %Y",
        "%d %m %Y", "%d %b %y", "%d %B %y", "%Y%m%d", "%d %m %y"
    ]

    for date_format in date_formats:
        try:
            parsed_date = datetime.strptime(birthday_input, date_format)
            return parsed_date.strftime("%d-%m-%Y")  
        except ValueError:
            continue

    return False

async def ask_birthday(update: Update, context: CallbackContext):
    user = update.effective_user
    language = auto_language(context, user)

    if context.user_data.get('step') == 'ask_birthday':
        birthday = update.message.text.strip()
        print(birthday)
        
        formatted_birthday = check_birthday(birthday)
        print(formatted_birthday)
        
        if not formatted_birthday:
            await update.message.reply_text(languages[language]["error_invalid_birthday"])
            return

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

        await query.edit_message_text(text=f"Gender selected: {escape_markdown(selected_gender)}")

        await query.message.reply_text(
            languages[language]["ask_location"], 
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("Share Location", request_location=True)]],
                resize_keyboard=True, one_time_keyboard=True
            )
        )
        context.user_data['step'] = 'ask_location'
    
async def help_command(update: Update, context: CallbackContext):
    print("HELP COMMAND")
    user = update.effective_user
    language = auto_language(context, user)
    print(language)

    if await is_user_registered(user.id):
        print(user.id)
        print("Somewhere")
        available_commands = (
            f"/start - {languages[language]['help_start']}\n"
            f"/register - {languages[language]['help_register']}\n"
            f"/discounts - {languages[language]['help_discounts']}\n"
            f"/languages - {languages[language]['help_languages']}\n"
        )
        print("SOMEWHERE ELSE")
        await update.message.reply_text(
            languages[language]['available_commands'] + f"\n{available_commands}"
        )
    else:
        await update.message.reply_text(languages[language]['not_registered_help'])

async def languages_command(update: Update, context: CallbackContext):
    print("LANGUAGE COMMAND")
    keyboard = [
        [InlineKeyboardButton("🇦🇿 Azerbaijani", callback_data='az')],
        [InlineKeyboardButton("🇬🇧 English", callback_data='en')],
        [InlineKeyboardButton("🇹🇷 Turkish", callback_data='tr')],
        [InlineKeyboardButton("🇷🇺 Russian", callback_data='ru')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("Please select your language:", reply_markup=reply_markup)

async def language_selection(update: Update, context: CallbackContext):
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


async def discounts_command(update: Update, context: CallbackContext):
    user = update.effective_user
    language = context.user_data.get('language', 'en')

    if not await is_user_registered(user.id):
        await update.message.reply_text(languages[language]["not_registered"])
        return

    keyboard = [
        [InlineKeyboardButton("All Discounted Products", callback_data='all')],
        [InlineKeyboardButton("Filter Discounts", callback_data='filter')],
        [InlineKeyboardButton("Search", callback_data='search')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose an option:", reply_markup=reply_markup)


async def display_product(query_or_message, product):
    photo_url = product['image_url']
    if is_valid_url(photo_url):
        try:
            price = Decimal(product['normal_price']).quantize(Decimal('0.01'))
            discount_price = Decimal(product['discount_price']).quantize(Decimal('0.01'))
            caption = (
                f"Title: {product['name']}\n"
                f"Description: {product['description']}\n"
                f"Original Price: {price} ₼\n"
                f"Discounted Price: {discount_price} ₼\n"
                f"Last Day: {product['discount_end_date'].strftime('%d %B %Y')}\n"
                f"Link: {product['url']}\n"
            )
            await query_or_message.reply_photo(photo=photo_url, caption=caption)
        except Exception as e:
            await query_or_message.reply_text(f"An error occurred while displaying the product: {product['name']}.")
    else:
        await query_or_message.reply_text(f"Invalid image for the product: {product['name']}.")

def is_valid_url(url: str) -> bool:
    regex = re.compile(
        r'^(https?:\/\/)?'            
        r'([a-z0-9\-]+\.)+[a-z]{2,}'  
        r'(:[0-9]{1,5})?'             
        r'(\/.*)?$'                   
    )
    
    return re.match(regex, url) is not None

async def filter_search_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    choice = query.data
    print(choice)

    if choice == 'all':
        await handle_all_discounted_products(query)
    elif choice == 'filter':
        print(query)
        print(update.callback_query)
        await display_filter_options(query)
    elif choice == 'search':
        await prompt_search_product(query, context)


async def handle_all_discounted_products(query):
    products = await fetch_all_discounted_products()  
    if not products:
        await query.message.reply_text("No discounted products found.")
        return

    for product in products:
        await display_product(query.message, product)


async def display_filter_options(query):
    print("SALAMMMMMMMMMMMMMMMMMMMM @@@@")
    keyboard = [
        [InlineKeyboardButton("Filter by Brand", callback_data='filter_brand')],
        [InlineKeyboardButton("Filter by Category", callback_data='filter_category')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    print(reply_markup)
    await query.message.reply_text("Select filter type:", reply_markup=reply_markup)


async def display_brand_filter_options(query):
    print("SALAMMMMMMMMMMMMMMMMMMMM @")
    brands = await fetch_all_brands()

    keyboard = [
        [InlineKeyboardButton(brand['title'], callback_data=f'brand_{brand["id"]}')]
        for brand in brands
    ]
    if not brands:
        await query.message.reply_text("No brands available for filtering.")
        return
    
    print(query)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("Select a brand:", reply_markup=reply_markup)


async def display_category_filter_options(query):
    categories = await fetch_all_categories()
    keyboard = [
        [InlineKeyboardButton(category['title'], callback_data=f'category_{category["id"]}')]
        for category in categories
    ]
    if not categories:
        await query.message.reply_text("No categories available for filtering.")
        return
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("Select a category:", reply_markup=reply_markup)


async def prompt_search_product(query, context):
    await query.message.reply_text("Please enter the product name or description to search for discounts:")
    context.user_data['search_mode'] = True

async def specific_filter_handler(update: Update, context: CallbackContext):
    print("SALAAAAAAAAAAAAAAMMMMMMMMM")
    query = update.callback_query
    data = query.data
    print(data)

    if len(data) != 2:
        await query.message.reply_text("Invalid filter selection.")
        return

    filter_type, value = data
    logging.info(f"Filter type selected: {filter_type}, Value: {value}")

    try:
        print(filter_type)
        if filter_type == 'brand':
            print("FIlter brnd")
            products = await fetch_products_by_brand(value)
        elif filter_type == 'category':
            print("FIlter categry")
            products = await fetch_products_by_category(value)
        else:
            await query.message.reply_text("Unknown filter type.")
            return

        if not products:
            await query.message.reply_text(f"No discounted products found for the selected {filter_type}.")
            return

        for product in products:
            await display_product(query.message, product)
    except Exception as e:
        logging.error(f"Error fetching products: {e}")
        await query.message.reply_text("An error occurred while fetching products.")



async def handle_search_query(update: Update, context: CallbackContext):
    if context.user_data.get('search_mode'):
        search_query = update.message.text
        products = await fetch_products_by_search(search_query)
        if not products:
            await update.message.reply_text("No matching products found.")
            return

        for product in products:
            await display_product(update.message, product)

        context.user_data['search_mode'] = False
    else:
        await update.message.reply_text("Please enter a valid search query.")



async def location_handler(update: Update, context: CallbackContext):
    language = auto_language(context, update.effective_user)
    if context.user_data.get('step') == 'ask_location':
        if update.message.location:
            latitude = update.message.location.latitude
            longitude = update.message.location.longitude
            context.user_data['location'] = {'latitude': latitude, 'longitude': longitude}

            recommendation_buttons = [["Skip Recommendation"]]
            reply_markup = ReplyKeyboardMarkup(recommendation_buttons, one_time_keyboard=True, resize_keyboard=True)
            context.user_data['step'] = 'ask_store_recommendation'
            await update.message.reply_text(languages[language]['ask_store_recommendation'], reply_markup=reply_markup)
        else:
            region = update.message.text
            context.user_data['location'] = {"region": region}
            context.user_data['step'] = 'ask_store_recommendation'
            await update.message.reply_text(languages[language]['ask_store_recommendation'])
    else:
        await update.message.reply_text(
            "Thank you for sending your location. However, we only request location during the registration process."
        )
async def store_recommendation_handler(update: Update, context: CallbackContext):
    recommendation = update.message.text
    user = update.effective_user
    language = auto_language(context, user)

    if recommendation == "Skip Recommendation":
        context.user_data['store_recommendation'] = None
        await update.message.reply_text("No store recommendation recorded.")

    else:
        context.user_data['store_recommendation'] = recommendation

    location = context.user_data.get('location')
    if isinstance(location, dict):
        location_str = f"{location.get('region', 'Unknown')}, Latitude: {location.get('latitude', 'N/A')}, Longitude: {location.get('longitude', 'N/A')}"
    else:
        location_str = location

    user_data = {
        'telegram_id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'birthday': context.user_data.get('birthday'),
        'gender': context.user_data.get('gender'),
        'location': location_str,
        'language': auto_language(context, user),
    }

    success = await store_user_data(user_data)  
    if success:
        await update.message.reply_text(languages[language]["registration_success"])
    else:
        await update.message.reply_text("An error occurred while saving your data. Please try again later.")

    context.user_data.clear()

async def feedback_command(update: Update, context: CallbackContext):
    language = context.user_data.get('language', 'en')
    await update.message.reply_text("Please provide your feedback:")
    context.user_data['step'] = 'feedback'

async def handle_feedback(update: Update, context: CallbackContext):
    if context.user_data.get('step') == 'feedback':
        feedback_text = update.message.text
        user_id = update.effective_user.id
        
        success = await save_feedback(user_id, feedback_text)

        if success:
            await update.message.reply_text("Thank you for your feedback!")
        else:
            await update.message.reply_text("Failed to save feedback. Please try again.")

        context.user_data['step'] = None  



async def save_feedback(user_id, feedback_text):
    try:
        user_profile = await Profile.objects.get(telegram_id=user_id)
        
        feedback = Feedback(user=user_profile, description=feedback_text)
        await feedback.save() 
    except ObjectDoesNotExist:
        logging.error(f"User with telegram_id {user_id} does not exist.")
        return False
    except Exception as e:
        logging.error(f"Error storing feedback: {e}")
        return False
    return True


async def command_restriction(update: Update, context: CallbackContext):
    user = update.effective_user
    language = context.user_data.get('language', 'en')

    if not await is_user_registered(user.id):
        if update.message.text.startswith('/discounts'):
            await update.message.reply_text(languages[language]["not_registered"])
            return

    if update.message.text == '/discounts':
        await discounts_command(update, context)

async def text_message_handler(update: Update, context: CallbackContext):
    step = context.user_data.get('step')

    if step == 'ask_birthday':
        await ask_birthday(update, context)
    elif step == 'ask_store_recommendation':
        await store_recommendation_handler(update, context)
    elif step == 'ask_location':
        await location_handler(update, context)
    elif context.user_data.get('search_mode'):
        await handle_search_query(update, context)
    else:
        await update.message.reply_text("I don't understand that command. Please follow the prompts.")


# if __name__ == '__main__':
#     app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_API")).build()

#     app.add_handler(CommandHandler("start", start))
#     app.add_handler(CommandHandler("register", register))
#     app.add_handler(CommandHandler("feedback", feedback_command))  
#     app.add_handler(CommandHandler("help", help_command))
#     app.add_handler(CommandHandler("languages", languages_command))
#     app.add_handler(CommandHandler("discounts", discounts_command))
#     app.add_handler(CommandHandler('delete_me', delete_me))
#     app.add_handler(CommandHandler("profile", profile_command))


#     app.add_handler(MessageHandler(filters.LOCATION, location_handler))  
#     app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))  
#     app.add_handler(CallbackQueryHandler(button_handler, pattern='^(male|female|other)$'))
#     app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_feedback))
#     app.add_handler(CallbackQueryHandler(language_selection, pattern='^(az|en|tr|ru)$'))
#     app.add_handler(CallbackQueryHandler(filter_search_handler, pattern='^(all|filter|search|filter_brand|filter_category)$'))
#     app.add_handler(CallbackQueryHandler(specific_filter_handler, pattern='^(brand_|category_)'))
#     app.add_handler(MessageHandler(filters.COMMAND, command_restriction))

#     app.run_polling()