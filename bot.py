import telebot
import os
import time
import logging
import g4f

# إعداد السجلات بشكل بسيط لتقليل استهلاك الموارد
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# جلب توكن البوت من المتغيرات البيئية
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# --- محرك الذكاء الاصطناعي (رسمي، لبق، ومختصر) ---

def get_ai_response(user_message):
    """
    توليد رد رسمي جداً ومختصر مع التعامل بذكاء مع التحايا والجمل المبتورة.
    """
    msg = user_message.strip()
    
    # 1. ردود فورية للتحايا (بدون ذكاء اصطناعي لزيادة السرعة)
    if msg in ["سلام عليكم", "السلام عليكم", "سلام", "هلو", "مرحبا"]:
        return "عليكم السلام أستاذ، تفضل حضرتك شلون أقدر أساعدك؟"
    
    # 2. التعامل الذكي مع الجمل غير المكتملة (مثل: أريد أسألك عن)
    incomplete_triggers = ["اريد اسئلك عن", "اريد اسألك", "عندي سؤال", "ممكن سؤال", "ممكن اسئلك"]
    if any(trigger in msg for trigger in incomplete_triggers) and len(msg) < 25:
        return "العفو أستاذ، بشنو تريد أساعدك بالضبط؟"

    try:
        # تعليمات صارمة للموديل للحفاظ على الهوية الرسمية والاختصار
        system_instruction = (
            "أنت مساعد رسمي ولبق جداً. ردك يجب أن يكون مختصراً ومفيداً. "
            "خاطب المستخدم دائماً بكلمة 'أستاذ'. "
            "إذا كانت جملة المستخدم غير مكتملة، اطلب منه التوضيح بأسلوب: 'العفو أستاذ، بشنو تريد أساعدك بالضبط؟'. "
            "ممنوع استخدام عبارات الدلع أو الحشو الزائد."
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
        return "تفضل أستاذ، بشنو أقدر أساعدك؟"
            
    except Exception:
        return "تفضل أستاذ، بشنو أقدر أخدمك؟"

# --- معالجة الرسائل ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """ترحيب رسمي مباشر"""
    bot.reply_to(message, "أهلاً بك أستاذ، تفضل حضرتك شلون أقدر أساعدك؟")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """استلام ومعالجة الرسائل بسرعة لتقليل الضغط على Railway"""
    chat_id = message.chat.id
    
    # جلب الرد
    final_reply = get_ai_response(message.text)

    try:
        bot.send_message(chat_id, final_reply)
    except Exception:
        pass

# --- آلية التشغيل المستقرة والسريعة ---

def start_bot():
    """تشغيل البوت مع تقليل الطلبات لتوفير موارد المستضيف"""
    while True:
        try:
            bot.remove_webhook()
            # polling مع فاصل زمني بسيط لتوفير الـ CPU
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    # تشغيل الملف كاملاً مع التعديلات المطلوبة
    start_bot()
