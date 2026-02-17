import os
import telebot
import time
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# تحميل المفاتيح
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN") # مفتاح Hugging Face المجاني

# إعداد البوت وموكل الذكاء الاصطناعي
bot = telebot.TeleBot(TOKEN, threaded=False)
# سنستخدم موديل Llama-3-8B لأنه الأذكى حالياً ويفهم اللهجة العراقية
client = InferenceClient("meta-llama/Meta-Llama-3-8B-Instruct", token=HF_TOKEN)

def get_ai_reply(user_text):
    try:
        prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\nأنت عبود، مساعد ذكي ومثقف من العراق. تتحدث باللهجة العراقية الودودة. أنت آمن جداً وتكره العنف والإرهاب.<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{user_text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
        
        response = ""
        for message in client.chat_completion(
            messages=[
                {"role": "system", "content": "أنت عبود، مساعد ذكي عراقي. تتحدث بلهجة عراقية محترمة. أنت آمن جداً ومثقف."},
                {"role": "user", "content": user_text}
            ],
            max_tokens=500,
            stream=False
        ):
            response += message.choices[0].delta.content or ""
        
        # إذا كانت الاستجابة فارغة (أحياناً في الـ stream)
        if not response:
            # محاولة أخرى بصيغة بسيطة
            output = client.text_generation(prompt, max_new_tokens=200)
            return output
            
        return response
    except Exception as e:
        print(f"AI Error: {e}")
        # إذا فشل الموديل الأول، نجرب موديل Mistral كبديل سريع
        try:
            alt_client = InferenceClient("mistralai/Mistral-7B-Instruct-v0.2", token=HF_TOKEN)
            return alt_client.text_generation(f"User: {user_text}\nAbood (Iraqi AI):", max_new_tokens=150)
        except:
            return "والله يا خوي الضغط عالي ع السيرفر، ثواني وأرجعلك."

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "هلا بيك! أنا عبود، بنسختي المطورة والمستقرة. شلون أقدر أساعدك؟")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    chat_id = message.chat.id
    try:
        bot.send_chat_action(chat_id, 'typing')
        reply = get_ai_reply(message.text)
        bot.send_message(chat_id, reply)
    except Exception as e:
        bot.send_message(chat_id, "اعتذر منك، صار عندي عطل فني بسيط.")

if __name__ == "__main__":
    print("🚀 Abood is Running with Llama 3 Power...")
    bot.infinity_polling(timeout=90)
