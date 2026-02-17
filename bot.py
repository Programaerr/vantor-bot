import telebot
import os
import time
import logging
import g4f

# إعداد السجلات
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# جلب التوكن
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    logger.error("خطأ: BOT_TOKEN غير موجود في الإعدادات!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# --- محرك الذكاء الاصطناعي الذكي والمستقر ---

def get_ai_response(user_message):
    """
    جلب رد ذكي باستخدام أفضل الموديلات المتاحة تلقائياً لتجنب أخطاء المسميات.
    """
    try:
        # استخدام التحديد التلقائي للموديل لضمان العمل مهما تغيرت إصدارات المكتبة
        response = g4f.ChatCompletion.create(
            model=g4f.models.default, # اختيار الموديل الافتراضي المستقر تلقائياً
            messages=[
                {"role": "system", "content": "أنت VANTOR، مساعد ذكي جداً وقادر على الإجابة على كل الأسئلة بذكاء ومنطق باللغة العربية."},
                {"role": "user", "content": user_message}
            ],
        )
        
        if response and len(str(response)) > 0:
            return response
        else:
            return "أنا أفكر بعمق حالياً، هل يمكنك إعادة صياغة سؤالك؟"
            
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return "أعتذر، حدث ضغط بسيط في معالجة البيانات. أنا معك الآن، ماذا تريد أن تسأل؟"

# --- معالجة الرسائل ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = "مرحباً! أنا VANTOR الذكي. كيف يمكنني مساعدتك اليوم؟"
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    chat_id = message.chat.id
    user_text = message.text

    # إظهار حالة الكتابة
    bot.send_chat_action(chat_id, 'typing')
    
    logger.info(f"رسالة من {chat_id}: {user_text}")

    # جلب الرد من الذكاء الاصطناعي
    reply = get_ai_response(user_text)

    try:
        bot.send_message(chat_id, reply)
        logger.info(f"تم الرد بنجاح على: {chat_id}")
    except Exception as e:
        logger.error(f"فشل الإرسال: {e}")

# --- آلية التشغيل ومنع التعارض ---

def run_bot():
    """
    تشغيل البوت مع محاولة تنظيف الاتصالات القديمة لمنع خطأ 409 Conflict.
    """
    while True:
        try:
            logger.info("محاولة بدء تشغيل البوت ومنع التعارض...")
            # إزالة الويب هوك والاتصالات السابقة
            bot.remove_webhook()
            time.sleep(1) 
            
            # البدء باستقبال الرسائل
            bot.polling(none_stop=True, interval=2, timeout=40)
            
        except Exception as e:
            if "Conflict" in str(e):
                logger.warning("يوجد تعارض: نسخة أخرى تعمل. سأحاول إيقافها والبدء مجدداً...")
                time.sleep(10) # انتظار أطول لكي يقوم التليجرام بإغلاق الجلسة القديمة
            else:
                logger.error(f"خطأ غير متوقع: {e}")
                time.sleep(5)

if __name__ == "__main__":
    run_bot()
