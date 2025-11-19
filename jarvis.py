import pyttsx3
import datetime
import webbrowser
import os
import requests
import subprocess
import psutil
import tkinter as tk
from tkinter import scrolledtext
from fuzzywuzzy import fuzz, process
import urllib.parse
import json
from pathlib import Path
from vosk import Model, KaldiRecognizer
import sounddevice as sd
import queue
import speech_recognition as sr
import json as js
import threading
import time
import keyboard
import sys
import queue as threading_queue

# ========== INIT ==========
engine = pyttsx3.init()
engine.setProperty('rate', 150)
speech_lock = threading.Lock()

KNOWN_APPS_FILE = "known_apps.json"
AI_LOG_FILE = "ai_training_data.txt"
WAKE_WORDS = ["jarvis", "jerry", "service", "charge this", "doris", "generous"]
ALIAS_MAP = {
    "valo": "valorant",
    "veteran": "valorant",
    "editor": "notepad",
    "note pad": "notepad",
    "not bad": "notepad",
    "not by": "notepad",
    "chrome": "chrome",
    "google": "chrome",
    "vs code": "code",
    "vscode": "code",
    "code editor": "code",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "spotify": "spotify",
    "discord": "discord",
    "paint": "mspaint",
    "explorer": "explorer"
}

vosk_model = Model("model")
samplerate = 16000
q = queue.Queue()
command_queue = threading_queue.Queue()

# ========== AI CHAT FEATURE ==========
def ask_ai(question):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3", "prompt": question, "stream": False},
            timeout=10
        )
        data = response.json()
        return data.get("response", "I'm not sure how to answer that.")
    except:
        return "I'm having trouble connecting to the AI service."

def log_ai_training(question, response):
    with open(AI_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"Q: {question}\nA: {response}\n\n")

def show_training_log():
    if not Path(AI_LOG_FILE).exists():
        speak("There is no training data yet.")
        return

    window = tk.Tk()
    window.title("AI Training Log")
    window.geometry("600x500")

    txt = scrolledtext.ScrolledText(window, wrap=tk.WORD)
    with open(AI_LOG_FILE, "r", encoding="utf-8") as f:
        txt.insert(tk.END, f.read())
    txt.pack(expand=True, fill='both', padx=10, pady=10)

    window.mainloop()

# ========== SPEECH ==========
def speak(text):
    with speech_lock:
        print("Jarvis:", text)
        engine.say(text)
        engine.runAndWait()

def callback(indata, frames, time, status):
    if status:
        print(status)
    q.put(bytes(indata))

def listen():
    rec = KaldiRecognizer(vosk_model, samplerate)
    with sd.RawInputStream(samplerate=samplerate, blocksize=8000, dtype='int16', channels=1, callback=callback):
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = js.loads(rec.Result())
                text = result.get("text", "").strip()
                if text:
                    print("You said (Vosk):", text)
                    return text.lower()

# ========== UTILITY ==========
def is_similar(phrase, keywords, threshold=70):
    return any(fuzz.partial_ratio(phrase, kw) >= threshold for kw in keywords)

def search_common_folders(app_name):
    folders = [
        Path.home() / "Desktop",
        # Path.home() / "Downloads",
        Path.home() / "Documents",
        Path("C:/ProgramData/Microsoft/Windows/Start Menu/Programs")
    ]
    matches = []
    for folder in folders:
        for root, dirs, files in os.walk(folder):
            for file in files:
                if app_name.lower().replace(" ", "") in file.lower().replace(" ", ""):
                    full_path = os.path.join(root, file)
                    matches.append(full_path)
    matches.sort(key=lambda x: ("desktop" not in x.lower(), len(x)))
    return matches

