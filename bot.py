import telebot
import os
import time
import logging

# إعداد السجلات لمراقبة أداء البوت في Railway بدقة
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# جلب التوكن من الـ Secrets في Railway
# تأكد من وجود متغير باسم BOT_TOKEN في إعدادات Railway
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# التحقق من أن التوكن تم سحبه بنجاح من Secrets
if not BOT_TOKEN:
    logger.error("خطأ: لم يتم العثور على BOT_TOKEN في متغيرات البيئة (Secrets)!")
    # في حال عدم وجود توكن، سيتوقف البوت عن العمل لتنبيهك
    exit(1)

# تهيئة البوت باستخدام التوكن
bot = telebot.TeleBot(BOT_TOKEN)

# --- معالجة الأوامر ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """الرد عند إرسال /start"""
    logger.info(f"مستخدم بدأ البوت: {message.chat.id}")
    try:
        # قمنا بتغيير الرد هنا لضمان عدم تكرار جملة 'الخلل التقني'
        bot.reply_to(message, "أهلاً بك! البوت يعمل الآن بشكل صحيح وتم إصلاح الخلل.")
    except Exception as e:
        logger.error(f"فشل في إرسال ترحيب: {e}")

# --- معالجة الرسائل النصية (هنا تم حل مشكلة الرد الثابت) ---

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """
    استقبال الرسائل ومعالجتها.
    تم حذف جملة 'صار عندي خلل تقني' واستبدالها بمنطق تفاعلي.
    """
    user_input = message.text
    chat_id = message.chat.id
    
    logger.info(f"رسالة من {chat_id}: {user_input}")

    try:
        # هنا نضع منطق الرد الصحيح
        # إذا كنت تريد ردوداً ذكية، يمكنك إضافة شروط هنا
        if user_input.lower() in ['هلو', 'هلا', 'مرحبا']:
            reply = "هلا بك! كيف أقدر أساعدك اليوم؟"
        elif user_input.lower() == 'ه':
            reply = "نعم؟ هل هناك شيء تود الاستفسار عنه؟"
        else:
            # الرد الافتراضي يكون صدى للرسالة أو رداً منطقياً
            reply = f"وصلت رسالتك: {user_input}"

        # إرسال الرد الفعلي للمستخدم
        bot.send_message(chat_id, reply)
        logger.info(f"تم إرسال الرد بنجاح لـ {chat_id}")

    except Exception as e:
        # في حال حدوث خطأ حقيقي، نسجله في الـ Logs بدلاً من إرساله للمستخدم كرسالة ثابتة
        logger.error(f"خطأ في معالجة الرسالة: {e}")
        # يمكنك إرسال رسالة تنبيه بسيطة فقط إذا أردت، لكننا سنتركها فارغة لضمان عدم التكرار
        # bot.send_message(chat_id, "عذراً، واجهت مشكلة بسيطة في فهم الرسالة.")

# --- آلية التشغيل المستقر (Polling) ---

def run_bot():
    """تشغيل البوت مع مراعاة بيئة استضافة Railway"""
    while True:
        try:
            logger.info("بدء الاتصال مع سيرفرات تيليجرام...")
            
            # التأكد من إغلاق أي جلسة قديمة (لحل مشكلة Conflict 409)
            bot.remove_webhook()
            
            # تشغيل البوت بانتظار طويل (Long Polling) لضمان الاستقرار
            bot.polling(none_stop=True, interval=0, timeout=60)
            
        except Exception as e:
            # تسجيل الخطأ والانتظار قبل إعادة التشغيل تلقائياً
            logger.error(f"انقطع الاتصال، سأعيد المحاولة: {e}")
            time.sleep(10)

if __name__ == "__main__":
    # كتابة الكود كاملاً لضمان عدم فقدان أي وظيفة
    run_bot()
