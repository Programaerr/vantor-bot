import telebot
import os
import time
import logging
import g4f  # مكتبة توفر ذكاء اصطناعي مجاني

# إعداد السجلات لمراقبة أداء البوت في Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# جلب توكن التليجرام من الـ Secrets في Railway
# تأكد من تسمية المتغير BOT_TOKEN في إعدادات Variables في Railway
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    logger.error("خطأ: لم يتم العثور على BOT_TOKEN في المتغيرات السرية!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# --- محرك الذكاء الاصطناعي المجاني المصحح ---

def get_ai_response(user_message):
    """
    إرسال نص المستخدم إلى نماذج ذكاء اصطناعي مجانية.
    تم تعديل طريقة استدعاء الموديل لتجنب أخطاء الإصدارات (AttributeError).
    """
    try:
        # استخدام string للموديل بدلاً من الكائن المباشر لتجنب أخطاء السجلات
        response = g4f.ChatCompletion.create(
            model="gpt-3.5-turbo", 
            messages=[
                {"role": "system", "content": "أنت مساعد ذكي ومفيد يدعى VANTOR. أجب على كافة الأسئلة باللغة العربية الفصحى وبأسلوب ذكي ومنطقي."},
                {"role": "user", "content": user_message}
            ],
        )
        
        if response and len(response) > 0:
            return response
        else:
            return "عذراً، لم أستطع معالجة الرد حالياً. هل يمكنك المحاولة مرة أخرى؟"
            
    except Exception as e:
        logger.error(f"خطأ في محرك الذكاء الاصطناعي: {e}")
        # محاولة أخيرة باستخدام موديل افتراضي آخر في حال فشل الأول
        try:
            response = g4f.ChatCompletion.create(
                model=g4f.models.default,
                messages=[{"role": "user", "content": user_message}],
            )
            return response
        except:
            return "أواجه ضغطاً في التفكير حالياً، سأكون معك خلال لحظات."

# --- معالجة الرسائل ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """ترحيب ذكي عند بداية التشغيل"""
    welcome_text = (
        "مرحباً بك! أنا VANTOR.\n"
        "أنا الآن مدعوم بنظام ذكاء اصطناعي متكامل. اسألني أي سؤال وسأجيبك فوراً."
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """استقبال الرسائل وتحويلها للمحرك الذكي"""
    chat_id = message.chat.id
    user_text = message.text

    # إظهار حالة "يكتب الآن" في تليجرام
    bot.send_chat_action(chat_id, 'typing')
    
    logger.info(f"رسالة من {chat_id}: {user_text}")

    # جلب الرد الذكي
    final_reply = get_ai_response(user_text)

    try:
        # إرسال الإجابة النهائية للمستخدم
        bot.send_message(chat_id, final_reply)
        logger.info(f"تم الرد على {chat_id} بنجاح.")
    except Exception as e:
        logger.error(f"فشل إرسال الرسالة: {e}")

# --- آلية التشغيل المستمر ---

def start_polling():
    """تشغيل البوت بوضعية الاستقرار لضمان عدم التوقف"""
    while True:
        try:
            logger.info("جاري تشغيل البوت الذكي (VANTOR)...")
            bot.remove_webhook()
            bot.polling(none_stop=True, interval=1, timeout=60)
        except Exception as e:
            logger.error(f"خطأ في الاتصال: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # تشغيل الكود بالكامل
    start_polling()
