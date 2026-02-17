import os
import re
import logging
import telebot
from supabase import create_client, Client
import g4f

# إعداد السجلات لمراقبة الأداء وتحديد الأخطاء
logging.basicConfig(level=logging.INFO)

# بيانات الاعتماد من متغيرات البيئة
TOKEN = os.environ.get("TELEGRAM_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# إنشاء عميل Supabase وعميل البوت
bot = telebot.TeleBot(TOKEN)

# التحقق من اتصال Supabase عند التشغيل
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logging.info("تم الاتصال بـ Supabase بنجاح.")
except Exception as e:
    logging.error(f"فشل الاتصال الأولي بـ Supabase: {e}")

# قاموس لتخزين حالة المستخدم
user_states = {}

def get_ai_response(prompt):
    """استخدام g4f للرد على الرسائل العامة بذكاء"""
    try:
        response = g4f.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        return response
    except Exception as e:
        logging.error(f"AI Error: {e}")
        return "تفضل أستاذي، كيف يمكنني مساعدتك اليوم؟"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_states[user_id] = None # تصغير الحالة عند البدء
    bot.reply_to(message, f"أهلاً بك أستاذ {message.from_user.first_name} في نظام VANTOR.\nيمكنك الاستفسار عن حالة طلبك في أي وقت.")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.chat.id
    text = message.text.strip().lower()

    # 1. استثناء التحيات من نظام التتبع (لكي لا يطلب الرقم عند السلام)
    greetings = ['سلام', 'هلا', 'مرحبا', 'شلونك', 'صباح', 'مساء', 'السلام']
    if any(word in text for word in greetings) and user_states.get(user_id) != 'waiting_for_order':
        ai_reply = get_ai_response(message.text)
        bot.reply_to(message, ai_reply)
        return

    # 2. إذا كان البوت ينتظر رقماً ووصله نص يحتوي على أرقام
    if user_states.get(user_id) == 'waiting_for_order':
        order_id_match = re.search(r'\d+', text)
        if order_id_match:
            order_id = order_id_match.group()
            user_states[user_id] = None # إنهاء الحالة فور استلام الرقم
            process_order_tracking(message, order_id)
            return
        else:
            # إذا سلم المستخدم وهو في حالة التتبع، نخرجه منها ونرد بذكاء
            if any(word in text for word in greetings):
                user_states[user_id] = None
                bot.reply_to(message, "وعليكم السلام، كيف أخدمك؟")
            else:
                bot.reply_to(message, "أستاذي العزيز، يرجى تزويدي برقم الطلب (أرقام فقط) لنتمكن من مساعدتك.")
            return

    # 3. الكشف عن نية التتبع (بشرط ألا يكون مجرد سلام)
    tracking_keywords = ['تتبع', 'وين', 'وصل', 'طلبي', 'اين', 'الطلب', 'وين صار']
    if any(word in text for word in tracking_keywords):
        user_states[user_id] = 'waiting_for_order'
        bot.reply_to(message, "على الرحب والسعة، يرجى تزويدي برقم الطلب الخاص بك:")
        return

    # 4. أي كلام آخر يذهب للذكاء الاصطناعي
    ai_reply = get_ai_response(message.text)
    bot.reply_to(message, ai_reply)

def process_order_tracking(message, order_id):
    """البحث الفعلي في قاعدة البيانات مع معالجة الأخطاء"""
    try:
        # ملاحظة: تأكد أن اسم الجدول 'orders' والعمود 'order_number'
        query = supabase.table('orders').select("*").eq('order_number', order_id).execute()
        
        # التأكد من وجود بيانات في الاستجابة
        if query.data and len(query.data) > 0:
            order_data = query.data[0]
            status = order_data.get('status', 'قيد المعالجة')
            bot.send_message(message.chat.id, f"أستاذي العزيز، طلبك ذو الرقم (#{order_id}) حالته الآن: {status}.")
        else:
            bot.send_message(message.chat.id, f"عذراً، لم أجد طلباً بالرقم (#{order_id}) في سجلاتنا. يرجى التأكد من الرقم.")
            
    except Exception as e:
        logging.error(f"خطأ في الوصول لـ Supabase: {e}")
        bot.send_message(message.chat.id, "أعتذر منك، حدث خلل فني أثناء جلب بيانات الطلب. يرجى المحاولة بعد قليل.")

if __name__ == '__main__':
    logging.info("البوت بدأ العمل بنظام الفلترة الذكي...")
    bot.infinity_polling()
