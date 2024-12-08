import os
from dotenv import load_dotenv
import logging
import psycopg2
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import CallbackContext
from datetime import datetime, timedelta
from decimal import Decimal
from .models import Profile, Product, Brand, Category, Recommendations, Feedback, SavedProduct, Merchant
from django.db.models import Q
from asgiref.sync import sync_to_async
from telegram.helpers import escape_markdown
import re
from django.utils import timezone 
import asyncio
from django.db import IntegrityError
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist


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


languages = {
    'tr': {
        'telegram_id': 'Telegram ID',
        'username': 'Kullanıcı Adı',
        'first_name': 'İsim',
        'last_name': 'Soyisim',
        'birthday': 'Doğum Günü',
        'gender': 'Cinsiyet',
        'location': 'Konum',
        'language': 'Dil',
        'role': 'Rol',
        'discount': 'İndirim',
        'notification_times': 'Bildirim Zamanları',
        'edit': 'Profili Düzenle',
        'profile_not_found': 'Profil bulunamadı.',
        'select_edit_option': 'Lütfen düzenlemek istediğiniz seçeneği seçin:',
        'cancel': 'İptal Et',
        'enter_new_location': 'Lütfen yeni konumunuzu girin:',
        'enter_new_birthdate': 'Lütfen yeni doğum tarihinizi girin (GG-AA-YYYY):',
        'select_gender': 'Lütfen cinsiyetinizi seçin:',
        'male': 'Erkek',
        'female': 'Kadın',
        'other': 'Diğer',
        "sign_up_message": "Üyeliğinizi tamamlayarak tüm özelliklerin kilidini açın. Bilgilerinizi paylaşmak için adımları takip edin:",
        'gender_updated': 'Cinsiyet başarıyla güncellendi.',
        'gender_update_failed': 'Cinsiyet güncellenirken bir hata oluştu.',
        'location_updated': 'Konum başarıyla güncellendi.',
        'location_update_failed': 'Konum güncellenirken bir hata oluştu.',
        'birthdate_updated': 'Doğum tarihi başarıyla güncellendi.',
        'birthdate_update_failed': 'Doğum tarihi güncellenirken bir hata oluştu.',
        'birthdate_too_early': 'Doğum tarihi çok erken.',
        'must_be_at_least_13': 'En az 13 yaşında olmalısınız.',
        'invalid_date_format': 'Geçersiz tarih formatı. Lütfen GG-AA-YYYY formatında girin.',
        'greeting': 'Merhaba {name}, hoş geldin!',
        'invalid_language': 'Geçersiz dil seçimi. Lütfen desteklenen dillerden birini seçin.',
        'error_message': 'Bir hata oluştu: {error}',
        'delete_success': 'Hesabınız başarıyla silindi.',
        'delete_failure': 'Hesap silme işlemi sırasında bir hata oluştu. Lütfen tekrar deneyin.',
        'ask_birthday': 'Lütfen doğum tarihinizi girin (GG-AA-YYYY):',
        'already_registered': 'Zaten kayıtlısınız.',
"error_invalid_birthday": "⚠️ Geçersiz doğum tarihi. Lütfen doğru formatta girin.",
        "error_date_too_early": "⚠️ Tarih 1 Ocak 1901'den sonraki bir tarih olmalıdır.",
        "error_under_13": "⚠️ Kayıt olmak için en az 13 yaşında olmalısınız.",
        "ask_gender": "Lütfen cinsiyetinizi seçin:",
"ask_location": "Lütfen konumunuzu paylaşın veya bölgenizi yazın:",
        "share_location": "Konumu Paylaş",
        "prompt_share_location": "Lütfen konumunuzu paylaşın.",
        "prompt_type_region": "Lütfen bölgenizi yazın:",
        "region_received": "Bölge alındı: {}",
"main_commands": (
            "✨ *Ana Komutlar:*\n"
            f"👉 /start - 🟢 Botu başlatın ve karşılama mesajı alın.\n"
            f"👉 /register - ✍️ Sistemde yeni bir kullanıcı kaydedin.\n"
            f"👉 /help - ℹ️ Mevcut komutlar hakkında yardım ve bilgi alın.\n"
            f"👉 /languages - 🌐 Bot etkileşimleri için tercih ettiğiniz dili seçin.\n\n"
        ),
        "discounts_offers": (
            "💸 *İndirimler ve Teklifler:*\n"
            f"👉 /discounts - 💵 Üzerinde mevcut indirimler ve teklifler görün.\n\n"
        ),
        "profile_account": (
            "👤 *Profil ve Hesap:*\n"
            f"👉 /profile - 👥 Kullanıcı profil bilgilerinizi görüntüleyin veya güncelleyin.\n"
            f"👉 /delete_me - ❌ Hesabınızı ve tüm ilgili verileri silin.\n"
            f"👉 /saved - 💾 Kaydedilmiş ürün listenize erişin.\n\n"
        ),
        "merchant_features": (
            "🏪 *Tüccar Özellikleri:*\n"
            f"👉 /merchant - 🛒 Tüccar spesifik işlevselliklere erişin."
        ),
        "not_registered": "Henüz kayıtlı değilsiniz. Komutlara erişmek için lütfen kayıt olun.",
        "select_language": "Lütfen bir dil seçin:",
        "az": "🇦🇿 Azerbaycan",
        "en": "🇬🇧 İngilizce",
        "tr": "🇹🇷 Türkçe",
        "ru": "🇷🇺 Rusça",
         "not_registered": "Kayıtlı değilsiniz.",
        "real_time_discounts": "Gerçek Zamanlı İndirimler",
        "favorite_categories": "Favori Kategoriler",
        "favorite_stores": "Favori Mağazalar",
        "saved_discounts": "Kaydedilmiş İndirimler",
        "profile": "Profil",
        "choose_option": "Bir seçenek seçin:",
        "product_saved": "Ürün {product_name} başarıyla kaydedildi!",
        "product_unsaved": "Ürün {product_name} kayıtlardan kaldırıldı!",
        "product_not_exist": "ID'si {product_id} olan ürün mevcut değil.",
        "user_not_found": "Kullanıcı bulunamadı.",
        "generic_error": "Bir hata oluştu, lütfen tekrar deneyin.",
        'select_filter_type': "Filtre türünü seçin:",
        'by_categories': "Kategoriye Göre",
        'by_stores': "Mağazalara Göre",
        'by_brands': "Markaya Göre",
 'no_brands_available': "Filtrelemek için mevcut marka yok.",
        'select_brand': "Bir marka seçin:",
        'add_to_favorites': "Favorilere ekle",
        'added_to_favorites': "başarıyla favorilere eklendi.",
        'removed_from_favorites': "favorilerden başarıyla kaldırıldı.",
        'brand_not_found': "Marka bulunamadı.",
        'invalid_brand_id': "Geçersiz marka ID'si.",
'category_not_found': "Kategori bulunamadı.",
        'invalid_category_id': "Geçersiz kategori ID'si.",
'no_categories': "Filtreleme için mevcut kategori yok.",
        'select_category': "Bir kategori seçin:",
        'add': "Ekle",
'no_stores': "Filtreleme için mevcut mağaza yok.",
        'select_store': "Bir mağaza seçin:",
        'no_products_found': "Ürün bulunamadı.",
        'invalid_store_id': "Geçersiz mağaza ID.",
'no_fav_brands_products': "Favori markalarınız için hiçbir ürün bulunamadı.",
        'no_fav_categories_products': "Favori kategorileriniz için hiçbir ürün bulunamadı.",
'no_categories': "Filtreleme için kullanılabilir kategori yok.",
            'select_category': "Bir kategori seçin:",
            'edit_category': "Düzenle",
'no_categories': "Şu anda kullanılabilir kategori yok.",
            'select_category': "Lütfen favori kategorinizi seçin:",
        "favorite_category_updated": "Favori kategoriniz başarıyla güncellendi.",
 "location_saved": "Teşekkürler! Konumunuz kaydedildi. Lütfen favori kategorinizi seçin.",
        "location_invalid": "Konum istekleri yalnızca kayıt sırasında geçerlidir. İşlem yapılmadı.",
"no_categories_available": "Şu anda mevcut bir kategori yok.",
        "select_favorite_category": "Lütfen favori kategorinizi seçin:",
"add_favorite_store": "Favori mağazanızı ekleyin veya 'Geç' butonuna basın:",
        "skip": "Geç",
        "category_not_found": "⚠️ Seçilen kategori bulunamadı.",
        "category_selection_error": "⚠️ Bir hata oluştu. Kategori seçimi tamamlanamadı.",
        "unexpected_error": "⚠️ Beklenmeyen bir hata oluştu",
"store_recommendation_skipped": "Mağaza öneriniz atlandı. Lütfen bir indirim yüzdesi seçin:",
        "skip_button": "❌ Geç",
        "store_recommendation_not_saved": "Mağaza öneriniz kaydedilmedi.",
        "select_discount_percentage": "Lütfen bir indirim yüzdesi seçin:",
        "select_notification_time": "Lütfen bildirim zamanınızı seçin:",
"registration_completed": "🎉 Kayıt ve mağaza önerisi başarıyla tamamlandı!",
        "error_saving_categories": "⚠️ Favori kategorileriniz kaydedilirken bir hata oluştu.",
        "favorite_categories_added": "🎉 Favori kategoriler başarıyla eklendi!",
        "no_favorite_categories": "⚠️ Favori kategoriniz bulunamadı.",
        "error_saving_recommendation": "⚠️ Mağaza öneriniz kaydedilirken bir hata oluştu.",
        "error_saving_data": "⚠️ Bilgileriniz kaydedilirken bir hata oluştu. Lütfen tekrar deneyin.",
"feedback_success":"Geri bildiriminiz için teşekkür ederiz!",
'feedback_failure':"Geri bildirim kaydedilemedi. Lütfen tekrar deneyin.",
            'unknown_command': "Bu komutu anlamıyorum. Lütfen yönlendirmeleri takip edin.",
'not_registered': "Kayıtlı değilsiniz. Lütfen önce kayıt olun.",
            'merchant_member': "🎉🎯 {merchant} adlı mağazanın üyesisiniz.\n"
                               "Bu mağaza için aşağıdaki seçenekleri yapabilirsiniz:\n\n"
                               "1️⃣ *Mağazayı Değiştir*\n"
                               "2️⃣ *Mağazadan Ayrıl*\n"
                               "3️⃣ *Ürün Ekle*\n"
                               "4️⃣ *Tüm Ürünleri Gör*\n\n"
                               "Lütfen aşağıdaki seçeneklerden birini seçin:",
            'not_merchant': "Mağaza yetkiniz yok.",
            'error': "Bir hata oluştu. Lütfen tekrar deneyin.",
            'buttons': {
                'edit_merchant': "Mağazayı Düzenle",
                'leave_merchant': "Mağazadan Ayrıl",
                'add_product': "Ürün Ekle",
                'all_products': "Tüm Ürünler"
            },
 'not_merchant_admin': "Şu anda bir mağaza yöneticisi değilsiniz.",
            'error': "Bir hata oluştu. Lütfen tekrar deneyin.",
            'enter_product_name': "Lütfen ürün adını girin:",
            'no_products_found_merchant': "Bu mağaza için ürün bulunamadı.",
            'not_merchant': "Mağaza yetkiniz yok.",
            'select_option': "Lütfen düzenlemek istediğiniz seçeneği seçin:",
            'update_name': "Mağaza Adını Güncelle",
            'show_users': "Mağaza Kullanıcılarını Göster",
            'enter_new_name': "Lütfen yeni mağaza adını girin:",
        'merchant_users': "Mağaza rolüne sahip kullanıcılar:",
'no_users': "⚠️ Kullanıcı bulunamadı.",
        'error_occurred': "❌ Bir hata oluştu:",
        'remove_user': "Kaldır",
'user_removed': "✅ {username} adlı kullanıcı mağaza rolünden kaldırıldı.",
        'user_not_found': "⚠️ Kullanıcı bulunamadı.",
 'merchant_id_not_found': "⚠️ Mağaza ID bulunamadı. Lütfen tekrar deneyin.",
        'merchant_updated': "✅ Mağaza adı '{new_name}' olarak güncellendi!",
        'merchant_not_found': "⚠️ Mağaza bulunamadı.",
        'error_occurred': "❌ Bir hata oluştu:",
        'confirm_leave_merchant': "Ticaret rolünü bırakmak istediğinizden emin misiniz?",
        'yes_leave_merchant': "Evet, ticaret rolünden ayrıl",
        'no_keep_role': "Hayır, rolümü koru",
        'leave_success': "Ticaret rolünden başarıyla ayrıldınız.",
        'update_issue': "Profilinizi güncellerken bir sorun oluştu.",
        'profile_not_exist': "Profiliniz mevcut değil.",
        'keep_role_message': "Ticaret rolünü korumayı seçtiniz.",
'product_remove_success': "✅ Product '{}' has been removed successfully!",
        'no_permission_to_remove_product': "⚠️ You do not have permission to remove this product.",
        'product_not_found': "⚠️ Product with id {} does not exist.",
'product_title': "Başlık",
        'product_description': "Açıklama",
        'original_price': "Orijinal Fiyat",
        'discounted_price': "İndirimli Fiyat",
        'last_day': "Son Gün",
        'save': "Kaydet",
        'remove': "Kaldır",
        'link': "Bağlantı",
        'display_error': "Ürünü gösterirken bir hata oluştu: {}.",
        'invalid_image': "Geçersiz resim: {}.",
        "language_changed": "Dil değiştirildi.",
        "available_commands": "Mevcut Komutlar",
    },
    'en': {
        'telegram_id': 'Telegram ID',
        'username': 'Username',
        'first_name': 'First Name',
        'last_name': 'Last Name',
        'birthday': 'Birthday',
        'gender': 'Gender',
        'location': 'Location',
        'language': 'Language',
        'role': 'Role',
        'discount': 'Discount',
        'notification_times': 'Notification Times',
        'edit': 'Edit Profile',
        'profile_not_found': 'Profile not found.',
        'select_edit_option': 'Please select an option to edit:',
        'cancel': 'Cancel',
        'enter_new_location': 'Please enter your new location:',
        'enter_new_birthdate': 'Please enter your new birthdate (DD-MM-YYYY):',
        'select_gender': 'Please select your gender:',
        'male': 'Male',
        'female': 'Female',
        'other': 'Other',
        "sign_up_message": "Please finish signing up to unlock all features. Just follow the steps to share your information:",
        'gender_updated': 'Gender has been successfully updated.',
        'gender_update_failed': 'An error occurred while updating gender.',
        'location_updated': 'Location has been successfully updated.',
        'location_update_failed': 'An error occurred while updating location.',
        'birthdate_updated': 'Birthdate has been successfully updated.',
        'birthdate_update_failed': 'An error occurred while updating birthdate.',
        'birthdate_too_early': 'Birthdate is too early.',
        'must_be_at_least_13': 'You must be at least 13 years old.',
        'invalid_date_format': 'Invalid date format. Please enter in DD-MM-YYYY format.',
        'greeting': 'Hello {name}, welcome!',
        'invalid_language': 'Invalid language selection. Please choose one of the supported languages.',
        'error_message': 'An error occurred: {error}',
        'delete_success': 'Your account has been successfully deleted.',
        'delete_failure': 'An error occurred while deleting your account. Please try again.',
        'ask_birthday': 'Please enter your birthdate (DD-MM-YYYY):',
        'already_registered': 'You are already registered.',
        "error_invalid_birthday": "⚠️ Invalid birthday. Please enter a valid format.",
        "error_date_too_early": "⚠️ The date must be later than 1 January 1901.",
        "error_under_13": "⚠️ You must be at least 13 years old to register.",
        "ask_gender": "Please select your gender:",
        "ask_location": "Please share your location or type your region:",
        "share_location": "Share Location",
        "prompt_share_location": "Please share your location.",
        "prompt_type_region": "Please type your region:",
        "region_received": "Region received: {}",
        "main_commands": (
            "✨ *Main Commands:*\n"
            f"👉 /start - 🟢 Start the bot and receive a welcome message.\n"
            f"👉 /register - ✍️ Register a new user in the system.\n"
            f"👉 /help - ℹ️ Get assistance and information about available commands.\n"
            f"👉 /languages - 🌐 Choose your preferred language for bot interactions.\n\n"
        ),
        "discounts_offers": (
            "💸 *Discounts & Offers:*\n"
            f"👉 /discounts - 💵 View available discounts and offers on products.\n\n"
        ),
        "profile_account": (
            "👤 *Profile & Account:*\n"
            f"👉 /profile - 👥 View or update your user profile information.\n"
            f"👉 /delete_me - ❌ Delete your account and all related data.\n"
            f"👉 /saved - 💾 Access your saved products list.\n\n"
        ),
        "merchant_features": (
            "🏪 *Merchant Features:*\n"
            f"👉 /merchant - 🛒 Access merchant-specific functionalities."
        ),
        "not_registered": "You are not registered. Please register to access the commands.",
        "select_language": "Please select a language:",
        "az": "🇦🇿 Azerbaijani",
        "en": "🇬🇧 English",
        "tr": "🇹🇷 Turkish",
        "ru": "🇷🇺 Russian",
         "not_registered": "You are not registered.",
        "real_time_discounts": "Real Time Discounts",
        "favorite_categories": "Favorite Categories",
        "favorite_stores": "Favorite Stores",
        "saved_discounts": "Saved Discounts",
        "profile": "Profile",
        "choose_option": "Choose an option:",
        "product_saved": "Product {product_name} saved successfully!",
        "product_unsaved": "Product {product_name} unsaved successfully!",
        "product_not_exist": "Product with id {product_id} does not exist.",
        "user_not_found": "User not found.",
        "generic_error": "An error occurred, please try again.",
        'select_filter_type': "Select filter type:",
        'by_categories': "By Categories",
        'by_stores': "By Stores",
        'by_brands': "By Brands",
        'no_brands_available': "No brands available for filtering.",
        'select_brand': "Select a brand:",
        'add_to_favorites': "Add to favorites",
        'added_to_favorites': "has been successfully added to favorites.",
        'removed_from_favorites': "has been successfully removed from favorites.",
        'brand_not_found': "No brand found.",
        'invalid_brand_id': "Invalid brand ID.",
        'category_not_found': "No category found.",
        'invalid_category_id': "Invalid category ID.",
        'select_category': "Select a category:",
        'add': "Add",
        'no_stores': "No store available for filtering.",
        'select_store': "Select a store:",
        'no_products_found': "No products found.",
        'invalid_store_id': "Invalid store ID.",
        'no_fav_brands_products': "No products were found for your favorite brands.",
        'no_fav_categories_products': "No products were found for your favorite categories.",
        'select_category': "Select a category:",
        'edit_category': "Edit",
        'no_categories': "Currently, there are no categories available.",
        'select_category': "Please select your favorite category:",
        "favorite_category_updated": "Your favorite category has been successfully updated.",
        "location_saved": "Thank you! Your location has been saved. Please proceed to select your favorite category.",
        "location_invalid": "Location requests are only valid during registration. No action taken.",
        "no_categories_available": "Currently, there are no categories available.",
        "select_favorite_category": "Please select your favorite category:",
        "add_favorite_store": "Add your favorite store or press the 'Skip' button:",
        "skip": "Skip",
        "category_not_found": "⚠️ The selected category was not found.",
        "category_selection_error": "⚠️ An error occurred. Category selection could not be completed.",
        "unexpected_error": "⚠️ An unexpected error occurred",
        "store_recommendation_skipped": "Your store recommendation has been skipped. Please select a discount percentage:",
        "skip_button": "❌ Skip",
        "store_recommendation_not_saved": "Your store recommendation has not been saved.",
        "select_discount_percentage": "Please select a discount percentage:",
        "select_notification_time": "Please select your notification time:",
        "registration_completed": "🎉 Registration and store recommendation completed successfully!",
        "error_saving_categories": "⚠️ An error occurred while saving your favorite categories.",
        "favorite_categories_added": "🎉 Favorite categories added successfully!",
        "no_favorite_categories": "⚠️ No favorite categories found.",
        "error_saving_recommendation": "⚠️ An error occurred while saving your store recommendation.",
        "error_saving_data": "⚠️ An error occurred while saving your data. Please try again.",
        "feedback_success":"Thank you for your feedback!",
        'feedback_failure':"Failed to save feedback. Please try again.",
        'unknown_command': "I don't understand that command. Please follow the prompts.",
        'not_registered': "You are not registered. Please register first.",
        'merchant_member': "🎉🎯 You are a member of the merchant named {merchant}.\n"
                               "You can make the following selections for this merchant:\n\n"
                               "1️⃣ *Change the Merchant*\n"
                               "2️⃣ *Leave the Merchant*\n"
                               "3️⃣ *Add Product*\n"
                               "4️⃣ *View All Products*\n\n"
                               "Please make a selection from the options below:",
        'not_merchant': "You do not have merchant permissions.",
        'error': "An error occurred. Please try again.",
        'buttons': {
                'edit_merchant': "Edit Merchant",
                'leave_merchant': "Leave Merchant",
                'add_product': "Add Product",
                'all_products': "All Products"
            },
        'not_merchant_admin': "You are not currently a merchant admin.",
        'enter_product_name': "Please enter the product name:",
        'no_products_found_merchant': "No products found for this merchant.",
        'select_option': "Please select the option you want to edit:",
        'update_name': "Update Merchant Name",
        'show_users': "Show Merchant Users",
        'enter_new_name': "Please enter the new merchant name:",
        'merchant_users': "Users with Merchant role:",
        'no_users': "⚠️ No users found.",
        'error_occurred': "❌ An error occurred:",
        'remove_user': "Remove",
        'user_removed': "✅ User {username} has been removed from the merchant role.",
        'user_not_found': "⚠️ User not found.",
        'merchant_id_not_found': "⚠️ Merchant ID not found. Please try again.",
        'merchant_updated': "✅ Merchant name has been updated to '{new_name}'!",
        'merchant_not_found': "⚠️ Merchant not found.",
        'confirm_leave_merchant': "Are you sure you want to leave the merchant role?",
        'yes_leave_merchant': "Yes, leave merchant role",
        'no_keep_role': "No, keep my role",
        'leave_success': "You have successfully left the merchant role.",
        'update_issue': "There was an issue updating your profile.",
        'profile_not_exist': "Your profile does not exist.",
        'keep_role_message': "You have chosen to keep your merchant role.",
        'product_remove_success': "✅ Product '{}' has been removed successfully!",
        'no_permission_to_remove_product': "⚠️ You do not have permission to remove this product.",
        'product_not_found': "⚠️ Product with id {} does not exist.",
        'product_title': "Title",
        'product_description': "Description",
        'original_price': "Original Price",
        'discounted_price': "Discounted Price",
        'last_day': "Last Day",
        'save': "Save",
        'remove': "Remove",
        'link': "Link",
        'display_error': "An error occurred while displaying the product: {}.",
        'invalid_image': "Invalid image for the product: {}.",
        "language_changed": "Language changed.",
        "available_commands": "Available Commands",
    },
    "az": {
        'telegram_id': 'Telegram ID',
        'username': 'İstifadəçi adı',
        'first_name': 'Ad',
        'last_name': 'Soyad',
        'birthday': 'Doğum tarixi',
        'gender': 'Cins',
        'location': 'Məkan',
        'language': 'Dil',
        'role': 'Rol',
        'discount': 'Endirim',
        'notification_times': 'Bildiriş vaxtları',
        'edit': 'Profil düzəlişi',
        'profile_not_found': 'Profil tapılmadı.',
        'select_edit_option': 'Düzəliş etmək üçün bir seçim seçin:',
        'cancel': 'İmtina et',
        'enter_new_location': 'Yeni məkanınızı daxil edin:',
        'enter_new_birthdate': 'Yeni doğum tarixini daxil edin (GG-AA-YYYY):',
        'select_gender': 'Cinsinizi seçin:',
        'male': 'Kişi',
        'female': 'Qadın',
        'other': 'Digər',
        "sign_up_message": "Bütün xüsusiyyətləri açmaq üçün qeydiyyatdan keçin. Məlumatınızı paylaşmaq üçün addımları izləyin:",
        'gender_updated': 'Cins uğurla yeniləndi.',
        'gender_update_failed': 'Cinsi yeniləyərkən xəta baş verdi.',
        'location_updated': 'Məkan uğurla yeniləndi.',
        'location_update_failed': 'Məkanı yeniləyərkən xəta baş verdi.',
        'birthdate_updated': 'Doğum tarixi uğurla yeniləndi.',
        'birthdate_update_failed': 'Doğum tarixini yeniləyərkən xəta baş verdi.',
        'birthdate_too_early': 'Doğum tarixi çox erkəndir.',
        'must_be_at_least_13': 'Ən azı 13 yaşında olmalısınız.',
        'invalid_date_format': 'Yanlış tarix formatı. GG-AA-YYYY formatında daxil edin.',
        'greeting': 'Salam {name}, xoş gəlmisiniz!',
        'invalid_language': 'Yanlış dil seçimi. Dəstəklənən dillərdən birini seçin.',
        'error_message': 'Xəta baş verdi: {error}',
        'delete_success': 'Hesabınız uğurla silindi.',
        'delete_failure': 'Hesabı silərkən xəta baş verdi. Zəhmət olmasa yenidən cəhd edin.',
        'ask_birthday': 'Doğum tarixini daxil edin (GG-AA-YYYY):',
        'already_registered': 'Artıq qeydiyyatdan keçmisiniz.',
        "error_invalid_birthday": "⚠️ Yanlış doğum tarixi. Düzgün formatda daxil edin.",
        "error_date_too_early": "⚠️ Tarix 1901-ci ilin 1 yanvarından sonra olmalıdır.",
        "error_under_13": "⚠️ Qeydiyyatdan keçmək üçün ən azı 13 yaşında olmalısınız.",
        "ask_gender": "Cinsinizi seçin:",
        "ask_location": "Məkanınızı paylaşın və ya bölgənizi daxil edin:",
        "share_location": "Məkânı paylaş",
        "prompt_share_location": "Zəhmət olmasa məkânınızı paylaşın.",
        "prompt_type_region": "Zəhmət olmasa bölgənizi daxil edin:",
        "region_received": "Bölgə alındı: {}",
        "main_commands": (
            "✨ *Əsas Əmrər:*\n"
            f"👉 /start - 🟢 Botu başladın və xoş gəlmisiniz mesajı alın.\n"
            f"👉 /register - ✍️ Sistemdə yeni istifadəçi qeydiyyatdan keçirin.\n"
            f"👉 /help - ℹ️ Mövcud əmrlər haqqında kömək və məlumat alın.\n"
            f"👉 /languages - 🌐 Bot inteqrasiyaları üçün sevimli dilinizi seçin.\n\n"
        ),
        "discounts_offers": (
            "💸 *Endirimlər & Təkliflər:*\n"
            f"👉 /discounts - 💵 Məhsullardakı endirimləri və təklifləri görün.\n\n"
        ),
        "profile_account": (
            "👤 *Profil & Hesab:*\n"
            f"👉 /profile - 👥 İstifadəçi profil məlumatlarınızı görün və ya yeniləyin.\n"
            f"👉 /delete_me - ❌ Hesabınızı və bütün əlaqəli məlumatlarınızı silin.\n"
            f"👉 /saved - 💾 Saxlanmış məhsul siyahınıza daxil olun.\n\n"
        ),
        "merchant_features": (
            "🏪 *Ticarətçi Xüsusiyyətləri:*\n"
            f"👉 /merchant - 🛒 Ticarətçiyə xüsusi funksiyalardan istifadə edin."
        ),
        "not_registered": "Siz qeydiyyatdan keçməmisiniz. Əmrlərə daxil olmaq üçün qeydiyyatdan keçin.",
        "select_language": "Zəhmət olmasa bir dil seçin:",
        "az": "🇦🇿 Azərbaycan",
        "en": "🇬🇧 İngilis",
        "tr": "🇹🇷 Türk",
        "ru": "🇷🇺 Rus",
        "not_registered": "Siz qeydiyyatdan keçməyibsiniz.",
        "real_time_discounts": "Real Vaxt Endirimləri",
        "favorite_categories": "Sevimli Kateqoriyalar",
        "favorite_stores": "Sevimli Mağazalar",
        "saved_discounts": "Saxlanmış Endirimlər",
        "profile": "Profil",
        "choose_option": "Bir seçim edin:",
        "product_saved": "Məhsul {product_name} uğurla saxlanıldı!",
        "product_unsaved": "Məhsul {product_name} uğurla silindi!",
        "product_not_exist": "ID {product_id} olan məhsul yoxdur.",
        "user_not_found": "İstifadəçi tapılmadı.",
        "generic_error": "Xəta baş verdi, zəhmət olmasa yenidən cəhd edin.",
        'select_filter_type': "Filtrləmə növünü seçin:",
        'by_categories': "Kateqoriyalarla",
        'by_stores': "Mağazalarla",
        'by_brands': "Brendlərlə",
        'no_brands_available': "Filtrləmək üçün heç bir marka mövcud deyil.",
        'select_brand': "Bir marka seçin:",
        'add_to_favorites': "Sevimlilərə əlavə et",
        'added_to_favorites': "sevimlilərə uğurla əlavə edildi.",
        'removed_from_favorites': "sevimlilərdə uğurla silindi.",
        'brand_not_found': "Heç bir marka tapılmadı.",
        'invalid_brand_id': "Yanlış marka ID-si.",
        'category_not_found': "Heç bir kateqoriya tapılmadı.",
        'invalid_category_id': "Yanlış kateqoriya ID-si.",
        'select_category': "Bir kateqoriya seçin:",
        'add': "Əlavə et",
        'no_stores': "Filtrləmək üçün heç bir mağaza mövcud deyil.",
        'select_store': "Bir mağaza seçin:",
        'no_products_found': "Məhsul tapılmadı.",
        'invalid_store_id': "Yanlış mağaza ID-si.",
        'no_fav_brands_products': "Sevimli markalarınız üçün heç bir məhsul tapılmadı.",
        'no_fav_categories_products': "Sevimli kateqoriyalarınız üçün heç bir məhsul tapılmadı.",
        'select_category': "Kateqoriya seç:",
        'edit_category': "Düzəliş et",
        'no_categories': "Hal-hazırda, heç bir kateqoriya mövcud deyil.",
        "favorite_category_updated": "Sevimli kateqoriyanız uğurla yeniləndi.",
        "location_saved": "Təşəkkürlər! Məkanınız saxlanıldı. Zəhmət olmasa sevimli kateqoriyanızı seçməyə davam edin.",
        "location_invalid": "Məkan tələbləri yalnız qeydiyyat zamanı etibarlıdır. Heç bir əməliyyat həyata keçirilmədi.",
        "no_categories_available": "Hal-hazırda, heç bir kateqoriya mövcud deyil.",
        "select_favorite_category": "Zəhmət olmasa sevimli kateqoriyanızı seçin:",
        "add_favorite_store": "Sevimli mağazanızı əlavə edin və ya 'Keç' düyməsini basın:",
        "skip": "Keç",
        "category_not_found": "⚠️ Seçilən kateqoriya tapılmadı.",
        "category_selection_error": "⚠️Xəta baş verdi. Kateqoriya seçimi tamamlana bilmədi.",
        "unexpected_error": "⚠️ Başqa bir xəta baş verdi",
        "store_recommendation_skipped": "Mağaza tövsiyə edilmədi. Zəhmət olmasa, endirim faizini seçin:",
        "skip_button": "❌ Keç",
        "store_recommendation_not_saved": "Mağaza tövsiyəniz saxlanılmadı.",
        "select_discount_percentage": "Zəhmət olmasa, endirim faizini seçin:",
        "select_notification_time": "Zəhmət olmasa, bildiriş vaxtınızı seçin:",
        "registration_completed": "🎉 Qeydiyyat və mağaza tövsiyəsi uğurla tamamlandı!",
        "error_saving_categories": "⚠️ Sevimli kateqoriyaların saxlanılmasında xəta baş verdi.",
        "favorite_categories_added": "🎉 Sevimli kateqoriyalar uğurla əlavə edildi!",
        "no_favorite_categories": "⚠️ Sevimli kateqoriyalar tapılmadı.",
        "error_saving_recommendation": "⚠️ Mağaza tövsiyəsini saxlayarkən xəta baş verdi.",
        "error_saving_data": "⚠️ Məlumatınızı saxlayarkən xəta baş verdi. Zəhmət olmasa, yenidən cəhd edin.",
        "feedback_success": "Fikrinizi bildirdiyiniz üçün təşəkkür edirik!",
        "feedback_failure": "Fikrinizi saxlamaq mümkün olmadı. Zəhmət olmasa, yenidən cəhd edin.",
        "unknown_command": "Bu əmri başa düşmürəm. Zəhmət olmasa, təlimatlara əməl edin.",
        "not_registered": "Siz qeydiyyatdan keçməmisiniz. Zəhmət olmasa, əvvəlcə qeydiyyatdan keçin.",
        "merchant_member": "🎉🎯 Siz {merchant} adlı ticarətçinin üzvüsünüz.\n"
                        "Bu ticarətçi üçün aşağıdakı seçimləri edə bilərsiniz:\n\n"
                        "1️⃣ *Ticarətçini Dəyişdir*\n"
                        "2️⃣ *Ticarətçidən Çıx*\n"
                        "3️⃣ *Məhsul Əlavə Et*\n"
                        "4️⃣ *Bütün Məhsulları Gör*\n\n"
                        "Aşağıdakı seçimlərdən birini seçin:",
        "not_merchant": "Sizin ticarətçi icazəniz yoxdur.",
        "error": "Bir xəta baş verdi. Zəhmət olmasa, yenidən cəhd edin.",
        "buttons": {
            "edit_merchant": "Ticarətçini Dəyişdir",
            "leave_merchant": "Ticarətçidən Çıx",
            "add_product": "Məhsul Əlavə Et",
            "all_products": "Bütün Məhsullar"
        },
        "not_merchant_admin": "Siz hal-hazırda ticarətçi admini deyilsiniz.",
        "enter_product_name": "Zəhmət olmasa, məhsulun adını daxil edin:",
        "no_products_found_merchant": "Bu ticarətçi üçün heç bir məhsul tapılmadı.",
        "select_option": "Zəhmət olmasa, redaktə etmək istədiyiniz seçimi seçin:",
        "update_name": "Ticarətçi Adını Yenilə",
        "show_users": "Ticarətçi İstifadəçilərini Göstər",
        "enter_new_name": "Zəhmət olmasa, yeni ticarətçi adını daxil edin:",
        "merchant_users": "Ticarətçi roluna malik istifadəçilər:",
        "no_users": "⚠️ Heç bir istifadəçi tapılmadı.",
        "remove_user": "Sil",
        "user_removed": "✅ {username} adlı istifadəçi ticarətçi rolundan silindi.",
        "user_not_found": "⚠️ İstifadəçi tapılmadı.",
        "merchant_id_not_found": "⚠️ Ticarətçi ID-si tapılmadı. Zəhmət olmasa, yenidən cəhd edin.",
        "merchant_updated": "✅ Ticarətçi adı '{new_name}' olaraq yeniləndi!",
        "merchant_not_found": "⚠️ Ticarətçi tapılmadı.",
        "confirm_leave_merchant": "Ticarətçi rolunu tərk etmək istədiyinizə əminsinizmi?",
        "yes_leave_merchant": "Bəli, ticarətçi rolunu tərk et",
        "no_keep_role": "Xeyr, rolumu saxlamaq istəyirəm",
        "leave_success": "Ticarətçi rolunu uğurla tərk etdiniz.",
        "update_issue": "Profilinizi yeniləməkdə problem yarandı.",
        "profile_not_exist": "Profiliniz mövcud deyil.",
        "keep_role_message": "Siz ticarətçi rolunuzu saxlamağı seçdiniz.",
        "product_remove_success": "✅ '{}' məhsulu uğurla silindi!",
        "no_permission_to_remove_product": "⚠️ Bu məhsulu silmək üçün icazəniz yoxdur.",
        "product_not_found": "⚠️ ID-si {} olan məhsul mövcud deyil.",
        "product_title": "Başlıq",
        "product_description": "Təsvir",
        "original_price": "Əsas Qiymət",
        "discounted_price": "Endirimli Qiymət",
        "last_day": "Son Gün",
        "save": "Saxla",
        "remove": "Sil",
        "link": "Link",
        "display_error": "Məhsulu göstərərkən xəta baş verdi: {}.",
        "invalid_image": "Məhsul üçün keçərsiz şəkil: {}.",
        "language_changed": "Dil dəyişdirildi.",
        "available_commands": "Mövcud Əmrlər",
    },
    'ru': {
    'telegram_id': 'Телеграм ID',
    'username': 'Имя пользователя',
    'first_name': 'Имя',
    'last_name': 'Фамилия',
    'birthday': 'День рождения',
    'gender': 'Пол',
    'location': 'Местоположение',
    'language': 'Язык',
    'role': 'Роль',
    'discount': 'Скидка',
    'notification_times': 'Время уведомления',
    'edit': 'Редактировать профиль',
    'profile_not_found': 'Профиль не найден.',
    'select_edit_option': 'Пожалуйста, выберите опцию для редактирования:',
    'cancel': 'Отмена',
    'enter_new_location': 'Пожалуйста, введите ваше новое местоположение:',
    'enter_new_birthdate': 'Пожалуйста, введите вашу новую дату рождения (ДД-ММ-ГГГГ):',
    'select_gender': 'Пожалуйста, выберите ваш пол:',
    'male': 'Мужчина',
    'female': 'Женщина',
    'other': 'Другое',
    "sign_up_message": "Пожалуйста, завершите регистрацию, чтобы разблокировать все функции. Просто следуйте инструкциям, чтобы поделиться своей информацией:",
    'gender_updated': 'Пол успешно обновлен.',
    'gender_update_failed': 'Произошла ошибка при обновлении пола.',
    'location_updated': 'Местоположение успешно обновлено.',
    'location_update_failed': 'Произошла ошибка при обновлении местоположения.',
    'birthdate_updated': 'Дата рождения успешно обновлена.',
    'birthdate_update_failed': 'Произошла ошибка при обновлении даты рождения.',
    'birthdate_too_early': 'Дата рождения слишком ранняя.',
    'must_be_at_least_13': 'Вы должны быть не моложе 13 лет.',
    'invalid_date_format': 'Неверный формат даты. Пожалуйста, введите в формате ДД-ММ-ГГГГ.',
    'greeting': 'Здравствуйте, {name}, добро пожаловать!',
    'invalid_language': 'Неверный выбор языка. Пожалуйста, выберите один из поддерживаемых языков.',
    'error_message': 'Произошла ошибка: {error}',
    'delete_success': 'Ваш аккаунт был успешно удален.',
    'delete_failure': 'Произошла ошибка при удалении вашего аккаунта. Пожалуйста, попробуйте снова.',
    'ask_birthday': 'Пожалуйста, введите вашу дату рождения (ДД-ММ-ГГГГ):',
    'already_registered': 'Вы уже зарегистрированы.',
    "error_invalid_birthday": "⚠️ Неверная дата рождения. Пожалуйста, введите правильный формат.",
    "error_date_too_early": "⚠️ Дата должна быть позже 1 января 1901 года.",
    "error_under_13": "⚠️ Вы должны быть не моложе 13 лет для регистрации.",
    "ask_gender": "Пожалуйста, выберите ваш пол:",
    "ask_location": "Пожалуйста, поделитесь вашим местоположением или введите ваш регион:",
    "share_location": "Поделиться местоположением",
    "prompt_share_location": "Пожалуйста, поделитесь своим местоположением.",
    "prompt_type_region": "Пожалуйста, введите ваш регион:",
    "region_received": "Регион получен: {}",
    "main_commands": (
        "✨ *Главные команды:*\n"
        f"👉 /start - 🟢 Начать бота и получить приветственное сообщение.\n"
        f"👉 /register - ✍️ Зарегистрироваться в системе.\n"
        f"👉 /help - ℹ️ Получить помощь и информацию о доступных командах.\n"
        f"👉 /languages - 🌐 Выберите предпочитаемый язык для взаимодействия с ботом.\n\n"
    ),
    "discounts_offers": (
        "💸 *Скидки и предложения:*\n"
        f"👉 /discounts - 💵 Просмотреть доступные скидки и предложения на продукты.\n\n"
    ),
    "profile_account": (
        "👤 *Профиль и аккаунт:*\n"
        f"👉 /profile - 👥 Просмотреть или обновить информацию о вашем профиле.\n"
        f"👉 /delete_me - ❌ Удалить ваш аккаунт и все связанные данные.\n"
        f"👉 /saved - 💾 Получить доступ к списку сохраненных продуктов.\n\n"
    ),
    "merchant_features": (
        "🏪 *Функции для продавцов:*\n"
        f"👉 /merchant - 🛒 Получить доступ к функциям, предназначенным для продавцов."
    ),
    "not_registered": "Вы не зарегистрированы. Пожалуйста, зарегистрируйтесь, чтобы получить доступ к командам.",
    "select_language": "Пожалуйста, выберите язык:",
    "az": "🇦🇿 Азербайджанский",
    "en": "🇬🇧 Английский",
    "tr": "🇹🇷 Турецкий",
    "ru": "🇷🇺 Русский",
    "not_registered": "Вы не зарегистрированы.",
    "real_time_discounts": "Скидки в реальном времени",
    "favorite_categories": "Любимые категории",
    "favorite_stores": "Любимые магазины",
    "saved_discounts": "Сохраненные скидки",
    "profile": "Профиль",
    "choose_option": "Выберите опцию:",
    "product_saved": "Продукт {product_name} успешно сохранен!",
    "product_unsaved": "Продукт {product_name} успешно удален!",
    "product_not_exist": "Продукт с id {product_id} не существует.",
    "user_not_found": "Пользователь не найден.",
    "generic_error": "Произошла ошибка, пожалуйста, попробуйте снова.",
    'select_filter_type': "Выберите тип фильтра:",
    'by_categories': "По категориям",
    'by_stores': "По магазинам",
    'by_brands': "По брендам",
    'no_brands_available': "Нет доступных брендов для фильтрации.",
    'select_brand': "Выберите бренд:",
    'add_to_favorites': "Добавить в избранное",
    'added_to_favorites': "успешно добавлен в избранное.",
    'removed_from_favorites': "успешно удален из избранного.",
    'brand_not_found': "Бренд не найден.",
    'invalid_brand_id': "Неверный ID бренда.",
    'category_not_found': "Категория не найдена.",
    'invalid_category_id': "Неверный ID категории.",
    'select_category': "Выберите категорию:",
    'add': "Добавить",
    'no_stores': "Нет доступных магазинов для фильтрации.",
    'select_store': "Выберите магазин:",
    'no_products_found': "Товары не найдены.",
    'invalid_store_id': "Неверный ID магазина.",
    'no_fav_brands_products': "Не найдено товаров для ваших любимых брендов.",
    'no_fav_categories_products': "Не найдено товаров для ваших любимых категорий.",
    'select_category': "Выберите категорию:",
    'edit_category': "Редактировать",
    'no_categories': "В настоящее время нет доступных категорий.",
    'select_category': "Пожалуйста, выберите вашу любимую категорию:",
    "favorite_category_updated": "Ваша любимая категория успешно обновлена.",
    "location_saved": "Спасибо! Ваше местоположение сохранено. Пожалуйста, продолжите выбирать вашу любимую категорию.",
    "location_invalid": "Запросы на местоположение действительны только во время регистрации. Действие не выполнено.",
    "no_categories_available": "В настоящее время нет доступных категорий.",
    "select_favorite_category": "Пожалуйста, выберите вашу любимую категорию:",
    "add_favorite_store": "Добавьте ваш любимый магазин или нажмите кнопку 'Пропустить':",
    "skip": "Пропустить",
    "category_not_found": "⚠️ Выбранная категория не найдена.",
    "category_selection_error": "⚠️ Произошла ошибка. Выбор категории не может быть завершен.",
    "unexpected_error": "⚠️ Произошла неожиданная ошибка",
    "store_recommendation_skipped": "Ваша рекомендация магазина была пропущена. Пожалуйста, выберите процент скидки:",
    "skip_button": "❌ Пропустить",
    "store_recommendation_not_saved": "Ваша рекомендация магазина не была сохранена.",
    "select_discount_percentage": "Пожалуйста, выберите процент скидки:",
    "select_notification_time": "Пожалуйста, выберите время уведомления:",
    "registration_completed": "🎉 Регистрация и рекомендация магазина успешно завершены!",
    "error_saving_categories": "⚠️ Произошла ошибка при сохранении ваших любимых категорий.",
    "favorite_categories_added": "🎉 Любимые категории успешно добавлены!",
    "no_favorite_categories": "⚠️ Любимые категории не найдены.",
    "error_saving_recommendation": "⚠️ Произошла ошибка при сохранении вашей рекомендации магазина.",
    "error_saving_data": "⚠️ Произошла ошибка при сохранении ваших данных. Пожалуйста, попробуйте еще раз.",
    "feedback_success": "Спасибо за ваш отзыв!",
    "feedback_failure": "Не удалось сохранить отзыв. Пожалуйста, попробуйте еще раз.",
    "unknown_command": "Я не понимаю эту команду. Пожалуйста, следуйте подсказкам.",
    "not_registered": "Вы не зарегистрированы. Пожалуйста, сначала зарегистрируйтесь.",
    "merchant_member": "🎉🎯 Вы являетесь членом торговца с именем {merchant}.\n"
                       "Вы можете сделать следующие выборы для этого торговца:\n\n"
                       "1️⃣ *Изменить торговца*\n"
                       "2️⃣ *Покинуть торговца*\n"
                       "3️⃣ *Добавить продукт*\n"
                       "4️⃣ *Посмотреть все продукты*\n\n"
                       "Пожалуйста, выберите один из вариантов ниже:",
    "not_merchant": "У вас нет разрешений торговца.",
    "error": "Произошла ошибка. Пожалуйста, попробуйте еще раз.",
    "buttons": {
        "edit_merchant": "Редактировать торговца",
        "leave_merchant": "Покинуть торговца",
        "add_product": "Добавить продукт",
        "all_products": "Все продукты"
    },
    "not_merchant_admin": "Вы сейчас не администратор торговца.",
    "enter_product_name": "Пожалуйста, введите название продукта:",
    "no_products_found_merchant": "Продукты для этого торговца не найдены.",
    "select_option": "Пожалуйста, выберите вариант, который хотите изменить:",
    "update_name": "Обновить название торговца",
    "show_users": "Показать пользователей торговца",
    "enter_new_name": "Пожалуйста, введите новое название торговца:",
    "merchant_users": "Пользователи с ролью торговца:",
    "no_users": "⚠️ Пользователи не найдены.",
    "error_occurred": "❌ Произошла ошибка:",
    "remove_user": "Удалить",
    "user_removed": "✅ Пользователь {username} был удален из роли торговца.",
    "user_not_found": "⚠️ Пользователь не найден.",
    "merchant_id_not_found": "⚠️ ID торговца не найден. Пожалуйста, попробуйте еще раз.",
    "merchant_updated": "✅ Название торговца обновлено на '{new_name}'!",
    "merchant_not_found": "⚠️ Торговец не найден.",
    "confirm_leave_merchant": "Вы уверены, что хотите покинуть роль торговца?",
    "yes_leave_merchant": "Да, покинуть роль торговца",
    "no_keep_role": "Нет, я хочу сохранить свою роль",
    "leave_success": "Вы успешно покинули роль торговца.",
    "update_issue": "Произошла проблема при обновлении вашего профиля.",
    "profile_not_exist": "Ваш профиль не существует.",
    "keep_role_message": "Вы решили сохранить свою роль торговца.",
    "product_remove_success": "✅ Продукт '{}' успешно удален!",
    "no_permission_to_remove_product": "⚠️ У вас нет разрешения на удаление этого продукта.",
    "product_not_found": "⚠️ Продукт с ID {} не существует.",
    "product_title": "Название",
    "product_description": "Описание",
    "original_price": "Исходная цена",
    "discounted_price": "Скидочная цена",
    "last_day": "Последний день",
    "save": "Сохранить",
    "remove": "Удалить",
    "link": "Ссылка",
    "display_error": "Произошла ошибка при отображении продукта: {}.",
    "invalid_image": "Недействительное изображение для продукта: {}.",
    "language_changed": "Язык изменен.",
    "available_commands": "Доступные команды"
}
}


