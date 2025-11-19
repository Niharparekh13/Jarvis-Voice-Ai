import requests
from config import AI_LOG_FILE
from ui.log_viewer import show_log_ui

def ask_ai(question):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3", "prompt": question, "stream": False},
            timeout=10
        )
        return response.json().get("response", "I'm not sure how to answer that.")
    except:
        return "I'm having trouble connecting to the AI service."

def log_ai_training(question, response):
    with open(AI_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"Q: {question}\nA: {response}\n\n")

def show_training_log():
    show_log_ui()
