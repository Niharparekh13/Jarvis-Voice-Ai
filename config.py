import os
from pathlib import Path

KNOWN_APPS_FILE = "data/known_apps.json"
AI_LOG_FILE = "data/ai_training_data.txt"
MEMORY_FILE = "data/memory.json"
MEMORY_LOG_FILE = "data/memory_log.json"


WAKE_WORDS = [
    "jarvis", "jerry", "service", "charge this", "doris", "generous"
]

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