# ========== APP CONTROL ==========
def load_known_apps():
    if Path(KNOWN_APPS_FILE).exists():
        with open(KNOWN_APPS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_known_app(app_name, path):
    apps = load_known_apps()
    apps[app_name.lower()] = path
    with open(KNOWN_APPS_FILE, 'w') as f:
        json.dump(apps, f, indent=4)

def fuzzy_match_app(name):
    known_apps = load_known_apps()
    name = ALIAS_MAP.get(name.strip(), name.strip())
    all_names = list(known_apps.keys()) + list(ALIAS_MAP.values())
    match, score = process.extractOne(name.replace(" ", ""), all_names)
    return match if score >= 70 else name

def open_app(app_name):
    app_name = app_name.lower().strip()
    app_key = fuzzy_match_app(app_name)
    apps = load_known_apps()

    if app_key in apps:
        path = apps[app_key]
        if os.path.exists(path):
            try:
                os.startfile(path)
                speak(f"{app_key} opened from memory.")
                return True
            except Exception:
                speak(f"I remember {app_key}, but couldn't open it. Try teaching me again.")
                return False

    fallback_paths = [
        f"C:\\Program Files\\{app_key}\\{app_key}.exe",
        f"C:\\Program Files (x86)\\{app_key}\\{app_key}.exe",
        f"C:\\Users\\{os.getlogin()}\\AppData\\Local\\{app_key}\\{app_key}.exe",
        f"C:\\Windows\\System32\\{app_key}.exe"
    ]
    for path in fallback_paths:
        if os.path.exists(path):
            os.startfile(path)
            speak(f"{app_key} opened from fallback path.")
            return True

    results = search_common_folders(app_key)
    if results:
        try:
            os.startfile(results[0])
            speak(f"Opened {results[0]} from search.")
            return True
        except Exception:
            speak("I found a file, but couldn't open it. It might not be an executable.")
            return False

    speak(f"I couldn't find {app_key}. Would you like to teach me where it is?")
    confirm = listen()
    if "yes" in confirm:
        speak("Please type or paste the full path to the .exe or file below:")
        path = input("Enter full path: ").strip('"')
        if os.path.exists(path):
            save_known_app(app_key, path)
            os.startfile(path)
            speak(f"{app_key} has been learned and opened.")
            return True
        else:
            speak("That path doesn't exist or is not valid.")
            return False
    return False

def close_app(app_name):
    found = False
    for proc in psutil.process_iter(['pid', 'name']):
        if app_name.lower() in proc.info['name'].lower():
            os.system(f"taskkill /f /pid {proc.info['pid']}")
            found = True
    speak(f"{app_name} has been closed." if found else f"I couldn’t find any app named {app_name} running.")

# ========== COMMAND HANDLER ==========
def process_command(command):
    fillers = ["can you", "could you", "would you", "just", "please", "i want you to", "jarvis", "hey"]
    for word in fillers:
        command = command.replace(word, "")
    command = command.strip()

    if any(x in command for x in ["open", "launch", "start"]):
        app_name = command.replace("open", "").replace("launch", "").replace("start", "").strip()
        speak(f"Trying to open {app_name}")
        opened = open_app(app_name)
        if not opened:
            speak("Let me ask the AI what to do.")
            ai_response = ask_ai(f"Is '{app_name}' a website? If yes, provide the full URL. If not, reply 'unrecognized'.")
            if "http" in ai_response:
                webbrowser.open(ai_response.strip())
                speak(f"I've opened the website: {ai_response.strip()}")
                log_ai_training(app_name, f"Opened URL: {ai_response.strip()}")
            elif "unrecognized" not in ai_response.lower():
                speak("AI thinks this might be a question, let me try to answer it.")
                answer = ask_ai(app_name)
                speak(answer)
                log_ai_training(app_name, answer)
            else:
                speak("I still couldn't understand that.")

    elif any(x in command for x in ["close", "exit", "shutdown"]):
        app_name = command.replace("close", "").replace("exit", "").replace("shutdown", "").strip()
        speak(f"Trying to close {app_name}")
        close_app(app_name)

    elif is_similar(command, ['time', 'what is the time']):
        now = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The time is {now}")

    elif is_similar(command, ['exit', 'goodbye']):
        speak("Goodbye!")
        os._exit(0)

    elif "show training" in command or "show learning" in command:
        show_training_log()

    elif len(command.split()) > 3:
        speak("Let me think about that.")
        response = ask_ai(command)
        speak(response)
        log_ai_training(command, response)

    else:
        speak("Let me think about that.")
        ai_response = ask_ai(f"What action should I take for this command: '{command}'? Be specific. Reply with either a URL to open, or say it's a question, or say it's unrecognized.")

        if "http" in ai_response:
            webbrowser.open(ai_response.strip())
            speak(f"I've opened the website I believe you meant: {ai_response.strip()}")
            log_ai_training(command, f"Opened URL: {ai_response.strip()}")
        elif "question" in ai_response.lower():
            answer = ask_ai(command)
            speak(answer)
            log_ai_training(command, answer)
        else:
            speak("I didn't understand that. Try saying open, close, or ask a clear question.")

# ========== MAIN LOOP ==========
def input_thread():
    while True:
        try:
            typed = input("\nType command (or press Enter to skip): ").strip().lower()
            if typed:
                command_queue.put(typed)
        except Exception as e:
            print("Error in input thread:", e)
            break

def main_loop():
    speak("Jarvis is now running. Press F4 to speak or type a command below.")
    threading.Thread(target=input_thread, daemon=True).start()

    while True:
        try:
            if keyboard.is_pressed('F4'):
                speak("Listening...")
                command = listen()
                if command:
                    process_command(command)
                time.sleep(1)

            while not command_queue.empty():
                typed_command = command_queue.get()
                process_command(typed_command)

        except KeyboardInterrupt:
            speak("Shutting down.")
            break
        except Exception as e:
            print("Error in main loop:", e)

# ========== RUN ==========
if __name__ == "__main__":
    main_loop()
