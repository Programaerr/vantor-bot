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

# بيانات الاعتماد (تأكد من ضبطها في متغيرات البيئة)
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

# قاموس لتخزين حالة المستخدم
user_states = {}

def get_ai_response(prompt):
    """وظيفة جلب رد الذكاء الاصطناعي باللهجة العراقية وتجنب تحليل الألوان"""
    try:
        # تعليمات صارمة للبوت ليتحدث عراقي ويبتعد عن الألوان
        system_instruction = (
            "أنت مساعد ذكي لبوت شركة VANTOR للتجارة والشحن. "
            "تحدث بلهجة عراقية بغدادية محترمة ولطيفة جداً. "
            "ممنوع تحلل أرقام الهكس (Hex Codes) كألوان إلا إذا سألك المستخدم صراحة عن لون. "
            "إذا أرسل المستخدم رقماً، اعتبره رقم طلب أو استفسار عام. "
            "استخدم كلمات مثل: 'تدلل'، 'عيوني'، 'أبشر'، 'من رخصتك'، 'غالي والطلب رخيص'."
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
        return "يا هلا بيك عيوني، أنا معك، كلي بشنو أكدر أخدمك اليوم؟"
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return "أهلاً بك أستاذي العزيز، أنا موجود، شلون أكدر أساعدك بخصوص طلبك؟"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.chat.id
    user_states[user_id] = None 
    welcome_text = (
        f"يا هلا ومية هلا بيك أستاذ {message.from_user.first_name} بنظام VANTOR.\n\n"
        "أنا مساعدك الذكي، تكدر تستفسر عن طلبك بس أرسل كلمة 'تتبع' أو 'وين وصلي'، "
        "أو إذا عندك أي سؤال ثاني أنا حاضر وأجاوبك عيوني."
    )
    bot.send_message(user_id, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.chat.id
    text = message.text.strip()

    # كلمات التحية العراقية
    greetings = [
        'سلام', 'هلا', 'مرحبا', 'شلونك', 'شلونج', 'هلو', 'الو', 
        'كوة', 'صباح الخير', 'مساء الخير', 'يا هلا', 'شخباركم'
    ]

    # 1. إذا كان البوت ينتظر رقم طلب أو المستخدم أرسل رقم يبدأ بـ #
    if user_states.get(user_id) == 'waiting_for_order' or text.startswith('#'):
        # استخراج الرقم فقط
        order_id_match = re.search(r'\d+', text)
        if order_id_match:
            order_id = order_id_match.group()
            user_states[user_id] = None 
            process_order_tracking(message, order_id)
            return

    # 2. الكشف عن نية تتبع الطلب (بالعراقي)
    tracking_keywords = [
        'تتبع', 'وين', 'وصل', 'طلبي', 'اين', 'الطلب', 
        'وين صار', 'حالة', 'شصار', 'شوكت'
    ]
    if any(word in text.lower() for word in tracking_keywords):
        user_states[user_id] = 'waiting_for_order'
        bot.send_message(user_id, "من رخصتك عيوني، زودني برقم الطلب مالتك (مثلاً #123) حتى أشوفلك وين صار:")
        return

    # 3. الرد العام باستخدام الذكاء الاصطناعي (باللهجة العراقية)
    ai_reply = get_ai_response(text)
    bot.send_message(user_id, ai_reply)

def process_order_tracking(message, order_id):
    """البحث في قاعدة بيانات Supabase ورد النتيجة بالعراقي"""
    user_id = message.chat.id
    bot.send_message(user_id, f"تدلل عيوني، جاري البحث عن الطلب رقم (#{order_id})...")
    
    found = False
    # تجربة الأعمدة المحتملة لرقم الطلب
    potential_columns = ['id', 'order_number', 'order_id']
    
    for col in potential_columns:
        try:
            query = supabase.table('orders').select("*").eq(col, order_id).execute()
            if query.data and len(query.data) > 0:
                order_data = query.data[0]
                # جلب الحالة وترجمتها للعراقي
                status = order_data.get('status', 'قيد المعالجة')
                
                status_translations = {
                    'pending': 'بعده قيد الانتظار، إن شاء الله قريباً يتحرك.',
                    'processing': 'جاري تجهيز طلبك هسة بالمخازن.',
                    'shipped': 'أبشر، طلبك حالياً بالطريق إلك.',
                    'delivered': 'تم التسليم بنجاح، بالعافية عليك عيوني.',
                    'cancelled': 'للأسف الطلب ملغي، تواصل مع الدعم للمزيد من التفاصيل.'
                }
                
                status_msg = status_translations.get(status.lower(), f"حالته الحالية هي: {status}")
                
                bot.send_message(user_id, f"أستاذي العزيز، لكيتلك الطلب رقم (#{order_id})، و {status_msg}")
                found = True
                break
        except Exception as e:
            logger.error(f"Database error on column {col}: {e}")
            continue
            
    if not found:
        bot.send_message(user_id, f"والله يا عيوني بحثت بس ما لكيت طلب بهذا الرقم (#{order_id})، تأكد من الرقم يرحم والديك.")

if __name__ == '__main__':
    logger.info("البوت يعمل الآن بالهوية العراقية لشركة VANTOR...")
    
    try:
        bot.remove_webhook()
    except:
        pass
        
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=90)
        except Exception as e:
            logger.error(f"Polling Error: {e}")
            time.sleep(10)
