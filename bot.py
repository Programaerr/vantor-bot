# bot.py
import os
import telebot
from core import handle_vantor_logic

TOKEN = os.environ.get("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(func=lambda message: True)
def main_handler(message):
    # البوت يروح للـ core والـ core يروح للـ JSON
    reply = handle_vantor_logic(message.text, message.chat.id)
    bot.reply_to(message, reply)

if __name__ == '__main__':
    print("VANTOR Bot is running and reading from JSON...")
    bot.infinity_polling()
    if user_id not in user_data:
        user_data[user_id] = {'state': None, 'last_order_id': None}

    # التحقق من وجود رقم في الرسالة (أولوية تتبع الطلب)
    order_id_match = re.search(r'\d+', text)
    
    # كلمات إعادة البحث
    re_check_keywords = ['متأكد', 'صح', 'مرة ثانية', 'عيد البحث', 'شصار بطلبي']
    if any(word in text for word in re_check_keywords) and user_data[user_id]['last_order_id']:
        process_order_tracking(message, user_data[user_id]['last_order_id'])
        return

    # إذا أرسل رقم طلب مباشرة
    if order_id_match and (len(order_id_match.group()) >= 4 or text.startswith('#')):
        order_id = order_id_match.group()
        user_data[user_id]['last_order_id'] = order_id
        process_order_tracking(message, order_id)
        return

    # الكشف عن نية التتبع
    tracking_keywords = ['تتبع', 'وين وصل', 'طلبي', 'حالة الطلب', 'شوكت يوصل']
    if any(word in text.lower() for word in tracking_keywords):
        user_data[user_id]['state'] = 'waiting_for_order'
        bot.send_message(user_id, "من رخصتك عيوني، زودني برقم الطلب مالتك حتى أشوفلك القطع وين صارت:")
        return

    # الرد العام باستخدام الذكاء الاصطناعي (يلتزم بالبرومبت الصارم)
    ai_reply = get_ai_response(text, user_id)
    bot.send_message(user_id, ai_reply)

def process_order_tracking(message, order_id):
    """البحث في سجلات VANTOR والرد باستخدام STATUS_MAP من الإعدادات"""
    user_id = message.chat.id
    bot.send_message(user_id, f"تدلل أغاتي، جاري التشييك على طلب الملابس رقم (#{order_id})...")
    
    found = False
    potential_columns = ['id', 'order_number', 'order_id']
    
    for col in potential_columns:
        try:
            query = supabase.table('orders').select("*").eq(col, order_id).execute()
            if query.data and len(query.data) > 0:
                order_data = query.data[0]
                status = order_data.get('status', 'processing').lower()
                
                # استخدام الترجمة من config.py
                msg = STATUS_MAP.get(status, f"حالة طلبك الحالية هي: {status}")
                bot.send_message(user_id, f"أستاذي العزيز، بخصوص طلبك رقم (#{order_id})، {msg}")
                found = True
                break
        except:
            continue
            
    if not found:
        bot.send_message(user_id, f"والله يا عيني بحثت بسجلاتنا وما لكيت رقم طلب ملابس بهذا الرقم (#{order_id}). تأكد من الرقم يرحم والديك.")

if __name__ == '__main__':
    logger.info("VANTOR CLOTHING BOT IS RUNNING...")
    
    try:
        bot.remove_webhook()
    except:
        pass
        
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=90)
        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(10)