@sync_to_async
def fetch_all_discounted_products_sync():
    return list(Product.objects.filter(
        discount_end_date__gte=datetime.now(),
        discount_start_date__lte=datetime.now()
    ).values())


async def fetch_all_discounted_products():
    return await fetch_all_discounted_products_sync()


@sync_to_async
def increment_click_count_sync(product_id):
    try:
        product = Product.objects.get(id=product_id)
        product.click_count = product.click_count + 1 if product.click_count else 1
        product.save()
        return {"success": True, "message": "Click count incremented successfully."}
    except Product.DoesNotExist:
        return {"success": False, "message": "Product not found."}


async def increment_click_count(product_id):
    return await increment_click_count_sync(product_id)


@sync_to_async
def fetch_all_discounted_products_by_merchant_sync(id):
    return list(Product.objects.filter(
        merchant__title=id,
        discount_end_date__gte=datetime.now(),
        discount_start_date__lte=datetime.now()
    ).values())


async def fetch_all_discounted_products_by_merchant(id):
    return await fetch_all_discounted_products_by_merchant_sync(id)


@sync_to_async
def fetch_all_brands_sync():
    return list(Brand.objects.all().values())


async def fetch_all_brands():
    return await fetch_all_brands_sync()


@sync_to_async
def fetch_all_categories_sync():
    return list(Category.objects.all().values())


