# core.py
import json
import re
import g4f
import os
from supabase import create_client, Client
from config import SYSTEM_PROMPT, STATUS_MAP, DATASET_PATH

# إعداد Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def find_best_match_in_json(user_text):
    """البحث عن رد مطابق في ملف الـ JSONL"""
    user_text = user_text.strip().lower()
    if not os.path.exists(DATASET_PATH):
        return None
    try:
        with open(DATASET_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                if 'messages' in data and len(data['messages']) >= 2:
                    dataset_user_msg = data['messages'][0]['content'].lower()
                    if dataset_user_msg == user_text:
                        return data['messages'][1]['content']
    except Exception:
        pass
    return None

def handle_vantor_logic(text, user_id):
    # 1. البحث في ملف الـ JSON (الأولوية للبيانات العراقية)
    match = find_best_match_in_json(text)
    if match:
        return match

    # 2. تتبع الطلب (إذا أرسل رقم طلب)
    order_id_match = re.search(r'\d+', text)
    if order_id_match and len(text) < 15:
        return track_order(order_id_match.group())

    # 3. استخدام الذكاء الاصطناعي كخيار أخير
    return get_ai_reply(text)

def track_order(order_id):
    for col in ['id', 'order_number', 'order_id']:
        try:
            query = supabase.table('orders').select("*").eq(col, order_id).execute()
            if query.data:
                status = query.data[0].get('status', 'processing').lower()
                return f"أغاتي، بخصوص طلبك رقم (#{order_id})، {STATUS_MAP.get(status, status)}"
        except: continue
    return f"والله يا عيني بحثت بسجلاتنا وما لكيت رقم طلب (#{order_id})."

def get_ai_reply(prompt):
    try:
        response = g4f.ChatCompletion.create(
            model=g4f.models.default,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
        )
        return response if response else "يا هلا بيك بـ VANTOR، شلون أخدمك؟"
    except:
        return "أهلاً بيك غالي، نورت فانتور للملابس."

    # 3. ثالثاً: إذا ما لكينا رد بالملف، نستخدم الذكاء الاصطناعي كبديل
    return get_ai_reply(text)

def get_ai_reply(prompt):
    try:
        response = g4f.ChatCompletion.create(
            model=g4f.models.default,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
        )
        return response if response else "هلا بيك بـ VANTOR، بشنو أخدمك؟"
    except:
        return "أهلاً بيك غالي، نورت فانتور."
