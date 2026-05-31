def normalize_text(text):
    text = text.lower()
    
    # توحيد الأحرف
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ة", "ه").replace("ى", "ي")
    
    # إزالة التشكيل
    import re
    text = re.sub(r'[ًٌٍَُِّْ]', '', text)
    
    # إزالة التكرار
    import re
    text = re.sub(r'(.)\1+', r'\1', text)
    
    return text.strip()

def is_correct_answer(user_answer, correct_answer):
    return normalize_text(user_answer) == normalize_text(correct_answer)