import pyttsx3
import json as js
import threading
import time
import sounddevice as sd
from vosk import KaldiRecognizer
from models.vosk_model import vosk_model, samplerate, callback, q

speech_lock = threading.Lock()
engine = pyttsx3.init()
engine.setProperty('rate', 150)

def speak(text):
    with speech_lock:
        try:
            print("Jarvis:", text)
            engine.say(text)
            engine.runAndWait()
        except RuntimeError as e:
            print("Speech engine error:", e)
            try:
                engine.stop()
            except:
                pass
            time.sleep(0.1)

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