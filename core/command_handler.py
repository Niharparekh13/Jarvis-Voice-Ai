import os
import time
import threading
import webbrowser
import keyboard
import queue as threading_queue
import re
from datetime import datetime
from core.speech import speak, listen, engine
from core.utils import is_similar, load_memory, save_memory
from core.app_control import open_app, close_app
from ai.chat import ask_ai, log_ai_training, show_training_log
from core.memory_log import save_to_memory_log, search_memory

command_queue = threading_queue.Queue()
memory = load_memory()
conversation_history = []

def process_command(command):
    fillers = ["can you", "could you", "would you", "just", "please", "i want you to", "jarvis", "hey"]
    for word in fillers:
        command = command.replace(word, "")
    command = command.strip()

    # Save to short-term memory
    conversation_history.append(command)
    memory["last_conversation"] = conversation_history[-5:]
    save_memory(memory)

    # AI classification
    classification_prompt = (
        f"Classify this user command: '{command}'\n"
        "Reply with ONLY ONE of these:\n"
        "remember → if the user is sharing something they want stored (e.g. tasks, facts, plans)\n"
        "recall → if the user is asking what they said before\n"
        "open_app → if they want to open an app\n"
        "close_app → if they want to close something\n"
        "ask_ai → if it's a question or a general chat"
    )
    ai_reply = ask_ai(classification_prompt).strip().lower()

    # Normalize AI response
    for keyword in ["remember", "recall", "open_app", "close_app", "ask_ai"]:
        if keyword in ai_reply:
            action_type = keyword
            break
    else:
        action_type = "ask_ai"

    if action_type == "ask_ai":
        name_match = re.search(r"\b(?:my name is|i am|call me)\s+([a-zA-Z ]+)", command)
        if name_match:
            name = name_match.group(1).strip()
            memory["name"] = name
            speak(f"Nice to meet you, {name}. I'll remember your name.")
            save_memory(memory)
            return

        bday_match = re.search(r"\b(?:my birthday is|i was born on)\s+(?:on\s+)?([0-9a-zA-Z ,]+)", command)
        if bday_match:
            birthday = bday_match.group(1).strip()
            memory["birthday"] = birthday
            speak(f"Thanks! I've saved your birthday as {birthday}.")
            save_memory(memory)
            return

    recall_triggers = [
        "what did i say", "what did i tell you", "what did i mention",
        "what did i say about", "what do i need", "remind me",
        "what do i need to get", "what do i have to get", "what was i supposed to get"
    ]
    if action_type == "ask_ai" and any(x in command.lower() for x in recall_triggers):
        result = search_memory(command)
        if result:
            speak(f"You told me: {result}")
        else:
            speak("I couldn't find anything about that.")
        return

    if action_type == "remember":
        save_to_memory_log(command)
        speak("Got it. I've saved that for you.")
        return

    elif action_type == "recall":
        command_lower = command.lower()

        if "name" in command_lower:
            if "name" in memory:
                speak(f"Your name is {memory['name']}.")
            else:
                speak("I don’t know your name yet. You can tell me by saying 'my name is...'")
            return

        if "birthday" in command_lower or "birth date" in command_lower or "when is my birthday" in command_lower:
            if "birthday" in memory:
                speak(f"Your birthday is {memory['birthday']}.")
            else:
                speak("I don’t know your birthday yet. You can tell me by saying 'my birthday is...'")
            return

        result = search_memory(command)
        if result:
            speak(f"You told me: {result}")
        else:
            speak("I couldn't find anything about that.")
        return

    elif action_type == "open_app":
        app_name = command.replace("open", "").replace("start", "").replace("launch", "").strip()
        speak(f"Trying to open {app_name}")
        opened = open_app(app_name)
        if not opened:
            speak(f"I couldn't open {app_name}. You might need to teach me where it is.")
        return

    elif action_type == "close_app":
        app_name = command.replace("close", "").replace("exit", "").replace("shutdown", "").strip()
        speak(f"Trying to close {app_name}")
        close_app(app_name)
        return

    elif action_type == "ask_ai":
        if command.startswith("remember that"):
            parts = command.replace("remember that", "").split(" is ")
            if len(parts) == 2:
                key, value = parts[0].strip(), parts[1].strip()
                memory[key] = value
                save_memory(memory)
                speak(f"Got it. I will remember that {key} is {value}.")
                return

        if any(x in command for x in ["who am i", "do you remember me", "what did i tell you"]):
            if memory:
                summary = "; ".join([f"{k}: {v}" for k, v in memory.items() if k != "last_conversation"])
                speak(f"Here's what I remember: {summary}")
            else:
                speak("You haven't told me anything to remember yet.")
            return

        if any(command.startswith(x) for x in ["what is", "who is", "do you know", "do you remember"]):
            key = command.replace("what is", "").replace("who is", "").replace("do you know", "").replace("do you remember", "").strip()
            for k in memory:
                if is_similar(key, [k]):
                    speak(f"You told me that {k} is {memory[k]}.")
                    return

        if is_similar(command, ['time', 'what is the time']):
            now = datetime.now().strftime("%I:%M %p")
            speak(f"The time is {now}")
            return

        elif "show training" in command or "show learning" in command:
            show_training_log()
            return

        elif len(command.split()) > 3:
            speak("Let me think about that.")
            response = ask_ai(command)
            speak(response)
            log_ai_training(command, response)
            return

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
                time.sleep(0.1)

        except KeyboardInterrupt:
            try:
                speak("Shutting down.")
                engine.stop()
            except:
                pass
            break

        except Exception as e:
            print("Error in main loop:", e)
            try:
                engine.stop()
            except:
                pass