async def fetch_all_categories():
    return await fetch_all_categories_sync()


@sync_to_async
def fetch_all_stores_sync():
    return list(Merchant.objects.all().values())


async def fetch_all_stores():
    return await fetch_all_stores_sync()


@sync_to_async
def fetch_user_favorite_brands(user):
    return list(user.favorite_brands.values_list('id', flat=True))


@sync_to_async
def fetch_products_by_brand_ids(brand_ids):
    return list(Product.objects.filter(brand_id__in=brand_ids).values())


async def fetch_all_fav_brands_products(user):
    favorite_brand_ids = await fetch_user_favorite_brands(user)

    if favorite_brand_ids:
        products = await fetch_products_by_brand_ids(favorite_brand_ids)
        return products
    else:
        return []


@sync_to_async
def fetch_user_favorite_categories(user):
    return list(user.favorite_categories.values_list('id', flat=True))


@sync_to_async
def fetch_products_by_categories_ids(category_ids):
    return list(Product.objects.filter(category_id__in=category_ids).values())


async def fetch_all_fav_categories_products(user):
    favorite_category_ids = await fetch_user_favorite_categories(user)

    if favorite_category_ids:
        products = await fetch_products_by_categories_ids(favorite_category_ids)
        return products
    else:
        return []
    

@sync_to_async
def fetch_user_favorite_category_sync(user):
    return list(user.favorite_categories.all())


