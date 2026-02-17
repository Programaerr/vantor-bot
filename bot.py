import telebot
import os
import time
import logging

# إعداد نظام السجلات لمراقبة أداء البوت في Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# جلب التوكن من المتغيرات البيئية (Secrets) في Railway
# تأكد من إضافة متغير باسم BOT_TOKEN في قسم Variables في Railway
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# التحقق من وجود التوكن قبل البدء
if not BOT_TOKEN:
    logger.error("خطأ: لم يتم العثور على BOT_TOKEN في متغيرات البيئة (Secrets)!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# --- منطقة منطق الردود (Logic) ---
# هنا يمكنك تعديل الردود لضمان إعطاء إجابة صحيحة

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """الرد على أمر التشغيل"""
    logger.info(f"أمر /start من المستخدم: {message.chat.id}")
    bot.reply_to(message, "أهلاً بك! البوت يعمل الآن باستخدام Secrets منصة Railway بنجاح.")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """
    هنا يتم استقبال ومعالجة كل الرسائل.
    تأكد من كتابة المنطق الذي تريده هنا ليكون الرد صحيحاً.
    """
    try:
        user_input = message.text
        logger.info(f"رسالة جديدة: {user_input}")

        # مثال لمنطق رد (قم بتغييره حسب حاجتك):
        # إذا كنت تريد ردوداً محددة بناءً على نص معين
        if "مرحبا" in user_input:
            response = "أهلاً وسهلاً بك!"
        else:
            # هنا تضع الرد الافتراضي أو منطق المعالجة
            response = f"لقد استلمت رسالتك وهي: {user_input}"

        bot.send_message(message.chat.id, response)
        logger.info(f"تم إرسال الرد بنجاح")

    except Exception as e:
        logger.error(f"حدث خطأ أثناء معالجة الرسالة: {e}")

# --- آلية التشغيل المستقر في بيئة Railway ---

def run_bot():
    """تشغيل البوت مع معالجة الأخطاء الشائعة في الاستضافة"""
    while True:
        try:
            logger.info("جاري بدء تشغيل البوت (Polling)...")
            # حذف أي ويب هوك قديم لضمان عدم حدوث Conflict
            bot.remove_webhook()
            # تشغيل البوت
            bot.polling(none_stop=True, interval=0, timeout=40)
        except Exception as e:
            logger.error(f"خطأ في الاتصال أو التعارض: {e}")
            # الانتظار قبل إعادة المحاولة لتجنب الحظر أو تكرار الأخطاء
            time.sleep(10)

if __name__ == "__main__":
    # كتابة الملف كاملاً دون اختصارات لضمان التشغيل الصحيح
    run_bot()
