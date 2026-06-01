import re

def normalize_arabic(text):
    text = text.lower()
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ة", "ه").replace("ى", "ي")
    text = re.sub(r'[ًٌٍَُِّْ]', '', text)
    text = re.sub(r'(.)\1+', r'\1', text)
    return text.strip()

def is_correct(user_answer, correct_answer):
    return normalize_arabic(user_answer) == normalize_arabic(correct_answer)

def extract_command(text):
    text = text.strip()
    if text.startswith("/"):
        parts = text.split()
        cmd = parts[0][1:]
        args = parts[1:] if len(parts) > 1 else []
        return cmd, args
    return None, None