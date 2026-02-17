import os
import re
import logging
import telebot
from supabase import create_client, Client
import g4f
import requests

# إعداد السجلات لمراقبة الأداء
logging.basicConfig(level=logging.INFO)

# بيانات الاعتماد (تأكد من ضبطها في متغيرات البيئة ببيئة التشغيل)
TOKEN = os.environ.get("TELEGRAM_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# إنشاء عميل البوت وعميل Supabase
# استخدمنا threaded=False لزيادة الاستقرار في بعض بيئات الحاويات (Containers)
bot = telebot.TeleBot(TOKEN, threaded=False)

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logging.info("تم الاتصال بـ Supabase بنجاح.")
except Exception as e:
    logging.error(f"خطأ في الاتصال بـ Supabase: {e}")

# قاموس لتخزين حالة المستخدم
user_states = {}

def get_ai_response(prompt):
    """وظيفة لاستخدام g4f للرد على الرسائل العامة"""
    try:
        # قمنا بتحديد الموديل واستخدام مزودين افتراضيين لضمان المجانية والاستقرار
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_35_turbo,
            messages=[{"role": "user", "content": prompt}],
        )
        # التأكد من أن الرد ليس فارغاً
        if response and len(str(response)) > 0:
            return response
        return "أهلاً بك أستاذي، أنا معك، كيف يمكنني خدمتك؟"
    except Exception as e:
        logging.error(f"AI Error: {e}")
        # رد احتياطي في حال فشل الاتصال بالمزودين المجانيين
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

    # كلمات التحية لتجنب تداخلها مع نظام التتبع
    greetings = ['سلام', 'هلا', 'مرحبا', 'السلام', 'شلونك', 'صباح', 'مساء']

    # 1. إذا كان البوت ينتظر رقم طلب
    if user_states.get(user_id) == 'waiting_for_order':
        # البحث عن أي أرقام في الرسالة
        order_id_match = re.search(r'\d+', text)
        if order_id_match:
            order_id = order_id_match.group()
            user_states[user_id] = None # إنهاء الحالة فوراً
            process_order_tracking(message, order_id)
            return
        else:
            # إذا أرسل سلام وهو في حالة انتظار الرقم، نلغي الحالة ونرد عليه
            if any(word in text for word in greetings):
                user_states[user_id] = None
                ai_reply = get_ai_response(message.text)
                bot.send_message(user_id, ai_reply)
            else:
                bot.send_message(user_id, "من فضلك أرسل رقم الطلب فقط (أرقام) لكي أتمكن من مساعدتك.")
            return

    # 2. الكشف عن نية تتبع الطلب
    tracking_keywords = ['تتبع', 'وين', 'وصل', 'طلبي', 'اين', 'الطلب', 'وين صار']
    if any(word in text for word in tracking_keywords):
        user_states[user_id] = 'waiting_for_order'
        bot.send_message(user_id, "أبشر، زودني برقم الطلب الخاص بك لأتحقق من حالته:")
        return

    # 3. الرد العام باستخدام الذكاء الاصطناعي (للسلام وغيره)
    ai_reply = get_ai_response(message.text)
    bot.send_message(user_id, ai_reply)

def process_order_tracking(message, order_id):
    """البحث في قاعدة بيانات Supabase"""
    user_id = message.chat.id
    bot.send_message(user_id, f"جاري البحث عن الطلب رقم (#{order_id})...")
    
    try:
        # تم تعديل الاستعلام ليستخدم id بدلاً من order_number بناءً على سجلات الخطأ السابقة
        # إذا كان اسم العمود في قاعدة بياناتك هو id، فالتعديل أدناه سيحل المشكلة
        query = supabase.table('orders').select("*").eq('id', order_id).execute()
        
        if query.data and len(query.data) > 0:
            order_data = query.data[0]
            status = order_data.get('status', 'تحت المعالجة')
            bot.send_message(user_id, f"أستاذي، طلبك رقم (#{order_id}) حالته الحالية هي: {status}.")
        else:
            # محاولة أخيرة بالبحث في عمود order_number إذا كان التعديل أعلاه لم يصب الهدف
            try:
                query_alt = supabase.table('orders').select("*").eq('order_number', order_id).execute()
                if query_alt.data and len(query_alt.data) > 0:
                    order_data = query_alt.data[0]
                    status = order_data.get('status', 'تحت المعالجة')
                    bot.send_message(user_id, f"أستاذي، طلبك رقم (#{order_id}) حالته الحالية هي: {status}.")
                    return
            except:
                pass
                
            bot.send_message(user_id, f"عذراً، لم أجد طلب مسجل بالرقم (#{order_id}). تأكد من الرقم مرة أخرى.")
            
    except Exception as e:
        logging.error(f"Supabase Error: {e}")
        bot.send_message(user_id, "أعتذر أستاذي، واجهت مشكلة تقنية أثناء محاولة جلب البيانات. حاول لاحقاً.")

if __name__ == '__main__':
    logging.info("البوت يعمل الآن بنظام VANTOR المحدث...")
    # استخدام skip_pending لتجاهل الرسائل القديمة التي أرسلت والبوت مطفأ
    try:
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        logging.error(f"Polling Error: {e}")
