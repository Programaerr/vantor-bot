# core.py
import json
import re
import g4f
import os
from config import SYSTEM_PROMPT, STATUS_MAP, DATASET_PATH

def find_best_match_in_json(user_text):
    """يبحث في ملف الـ JSONL عن رد مطابق لرسالة المستخدم"""
    user_text = user_text.strip().lower()
    try:
        if not os.path.exists(DATASET_PATH):
            return None
            
        with open(DATASET_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                # messages[0] هو المستخدم، messages[1] هو البوت
                dataset_user_msg = data['messages'][0]['content'].lower()
                if dataset_user_msg == user_text:
                    return data['messages'][1]['content']
    except Exception as e:
        print(f"Error reading JSONL: {e}")
    return None

def handle_vantor_logic(text, user_id):
    # 1. أولاً: نبحث في ملف الـ JSONL اللي رفعته (الأولوية القصوى)
    match = find_best_match_in_json(text)
    if match:
        return match

    # 2. ثانياً: إذا كان رقم طلب، نبحث في الداتابيز (تتبع)
    order_id_match = re.search(r'\d+', text)
    if order_id_match and len(text) < 15:
        # هنا تضع كود السوبابيس المعتاد لتتبع الطلب
        return f"جاري تتبع الطلب رقم {order_id_match.group()}..."

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
