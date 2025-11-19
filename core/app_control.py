import os
import json
import psutil
from pathlib import Path
from fuzzywuzzy import process
from config import KNOWN_APPS_FILE, ALIAS_MAP
from core.speech import speak
from core.utils import is_similar


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

def search_common_folders(app_name):
    folders = [
        Path.home() / "Desktop",
        Path.home() / "Documents",
        Path("C:/ProgramData/Microsoft/Windows/Start Menu/Programs")
    ]
    matches = []
    for folder in folders:
        for root, dirs, files in os.walk(folder):
            for file in files:
                if app_name.lower().replace(" ", "") in file.lower().replace(" ", ""):
                    matches.append(os.path.join(root, file))
    matches.sort(key=lambda x: ("desktop" not in x.lower(), len(x)))
    return matches

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
    from core.speech import listen
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
