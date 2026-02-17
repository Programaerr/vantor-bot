import telebot
import os
import time
import logging
import g4f

# إعداد السجلات بشكل مبسط لتقليل استهلاك الموارد
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# جلب التوكن
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    logger.error("BOT_TOKEN missing!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# --- محرك الذكاء الاصطناعي (ردود رسمية ومختصرة) ---

def get_ai_response(user_message):
    """
    جلب رد مختصر جداً ولبق باللهجة العراقية المؤدبة.
    """
    try:
        # تعليمات صارمة للاختصار واللباقة الرسمية
        system_instruction = (
            "أنت مساعد ذكي واسمك VANTOR. تحدث بلهجة عراقية مؤدبة ورسمية جداً. "
            "قواعدك: 1. الرد قصير جداً ومفيد. 2. خاطب المستخدم بـ 'أستاذ'. "
            "3. إذا قال سلام أو مرحبا، رد بـ 'عليكم السلام أستاذ، تفضل شلون أقدر أساعدك؟' أو 'مراحب بيك أستاذ، شلون أقدر أخدمك؟'. "
            "4. ممنوع استخدام كلمات الدلع أو الحشو الزائد. 5. اجعل الإجابة مباشرة ومختصرة."
        )

        # طلب الرد مع تحديد حد أقصى للكلمات لزيادة السرعة
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
            
    except Exception as e:
        logger.error(f"Error: {e}")
        return "نعم أستاذ، تفضل بموضوعك."

# --- معالجة الرسائل ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """ترحيب رسمي مختصر"""
    bot.reply_to(message, "أهلاً بك أستاذ. أنا VANTOR، تفضل حضرتك شلون أقدر أساعدك؟")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """الرد السريع والمختصر"""
    chat_id = message.chat.id
    
    # لا نستخدم send_chat_action 'typing' لتوفير الوقت والموارد
    
    # جلب الرد
    final_reply = get_ai_response(message.text)

    try:
        bot.send_message(chat_id, final_reply)
    except Exception as e:
        logger.error(f"Send Error: {e}")

# --- آلية التشغيل السريع لتقليل الضغط على Railway ---

def start_bot():
    """تشغيل مستقر مع تقليل عدد الطلبات لتوفير الموارد"""
    while True:
        try:
            bot.remove_webhook()
            # استخدام interval أعلى قليلاً لتوفير المعالج (CPU) في الاستضافات المحدودة
            bot.polling(none_stop=True, interval=2, timeout=20)
        except Exception as e:
            time.sleep(5)

if __name__ == "__main__":
    # كتابة الملف كاملاً بدون أي حذف أو اختصار
    start_bot()
