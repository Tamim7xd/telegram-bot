import json

FILES = {
    "mcq": "data/mcq.json",
    "puzzles": "data/puzzles.json",
    "proverbs": "data/proverbs.json",
    "general": "data/general_qa.json",
    "speed": "data/speed_words.json",
    "luck": "data/luck_boxes.json"
}


def load(cat):

    try:
        return json.load(open(FILES[cat], "r", encoding="utf-8"))
    except:
        return []
