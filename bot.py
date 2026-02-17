import os
import re
import logging
import telebot
from supabase import create_client, Client
import g4f
import requests

# إعداد السجلات لمراقبة الأداء
logging.basicConfig(level=logging.INFO)

# بيانات الاعتماد (تأكد من ضبطها في متغيرات البيئة)
TOKEN = os.environ.get("TELEGRAM_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# إنشاء عميل Supabase وعميل البوت
bot = telebot.TeleBot(TOKEN)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# قاموس لتخزين حالة المستخدم (هل هو في مرحلة انتظار رقم الطلب أم لا)
user_states = {}

def get_ai_response(prompt):
    """وظيفة لاستخدام g4f للرد على الرسائل العامة"""
    try:
        response = g4f.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        return response
    except Exception as e:
        logging.error(f"AI Error: {e}")
        return "أعتذر أستاذي، واجهت مشكلة في معالجة طلبك حالياً."

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        f"أهلاً بك {message.from_user.first_name} في نظام VANTOR.\n"
        "أنا هنا لمساعدتك، يمكنك الاستفسار عن طلبك أو الدردشة معي."
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.chat.id
    text = message.text.lower()

    # 1. التحقق إذا كان المستخدم في حالة انتظار رقم الطلب
    if user_states.get(user_id) == 'waiting_for_order':
        order_id_match = re.search(r'\d+', text)
        if order_id_match:
            order_id = order_id_match.group()
            process_order_tracking(message, order_id)
            return
        else:
            bot.reply_to(message, "من فضلك أستاذي، أرسل رقم الطلب بشكل صحيح (أرقام فقط).")
            return

    # 2. التحقق من "نية" المستخدم (هل يريد التتبع؟)
    # نستخدم كلمات مفتاحية ليكون البوت مرناً مع الأخطاء الإملائية
    keywords = ['تتبع', 'وين', 'وصل', 'طلبي', 'اين', 'order', 'track']
    if any(word in text for word in keywords):
        user_states[user_id] = 'waiting_for_order'
        bot.reply_to(message, "تفضل أستاذي، زودني برقم الطلب الخاص بك لأتحقق لك من حالته:")
        return

    # 3. إذا لم يكن يريد التتبع، نستخدم الذكاء الاصطناعي g4f للرد
    ai_reply = get_ai_response(message.text)
    bot.reply_to(message, ai_reply)

def process_order_tracking(message, order_id):
    """البحث في قاعدة بيانات Supabase عن حالة الطلب"""
    user_id = message.chat.id
    bot.send_message(user_id, f"جاري البحث عن الطلب رقم (#{order_id})...")
    
    try:
        # البحث في جدول orders (تأكد أن اسم الجدول والعمود صحيحين في Supabase)
        response = supabase.table('orders').select("*").eq('order_number', order_id).execute()
        
        if response.data:
            order_data = response.data[0]
            status = order_data.get('status', 'قيد المعالجة')
            bot.send_message(user_id, f"أستاذي العزيز، طلبك ذو الرقم (#{order_id}) حالته الآن: {status}.")
        else:
            bot.send_message(user_id, f"عذراً، لم أجد طلباً بالرقم (#{order_id}) في سجلاتنا.")
            
    except Exception as e:
        logging.error(f"Supabase Error: {e}")
        bot.send_message(user_id, "حدث خطأ أثناء الاتصال بقاعدة البيانات، يرجى المحاولة لاحقاً.")
    
    # إنهاء حالة الانتظار بعد الرد
    user_states[user_id] = None

if __name__ == '__main__':
    logging.info("البوت بدأ العمل باستخدام pyTelegramBotAPI...")
    bot.infinity_polling()
