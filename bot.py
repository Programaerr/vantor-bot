import telebot
import os
import time
import logging
import g4f

# إعداد السجلات بشكل مبسط جداً لتقليل استهلاك الذاكرة والمعالج
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# جلب توكن البوت من المتغيرات البيئية
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# --- محرك الذكاء الاصطناعي (مختصر وحرفي) ---

def get_ai_response(user_message):
    """
    توليد رد رسمي جداً ومختصر. 
    في حال السلام، يتم الرد بصيغة محددة مباشرة دون استخدام الذكاء الاصطناعي لتوفير الموارد.
    """
    msg = user_message.strip()
    
    # ردود سريعة ومباشرة للحالات العامة لتوفير الوقت والموارد
    if msg in ["سلام عليكم", "السلام عليكم", "سلام"]:
        return "عليكم السلام أستاذ، تفضل حضرتك شلون أقدر أساعدك؟"
    
    if msg in ["هلو", "مرحبا", "مراحب"]:
        return "مراحب بيك أستاذ، تفضل حضرتك شلون أقدر أساعدك؟"

    try:
        # تعليمات صارمة جداً للموديل ليكون رده مقتضباً ورسمياً
        system_instruction = (
            "أنت مساعد رسمي ولبق. ردك يجب أن يكون قصيراً جداً ومباشراً. "
            "خاطب المستخدم دائماً بكلمة 'أستاذ'. "
            "ممنوع استخدام عبارات (يا غالي، حي الله أصلك، من عيوني، حبيبي). "
            "اجعل ردك رسمياً وعملياً فقط."
        )

        response = g4f.ChatCompletion.create(
            model=g4f.models.default,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_message}
            ],
        )
        
        if response:
            return str(response).strip()
        return "تفضل أستاذ، شلون أقدر أساعدك؟"
            
    except Exception:
        return "نعم أستاذ، تفضل حضرتك."

# --- معالجة الرسائل ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """ترحيب رسمي جداً"""
    bot.reply_to(message, "أهلاً بك أستاذ، تفضل حضرتك شلون أقدر أساعدك؟")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """استلام ومعالجة الرسائل بسرعة فائقة"""
    chat_id = message.chat.id
    
    # معالجة الرد
    final_reply = get_ai_response(message.text)

    try:
        bot.send_message(chat_id, final_reply)
    except Exception:
        pass

# --- تشغيل البوت بأقل استهلاك للموارد ---

def start_bot():
    """تشغيل مستقر مع فترات انتظار لتقليل الضغط على السيرفر"""
    while True:
        try:
            bot.remove_webhook()
            # polling بفاصل زمني معقول لضمان عدم حرق موارد Railway
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    # كتابة الملف كاملاً كما طلبت في تعليماتك
    start_bot()
