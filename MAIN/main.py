import random
import threading

from BRAIN.MAIN_BRAIN.BRAIN.brain import *
from AUTOMATION.MAIN_INTEGRATION._integration_automation import *
from FUNCTION.MAIN_FUNCTION_INTEGRATION.function_integration import *
from FUNCTION.JARVIS_LISTEN.listen import *
from DATA.JARVIS_DLG_DATASET.DLG import *
from BRAIN.ACTIVITY.GREETINGS.WELCOME_GREETINGS.welcome_greetings import *
from BRAIN.ACTIVITY.GREETINGS.WISH_GREETINGS.wish_greetings import *
from BRAIN.ACTIVITY.ADVICE.advice import *
from BRAIN.ACTIVITY.JOKE.joke import *
from AUTOMATION.JARVIS_AUTOMATION_BATTERY.BATTERY_PLUG_CHECK.battery_plug_check import *
from AUTOMATION.JARVIS_AUTOMATION_BATTERY.BATTERY_ALERT.battery_alert import *


def comain():
    while True:
        text = listen().lower()
        text = text.replace(" jar", "jarvis")
        Automation(text)
        Function_cmd(text)
        Greeting(text)

        if text in bye_key_word:
            x = random.choice(res_bye)
            speak(x)
        elif "jarvis" in text:
            response = brain_cmd(text)
            speak(response)
        else:
            pass

def main():
    while True:
        wake_cmd = hearing().lower()
        if wake_cmd in wake_key_word:
            # welcome_dlg1 = random.choice(welcome_dlg)
            # speak(welcome_dlg1)
            welcome()
            comain()
        else:
            pass

def jarvis():
    t1 = threading.Thread(target=main)
    t2 = threading.Thread(target=battery_alert)
    t3 = threading.Thread(target=check_plugin_status)
    t4 = threading.Thread(target=advice)
    t5 = threading.Thread(target=jokes)

    t1.start()
    t2.start()
    t3.start()
    t4.start()
    t5.start()

    t1.join()
    t2.join()
    t3.join()
    t4.join()
    t5.join()

jarvis()