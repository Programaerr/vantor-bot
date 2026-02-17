import telebot
import os
import time
import logging

# إعداد السجلات لمراقبة أداء البوت في Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# جلب التوكن من المتغيرات البيئية (Secrets) في Railway
# تأكد من إضافة BOT_TOKEN في قسم Variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# التحقق من وجود التوكن
if not BOT_TOKEN:
    logger.error("خطأ: لم يتم العثور على BOT_TOKEN في Secrets المنصة!")
    exit(1)

# تهيئة البوت
bot = telebot.TeleBot(BOT_TOKEN)

# --- دالة منطق الردود الذكية ---
def get_correct_response(text):
    """
    هنا يتم تحديد الرد الصحيح بناءً على ما يرسله المستخدم.
    تمت إضافة منطق للتعامل مع التحيات والكلمات الشائعة.
    """
    text = text.strip()
    
    # قاموس للردود السريعة
    responses = {
        "هلو": "أهلاً بك! كيف يمكنني مساعدتك اليوم؟",
        "هلا": "هلا بيك، نورت البوت.",
        "مرحبا": "مرحباً! أنا جاهز لخدمتك.",
        "السلام عليكم": "وعليكم السلام ورحمة الله وبركاته، كيف حالك؟",
        "سلام عليكم": "وعليكم السلام ورحمة الله وبركاته، أهلاً بك.",
        "من انت": "أنا بوت VANTOR، تم تطويري لأكون مساعدك الشخصي.",
        "شكرا": "العفو! هذا واجبنا.",
        "ه": "نعم؟ تفضل، أنا أسمعك."
    }

    # البحث في القاموس
    if text in responses:
        return responses[text]
    
    # إذا كانت الرسالة تحتوي على كلمة معينة (بحث جزئي)
    if "كيف" in text:
        return "أنا بخير والحمد لله، ماذا عنك؟"
    
    # الرد الافتراضي إذا لم يفهم البوت النص بشكل محدد
    return "وصلت رسالتك، هل يمكنني مساعدتك في شيء محدد؟"

# --- معالجة الرسائل ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """الرد على أمر التشغيل الأول"""
    welcome_msg = "أهلاً بك في بوت VANTOR! تم إصلاح كافة المشاكل التقنية والآن أنا مستعد للرد عليك."
    try:
        bot.reply_to(message, welcome_msg)
        logger.info(f"تم إرسال ترحيب للمستخدم: {message.chat.id}")
    except Exception as e:
        logger.error(f"خطأ في إرسال الترحيب: {e}")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """معالجة كافة الرسائل النصية وضمان رد صحيح"""
    try:
        user_text = message.text
        chat_id = message.chat.id
        
        logger.info(f"رسالة جديدة من {chat_id}: {user_text}")

        # الحصول على الرد المنطقي من الدالة التي أنشأناها
        final_reply = get_correct_response(user_text)

        # إرسال الرد
        bot.send_message(chat_id, final_reply)
        logger.info(f"تم إرسال الرد: {final_reply}")

    except Exception as e:
        logger.error(f"حدث خطأ أثناء معالجة الرسالة: {e}")
        # ملاحظة: لن نرسل رسالة "خلل تقني" للمستخدم لكي لا ينزعج، سنكتفي بتسجيلها في الـ Logs

# --- آلية التشغيل والاتصال المستمر ---

def start_bot():
    """تشغيل البوت بوضعية الاستقرار التام في Railway"""
    while True:
        try:
            logger.info("جاري محاولة الاتصال بتيليجرام...")
            # تنظيف أي جلسة معلقة
            bot.remove_webhook()
            # تشغيل البوت مع وضع مهلة انتظار طويلة لمنع التوقف
            bot.polling(none_stop=True, interval=1, timeout=60)
        except Exception as e:
            logger.error(f"انقطع الاتصال أو حدث تعارض: {e}")
            # الانتظار قليلاً قبل إعادة المحاولة تلقائياً
            time.sleep(5)

if __name__ == "__main__":
    # تشغيل الملف بالكامل
    start_bot()
