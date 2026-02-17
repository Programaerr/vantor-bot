import os
import telebot
import time
from dotenv import load_dotenv
import g4f

# تحميل المفاتيح
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TOKEN, threaded=False)

def get_ai_reply(user_text):
    try:
        # استدعاء الذكاء الاصطناعي مجاناً
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4o_mini, # أو llama_3
            messages=[
                {"role": "system", "content": "أنت عبود، مساعد ذكي عراقي. تتحدث بلهجة عراقية محترمة. أنت آمن جداً ومثقف."},
                {"role": "user", "content": user_text}
            ],
        )
        return response
    except Exception as e:
        print(f"AI Error: {e}")
        return "والله يا خوي صار عندي ثقل بالشبكة، جرب مرة ثانية."

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "هلا بيك! أنا عبود بنسختي الجديدة. تفضل اسألني أي شيء.")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    chat_id = message.chat.id
    try:
        bot.send_chat_action(chat_id, 'typing')
        reply = get_ai_reply(message.text)
        bot.send_message(chat_id, reply)
    except Exception as e:
        bot.send_message(chat_id, "اعتذر منك، صار خلل بسيط.")

if __name__ == "__main__":
    print("🚀 Abood is Running...")
    bot.infinity_polling()
