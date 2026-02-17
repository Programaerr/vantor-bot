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
    """وظيفة جلب رد الذكاء الاصطناعي باللهجة العراقية مع قيود صارمة"""
    try:
        # تعليمات صارمة جداً لعدم الخروج عن سياق الشركة
        system_instruction = (
            "أنت مساعد ذكي ومحترم لبوت شركة VANTOR للتجارة والشحن في العراق. "
            "تحدث بلهجة عراقية بغدادية مهذبة جداً. "
            "مهمتك هي الإجابة على استفسارات الزبائن العامة بحدود عمل الشركة فقط. "
            "إذا أرسل المستخدم رقماً، لا تحلله كألوان أو معلومات عامة من الإنترنت. "
            "إذا سألك عن شيء خارج نطاق التجارة والشحن، أجب بلباقة أنك متخصص بمساعدة زبائن VANTOR فقط. "
            "استخدم كلمات: عيوني، تدلل، أبشر، عيني، أغاتي."
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
        return "يا هلا بيك عيوني، بشنو أكدر أخدمك بخصوص شغلك وية VANTOR؟"
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return "أهلاً بيك غالي، أنا معك، شلون أكدر أساعدك بخصوص طلباتك؟"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.chat.id
    user_states[user_id] = None 
    welcome_text = (
        f"يا هلا ومية هلا بيك أستاذ {message.from_user.first_name} بنظام VANTOR.\n\n"
        "أنا مساعدك الذكي، تكدر تستفسر عن طلبك بس أرسل كلمة 'تتبع' أو 'وين وصلي'، "
        "أو إذا عندك أي سؤال بخصوص خدماتنا أنا حاضر عيوني."
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

    # 1. التحقق إذا كانت الرسالة عبارة عن رقم فقط أو تبدأ بـ # (نعتبرها طلب فوراً)
    order_id_match = re.fullmatch(r'#?\d+', text)
    if order_id_match or user_states.get(user_id) == 'waiting_for_order':
        order_id = re.search(r'\d+', text).group()
        user_states[user_id] = None 
        process_order_tracking(message, order_id)
        return

    # 2. الكشف عن نية تتبع الطلب (بالعراقي)
    tracking_keywords = [
        'تتبع', 'وين', 'وصل', 'طلبي', 'اين', 'الطلب', 
        'وين صار', 'حالة', 'شصار', 'شوكت', 'وين وصلت'
    ]
    if any(word in text.lower() for word in tracking_keywords):
        user_states[user_id] = 'waiting_for_order'
        bot.send_message(user_id, "من رخصتك عيوني، زودني برقم الطلب مالتك حتى أشوفلك حالته بقاعدة البيانات:")
        return

    # 3. الرد العام باستخدام الذكاء الاصطناعي (باللهجة العراقية)
    ai_reply = get_ai_response(text)
    bot.send_message(user_id, ai_reply)

def process_order_tracking(message, order_id):
    """البحث في قاعدة بيانات Supabase مع منع الذكاء الاصطناعي من التدخل في النتائج"""
    user_id = message.chat.id
    bot.send_message(user_id, f"صار عيوني، جاري البحث عن الطلب رقم (#{order_id}) بسجلات VANTOR...")
    
    found = False
    potential_columns = ['id', 'order_number', 'order_id']
    
    for col in potential_columns:
        try:
            query = supabase.table('orders').select("*").eq(col, order_id).execute()
            if query.data and len(query.data) > 0:
                order_data = query.data[0]
                status = order_data.get('status', 'قيد المعالجة')
                
                status_translations = {
                    'pending': 'بعده قيد الانتظار، إن شاء الله قريباً يتحرك.',
                    'processing': 'جاري تجهيز طلبك هسة بالمخازن.',
                    'shipped': 'أبشر، طلبك حالياً بالطريق إلك.',
                    'delivered': 'تم التسليم بنجاح، بالعافية عليك عيوني.',
                    'cancelled': 'للأسف الطلب ملغي، تواصل وية الإدارة حتى تعرف السبب.'
                }
                
                status_msg = status_translations.get(status.lower(), f"حالته الحالية هي: {status}")
                bot.send_message(user_id, f"أستاذي العزيز، لكيتلك الطلب رقم (#{order_id})، و {status_msg}")
                found = True
                break
        except Exception as e:
            continue
            
    if not found:
        # هنا المهم: لا نرسل الرقم للذكاء الاصطناعي إذا فشل البحث في الداتابيز
        bot.send_message(user_id, f"والله يا عيوني بحثت بكل السجلات وما لكيت طلب بهذا الرقم (#{order_id}). تأكد من الرقم يرحم والديك، أو خابر الدعم الفني.")

if __name__ == '__main__':
    logger.info("البوت يعمل الآن بالهوية العراقية الصارمة لشركة VANTOR...")
    
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