async def fetch_user_favorite_category(user):
    return await fetch_user_favorite_category_sync(user)


@sync_to_async
def fetch_products_by_brand_sync(brand_id):
    return list(Product.objects.filter(
        brand_id=brand_id,
        discount_end_date__gte=datetime.now(),
        discount_start_date__lte=datetime.now()
    ).values())


async def fetch_products_by_brand(brand_id):
    return await fetch_products_by_brand_sync(brand_id)
    

@sync_to_async
def fetch_products_by_time_sync(start_date, end_date):
    today = timezone.now().date()

    if start_date.lower() == "today":
        start_date = today
    elif start_date.lower() == "empty":
        start_date = None
    else:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid start date format. Please use YYYY-MM-DD.")

    if end_date.lower() == "today":
        end_date = today
    elif end_date.lower() == "empty":
        end_date = None
    else:
        try:
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid end date format. Please use YYYY-MM-DD.")

    query = Product.objects.all()

    if start_date and end_date:
        query = query.filter(discount_start_date__lte=end_date, discount_end_date__gte=start_date)

    elif start_date:
        query = query.filter(discount_end_date__gte=start_date)

    elif end_date:
        query = query.filter(discount_start_date__lte=end_date)

    return list(query.values())


async def fetch_products_by_time_brand(start_date, end_date):
    return await fetch_products_by_time_sync(start_date, end_date)


@sync_to_async
def fetch_brand_by_id_sync(brand_id):
    return Brand.objects.get(id=brand_id)


async def fetch_brand_by_id(brand_id):
    return await fetch_brand_by_id_sync(brand_id)


@sync_to_async
def fetch_category_by_id_sync(id):
    return Category.objects.get(id=id)


async def fetch_category_by_id(id):
    return await fetch_category_by_id_sync(id)


@sync_to_async
def fetch_products_by_category_sync(category_id):
    return list(Product.objects.filter(
        category_id=category_id,
        discount_end_date__gte=datetime.now(),
        discount_start_date__lte=datetime.now()
    ).values())


async def fetch_products_by_category(category_id):
    return await fetch_products_by_category_sync(category_id)


@sync_to_async
def fetch_products_by_store_sync(store_id):
    return list(Product.objects.filter(
        merchant=store_id,
        discount_end_date__gte=datetime.now(),
        discount_start_date__lte=datetime.now()
    ).values())


async def fetch_products_by_store(store_id):
    return await fetch_products_by_store_sync(store_id)


@sync_to_async
def is_user_registered_sync(telegram_id):
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
        
        profile = Profile.objects.create(**user_data)
        return profile.id  
    except Exception as e:
        logging.error(f"Error storing user data: {e}")
        return None  


async def store_user_data(user_data):
    return await store_user_data_sync(user_data)


async def add_user_favorite_category(user_id, category):
    try:
        user = await sync_to_async(Profile.objects.get)(telegram_id=user_id)
        
        if category:
            category_object = category
            favorite_categories = await sync_to_async(list)(user.favorite_categories.filter(id=category_object.id))
            
            if favorite_categories:
                await sync_to_async(user.favorite_categories.remove)(category_object)
                logging.info(f"Removed category {category_object.title} from user {user.username}'s favorites.")
            else:
                await sync_to_async(user.favorite_categories.add)(category_object)
                logging.info(f"Added category {category_object.title} to user {user.username}'s favorites.")
                
        return True
    except Exception as e:
        logging.error(f"Error storing user favorite category data: {e}")
        return False


@sync_to_async
def store_recommendation_data_sync(recommendation_data):
    try:
        if recommendation_data['description']=='Skip Recommendation':
            recommendation_data['description'] = ""
        Recommendations.objects.create(**recommendation_data)
        return True
    except Exception as e:
        logging.error(f"Error storing recommendation data: {e}")
        return False


async def store_recommendation_data(recommendation_data):
    return await store_recommendation_data_sync(recommendation_data)


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
    return await fetch_products_by_search_sync(search_query)


@sync_to_async
def get_user_profile_sync(user_id):
    try:
        user_data = Profile.objects.get(telegram_id=user_id)

        value = {
            "id": user_data.id,
            "telegram_id": user_data.telegram_id,
            "username": user_data.username,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "birthday": user_data.birthday.strftime("%d-%m-%Y") if user_data.birthday else "N/A",
            "gender": user_data.gender,
            "language": user_data.language,
            "location": user_data.location,
            "role": user_data.role,
            "min_discount": user_data.min_discount if user_data.min_discount is not None else "N/A",
            "max_discount": user_data.max_discount if user_data.max_discount is not None else "N/A",
            "min_time": user_data.min_time.strftime("%H:%M") if user_data.min_time else "N/A",
            "max_time": user_data.max_time.strftime("%H:%M") if user_data.max_time else "N/A",
        }

        if user_data.role == 'merchant':
            value['merchant'] = user_data.merchant_role.title
            value['merchant_id'] = user_data.merchant_role.id

        return value

    except Profile.DoesNotExist:
        logging.error(f"Profile with telegram_id {user_id} does not exist.")
        return None
    except Exception as e:
        logging.error(f"Error retrieving profile for telegram_id {user_id}: {e}")
        return None


async def get_user_profile(user_id):
    return await get_user_profile_sync(user_id)


@sync_to_async
def get_user_language_sync(user_id, update, context):
    try:
        user_data = Profile.objects.get(telegram_id=user_id)
        if user_data.language in {"en", "tr", "az", "ru"}:
            return user_data.language

        selected_language = context.user_data.get('selected_language')
        if selected_language in {'en', 'tr', 'ru', 'az'}:
            return selected_language

    except Profile.DoesNotExist:
        print(context.user_data)
        selected_language = context.user_data.get('selected_language')
        if selected_language in {'en', 'tr', 'ru', 'az'}:
            return selected_language
        return update.effective_user.language_code

    except Exception as e:
        logging.error(f"Error retrieving profile for telegram_id {user_id}: {e}")
        return "en"


async def get_user_language(user_id, update, context):
    return await get_user_language_sync(user_id, update, context)


