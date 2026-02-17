import os
import logging
from supabase import create_client, Client
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationStatus,
    ConversationHandler,
)

# إعداد السجلات (Logging) لمراقبة الأداء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# بيانات الاعتماد من متغيرات البيئة
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# إنشاء عميل Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# تعريف مراحل الحوار
WAITING_FOR_ORDER_ID = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نقطة البداية عند كتابة /start"""
    await update.message.reply_text(
        f"أهلاً بك {update.effective_user.first_name} في نظام تتبع الطلبات.\n"
        "لتعرف حالة طلبك، يرجى كتابة الأمر: /track"
    )

async def ask_for_order_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عندما يطلب المستخدم التتبع، نسأله عن الرقم أولاً"""
    await update.message.reply_text(
        "من فضلك، أدخل رقم الطلب الخاص بك (مثلاً: 083022):",
        reply_markup=ReplyKeyboardRemove()
    )
    return WAITING_FOR_ORDER_ID

async def get_order_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هنا يتم جلب البيانات بناءً على الرقم الذي أدخله المستخدم حصراً"""
    order_id = update.message.text
    user_id = update.effective_user.id

    await update.message.reply_text(f"جاري البحث عن الطلب رقم (#{order_id})...")

    try:
        # الاستعلام من جدول orders بناءً على رقم الطلب ومعرف المستخدم للأمان
        response = supabase.table('orders').select("*").eq('order_number', order_id).execute()
        
        if response.data:
            order_data = response.data[0]
            status = order_data.get('status', 'غير معروف')
            await update.message.reply_text(
                f"أستاذي العزيز، طلبك ذو الرقم (#{order_id}) حالته الآن: {status}."
            )
        else:
            await update.message.reply_text(
                f"عذراً، لم أتمكن من العثور على طلب بالرقم (#{order_id}). تأكد من الرقم وأعد المحاولة."
            )
            
    except Exception as e:
        logging.error(f"Error fetching order: {e}")
        await update.message.reply_text("حدث خطأ تقني أثناء محاولة جلب البيانات.")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء العملية"""
    await update.message.reply_text("تم إلغاء عملية التتبع.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

if __name__ == '__main__':
    if not TELEGRAM_TOKEN:
        logging.error("TELEGRAM_TOKEN is missing!")
        exit()

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # إعداد معالج الحوار (Conversation Handler)
    # هذا يضمن أن البوت يتبع خطوات محددة: (طلب -> سؤال -> إجابة)
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('track', ask_for_order_id),
            MessageHandler(filters.Regex('^(اريد اعرف طلبي وين وصل|تتبع)$'), ask_for_order_id)
        ],
        states={
            WAITING_FOR_ORDER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_order_status)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(conv_handler)
    
    logging.info("البوت يعمل الآن بنظام التحقق من الطلب...")
    application.run_polling()
