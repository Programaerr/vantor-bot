import os
import re
import logging
import telebot
from supabase import create_client, Client
import g4f
import requests
import time

# استيراد الإعدادات من الملف الجديد
from config import SYSTEM_PROMPT, STATUS_MAP

# إعداد السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# بيانات الاعتماد
TOKEN = os.environ.get("TELEGRAM_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

bot = telebot.TeleBot(TOKEN, threaded=False)

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("تم الاتصال بـ Supabase بنجاح.")
except Exception as e:
    logger.error(f"خطأ في الاتصال بـ Supabase: {e}")

user_data = {}

def get_ai_response(prompt, user_id):
    """جلب الرد باستخدام البرومبت الصارم من config.py"""
    try:
        response = g4f.ChatCompletion.create(
            model=g4f.models.default,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
        )
        if response and len(str(response)) > 0:
            return response
        return "يا هلا بيك عيني بـ VANTOR للملابس، بشنو أكدر أخدمك اليوم؟"
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return "أهلاً بيك غالي، شلون أكدر أساعدك بخصوص قطع الملابس اللي طلبتها؟"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.chat.id
    user_data[user_id] = {'state': None, 'last_order_id': None}
    welcome_text = (
        f"يا هلا ومية هلا بيك أستاذ {message.from_user.first_name} في براند VANTOR للملابس.\n\n"
        "أنا مساعدك الذكي، تكدر تتبع طلبك (أرسل رقم الطلب) "
        "أو استفسر عن أي شي بخصوص موديلاتنا وأنا حاضر عيوني."
    )
    bot.send_message(user_id, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.chat.id
    text = message.text.strip()
    
    if user_id not in user_data:
        user_data[user_id] = {'state': None, 'last_order_id': None}

    # التحقق من وجود رقم في الرسالة (أولوية تتبع الطلب)
    order_id_match = re.search(r'\d+', text)
    
    # كلمات إعادة البحث
    re_check_keywords = ['متأكد', 'صح', 'مرة ثانية', 'عيد البحث', 'شصار بطلبي']
    if any(word in text for word in re_check_keywords) and user_data[user_id]['last_order_id']:
        process_order_tracking(message, user_data[user_id]['last_order_id'])
        return

    # إذا أرسل رقم طلب مباشرة
    if order_id_match and (len(order_id_match.group()) >= 4 or text.startswith('#')):
        order_id = order_id_match.group()
        user_data[user_id]['last_order_id'] = order_id
        process_order_tracking(message, order_id)
        return

    # الكشف عن نية التتبع
    tracking_keywords = ['تتبع', 'وين وصل', 'طلبي', 'حالة الطلب', 'شوكت يوصل']
    if any(word in text.lower() for word in tracking_keywords):
        user_data[user_id]['state'] = 'waiting_for_order'
        bot.send_message(user_id, "من رخصتك عيوني، زودني برقم الطلب مالتك حتى أشوفلك القطع وين صارت:")
        return

    # الرد العام باستخدام الذكاء الاصطناعي (يلتزم بالبرومبت الصارم)
    ai_reply = get_ai_response(text, user_id)
    bot.send_message(user_id, ai_reply)

def process_order_tracking(message, order_id):
    """البحث في سجلات VANTOR والرد باستخدام STATUS_MAP من الإعدادات"""
    user_id = message.chat.id
    bot.send_message(user_id, f"تدلل أغاتي، جاري التشييك على طلب الملابس رقم (#{order_id})...")
    
    found = False
    potential_columns = ['id', 'order_number', 'order_id']
    
    for col in potential_columns:
        try:
            query = supabase.table('orders').select("*").eq(col, order_id).execute()
            if query.data and len(query.data) > 0:
                order_data = query.data[0]
                status = order_data.get('status', 'processing').lower()
                
                # استخدام الترجمة من config.py
                msg = STATUS_MAP.get(status, f"حالة طلبك الحالية هي: {status}")
                bot.send_message(user_id, f"أستاذي العزيز، بخصوص طلبك رقم (#{order_id})، {msg}")
                found = True
                break
        except:
            continue
            
    if not found:
        bot.send_message(user_id, f"والله يا عيني بحثت بسجلاتنا وما لكيت رقم طلب ملابس بهذا الرقم (#{order_id}). تأكد من الرقم يرحم والديك.")

if __name__ == '__main__':
    logger.info("VANTOR CLOTHING BOT IS RUNNING...")
    
    try:
        bot.remove_webhook()
    except:
        pass
        
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=90)
        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(10)
