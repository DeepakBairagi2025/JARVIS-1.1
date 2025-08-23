import time
import pyautogui as ui
import random
from DATA.JARVIS_DLG_DATASET.DLG import s1, s2
from FUNCTION.JARVIS_SPEAK.speak import speak


def search_manual(text):
    ui.press("/")
    ui.write(text)
    s12 = random.choice(s1)
    speak(s12)
    time.sleep(0.5)
    ui.press("enter")
    s12 = random.choice(s2)
    speak(s12)

