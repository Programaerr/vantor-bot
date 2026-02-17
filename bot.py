import os
import re
import logging
import telebot
from supabase import create_client, Client
import g4f
import requests
import time

# إعداد السجلات لمراقبة الأداء
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# بيانات الاعتماد
TOKEN = os.environ.get("TELEGRAM_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# إنشاء عميل البوت وعميل Supabase
bot = telebot.TeleBot(TOKEN, threaded=False)

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("تم الاتصال بـ Supabase بنجاح.")
except Exception as e:
    logger.error(f"خطأ في الاتصال بـ Supabase: {e}")

# قاموس لتخزين حالة المستخدم وآخر رقم طلب بحث عنه
user_data = {}

def get_ai_response(prompt, user_id):
    """وظيفة جلب رد الذكاء الاصطناعي بلهجة بغدادية ثابتة وصارمة"""
    try:
        # تعليمات مشددة جداً لضبط اللهجة والسياق
        system_instruction = (
            "أنت مساعد ذكي واسمك (بوت فانتور - VANTOR). "
            "تتحدث اللهجة العراقية البغدادية المحترمة فقط. "
            "ممنوع استخدام كلمات مثل (تبي، تذكرين، تذكري، أبشرك). "
            "استخدم بدلاً عنها (تريد، تدلل، عيوني، أغاتي، عيني). "
            "وظيفتك مساعدة زبائن شركة VANTOR للتجارة والشحن فقط. "
            "إذا المستخدم أصر على رقم طلب غير موجود، قل له بلباقة أن يتواصل مع الدعم الفني البشري."
        )
        
        response = g4f.ChatCompletion.create(
            model=g4f.models.default,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
        )
        if response and len(str(response)) > 0:
            return response
        return "يا هلا بيك عيني، بشنو أكدر أخدمك بخصوص شغلنا بـ VANTOR؟"
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return "أهلاً بيك غالي، أنا معك، شلون أكدر أساعدك؟"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.chat.id
    user_data[user_id] = {'state': None, 'last_order_id': None}
    welcome_text = (
        f"يا هلا ومية هلا بيك أستاذ {message.from_user.first_name} بنظام VANTOR.\n\n"
        "أنا مساعدك الذكي، تكدر تتبع طلبك (بس أرسل رقم الطلب) "
        "أو اسألني أي سؤال بخصوص خدماتنا وأنا حاضر عيوني."
    )
    bot.send_message(user_id, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.chat.id
    text = message.text.strip()
    
    # تهيئة بيانات المستخدم إذا لم تكن موجودة
    if user_id not in user_data:
        user_data[user_id] = {'state': None, 'last_order_id': None}

    # 1. فحص إذا كان الكلام يحتوي على رقم (تتبع تلقائي)
    order_id_match = re.search(r'\d+', text)
    
    # إذا المستخدم أكد على الرقم أو سأل "شصار" وكان عندنا رقم سابق
    re_check_keywords = ['متأكد', 'صح', 'مرة ثانية', 'عيد البحث', 'شصار', 'وين صار']
    if any(word in text for word in re_check_keywords) and user_data[user_id]['last_order_id']:
        process_order_tracking(message, user_data[user_id]['last_order_id'])
        return

    # إذا أرسل رقم مباشرة
    if order_id_match and (len(order_id_match.group()) >= 4 or text.startswith('#')):
        order_id = order_id_match.group()
        user_data[user_id]['last_order_id'] = order_id
        process_order_tracking(message, order_id)
        return

    # 2. الكشف عن نية التتبع بالكلام
    tracking_keywords = ['تتبع', 'وين وصل', 'طلبي', 'حالة الطلب', 'شحنتي']
    if any(word in text.lower() for word in tracking_keywords):
        user_data[user_id]['state'] = 'waiting_for_order'
        bot.send_message(user_id, "من رخصتك عيوني، زودني برقم الطلب مالتك حتى أشوفه لك بالسيستم:")
        return

    # 3. الرد العام (ذكاء اصطناعي بغدادي)
    ai_reply = get_ai_response(text, user_id)
    bot.send_message(user_id, ai_reply)

def process_order_tracking(message, order_id):
    """البحث في قاعدة البيانات مع ردود بغدادية ثابتة"""
    user_id = message.chat.id
    bot.send_message(user_id, f"تدلل أغاتي، جاري التشييك على الطلب رقم (#{order_id}) مرة ثانية...")
    
    found = False
    potential_columns = ['id', 'order_number', 'order_id']
    
    for col in potential_columns:
        try:
            query = supabase.table('orders').select("*").eq(col, order_id).execute()
            if query.data and len(query.data) > 0:
                order_data = query.data[0]
                status = order_data.get('status', 'processing')
                
                status_translations = {
                    'pending': 'بعده قيد الانتظار، وإن شاء الله ما نتأخر عليك.',
                    'processing': 'جاري تجهيزه هسة بالمخازن مالتنا.',
                    'shipped': 'أبشر عيني، طلبك حالياً بالطريق وجاي يتم توصيله.',
                    'delivered': 'تم التسليم، تتهنى بيه عيوني.',
                    'cancelled': 'للأسف الطلب ملغي، تواصل وية الإدارة حتى يحلولك الموضوع.'
                }
                
                msg = status_translations.get(status.lower(), f"حالته حالياً هي: {status}")
                bot.send_message(user_id, f"أستاذي العزيز، بخصوص الطلب (#{order_id})، {msg}")
                found = True
                break
        except:
            continue
            
    if not found:
        bot.send_message(user_id, f"والله يا عيني دورت بكل السجلات وما لكيت رقم (#{order_id}). إذا أنت متأكد من الرقم، فـ ياريت تراسل الدعم الفني (البشري) حتى يشييكون يدوي، لأن السيستم ما دا يقرأه هسة.")

if __name__ == '__main__':
    logger.info("VANTOR BOT IS RUNNING (BAGHDAD STYLE)...")
    
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
