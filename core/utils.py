import json
from fuzzywuzzy import fuzz
from config import MEMORY_FILE

def is_similar(phrase, keywords, threshold=70):
    return any(fuzz.partial_ratio(phrase, kw) >= threshold for kw in keywords)

def load_memory():
    try:
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_memory(memory):
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(memory, f, indent=4)