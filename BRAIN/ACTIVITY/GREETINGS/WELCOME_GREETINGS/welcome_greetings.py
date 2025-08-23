import random
from DATA.JARVIS_DLG_DATASET.DLG import welcome_dlg
from FUNCTION.JARVIS_SPEAK.speak import speak

def welcome():
    welcome = random.choice(welcome_dlg)
    speak(welcome)