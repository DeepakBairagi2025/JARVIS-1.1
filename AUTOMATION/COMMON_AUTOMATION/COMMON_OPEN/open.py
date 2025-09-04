import pyautogui as ui
from FUNCTION.JARVIS_SPEAK.speak import *
import random
from DATA.JARVIS_DLG_DATASET.DLG import open_dlg
import time

def open(text):
    x = random.choice(open_dlg)
    speak(x+" "+text)
    time.sleep(3)
    ui.hotkey("win")
    time.sleep(0.2)
    ui.write(text)
    time.sleep(0.5)
    ui.press("enter")

# open("edge")