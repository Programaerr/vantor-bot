import telebot
import os
import time
import logging
import g4f

# إعداد السجلات لمراقبة الأداء
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# جلب توكن التليجرام من المتغيرات البيئية
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    logger.error("خطأ: لم يتم العثور على BOT_TOKEN!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# --- محرك الذكاء الاصطناعي بلهجة عراقية واقعية ---

def get_ai_response(user_message):
    """
    جلب رد ذكي بلهجة عراقية طبيعية بعيدة عن التكلف أو الأخطاء اللغوية.
    """
    try:
        # تعليمات دقيقة لضبط اللهجة والسياق
        system_instruction = (
            "أنت مساعد ذكي واسمك VANTOR. أريدك أن تتحدث اللهجة العراقية العامية "
            "بأسلوب طبيعي وواقعي جداً، كأنك شخص عراقي مثقف وابن بلد. "
            "ابتعد عن رص الكلمات بشكل غبي. استخدم عبارات مثل: (هلا بيك، حي الله أصلك، "
            "شلون أقدر أساعدك، من عيوني، تدلل، عيوني لك، شكو ماكو بالأخبار). "
            "إذا سلم المستخدم، رد عليه بترحيب حار ومؤدب، وإذا سأل جاوبه بذكاء وبنفس اللهجة."
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
            return "والله يا غالي النت شوية تعبان عندي، تقدر تعيد سؤالك؟"
            
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return "صار عندي خلل بسيط بالشبكة، ثواني وأرجع أجاوبك من عيوني."

# --- معالجة الرسائل ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """ترحيب عراقي طبيعي"""
    welcome_text = (
        "هلا بيك عيني! نورتني. "
        "أنا VANTOR، أخوك وبخدمتك. شمحتاج أو شكو ببالك سؤال؟ أنا حاضر."
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """استلام الرسائل والرد عليها بذكاء ولهجة حقيقية"""
    chat_id = message.chat.id
    user_text = message.text

    # إظهار حالة الكتابة
    bot.send_chat_action(chat_id, 'typing')
    
    logger.info(f"رسالة من {chat_id}: {user_text}")

    # جلب الرد الذكي
    final_reply = get_ai_response(user_text)

    try:
        bot.send_message(chat_id, final_reply)
        logger.info(f"تم الرد بلهجة عراقية صحيحة على {chat_id}")
    except Exception as e:
        logger.error(f"فشل إرسال الرسالة: {e}")

# --- آلية التشغيل المستقر ---

def start_bot():
    """تشغيل البوت مع ضمان استقرار الجلسة"""
    while True:
        try:
            logger.info("جاري تشغيل VANTOR بلهجة عراقية معدلة...")
            bot.remove_webhook()
            bot.polling(none_stop=True, interval=1, timeout=60)
        except Exception as e:
            logger.error(f"حدث خطأ: {e}")
            time.sleep(10)

if __name__ == "__main__":
    # كتابة الملف كاملاً لضمان عدم حدوث نقص
    start_bot()
