import os
import re
import logging
import telebot
from supabase import create_client, Client
import g4f
import requests
import time

# إعداد السجلات لمراقبة الأداء
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# بيانات الاعتماد (تأكد من ضبطها في متغيرات البيئة ببيئة التشغيل)
TOKEN = os.environ.get("TELEGRAM_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# إنشاء عميل البوت وعميل Supabase
bot = telebot.TeleBot(TOKEN, threaded=False)

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("تم الاتصال بـ Supabase بنجاح.")
except Exception as e:
    logger.error(f"خطأ في الاتصال بـ Supabase: {e}")

# قاموس لتخزين حالة المستخدم
user_states = {}

def get_ai_response(prompt):
    """وظيفة لاستخدام g4f للرد على الرسائل العامة بطريقة مرنة"""
    try:
        # استخدام g4f بدون استيراد المزودين لتجنب أخطاء ImportError
        response = g4f.ChatCompletion.create(
            model=g4f.models.default,
            messages=[
                {"role": "system", "content": "أنت مساعد ذكي لبوت VANTOR. أجب بلهجة محترمة ولباقة."},
                {"role": "user", "content": prompt}
            ],
        )
        if response and len(str(response)) > 0:
            return response
        return "أهلاً بك أستاذي، أنا معك، كيف يمكنني خدمتك؟"
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return "أهلاً بك أستاذي، أنا معك، كيف يمكنني خدمتك؟"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.chat.id
    user_states[user_id] = None # إعادة ضبط الحالة
    welcome_text = (
        f"أهلاً بك أستاذ {message.from_user.first_name} في نظام VANTOR.\n"
        "يمكنك الاستفسار عن حالة طلبك بإرسال كلمة 'تتبع' أو 'طلب' أو أي سؤال آخر."
    )
    bot.send_message(user_id, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.chat.id
    text = message.text.strip().lower()

    # كلمات التحية
    greetings = ['سلام', 'هلا', 'مرحبا', 'السلام', 'شلونك', 'صباح', 'مساء', 'هلو', 'الو']

    # 1. إذا كان البوت ينتظر رقم طلب
    if user_states.get(user_id) == 'waiting_for_order':
        # البحث عن أي أرقام في الرسالة
        order_id_match = re.search(r'\d+', text)
        if order_id_match:
            order_id = order_id_match.group()
            user_states[user_id] = None # إنهاء الحالة
            process_order_tracking(message, order_id)
            return
        else:
            if any(word in text for word in greetings):
                user_states[user_id] = None
                ai_reply = get_ai_response(message.text)
                bot.send_message(user_id, ai_reply)
            else:
                bot.send_message(user_id, "من فضلك أرسل رقم الطلب فقط (أرقام) لكي أتمكن من مساعدتك.")
            return

    # 2. الكشف عن نية تتبع الطلب
    tracking_keywords = ['تتبع', 'وين', 'وصل', 'طلبي', 'اين', 'الطلب', 'وين صار', 'حالة']
    if any(word in text for word in tracking_keywords):
        user_states[user_id] = 'waiting_for_order'
        bot.send_message(user_id, "أبشر، زودني برقم الطلب الخاص بك لأتحقق من حالته:")
        return

    # 3. الرد العام باستخدام الذكاء الاصطناعي
    ai_reply = get_ai_response(message.text)
    bot.send_message(user_id, ai_reply)

def process_order_tracking(message, order_id):
    """البحث في قاعدة بيانات Supabase مع تجربة أكثر من عمود"""
    user_id = message.chat.id
    bot.send_message(user_id, f"جاري البحث عن الطلب رقم (#{order_id})...")
    
    found = False
    # قائمة بالأعمدة المحتملة لرقم الطلب في جدولك
    potential_columns = ['id', 'order_number', 'order_id']
    
    for col in potential_columns:
        try:
            query = supabase.table('orders').select("*").eq(col, order_id).execute()
            if query.data and len(query.data) > 0:
                order_data = query.data[0]
                status = order_data.get('status', 'تحت المعالجة')
                bot.send_message(user_id, f"أستاذي، طلبك رقم (#{order_id}) حالته الحالية هي: {status}.")
                found = True
                break
        except Exception:
            continue
            
    if not found:
        bot.send_message(user_id, f"عذراً، لم أجد طلباً مسجلاً بالرقم (#{order_id}). تأكد من الرقم مرة أخرى.")

if __name__ == '__main__':
    logger.info("البوت يعمل الآن بنظام VANTOR...")
    
    # حل مشكلة الـ Conflict وحذف الويب هوك
    try:
        bot.remove_webhook()
    except:
        pass
        
    # حلقة تشغيل دائمة لمعالجة أخطاء الاتصال
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=60)
        except Exception as e:
            logger.error(f"Polling Error: {e}")
            time.sleep(5)
