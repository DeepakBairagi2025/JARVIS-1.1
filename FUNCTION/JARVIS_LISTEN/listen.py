import speech_recognition as sr
import os
import threading
from mtranslate import translate
from colorama import Fore, Style, init

init(autoreset=True)

def print_loop():
    while True:
        print(Fore.LIGHTGREEN_EX + "I am Listening...", end="", flush=True)
        print(Style.RESET_ALL, end="", flush=True)
        print("",end="",flush=True)

def Trans_hindi_to_english(txt):
    english_txt = translate(txt, to_language='en-us')
    return english_txt

def listen():
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.energy_threshold = 1800
    recognizer.dynamic_energy_adjustment_damping = 0.15
    recognizer.dynamic_energy_ratio = 1.5
    recognizer.pause_threshold = 0.8
    recognizer.operation_timeout = None
    recognizer.phrase_threshold = 0.3
    recognizer.non_speaking_duration = 0.5
    
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        while True:
            print(Fore.LIGHTGREEN_EX + "I am Listening...", end="", flush=True)
            try:
                audio = recognizer.listen(source, timeout=None)
                print("\r"+Fore.LIGHTYELLOW_EX + "Got it! Now Recognizing...",end="",flush=True)
                recognized_txt = recognizer.recognize_google(audio).lower()
                if recognized_txt:
                    translated_txt = Trans_hindi_to_english(recognized_txt)
                    print("\r"+Fore.BLUE + "Mr.Zeno: " + translated_txt)
                    return translated_txt
                else:
                    return ""    
            except sr.UnknownValueError:
                recognized_txt = ""
            finally:
                print("\r",end="",flush=True)
        
        os.system("cls" if os.name == "nt" else "clear")
        # threading part
        listen_thread = threading.Thread(target=listen)
        print_loop = threading.Thread(target=print_loop)
        listen_thread.start()
        print_loop.start()
        listen_thread.join()
        print_loop.join()

def hearing():
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.energy_threshold = 2500
    recognizer.dynamic_energy_adjustment_damping = 0.015
    recognizer.dynamic_energy_ratio = 1.5
    recognizer.pause_threshold = 0.8
    recognizer.operation_timeout = None
    recognizer.phrase_threshold = 0.3
    recognizer.non_speaking_duration = 0.5
    
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        while True:
            try:
                audio = recognizer.listen(source, timeout=None)
                recognized_txt = recognizer.recognize_google(audio).lower()
                if recognized_txt:
                    translated_txt = Trans_hindi_to_english(recognized_txt)
                    return translated_txt
                else:
                    return ""    
            except sr.UnknownValueError:
                recognized_txt = ""
            finally:
                print("\r",end="",flush=True)