async def profile_command_filter(query, user_id):
    user_profile = await get_user_profile(user_id)

    if user_profile:
        language = user_profile.get('language', 'en')
        profile_info = (
            f"🆔 {languages[language]['telegram_id']}: {user_profile['telegram_id']}\n"
            f"👤 {languages[language]['username']}: {user_profile['username']}\n"
            f"🧑 {languages[language]['first_name']}: {user_profile['first_name']}\n"
            f"👨‍⚖️ {languages[language]['last_name']}: {user_profile['last_name']}\n"
            f"🎂 {languages[language]['birthday']}: {user_profile['birthday']}\n"
            f"⚧️ {languages[language]['gender']}: {languages[language][user_profile['gender']]}\n"
            f"📍 {languages[language]['location']}: {user_profile['location']}\n"
            f"🗣️ {languages[language]['language']}: {user_profile['language']}\n"
            f"👮 {languages[language]['role']}: {user_profile['role']}\n"
            f"💰 {languages[language]['discount']}: {user_profile['min_discount']}%-{user_profile['max_discount']}%\n"
            f"⏰ {languages[language]['notification_times']}: {user_profile['min_time']} - {user_profile['max_time']}\n"
        )
        
        keyboard = [
            [InlineKeyboardButton(languages[language]['edit'], callback_data="edit_profile")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(profile_info, reply_markup=reply_markup)
    else:
        await query.message.reply_text(languages[language]['profile_not_found'])


async def profile_command(update: Update, context):
    user = update.effective_user
    user_profile = await get_user_profile(user.id)
    if user_profile:
        language = user_profile.get('language', 'en')
        profile_info = (
            f"🆔 {languages[language]['telegram_id']}: {user_profile['telegram_id']}\n"
            f"👤 {languages[language]['username']}: {user_profile['username']}\n"
            f"🧑 {languages[language]['first_name']}: {user_profile['first_name']}\n"
            f"👨‍⚖️ {languages[language]['last_name']}: {user_profile['last_name']}\n"
            f"🎂 {languages[language]['birthday']}: {user_profile['birthday']}\n"
            f"⚧️ {languages[language]['gender']}: {languages[language][user_profile['gender']]}\n"
            f"📍 {languages[language]['location']}: {user_profile['location']}\n"
            f"🗣️ {languages[language]['language']}: {user_profile['language']}\n"
            f"👮 {languages[language]['role']}: {user_profile['role']}\n"
            f"💰 {languages[language]['discount']}: {user_profile['min_discount']}%-{user_profile['max_discount']}%\n"
            f"⏰ {languages[language]['notification_times']}: {user_profile['min_time']} - {user_profile['max_time']}\n"
        )
        keyboard = [
            [InlineKeyboardButton(languages[language]['edit'], callback_data="edit_profile")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.message:
            await update.message.reply_text(profile_info, reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.message.reply_text(profile_info, reply_markup=reply_markup)
    else:
        language = await get_user_language(user.id, update, context)
        if update.message:
            await update.message.reply_text(languages[language]['profile_not_found'])
        elif update.callback_query:
            await update.callback_query.message.reply_text(languages[language]['profile_not_found'])


MIN_DATE = datetime(1901, 1, 1)
MIN_AGE_DATE = datetime.now() - timedelta(days=13 * 365)


@sync_to_async
def update_profile_data(user_id, field, new_value):
    try:
        user_data = Profile.objects.get(telegram_id=user_id)
        setattr(user_data, field, new_value)
        user_data.save()
        return True
    except Profile.DoesNotExist:
        logging.error(f"Profile with telegram_id {user_id} does not exist.")
        return False
    except Exception as e:
        logging.error(f"Error updating profile for telegram_id {user_id}: {e}")
        return False


async def edit_profile_options(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    language = await get_user_language(query.from_user.id, update, context)
    
    keyboard = [
        [InlineKeyboardButton(languages[language]['location'], callback_data="edit_user_location")],
        [InlineKeyboardButton(languages[language]['birthday'], callback_data="edit_user_birthdate")],
        [InlineKeyboardButton(languages[language]['gender'], callback_data="edit_user_gender")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(languages[language]['select_edit_option'], reply_markup=reply_markup)


async def edit_user_location(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    language = await get_user_language(update.callback_query.from_user.id, update, context)  
    await update.callback_query.edit_message_text(languages[language]['enter_new_location'])
    context.user_data['edit_field'] = 'location'


async def edit_user_birthdate(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    language = await get_user_language(update.callback_query.from_user.id, update, context)
    await update.callback_query.edit_message_text(languages[language]['enter_new_birthdate'])
    context.user_data['edit_field'] = 'birthday'


async def edit_user_gender(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    language = await get_user_language(update.callback_query.from_user.id, update, context) 

    keyboard = [
        [
            InlineKeyboardButton(languages[language]['male'], callback_data="gender_male"),
            InlineKeyboardButton(languages[language]['female'], callback_data="gender_female"),
            InlineKeyboardButton(languages[language]['other'], callback_data="gender_other")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        languages[language]['select_gender'],
        reply_markup=reply_markup
    )
    context.user_data['edit_field'] = 'gender'


async def handle_user_response(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    edit_field = context.user_data.get('edit_field')

    language = await get_user_language(user_id, update, context) 

    if update.callback_query and edit_field == 'gender':
        await update.callback_query.answer()
        gender = update.callback_query.data.split("_")[1]  
        
        success = await update_profile_data(user_id, 'gender', gender)
        if success:
            await update.callback_query.edit_message_text(languages[language]['gender_updated'])
        else:
            await update.callback_query.edit_message_text(languages[language]['gender_update_failed'])
        
        context.user_data.pop('edit_field', None)

    elif edit_field == 'location':
        if update.message.location:
            latitude = update.message.location.latitude
            longitude = update.message.location.longitude
            location_data = f"Unknown, Latitude: {latitude}, Longitude: {longitude}"
        else:
            location_text = update.message.text
            location_data = f"{location_text}, Latitude: N/A, Longitude: N/A"
        
        success = await update_profile_data(user_id, 'location', location_data)
        if success:
            await update.message.reply_text(languages[language]['location_updated'])
        else:
            await update.message.reply_text(languages[language]['location_update_failed'])
        
        context.user_data.pop('edit_field', None)

    elif edit_field == 'birthday':
        try:
            birthday_input = update.message.text
            parsed_birthdate = check_birthday(birthday_input)
            if not parsed_birthdate:
                await update.message.reply_text(languages[language]['invalid_date_format'])
                return

            new_birthdate = datetime.strptime(parsed_birthdate, "%d-%m-%Y")
            
            if new_birthdate < MIN_DATE:
                await update.message.reply_text(languages[language]['birthdate_too_early'])
                context.user_data.pop('edit_field', None)
                return await profile_command(update, context)
            elif new_birthdate > MIN_AGE_DATE:
                await update.message.reply_text(languages[language]['must_be_at_least_13'])
                context.user_data.pop('edit_field', None)
                return await profile_command(update, context)

            success = await update_profile_data(user_id, 'birthday', new_birthdate)
            if success:
                await update.message.reply_text(languages[language]['birthdate_updated'])
            else:
                await update.message.reply_text(languages[language]['birthdate_update_failed'])

        except ValueError:
            await update.message.reply_text(languages[language]['invalid_date_format'])
        
    context.user_data.pop('edit_field', None)
    await profile_command(update, context)


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
    

async def change_language(update: Update, context: CallbackContext):
    query = update.callback_query
    selected_language = query.data
    telegram_id = query.from_user.id

    if selected_language not in languages:
        await query.answer(text=languages['en']['invalid_language'], show_alert=True)
        return

    context.user_data['language'] = selected_language
    context.user_data['selected_language'] = selected_language
    await update_user_language_sync(telegram_id, selected_language)

    await query.edit_message_text(text=languages[selected_language]['greeting'].format(name=query.from_user.first_name))


def auto_language(context, user):
    language = context.user_data.get('language', 'en') 
    if user.language_code in languages.keys():
        language = context.user_data.get('language', user.language_code)
    return language


async def start(update: Update, context: CallbackContext):
    user = update.effective_user    
    language = await get_user_language(user.id, update, context)

    try:
        await update.message.reply_text(languages[language]["greeting"].format(name=user.first_name))

        if await is_user_registered(user.id):
            await update.message.reply_text(languages[language]['already_registered'])
            return
        
        await update.message.reply_text(languages[language]["sign_up_message"]) 
        await register(update, context) 
    except Exception as e:
        await update.message.reply_text(languages[language]["error_message"].format(error=str(e)))


async def active_user(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    return await profile_data(tg_id=user_id)


async def delete_me(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    language = await get_user_language(user_id, update, context)
    if await delete_user_from_db_sync(user_id):
        await update.message.reply_text(languages[language]['delete_success'])
    else:
        await update.message.reply_text(languages[language]['delete_failure'])


async def register(update: Update, context: CallbackContext):
    user = update.effective_user
    language = await get_user_language(user.id, update, context)

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
    language = await get_user_language(user.id, update, context)

    if context.user_data.get('step') == 'ask_birthday':
        birthday = update.message.text.strip()
        
        formatted_birthday = check_birthday(birthday)
        
        if not formatted_birthday:
            await update.message.reply_text(languages[language]["error_invalid_birthday"])
            return

        parsed_date = datetime.strptime(formatted_birthday, "%d-%m-%Y")
        
        if parsed_date < datetime(1901, 1, 1):
            await update.message.reply_text(languages[language]["error_date_too_early"])
            return 
        
        if datetime.now() - parsed_date < timedelta(days=365 * 13):
            await update.message.reply_text(languages[language]["error_under_13"])
            return 
        
        context.user_data['birthday'] = formatted_birthday

        keyboard = [
            [InlineKeyboardButton(f"👨 {languages[language]['male']}", callback_data='male')],
            [InlineKeyboardButton(f"👩 {languages[language]['female']}", callback_data='female')],
            [InlineKeyboardButton(f"🌈 {languages[language]['other']}", callback_data='other')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(languages[language]["ask_gender"], reply_markup=reply_markup)
        context.user_data['step'] = 'ask_gender'


async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user = query.from_user
    language = await get_user_language(user.id, update, context)

    if context.user_data.get('step') == 'ask_gender':
        selected_gender = query.data
        context.user_data['gender'] = selected_gender
        await query.answer()

        await query.message.reply_text(
            languages[language]["ask_location"], 
            reply_markup=ReplyKeyboardMarkup(
                [
                    [
                        KeyboardButton(languages[language]["share_location"], request_location=True),
                    ]
                ],
                resize_keyboard=True, one_time_keyboard=True
            )
        )
        context.user_data['step'] = 'ask_location'
    
    elif context.user_data.get('step') == 'ask_location':
        if query.data == "Share Location":
            await query.answer(languages[language]["prompt_share_location"])
        elif query.data == "Type your region":
            await query.message.reply_text(languages[language]["prompt_type_region"])
            context.user_data['step'] = 'waiting_for_region'

    elif context.user_data.get('step') == 'waiting_for_region':
        user_region = update.message.text
        context.user_data['region'] = user_region
        await query.message.reply_text(
            languages[language]["region_received"].format(escape_markdown(user_region))
        )


async def help_command(update: Update, context: CallbackContext):
    user = update.effective_user
    language = await get_user_language(user.id, update, context)

    if await is_user_registered(user.id):
        available_commands = (
            languages[language]["main_commands"] +
            languages[language]["discounts_offers"] +
            languages[language]["profile_account"] +
            languages[language]["merchant_features"]
        )

        escaped_message = available_commands.replace('_', '\\_')\
                                             .replace('-', '\\-')\
                                             .replace('.', '\\.')

        await update.message.reply_text(
            f"🤖 *{languages[language]['available_commands']}:*\n\n{escaped_message}",
            parse_mode='MarkdownV2' 
        )
    else:
        await update.message.reply_text(languages[language]["not_registered"])


async def languages_command(update: Update, context: CallbackContext):
    user_language = context.user_data.get('language', 'en') 
    keyboard = [
        [InlineKeyboardButton(languages[user_language]['az'], callback_data='az')],
        [InlineKeyboardButton(languages[user_language]['en'], callback_data='en')],
        [InlineKeyboardButton(languages[user_language]['tr'], callback_data='tr')],
        [InlineKeyboardButton(languages[user_language]['ru'], callback_data='ru')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(languages[user_language]['select_language'], reply_markup=reply_markup)


async def language_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    selected_language = query.data
    context.user_data['language'] = selected_language
    context.user_data['selected_language'] = selected_language

    await update_user_language_sync(query.from_user.id, selected_language)

    await query.edit_message_text(text=languages[selected_language]['language_changed'])


async def discounts_command(update: Update, context: CallbackContext):
    query = update.callback_query 
    user = update.effective_user

    if query:
        message = query.message
    else:
        message = update.message

    language = await get_user_language(user.id, update, context) 

    if not await is_user_registered(user.id):
        await message.reply_text(languages[language]["not_registered"])
        return

    keyboard = [
        [InlineKeyboardButton(languages[language]["real_time_discounts"], callback_data='all')],
        [InlineKeyboardButton(languages[language]["favorite_categories"], callback_data='filter_favoritecategories')],
        [InlineKeyboardButton(languages[language]["favorite_stores"], callback_data='filter_favoritebrands')],
        [InlineKeyboardButton(languages[language]["saved_discounts"], callback_data='saved')],
        [InlineKeyboardButton(languages[language]["profile"], callback_data='profile')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply_text(languages[language]["choose_option"], reply_markup=reply_markup)


async def save_product(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    language = await get_user_language(query.from_user.id, update, context)
    product_id = query.data.split("_")[1]

    try:
        product = await sync_to_async(Product.objects.get)(id=product_id)
        user_id = query.from_user.id
        user = await sync_to_async(Profile.objects.get)(telegram_id=user_id)

        saved_product = await sync_to_async(SavedProduct.objects.filter)(user=user, product=product)

        if await sync_to_async(saved_product.exists)():
            await sync_to_async(saved_product.delete)()
            message = languages[language]["product_unsaved"].format(product_name=product.name)
        else:
            await sync_to_async(SavedProduct.objects.create)(user=user, product=product)
            message = languages[language]["product_saved"].format(product_name=product.name)

        if query.message.text:
            await query.edit_message_text(message)
        else:
            await query.message.reply_text(message)

    except Product.DoesNotExist:
        if query.message.text:
            await query.edit_message_text(languages[language]["product_not_exist"].format(product_id=product_id))
        else:
            await query.message.reply_text(languages[language]["product_not_exist"].format(product_id=product_id))

    except Profile.DoesNotExist:
        if query.message.text:
            await query.edit_message_text(languages[language]["user_not_found"])
        else:
            await query.message.reply_text(languages[language]["user_not_found"])

    except Exception:
        error_message = languages[language]["generic_error"]
        if query.message.text:
            await query.edit_message_text(error_message)
        else:
            await query.message.reply_text(error_message)


async def display_product(query_or_message, product, language):
    photo_url = product['image_url']
    if len(product['description'])>61:
        product['description'] = product['description'][:61]+"..."
    translations = {
        'tr': {
            'title': 'Başlık',
            'description': 'Açıklama',
            'price': 'Fiyat',
            'discount': 'İndirim',
            'last_day': 'Son gün',
            'save': 'Kaydet',
            'link': 'Bağlantı',
            'error_message': "Ürün görüntülenirken bir hata oluştu. Lütfen tekrar deneyin.",
            'invalid_image': "Ürün için geçersiz resim."
        },
        'en': {
            'title': 'Title',
            'description': 'Description',
            'price': 'Price',
            'discount': 'Discount',
            'last_day': 'Last day',
            'save': 'Save',
            'link': 'Link',
            'error_message': "An error occurred while displaying the product. Please try again.",
            'invalid_image': "Invalid image for the product."
        },
        'az': {
        'title': 'Başlıq',
        'description': 'Təsvir',
        'price': 'Qiymət',
        'discount': 'Endirim',
        'last_day': 'Son gün',
        'save': 'Yadda Saxla',
        'link': 'Keçid',
        'error_message': "Məhsul göstərilirkən xəta baş verdi. Zəhmət olmasa, yenidən yoxlayın.",
        'invalid_image': "Məhsul üçün etibarsız şəkil."
    },
    'ru': {
        'title': 'Название',
        'description': 'Описание',
        'price': 'Цена',
        'discount': 'Скидка',
        'last_day': 'Последний день',
        'save': 'Сохранить',
        'link': 'Ссылка',
        'error_message': "Произошла ошибка при отображении продукта. Пожалуйста, попробуйте снова.",
        'invalid_image': "Недействительное изображение для продукта."
    }
    }

    messages = translations.get(language, translations['en'])
    await increment_click_count(product_id=product['id'])
    if is_valid_url(photo_url):
        try:
            price = Decimal(product['normal_price']).quantize(Decimal('0.01'))
            discount_price = Decimal(product['discount_price']).quantize(Decimal('0.01'))
            discount_percentage = ((price - discount_price) / price * 100).quantize(Decimal('0.01'))
            
            discount_end_date = product['discount_end_date']
            if isinstance(discount_end_date, str):
                discount_end_date = datetime.strptime(discount_end_date, '%Y-%m-%d')

            caption = (
                f"<b>{messages['title']}</b>: {product['name']}\n"
                f"<b>{messages['description']}</b>: {product['description']}\n"
                f"<b>{messages['price']}</b>: {discount_price} ₼ 🔴<s>{price} ₼</s>\n"
                f"<b>{messages['discount']}</b>: {int(discount_percentage)}%\n"
                f"<b>{messages['last_day']}</b>: {discount_end_date.strftime('%d %B %Y')}\n"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton(messages['save'], callback_data=f"save_{product['id']}"),
                    InlineKeyboardButton(messages['link'], url=product['url'])
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query_or_message.reply_photo(photo=photo_url, caption=caption, reply_markup=reply_markup, parse_mode='HTML')
        
        except Exception as e:
            await query_or_message.reply_text(messages['error_message'])
    
    else:
        await query_or_message.reply_text(messages['invalid_image'])


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
    user_id = update.effective_user.id
    language = await get_user_language(user_id, update, context)
    if choice == 'all':
        await display_filter_options(query, language)
    elif choice == 'filter':
        await display_filter_options(query, language)
    elif choice == 'saved':
        await my_saved_products_filter(query, language)
    elif choice == 'profile':
        await profile_command_filter(query, user_id)


async def display_filter_options(query, language):
    keyboard = [
        [InlineKeyboardButton(languages[language]['by_categories'], callback_data='filter_category')],
        [InlineKeyboardButton(languages[language]['by_stores'], callback_data='filter_stores')],
        [InlineKeyboardButton(languages[language]['by_brands'], callback_data='filter_brand')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(languages[language]['select_filter_type'], reply_markup=reply_markup)


async def display_brand_filter_options(query, language):
    brands = await fetch_all_brands()

    if not brands:
        await query.message.reply_text(languages[language]['no_brands_available'])
        return

    keyboard = [
        [
            InlineKeyboardButton(brand['title'], callback_data=f'brand_{brand["id"]}'),
            InlineKeyboardButton(f"{languages[language]['add_to_favorites']} {brand['title']}", callback_data=f'favbrand_{brand["id"]}')
        ]
        for brand in brands
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(languages[language]['select_brand'], reply_markup=reply_markup)


async def add_brand_favorite(update: Update, context: CallbackContext):
    query = update.callback_query
    choice = query.data
    brand_id = choice.split('_')[1]
    user_id = update.effective_user.id
    language = await get_user_language(user_id, update, context)
    user = await sync_to_async(Profile.objects.get)(telegram_id=user_id)
    
    if brand_id:
        brands = await fetch_brand_by_id(brand_id)
        
        if brands:
            favorite_brands = await sync_to_async(list)(user.favorite_brands.filter(id=brands.id))
            
            if favorite_brands:
                await sync_to_async(user.favorite_brands.remove)(brands)
                await query.message.reply_text(f"{brands.title} {languages[language]['removed_from_favorites']}")
            else:
                await sync_to_async(user.favorite_brands.add)(brands)
                await query.message.reply_text(f"{brands.title} {languages[language]['added_to_favorites']}")
        else:
            await query.message.reply_text(languages[language]['brand_not_found'])
    else:
        await query.message.reply_text(languages[language]['invalid_brand_id'])


async def add_category_favorite(update: Update, context: CallbackContext):
    query = update.callback_query
    choice = query.data
    category_id = choice.split('_')[1]
    user_id = update.effective_user.id
    language = await get_user_language(user_id, update, context)
    user = await sync_to_async(Profile.objects.get)(telegram_id=user_id)
    
    if category_id:
        categories = await fetch_category_by_id(category_id)
        
        if categories:
            favorite_categories = await sync_to_async(list)(user.favorite_categories.filter(id=categories.id))
            
            if favorite_categories:
                await sync_to_async(user.favorite_categories.remove)(categories)
                await query.message.reply_text(f"{categories.title} {languages[language]['removed_from_favorites']}")
            else:
                await sync_to_async(user.favorite_categories.add)(categories)
                await query.message.reply_text(f"{categories.title} {languages[language]['added_to_favorites']}")
        else:
            await query.message.reply_text(languages[language]['category_not_found'])
    else:
        await query.message.reply_text(languages[language]['invalid_category_id'])


async def display_category_filter_options(query, language):
    categories = await fetch_all_categories()

    if not categories:
        await query.message.reply_text(languages[language]['no_categories'])
        return

    keyboard = [
        [InlineKeyboardButton(category['title'], callback_data=f'category_{category["id"]}'),
         InlineKeyboardButton(f"{languages[language]['add']} {category['title']}", callback_data=f'favcategory_{category["id"]}')
         ]
        for category in categories
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(languages[language]['select_category'], reply_markup=reply_markup)


async def display_store_filter_options(query, language):
    stores = await fetch_all_stores()

    if not stores:
        await query.message.reply_text(languages[language]['no_stores'])
        return

    keyboard = [
        [InlineKeyboardButton(store['title'], callback_data=f'store_{store["id"]}')]
        for store in stores
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(languages[language]['select_store'], reply_markup=reply_markup)


async def display_by_brand(update: Update, context: CallbackContext):
    query = update.callback_query
    choice = query.data
    brand_id = choice.split('_')[1]
    language = await get_user_language(update.effective_user.id, update, context)
    
    if brand_id:
        products = await fetch_products_by_brand(brand_id)
        if products:
            for product in products:
                discount_end_date = product['discount_end_date']
                if isinstance(discount_end_date, datetime) and timezone.is_naive(discount_end_date):
                    product['discount_end_date'] = timezone.make_aware(discount_end_date)
                await display_product(query.message, product, language)
        else:
            await query.message.reply_text(languages[language]['no_products_found'])
    else:
        await query.message.reply_text(languages[language]['invalid_brand_id'])


async def display_by_category(update: Update, context: CallbackContext):
    query = update.callback_query
    choice = query.data
    category_id = choice.split('_')[1]
    language = await get_user_language(update.effective_user.id, update, context)

    if category_id:
        products = await fetch_products_by_category(category_id)
        if products:
            for product in products:
                discount_end_date = product['discount_end_date']
                if isinstance(discount_end_date, datetime) and timezone.is_naive(discount_end_date):
                    product['discount_end_date'] = timezone.make_aware(discount_end_date)
                await display_product(query.message, product, language)
        else:
            await query.message.reply_text(languages[language]['no_products_found'])
    else:
        await query.message.reply_text(languages[language]['invalid_category_id'])


async def display_by_store(update: Update, context: CallbackContext):
    query = update.callback_query
    choice = query.data
    store_id = choice.split('_')[1]
    language = await get_user_language(update.effective_user.id, update, context)

    if store_id:
        products = await fetch_products_by_store(store_id)
        if products:
            for product in products:
                discount_end_date = product['discount_end_date']
                if isinstance(discount_end_date, datetime) and timezone.is_naive(discount_end_date):
                    product['discount_end_date'] = timezone.make_aware(discount_end_date)
                await display_product(query.message, product, language)
        else:
            await query.message.reply_text(languages[language]['no_products_found_merchant'])
    else:
        await query.message.reply_text(languages[language]['invalid_store_id'])


async def display_favorite_brands_products(query_message, user, language):
    user = await sync_to_async(Profile.objects.get)(telegram_id=user.id)
    
    products = await fetch_all_fav_brands_products(user)

    if not products:
        no_products_message = languages[language]['no_fav_brands_products']
        await query_message.reply_text(no_products_message)
        return

    for product in products:
        await display_product(query_message, product, language)


async def display_favorite_categories_products(query_message, user, language):
    user = await sync_to_async(Profile.objects.get)(telegram_id=user.id)
    products = await fetch_all_fav_categories_products(user)

    if not products:
        no_products_message = languages[language]['no_fav_categories_products']
        await query_message.reply_text(no_products_message)
        return

    for product in products:
        await display_product(query_message, product, language)


async def specific_filter_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user = query.from_user 
    choice = query.data
    language = await get_user_language(user.id, update, context)
    messages = {
    'unknown_filter': {
        'en': "Unknown Filter.",
        'tr': "Bilinmeyen Filtre.",
        'ru': "Неизвестный фильтр.",
        'az': "Naməlum Filtr."
        }
    }
    if choice == 'filter_brand':
        return await display_brand_filter_options(query, language)
    elif choice == 'filter_category':
        return await display_category_filter_options(query, language)
    elif choice == 'filter_stores':
        return await display_store_filter_options(query, language)
    elif choice == 'filter_favoritebrands':
        return await display_favorite_brands_products(query.message, user, language)
    elif choice == 'filter_favoritecategories':
        return await favorite_category_options(query, user, language)
    else:
        await query.message.reply_text(messages['unknown_filter'][language])
        return


async def favorite_category_options(query, user, language):
    user = await sync_to_async(Profile.objects.get)(telegram_id=user.id)
    categories = await fetch_user_favorite_category(user)
    
    if not categories:
        await query.message.reply_text(languages[language]['no_categories'])
        return
    
    keyboard = [
        [InlineKeyboardButton(category.title, callback_data=f'category_{category.id}')] for category in categories
    ]
    
    category = categories[0]
    keyboard.append([InlineKeyboardButton(languages[language]['edit_category'], callback_data=f'category_edit_{category.id}')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(languages[language]['select_category'], reply_markup=reply_markup)


async def edit_favorite_category(update, context):
    language = await get_user_language(user_id=update.effective_user.id, update=update, context=context)
    categories = await fetch_all_categories()

    if not categories:
        await update.callback_query.message.reply_text(languages[language]['no_categories'])
        return

    keyboard = []
    row = []

    for index, category in enumerate(categories, start=1):
        row.append(InlineKeyboardButton(category["title"], callback_data=f'favorite_category_edit_{category["id"]}'))
        
        if index % 2 == 0:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(languages[language]['select_category'], reply_markup=reply_markup)


@sync_to_async
def update_user_favorite_category(user, new_category_id):
    if user.favorite_categories.filter(id=new_category_id).exists():
        user.favorite_categories.remove(new_category_id)
    else:
        user.favorite_categories.add(new_category_id)
    user.save()


async def edit_favorite_category_fin(update, context):
    query = update.callback_query
    user = await sync_to_async(Profile.objects.get)(telegram_id=update.effective_user.id)
    new_category_id = int(query.data.split('_')[-1])
    language = await get_user_language(user_id=update.effective_user.id, update=update, context=context)
    await update_user_favorite_category(user, new_category_id)
    await query.edit_message_text(
        languages[language]["favorite_category_updated"]
    )        


async def handle_location(update: Update, context: CallbackContext):
    language = await get_user_language(user_id=update.effective_user.id, update=update, context=context)

    if context.user_data.get('step') == 'ask_location':
        location = update.message.location
        if location:
            context.user_data['location'] = {
                'latitude': location.latitude,
                'longitude': location.longitude
            }
            await update.message.reply_text(
                languages[language]["location_saved"]
            )
            context.user_data['step'] = 'ask_fav_category'
        else:
            region = update.message.text
            context.user_data['location'] = {"region": region}
            context.user_data['step'] = 'ask_fav_category'

        await favorite_category_selection(update, context)
    else:
        if context.user_data.get("edit_field")=='location':
            await handle_user_response(update, context)
        else:
            await update.message.reply_text(
                languages[language]["location_invalid"]
            )


async def favorite_category_selection(update: Update, context: CallbackContext):
    language = await get_user_language(update.effective_user.id, update, context)
    categories = await fetch_all_categories()

    if not categories:
        await update.message.reply_text(languages[language]["no_categories_available"])
        return

    keyboard = []
    row = []

    for index, category in enumerate(categories, start=1):
        row.append(InlineKeyboardButton(f'📂 {category["title"]}', callback_data=f'fav_category_{category["id"]}'))
        if index % 2 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(languages[language]["select_favorite_category"], reply_markup=reply_markup)


async def toggle_favorite_category(update: Update, context: CallbackContext):
    query = update.callback_query
    category_id = query.data.split('_')[2]
    language = await get_user_language(update.effective_user.id, update, context)

    try:
        category = await fetch_category_by_id(category_id)

        if category:
            context.user_data['favorite_category'] = category
            await query.message.reply_text(
                languages[language]["add_favorite_store"], 
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ " + languages[language]["skip"], callback_data='skip_store_recommendation')]
                ])
            )
            context.user_data['step'] = 'ask_store_recommendation'
        else:
            await query.message.reply_text(languages[language]["category_not_found"])
    except IntegrityError:
        await query.message.reply_text(languages[language]["category_selection_error"])
    except Exception as e:
        print(f"{languages[language]['unexpected_error']}: {str(e)}")
    finally:
        await query.answer()


async def skip_store_recommendation(update: Update, context: CallbackContext):
    query = update.callback_query
    language = await get_user_language(update.effective_user.id, update, context)

    context.user_data['store_recommendation'] = None
    keyboard = [
        [InlineKeyboardButton("🔖 10-30%", callback_data='discount_percentage_10_30')],
        [InlineKeyboardButton("🔖 30-50%", callback_data='discount_percentage_30_50')],
        [InlineKeyboardButton("🔖 50-90%", callback_data='discount_percentage_50_90')],
        [InlineKeyboardButton("🔖 10-90%", callback_data='discount_percentage_10_90')],
        [InlineKeyboardButton("🔖 0-100%", callback_data='discount_percentage_0_100')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(
        languages[language]["store_recommendation_skipped"],
        reply_markup=reply_markup
    )
    context.user_data['step'] = 'ask_discount_percentage'
    await query.answer()


async def store_recommendation_handler(update: Update, context: CallbackContext):
    language = await get_user_language(update.effective_user.id, update, context)

    if context.user_data.get('step') == 'ask_store_recommendation':
        recommendation = update.message.text

        if recommendation == languages[language]["skip_button"]:
            context.user_data['store_recommendation'] = None
            await update.message.reply_text(languages[language]["store_recommendation_not_saved"])
        else:
            context.user_data['store_recommendation'] = recommendation

        keyboard = [
            [InlineKeyboardButton("🔖 10-30%", callback_data='discount_percentage_10_30')],
            [InlineKeyboardButton("🔖 30-50%", callback_data='discount_percentage_30_50')],
            [InlineKeyboardButton("🔖 50-90%", callback_data='discount_percentage_50_90')],
            [InlineKeyboardButton("🔖 10-90%", callback_data='discount_percentage_10_90')],
            [InlineKeyboardButton("🔖 0-100%", callback_data='discount_percentage_0_100')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            languages[language]["select_discount_percentage"],
            reply_markup=reply_markup
        )
        context.user_data['step'] = 'ask_discount_percentage'


async def discount_percentage_options(update: Update, context: CallbackContext):
    query = update.callback_query
    language = await get_user_language(update.effective_user.id, update, context)
    _, _, disc_perc_min, disc_perc_max = query.data.split('_')

    context.user_data['min_discount'] = disc_perc_min
    context.user_data['max_discount'] = disc_perc_max

    if disc_perc_min and disc_perc_max:
        keyboard = [
            [InlineKeyboardButton("🕰 11:00-18:00", callback_data='notification_time_11_18')],
            [InlineKeyboardButton("🕰 18:00-22:00", callback_data='notification_time_18_22')],
            [InlineKeyboardButton("🕰 11:00-22:00", callback_data='notification_time_11_22')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            languages[language]["select_notification_time"],
            reply_markup=reply_markup
        )
        context.user_data['step'] = 'ask_notification_time'

    await query.answer()


async def notification_time(update: Update, context: CallbackContext):
    query = update.callback_query
    language = await get_user_language(update.effective_user.id, update, context)
    _, _, time_min, time_max = query.data.split('_')
    context.user_data['min_time'] = time_min
    context.user_data['max_time'] = time_max

    location = context.user_data.get('location')
    if isinstance(location, dict):
        location_str = f"{location.get('region', 'Unknown')}, Latitude: {location.get('latitude', 'N/A')}, Longitude: {location.get('longitude', 'N/A')}"
    else:
        location_str = location

    user_data = {
        'telegram_id': update.effective_user.id,
        'username': update.effective_user.username,
        'first_name': update.effective_user.first_name,
        'last_name': update.effective_user.last_name,
        'birthday': context.user_data.get('birthday'),
        'gender': context.user_data.get('gender'),
        'location': location_str,
        'language': language,
        'min_time': context.user_data.get('min_time'),
        'max_time': context.user_data.get('max_time'),
        'min_discount': context.user_data.get('min_discount'),
        'max_discount': context.user_data.get('max_discount')
    }

    user_id = await store_user_data(user_data)

    if user_id:
        recommendation_data = {
            "user_id": user_id,
            'description': context.user_data['store_recommendation']
        }
        success_recommendation = await store_recommendation_data(recommendation_data)

        if success_recommendation:
            await query.message.reply_text(languages[language]["registration_completed"])

            favorite_categories = context.user_data.get('favorite_category', {})
            if favorite_categories:
                success_categories = await add_user_favorite_category(update.effective_user.id, favorite_categories)
                if not success_categories:
                    await query.message.reply_text(languages[language]["error_saving_categories"])
                else:
                    await query.message.reply_text(languages[language]["favorite_categories_added"])
                    await discounts_command(update, context)
            else:
                await query.message.reply_text(languages[language]["no_favorite_categories"])
        else:
            await query.message.reply_text(languages[language]["error_saving_recommendation"])
    else:
        await query.message.reply_text(languages[language]["error_saving_data"])

    context.user_data.clear()


async def feedback_command(update: Update, context: CallbackContext):
    language = await get_user_language(update.effective_user.id, update, context)
    feedback_prompt = {
        'en': "Please provide your feedback:",
        'tr': "Lütfen geri bildiriminizi yazın:",
        'az': "Zəhmət olmasa fikrinizi yazın:",
    }
    await update.message.reply_text(feedback_prompt.get(language, "Please provide your feedback:"))
    context.user_data['step'] = 'feedback'


async def handle_feedback(update: Update, context: CallbackContext):
    if context.user_data.get('step') == 'feedback':
        feedback_text = update.message.text
        user_id = update.effective_user.id

        success = await save_feedback(user_id, feedback_text)
        language = await get_user_language(user_id, update, context)

        if success:
            await update.message.reply_text(languages[language]['feedback_success'])
        else:
            await update.message.reply_text(languages[language]['feedback_failure'])

        context.user_data['step'] = None


async def save_feedback(user_id, feedback_text):
    try:
        user_profile, created = await Profile.objects.aget_or_create(telegram_id=user_id)
        
        feedback = Feedback(user=user_profile, description=feedback_text)
        await feedback.asave()
        
        if created:
            logging.info(f"New profile created for user with telegram_id {user_id}.")
        
        logging.info(f"Feedback saved for user {user_id}: {feedback_text}")

    except ObjectDoesNotExist:
        logging.error(f"User profile with telegram_id {user_id} not found.")
        return False
    except Exception as e:
        logging.error(f"Error storing feedback for user {user_id}: {e}")
        return False

    return True


async def command_restriction(update: Update, context: CallbackContext):
    user = update.effective_user
    language = await get_user_language(user.id, update, context)
    if not await is_user_registered(user.id):
        if update.message.text.startswith('/discounts'):
            await update.message.reply_text(languages[language]["not_registered"])
            return
        if update.message.text.startswith('/merchant'):
            await update.message.reply_text(languages[language]["not_registered"])
            return
    if update.message.text == '/discounts':
        await discounts_command(update, context)
    if update.message.text == '/merchant':
        await merchant_role_func(update, context)


async def text_message_handler(update: Update, context: CallbackContext):
    step = context.user_data.get('step')
    language = await get_user_language(update.effective_user.id, update, context)

    if step == 'ask_birthday':
        await ask_birthday(update, context)
    elif step == 'ask_store_recommendation':
        await store_recommendation_handler(update, context)
    elif step == 'ask_location':
        await handle_location(update, context)
    elif step == 'ask_fav_category':
        await favorite_category_selection(update, context)
    elif step == 'feedback':
        await handle_feedback(update, context)
    elif 'adding_product' in context.user_data:
        await process_add_product(update, context)
    elif context.user_data.get('edit_field'):
        await handle_user_response(update, context)
    elif context.user_data.get('update_type') == 'edit_name':
        await receive_merchant_name(update, context)
    else:
        await update.message.reply_text(languages[language]['unknown_command'])


def is_time_to_notify(user_min_time, user_max_time):
    return True


async def send_user_favorite_products(user, new_products, context):
    favorite_brands_ids = await sync_to_async(list)(user.favorite_brands.values_list('id', flat=True))
    favorite_categories_ids = await sync_to_async(list)(user.favorite_categories.values_list('id', flat=True))
    min_discount = user.min_discount
    max_discount = user.max_discount
    user_favorite_products = [
        product for product in new_products
        if (product.brand_id in favorite_brands_ids or product.category_id in favorite_categories_ids) and
        (min_discount is None or product.discount_percentage >= min_discount) and 
        (max_discount is None or product.discount_percentage <= max_discount)
    ]
    messages = {
        'en': "🆕 *New Arrivals!* Discover the latest discounted products.",
        'tr': "🆕 *Yeni Gelenler!* Son indirimli ürünleri keşfedin.",
        'ru': "🆕 *Новые поступления!* Узнайте о последних со скидками продуктах.",
        'az': "🆕 *Yeni Gələnlər!* Ən son endirimli məhsulları kəşf edin."
    }
    language = user.language if hasattr(user, 'language') else 'en'
    if user_favorite_products:
        try:
            await context.bot.send_message(
                chat_id=user.telegram_id,
                text=messages.get(language, messages['en']),  
                parse_mode='Markdown'
            )
        except Exception as e:
            logging.error(f"Error sending new product message to {user.telegram_id}: {str(e)}")

        for product in user_favorite_products:
            await send_product_details(user, product, context)

            
async def send_product_details(user, product, context):

    photo_url = product.image_url
    if is_valid_url(photo_url):
        try:
            price = Decimal(product.normal_price).quantize(Decimal('0.01'))
            discount_price = Decimal(product.discount_price).quantize(Decimal('0.01'))
            discount_percentage = ((price - discount_price) / price * 100).quantize(Decimal('0.01'))
            await increment_click_count(product_id=product.id)
            brand_title = await sync_to_async(lambda: product.brand.title)()  
            category_title = await sync_to_async(lambda: product.category.title)() 
            product.description=product.description[:61]+"..."
            captions = {
                'en': (
                    f"<b>Title</b>: {product.name}\n"
                    f"<b>Brand</b>: {brand_title}\n"
                    f"<b>Category</b>: {category_title}\n"
                    f"<b>Description</b>: {product.description}\n"
                    f"<b>Price</b>: {discount_price} ₼ 🔴<s>{price} ₼</s>\n"
                    f"<b>Discount</b>: {int(discount_percentage)}%\n"
                    f"<b>Last day</b>: {product.discount_end_date.strftime('%d %B %Y')}\n"
                ),
                'tr': (
                    f"<b>Başlık</b>: {product.name}\n"
                    f"<b>Marka</b>: {brand_title}\n"
                    f"<b>Kategori</b>: {category_title}\n"
                    f"<b>Açıklama</b>: {product.description}\n"
                    f"<b>Fiyat</b>: {discount_price} ₼ 🔴<s>{price} ₼</s>\n"
                    f"<b>İndirim</b>: {int(discount_percentage)}%\n"
                    f"<b>Son gün</b>: {product.discount_end_date.strftime('%d %B %Y')}\n"
                ),
                'az': (
                    f"<b>Başlıq</b>: {product.name}\n"
                    f"<b>Marka</b>: {brand_title}\n"
                    f"<b>Kateqoriya</b>: {category_title}\n"
                    f"<b>Təsvir</b>: {product.description}\n"
                    f"<b>Qiymət</b>: {discount_price} ₼ 🔴<s>{price} ₼</s>\n"
                    f"<b>Endirim</b>: {int(discount_percentage)}%\n"
                    f"<b>Son gün</b>: {product.discount_end_date.strftime('%d %B %Y')}\n"
                )
            }
            button_texts = {
                'en': ["Save", "Link"],
                'tr': ["Kaydet", "Bağlantı"],
                'az': ["Saxla", "Bağlantı"]
            }
            language = user.language if hasattr(user, 'language') else 'en' 

            keyboard = [
                [
                    InlineKeyboardButton("Save", callback_data=f"save_{product.id}"),
                    InlineKeyboardButton("Link", url=product.url)
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_photo(
                chat_id=user.telegram_id,
                photo=photo_url,
                caption=captions.get(language, captions['en']),
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

        except Exception as e:
            logging.error(f"Error sending product photo to {user.telegram_id}: {str(e)}")
            await context.bot.send_message(chat_id=user.telegram_id, text="Oops! Something went wrong while displaying the product. Please try again later.")
    else:
        logging.warning(f"Invalid image URL for product {product.name}.")
        await context.bot.send_message(chat_id=user.telegram_id, text="This product's image is currently unavailable. Please check back later.")


async def send_scheduled_messages(context):
    
    users = await sync_to_async(list)(Profile.objects.all())
    
    for user in users:
        new_products = await sync_to_async(list)(Product.objects.filter(discount_percentage__gte=user.min_discount, discount_percentage__lte=user.max_discount, discount_start_date__gte=(timezone.now() - timedelta(hours=168))))
        if not new_products:
            continue

        user_min_time = user.min_time  
        user_max_time = user.max_time 

        if is_time_to_notify(user_min_time, user_max_time):
            await send_user_favorite_products(user, new_products, context)
            await asyncio.sleep(0.5)  


def run_async_send_scheduled_messages(context):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(send_scheduled_messages(context))
    finally:
        if not loop.is_closed():
            loop.close()


async def my_saved_products_filter(query, language):
    user_id =query.from_user.id
    messages = {
        'no_saved_products': {
            'en': "You haven't saved any products yet.",
            'tr': "Henüz kayıtlı ürününüz yok.",
            'az': "Hələ qeyd olunmuş məhsulunuz yoxdur.",
            'ru': "Вы еще не сохранили ни одного продукта."
        },
    }
    try:
        user = await sync_to_async(Profile.objects.get)(telegram_id=user_id)

        saved_products = await sync_to_async(lambda: list(
            SavedProduct.objects.filter(
                user=user,
                product__discount_end_date__gte=datetime.now()
            )
        ))()

        if saved_products:

            for saved_product in saved_products:
                product = await sync_to_async(lambda: {
                    'id': saved_product.product.id,
                    'name': saved_product.product.name,
                    'description': saved_product.product.description,
                    'normal_price': saved_product.product.normal_price,
                    'discount_price': saved_product.product.discount_price,
                    'discount_end_date': saved_product.product.discount_end_date,
                    'image_url': saved_product.product.image_url,
                    'url': saved_product.product.url
                })()

                await display_product(query.message, product, language)

        else:
            await query.message.reply_text(messages['no_saved_products'].get(language, messages['no_saved_products']['en']))

    except Profile.DoesNotExist:
        await query.message.reply_text("User not found. Please register first.")

    except Exception as e:
        await query.message.reply_text(f"An error occurred: {str(e)}")


async def my_saved_products(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    language = await get_user_language(user_id, update, context)
    messages = {
        'no_saved_products': {
            'en': "You haven't saved any products yet.",
            'tr': "Henüz kayıtlı ürününüz yok.",
            'az': "Hələ qeyd olunmuş məhsulunuz yoxdur.",
            'ru': "Вы еще не сохранили ни одного продукта."
        },
        'user_not_found': {
            'en': "User not found. Please register first.",
            'tr': "Kullanıcı bulunamadı. Lütfen önce kayıt olun.",
            'az': "İstifadəçi tapılmadı. Əvvəlcə qeydiyyatdan keçin.",
            'ru': "Пользователь не найден. Пожалуйста, зарегистрируйтесь сначала."
        },
        'error_occurred': {
            'en': "An error occurred: {}",
            'tr': "Bir hata oluştu: {}",
            'az': "Bir səhv baş verdi: {}",
            'ru': "Произошла ошибка: {}"
        }
    }

    try:
        user = await sync_to_async(Profile.objects.get)(telegram_id=user_id)

        saved_products = await sync_to_async(lambda: list(
            SavedProduct.objects.filter(
                user=user,
                product__discount_end_date__gte=datetime.now()
            )
        ))()


        if saved_products:

            for saved_product in saved_products:
                product = await sync_to_async(lambda: {
                    'id': saved_product.product.id,
                    'name': saved_product.product.name,
                    'description': saved_product.product.description,
                    'normal_price': saved_product.product.normal_price,
                    'discount_price': saved_product.product.discount_price,
                    'discount_end_date': saved_product.product.discount_end_date,
                    'image_url': saved_product.product.image_url,
                    'url': saved_product.product.url
                })()

                await display_product(update.message, product, language)

        else:
            language = user.language if hasattr(user, 'language') else 'en'
            await update.message.reply_text(messages['no_saved_products'].get(language, messages['no_saved_products']['en']))

    except Profile.DoesNotExist:
        language = 'en'
        await update.message.reply_text(messages['user_not_found'].get(language, messages['user_not_found']['en']))

    except Exception as e:
        language = 'en'
        await update.message.reply_text(messages['error_occurred'].get(language, messages['error_occurred']['en']).format(str(e)))
        

async def merchant_role_func(update: Update, context: CallbackContext):
    user = update.effective_user
    language = await get_user_language(user.id, update, context)

    if not await is_user_registered(user.id):
        await update.message.reply_text(languages[language]["not_registered"])
        return

    try:
        user_profile = await get_user_profile(user.id)

        if user_profile['role'] == "merchant":
            keyboard = [
                [
                    InlineKeyboardButton(languages[language]['buttons']['edit_merchant'], callback_data='edit_merchant')
                ],
                [
                    InlineKeyboardButton(languages[language]['buttons']['leave_merchant'], callback_data='leave_merchant')
                ],
                [
                    InlineKeyboardButton(languages[language]['buttons']['add_product'], callback_data='add_product')
                ],
                [
                    InlineKeyboardButton(languages[language]['buttons']['all_products'], callback_data='all_products')
                ]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                languages[language]['merchant_member'].format(merchant=user_profile['merchant']),
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(languages[language]["not_merchant"])

    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text(languages[language]["error"])


async def handle_merchant_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    user_profile = await get_user_profile(user.id)
    language = await get_user_language(user.id, update, context)

    if user_profile['role'] == "merchant":
        choice = query.data

        if choice == 'edit_merchant':
            profile_instance = await sync_to_async(Profile.objects.get)(telegram_id=user.id)
            if profile_instance.has_merchant_admin_privileges():
                await edit_merchant(update, context)
            else:
                await query.edit_message_text(languages[language]['not_merchant_admin'])

        elif choice == 'leave_merchant':
            try:
                await leave_merchant(update, context)
            except Exception as e:
                print(f"Error in leave_merchant: {e}")
                await query.edit_message_text(languages[language]['error'])

        elif choice == 'add_product':
            context.user_data['adding_product'] = True  
            context.user_data['step'] = 'ask_product_name' 
            await query.message.reply_text(languages[language]['enter_product_name'])
        
        elif choice == 'all_products':
            merchant_id = user_profile['merchant']
            products = await fetch_all_discounted_products_by_merchant(merchant_id)
            if products:
                for product in products:
                    await display_product_merchant(query.message, product, language) 
            else:
                await query.message.reply_text(languages[language]['no_products_found_merchant'])
    else:
        await query.message.reply_text(languages[language]['not_merchant'])


async def edit_merchant(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    language = await get_user_language(update.effective_user.id, update, context)
    
    keyboard = [
        [InlineKeyboardButton(languages[language]['update_name'], callback_data='edit_merchant_name')],
        [InlineKeyboardButton(languages[language]['show_users'], callback_data='show_merchant_users')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(languages[language]['select_option'], reply_markup=reply_markup)


async def edit_merchant_name(update: Update, context: CallbackContext):
    user = update.effective_user
    query = update.callback_query
    language = await get_user_language(user.id, update, context)
    profile_instance = await sync_to_async(Profile.objects.get)(telegram_id=user.id)
    if not profile_instance.has_merchant_admin_privileges():
        await query.edit_message_text(languages[language]['not_merchant_admin'])
        return
    await query.answer()
    await query.message.reply_text(languages[language]['enter_new_name'])
    context.user_data['update_type'] = 'edit_name'  


async def show_merchant_users(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    language = await get_user_language(user.id, update, context)

    try:
        user_profile = await sync_to_async(Profile.objects.get)(telegram_id=user.id)
        user_merchant_role = await sync_to_async(lambda: user_profile.merchant_role)()
        
        users = await sync_to_async(list)(Profile.objects.filter(role='merchant', merchant_role=user_merchant_role))

        if len(users)>1:
            user_buttons = []
            for merchant in users:
                if merchant.telegram_id != update.effective_user.id:
                    button = InlineKeyboardButton(
                        f"{languages[language]['remove_user']} {merchant.username}", 
                        callback_data=f"remove_merchant_{merchant.telegram_id}"
                    )
                    user_buttons.append([button])

            reply_markup = InlineKeyboardMarkup(user_buttons)
            await query.message.reply_text(languages[language]['merchant_users'], reply_markup=reply_markup)
        else:
            await query.message.reply_text(languages[language]['no_users'])
    except Exception as e:
        await query.message.reply_text(f"{languages[language]['error_occurred']}")


async def remove_merchant_user(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    merchant_id = query.data.split("_")[2]
    language = await get_user_language(update.effective_user.id, update, context)

    try:
        merchant_user = await sync_to_async(Profile.objects.get)(telegram_id=merchant_id)
        
        merchant_user.merchant_role = None  
        merchant_user.role = 'user'  
        merchant_user.is_merchant_admin = False
        await sync_to_async(merchant_user.save)()
        
        await query.message.reply_text(
            languages[language]['user_removed'].format(username=merchant_user.username)
        )    
    except Profile.DoesNotExist:
        await query.message.reply_text(languages[language]['user_not_found'])
    except Exception as e:
        await query.message.reply_text(f"{languages[language]['error_occurred']} {str(e)}")

    
async def receive_merchant_name(update: Update, context: CallbackContext):
    if context.user_data.get('update_type') == 'edit_name':
        new_name = update.message.text
        user = update.effective_user
        language = await get_user_language(user.id, update, context)
        profile_instance = await sync_to_async(Profile.objects.select_related('merchant_role').get)(telegram_id=user.id)

        merchant_id = await sync_to_async(lambda: profile_instance.merchant_role.id if profile_instance.merchant_role else None)()
        
        if merchant_id is None:
            await update.message.reply_text(languages[language]['merchant_id_not_found'])
            return

        try:
            merchant = await sync_to_async(Merchant.objects.get)(id=merchant_id)
            merchant.title = new_name

            await sync_to_async(merchant.save)()

            await update.message.reply_text(languages[language]['merchant_updated'].format(new_name=new_name))
        except ObjectDoesNotExist:
            await update.message.reply_text(languages[language]['merchant_not_found'])
        except Exception as e:
            await update.message.reply_text(f"{languages[language]['error_occurred']} {str(e)}")
        
        context.user_data['update_type'] = None


async def leave_merchant(update: Update, context: CallbackContext):
    query = update.callback_query
    user = update.effective_user
    language = await get_user_language(user.id, update, context)

    keyboard = [
        [InlineKeyboardButton(languages[language]['yes_leave_merchant'], callback_data='confirm_leave_merchant')],
        [InlineKeyboardButton(languages[language]['no_keep_role'], callback_data='cancel_leave_merchant')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.answer()
    await query.edit_message_text(
        languages[language]['confirm_leave_merchant'],
        reply_markup=reply_markup
    )


async def confirm_leave_merchant(update: Update, context: CallbackContext):
    query = update.callback_query
    user = update.effective_user
    language = await get_user_language(user.id, update, context)
    try:
        profile_instance = await sync_to_async(Profile.objects.get)(telegram_id=user.id)
        if profile_instance.is_merchant():
            profile_instance.role = 'user'
            profile_instance.merchant_role = None
            profile_instance.is_merchant_admin = False
            await sync_to_async(profile_instance.save)()

            await query.answer()
            await query.edit_message_text(languages[language]['leave_success'])
        else:
            await query.answer()
            await query.edit_message_text(languages[language]['not_merchant'])

    except Profile.DoesNotExist:
        await query.answer()
        await query.edit_message_text(languages[language]['profile_not_exist'])
    except IntegrityError:
        await query.answer()
        await query.edit_message_text(languages[language]['update_issue'])
    except Exception as e:
        print(f"Error in confirm_leave_merchant: {e}")
        await query.answer()
        await query.edit_message_text(languages[language]['error'])


async def cancel_leave_merchant(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    language = await get_user_language(update.effective_user.id, update, context)
    await query.edit_message_text(languages[language]['keep_role_message'])


async def remove_product(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    language = await get_user_language(user.id, update, context)
    try:
        user_profile = await sync_to_async(Profile.objects.get)(telegram_id=user.id)
        user_merchant_role = await sync_to_async(lambda: user_profile.merchant_role)()

        product_id = query.data.split("_")[3]
        product = await sync_to_async(Product.objects.prefetch_related('merchant').get)(id=product_id)

        if user_profile.role == 'merchant' and user_merchant_role and product.merchant.id == user_merchant_role.id:
            await sync_to_async(product.delete)()
            success_message = languages[language]['product_remove_success'].format(product.name)

            if query.message:
                await query.message.delete()
                await query.message.reply_text(success_message)
        else:
            error_message = languages[language]['no_permission_to_remove_product']
            await query.message.reply_text(error_message)

    except Product.DoesNotExist:
        error_message = languages[language]['product_not_found'].format(product_id)
        await query.message.reply_text(error_message)

    except Profile.DoesNotExist:
        error_message = languages[language]['profile_not_exist']
        await query.message.reply_text(error_message)

    except Exception as e:
        error_message = languages[language]['generic_error']
        await query.message.reply_text(error_message)


async def display_product_merchant(query_or_message, product, language):
    photo_url = product['image_url']
    language = languages[language]
    if is_valid_url(photo_url):
        try:
            price = Decimal(product['normal_price']).quantize(Decimal('0.01'))
            discount_price = Decimal(product['discount_price']).quantize(Decimal('0.01'))
            caption = (
                f"{language['product_title']}: {product['name']}\n"
                f"{language['product_description']}: {product['description']}\n"
                f"{language['original_price']}: {price} ₼\n"
                f"{language['discounted_price']}: {discount_price} ₼\n"
                f"{language['last_day']}: {product['discount_end_date'].strftime('%d %B %Y')}\n"
            )

            keyboard = [
                [
                    InlineKeyboardButton(language['save'], callback_data=f"save_{product['id']}"),
                    InlineKeyboardButton(language['remove'], callback_data=f"remove_merchant_product_{product['id']}"),
                    InlineKeyboardButton(language['link'], url=product['url'])
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query_or_message.reply_photo(photo=photo_url, caption=caption, reply_markup=reply_markup)
        except Exception as e:
            await query_or_message.reply_text(language['display_error'].format(product['name']))
    else:
        await query_or_message.reply_text(language['invalid_image'].format(product['name']))


def validate_date(date_str):
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


async def process_add_product(update: Update, context: CallbackContext):
    step = context.user_data.get('step')
    user = update.effective_user
    user_profile = await get_user_profile(user.id)
    merchant_id = user_profile['merchant_id']
    language = await get_user_language(user.id, update, context)
    translations = {
    'en': {
        'ask_product_name': "📝 Please enter the product name:",
        'product_name_saved': "✅ Product name saved! Now, please enter the product description:",
        'product_description_saved': "✅ Product description saved! Now, please choose a brand:",
        'choose_brand': "✅ Brand saved! Now, please choose a category:",
        'choose_category': "✅ Category saved! Now, enter the normal price (e.g., 99.99):",
        'normal_price_saved': "✅ Normal price saved! Now, enter the discounted price (e.g., 79.99):",
        'discount_price_saved': "✅ Discounted price saved! Now, 📅 Please provide the discount start date (YYYY-MM-DD) and end date (YYYY-MM-DD) separated by a space:",
        'discount_dates_saved': "✅ Discount dates saved! Now, enter the stock quantity (e.g., 10):",
        'stock_quantity_saved': "✅ Stock quantity saved! Now, enter the product image URL:",
        'image_url_saved': "✅ Image URL saved! Now, enter the product URL:",
        'product_url_saved': "✅ Product URL saved! The product will now be added.",
        'product_added': "🎉 The product '{name}' has been successfully added!",
        'invalid_price': "❌ Please enter a valid price.",
        'invalid_discount_price': "❌ Please enter a valid discounted price.",
        'invalid_dates': "❌ Please enter valid dates in the correct format.",
        'invalid_stock_quantity': "❌ Please enter a valid stock quantity.",
        'invalid_url': "❌ Please enter a valid URL.",
        'error_processing': "❌ There was an error processing your request. Please try again.",
    },
    'tr': {
        'ask_product_name': "📝 Lütfen ürün adını girin:",
        'product_name_saved': "✅ Ürün adı kaydedildi! Şimdi, lütfen ürün açıklamasını girin:",
        'product_description_saved': "✅ Ürün açıklaması kaydedildi! Şimdi, bir marka seçin:",
        'choose_brand': "✅ Marka kaydedildi! Şimdi, bir kategori seçin:",
        'choose_category': "✅ Kategori kaydedildi! Şimdi, normal fiyatı girin (örn: 99.99):",
        'normal_price_saved': "✅ Normal fiyat kaydedildi! Şimdi, indirimli fiyatı girin (örn: 79.99):",
        'discount_price_saved': "✅ İndirimli fiyat kaydedildi! Şimdi, 📅 Lütfen indirim başlangıç ve bitiş tarihini (YYYY-AA-GG) bir boşlukla ayırarak girin:",
        'discount_dates_saved': "✅ İndirim tarihleri kaydedildi! Şimdi, stok miktarını girin (örn: 10):",
        'stock_quantity_saved': "✅ Stok miktarı kaydedildi! Şimdi, ürün görselinin URL'sini girin:",
        'image_url_saved': "✅ Görsel URL'si kaydedildi! Şimdi, ürün URL'sini girin:",
        'product_url_saved': "✅ Ürün URL'si kaydedildi! Ürün şimdi ekleniyor.",
        'product_added': "🎉 Ürün '{name}' başarıyla eklendi!",
        'invalid_price': "❌ Lütfen geçerli bir fiyat girin.",
        'invalid_discount_price': "❌ Lütfen geçerli bir indirimli fiyat girin.",
        'invalid_dates': "❌ Lütfen geçerli tarihler girin.",
        'invalid_stock_quantity': "❌ Lütfen geçerli bir stok miktarı girin.",
        'invalid_url': "❌ Lütfen geçerli bir URL girin.",
        'error_processing': "❌ İsteğiniz işlenirken bir hata oluştu. Lütfen tekrar deneyin.",
    },
    'ru': {
        'ask_product_name': "📝 Пожалуйста, введите название продукта:",
        'product_name_saved': "✅ Название продукта сохранено! Теперь, пожалуйста, введите описание продукта:",
        'product_description_saved': "✅ Описание продукта сохранено! Теперь выберите бренд:",
        'choose_brand': "✅ Бренд сохранен! Теперь выберите категорию:",
        'choose_category': "✅ Категория сохранена! Теперь введите обычную цену (например, 99.99):",
        'normal_price_saved': "✅ Обычная цена сохранена! Теперь введите цену со скидкой (например, 79.99):",
        'discount_price_saved': "✅ Цена со скидкой сохранена! Теперь 📅 Пожалуйста, укажите дату начала и окончания скидки (ГГГГ-ММ-ДД), разделенные пробелом:",
        'discount_dates_saved': "✅ Даты скидки сохранены! Теперь введите количество на складе (например, 10):",
        'stock_quantity_saved': "✅ Количество на складе сохранено! Теперь введите URL изображения продукта:",
        'image_url_saved': "✅ URL изображения сохранен! Теперь введите URL продукта:",
        'product_url_saved': "✅ URL продукта сохранен! Продукт будет добавлен.",
        'product_added': "🎉 Продукт '{name}' был успешно добавлен!",
        'invalid_price': "❌ Пожалуйста, введите действительную цену.",
        'invalid_discount_price': "❌ Пожалуйста, введите действительную цену со скидкой.",
        'invalid_dates': "❌ Пожалуйста, введите действительные даты в правильном формате.",
        'invalid_stock_quantity': "❌ Пожалуйста, введите действительное количество на складе.",
        'invalid_url': "❌ Пожалуйста, введите действительный URL.",
        'error_processing': "❌ Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова.",
    },
    'az': {
        'ask_product_name': "📝 Zəhmət olmasa, məhsulun adını daxil edin:",
        'product_name_saved': "✅ Məhsulun adı yadda saxlandı! İndi zəhmət olmasa, məhsulun təsvirini daxil edin:",
        'product_description_saved': "✅ Məhsulun təsviri yadda saxlandı! İndi bir marka seçin:",
        'choose_brand': "✅ Marka yadda saxlandı! İndi bir kateqoriya seçin:",
        'choose_category': "✅ Kateqoriya yadda saxlandı! İndi normal qiyməti daxil edin (məsələn, 99.99):",
        'normal_price_saved': "✅ Normal qiymət yadda saxlandı! İndi endirimli qiyməti daxil edin (məsələn, 79.99):",
        'discount_price_saved': "✅ Endirimli qiymət yadda saxlandı! İndi 📅 Zəhmət olmasa, endirim başlanğıc və bitiş tarixini (YYYY-AA-GG) bir boşluqla ayıraraq daxil edin:",
        'discount_dates_saved': "✅ Endirim tarixləri yadda saxlandı! İndi stok miqdarını daxil edin (məsələn, 10):",
        'stock_quantity_saved': "✅ Stok miqdarı yadda saxlandı! İndi məhsulun görüntü URL-sini daxil edin:",
        'image_url_saved': "✅ Görüntü URL-si yadda saxlandı! İndi məhsul URL-sini daxil edin:",
        'product_url_saved': "✅ Məhsul URL-si yadda saxlandı! Məhsul artıq əlavə ediləcək.",
        'product_added': "🎉 Məhsul '{name}' uğurla əlavə edildi!",
        'invalid_price': "❌ Zəhmət olmasa, etibarlı bir qiymət daxil edin.",
        'invalid_discount_price': "❌ Zəhmət olmasa, etibarlı bir endirimli qiymət daxil edin.",
        'invalid_dates': "❌ Zəhmət olmasa, düzgün formatda etibarlı tarixlər daxil edin.",
        'invalid_stock_quantity': "❌ Zəhmət olmasa, etibarlı bir stok miqdarı daxil edin.",
        'invalid_url': "❌ Zəhmət olmasa, etibarlı bir URL daxil edin.",
        'error_processing': "❌ Sorğunuzu emal edərkən xəta baş verdi. Zəhmət olmasa, yenidən cəhd edin.",
    }
}

    if step is None:
        context.user_data['step'] = 'ask_product_name'
        await update.message.reply_text(translations[language]['ask_product_name'])

    elif step == 'ask_product_name':
        product_name = update.message.text
        context.user_data['product_name'] = product_name
        context.user_data['step'] = 'ask_product_description'
        await update.message.reply_text(translations[language]['product_name_saved'])

    elif step == 'ask_product_description':
        product_description = update.message.text
        context.user_data['product_description'] = product_description
        context.user_data['step'] = 'ask_brand'
        
        merchant_id = user_profile['merchant_id']
        merchant = await sync_to_async(Merchant.objects.get)(id=merchant_id)
        brands = await sync_to_async(list)(merchant.brands.all()) 

        keyboard = [[InlineKeyboardButton(brand.title, callback_data=f"merchant_brand_{brand.id}") for brand in brands[i:i + 2]] for i in range(0, len(brands), 2)]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(translations[language]['product_description_saved'], reply_markup=reply_markup)

    elif step == 'ask_brand':
        brand_id = update.callback_query.data.split('_')[2]
        context.user_data['brand_id'] = brand_id
        context.user_data['step'] = 'ask_category'
        
        categories = await sync_to_async(list)(Category.objects.all())

        keyboard = [[InlineKeyboardButton(category.title, callback_data=f"merchant_category_{category.id}") for category in categories[i:i + 2]] for i in range(0, len(categories), 2)]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.message.reply_text(translations[language]['choose_brand'], reply_markup=reply_markup)
        
    elif step == 'ask_category':
        category_id = update.callback_query.data.split('_')[2]
        context.user_data['category_id'] = category_id
        context.user_data['step'] = 'ask_normal_price'
        await update.callback_query.message.reply_text(translations[language]["choose_category"])

    elif step == 'ask_normal_price':
        normal_price = update.message.text
        if normal_price.replace('.', '', 1).isdigit(): 
            context.user_data['normal_price'] = normal_price
            context.user_data['step'] = 'ask_discount_price'
            await update.message.reply_text(translations[language]['normal_price_saved'])
        else:
            await update.message.reply_text(translations[language]['invalid_price'])

    elif step == 'ask_discount_price':
        discount_price = update.message.text
        if discount_price.replace('.', '', 1).isdigit():
            context.user_data['discount_price'] = discount_price
            context.user_data['step'] = 'wait_for_discount_dates'
            await update.message.reply_text(translations[language]['discount_price_saved'])
        else:
            await update.message.reply_text(translations[language]['invalid_discount_price'])

    elif step == 'wait_for_discount_dates':
        dates = update.message.text.split()
        if len(dates) == 2 and all(validate_date(date) for date in dates):
            context.user_data['discount_start_date'] = dates[0]
            context.user_data['discount_end_date'] = dates[1]
            context.user_data['step'] = 'ask_stock_quantity'
            await update.message.reply_text(translations[language]['discount_dates_saved'])
        else:
            await update.message.reply_text(translations[language]['invalid_dates'])

    elif step == 'ask_stock_quantity':
        stock_quantity = update.message.text
        if stock_quantity.isdigit():
            context.user_data['stock_quantity'] = stock_quantity
            context.user_data['step'] = 'ask_image_url'
            await update.message.reply_text(translations[language]['stock_quantity_saved'])
        else:
            await update.message.reply_text(translations[language]['invalid_stock_quantity'])

    elif step == 'ask_image_url':
        image_url = update.message.text
        if is_valid_url(image_url):
            context.user_data['image_url'] = image_url
            context.user_data['step'] = 'ask_product_url'
            await update.message.reply_text(translations[language]['image_url_saved'])
        else:
            await update.message.reply_text(translations[language]['invalid_url'])

    elif step == 'ask_product_url':
        product_url = update.message.text
        if is_valid_url(product_url):
            context.user_data['product_url'] = product_url

            product_data = {
                'name': context.user_data['product_name'],
                'description': context.user_data['product_description'],
                'brand_id': context.user_data['brand_id'],
                'category_id': context.user_data['category_id'],
                'merchant_id': merchant_id,
                'normal_price': context.user_data['normal_price'],
                'discount_price': context.user_data['discount_price'],
                'discount_start_date': context.user_data['discount_start_date'],
                'discount_end_date': context.user_data['discount_end_date'],
                'image_url': context.user_data['image_url'],
                'url': product_url,
                'stock_quantity': context.user_data['stock_quantity'],
                'is_active': True
            }

            await sync_to_async(Product.objects.create)(**product_data)

            await update.message.reply_text(translations[language]['product_added'].format(name=context.user_data['product_name']))

            del context.user_data['adding_product']
            del context.user_data['product_name']
            del context.user_data['product_description']
            del context.user_data['brand_id']
            del context.user_data['category_id']
            del context.user_data['normal_price']
            del context.user_data['discount_price']
            del context.user_data['discount_start_date']
            del context.user_data['discount_end_date']
            del context.user_data['stock_quantity']
            del context.user_data['image_url']
            del context.user_data['product_url']
            await merchant_role_func(update, context)

        else:
            await update.message.reply_text(translations[language]['invalid_url'])

    else:
        await update.message.reply_text(translations[language]['error_processing'])
