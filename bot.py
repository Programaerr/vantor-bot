import telebot
import os
import time
import logging
import g4f

# إعداد السجلات لمراقبة أداء البوت في Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# جلب توكن التليجرام من الـ Secrets في Railway
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    logger.error("خطأ: لم يتم العثور على BOT_TOKEN في المتغيرات السرية!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# --- محرك الذكاء الاصطناعي بالشخصية العراقية ---

def get_ai_response(user_message):
    """
    جلب رد ذكي باللهجة العراقية الكاملة باستخدام g4f.
    """
    try:
        # صياغة التعليمات لجعل الرد عراقي 100%
        system_instruction = (
            "أنت مساعد ذكي واسمك VANTOR. أريدك أن تتحدث اللهجة العراقية العامية "
            "بشكل كامل وطبيعي جداً. استخدم كلمات مثل (هلو، عيني، اغاتي، شلونه، شكو ماكو، تدلل، "
            "خادم ربك، صار، من عيوني). "
            "أجب على كل الأسئلة بذكاء ومنطق لكن بلسان عراقي فصيح ومحبب."
        )

        response = g4f.ChatCompletion.create(
            model=g4f.models.default,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_message}
            ],
        )
        
        if response and len(str(response)) > 0:
            return response
        else:
            return "والله يا غالي صار عندي فصل بالدماغ، تعيد سؤالك فدوة لعينك؟"
            
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return "آسف عيوني، صار عندي لود بالشبكة. ثواني وارجعلك!"

# --- معالجة الرسائل ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """ترحيب عراقي حار"""
    welcome_text = (
        "هلو عيني! أهلاً وسهلاً بيك. "
        "أنا VANTOR، وبخدمتك بأي وقت. اسألني شكو ببالك وتدلل!"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """استلام الرسائل والرد عليها بالعراقي"""
    chat_id = message.chat.id
    user_text = message.text

    # إظهار حالة "typing" لتعزيز التفاعل
    bot.send_chat_action(chat_id, 'typing')
    
    logger.info(f"رسالة من {chat_id}: {user_text}")

    # جلب الرد الذكي العراقي
    final_reply = get_ai_response(user_text)

    try:
        bot.send_message(chat_id, final_reply)
        logger.info(f"تم الرد باللهجة العراقية على {chat_id}")
    except Exception as e:
        logger.error(f"فشل إرسال الرسالة: {e}")

# --- آلية التشغيل ومنع التعارض المستقر ---

def start_bot():
    """تشغيل البوت مع ضمان استقرار الجلسة"""
    while True:
        try:
            logger.info("جاري تشغيل VANTOR العراقي...")
            bot.remove_webhook()
            # تقليل الفاصل الزمني قليلاً لسرعة الرد
            bot.polling(none_stop=True, interval=1, timeout=60)
        except Exception as e:
            logger.error(f"حدث خطأ: {e}")
            # إذا كان هناك تعارض، ننتظر قليلاً قبل إعادة التشغيل
            time.sleep(10)

if __name__ == "__main__":
    # تشغيل الملف بالكامل بدون اختصار
    start_bot()
