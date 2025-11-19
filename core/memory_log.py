import json
from datetime import datetime
from fuzzywuzzy import fuzz

MEMORY_LOG_FILE = "memory_log.json"

def save_to_memory_log(text):
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "text": text.lower()
    }

    try:
        with open(MEMORY_LOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        data = []

    data.append(entry)

    with open(MEMORY_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def search_memory(query, threshold=50):  # Lowered threshold for better matches
    try:
        with open(MEMORY_LOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        return None

    best_match = None
    best_score = 0

    for entry in reversed(data):  # Check recent entries first
        line = entry["text"]
        score = fuzz.partial_ratio(query.lower(), line.lower())

        # Debug print to see match scores
        print(f"[DEBUG] Comparing: '{query.lower()}' ⟷ '{line.lower()}' | Score: {score}")

        if score > best_score:
            best_score = score
            best_match = line

    if best_score >= threshold:
        return best_match
    return None
