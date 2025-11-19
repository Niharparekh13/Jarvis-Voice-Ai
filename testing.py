# from openai import OpenAI

# client = OpenAI(api_key="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")

# try:
#     response = client.chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=[
#             {"role": "user", "content": "What is a black hole?"}
#         ],
#         max_tokens=150
#     )
#     print(response.choices[0].message.content)
# except Exception as e:
#     print("Error:", e)
from vosk import Model, KaldiRecognizer
import sounddevice as sd
import queue
import json

q = queue.Queue()
model = Model("model")  # Make sure you have a 'model' folder with a Vosk model

def callback(indata, frames, time, status):
    q.put(bytes(indata))

rec = KaldiRecognizer(model, 16000)
with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16', channels=1, callback=callback):
    print("Speak something (offline)...")
    while True:
        data = q.get()
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            print("You said:", result.get("text", ""))
