import tkinter as tk
from tkinter import scrolledtext
from config import AI_LOG_FILE
from core.speech import speak

def show_log_ui():
    try:
        with open(AI_LOG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        speak("There is no training data yet.")
        return

    window = tk.Tk()
    window.title("AI Training Log")
    window.geometry("600x500")

    txt = scrolledtext.ScrolledText(window, wrap=tk.WORD)
    txt.insert(tk.END, content)
    txt.pack(expand=True, fill='both', padx=10, pady=10)

    window.mainloop()