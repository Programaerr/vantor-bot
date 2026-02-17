import os
import telebot
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# تحميل المتغيرات
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

bot = telebot.TeleBot(TOKEN, threaded=False)

# استخدام موديل موثوق
client = InferenceClient("mistralai/Mistral-7B-Instruct-v0.2", token=HF_TOKEN)

def get_ai_reply(user_text):
    try:
        # بناء البرومبت
        system_msg = "أنت عبود، مساعد ذكي من العراق. تجيب باللهجة العراقية الودودة."
        prompt = f"<s>[INST] {system_msg} \n {user_text} [/INST]"
        
        output = client.text_generation(
            prompt,
            max_new_tokens=250,
            temperature=0.7
        )
        return output.strip()
    
    except Exception as e:
        error_str = str(e)
        if "401" in error_str:
            return "يا خوي التوكن (Token) مال هجنج فيس غير صحيح أو مو مفعل. تأكد منه بـ Railway."
        elif "429" in error_str:
            return "يا خوي السيرفر عليه ضغط حالياً، اصبر ثواني وارجع."
        else:
            print(f"Detailed Error: {e}")
            return "صار عندي خلل تقني، جاي أحاول أصلحه."

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "هلا بيك! أنا عبود. شلون أقدر أساعدك اليوم؟")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    chat_id = message.chat.id
    try:
        bot.send_chat_action(chat_id, 'typing')
        reply = get_ai_reply(message.text)
        bot.send_message(chat_id, reply)
    except Exception as e:
        bot.send_message(chat_id, "اعتذر منك، جرب ترسل الرسالة مرة ثانية.")

if __name__ == "__main__":
    print("🚀 Abood is booting up...")
    bot.infinity_polling()
