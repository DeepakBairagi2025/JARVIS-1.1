from datetime import date
import datetime
import random

from DATA.JARVIS_DLG_DATASET.DLG import good_morningdlg, good_eveningdlg, good_afternoondlg, good_nightdlg
from FUNCTION.JARVIS_SPEAK.speak import speak

today = date.today()
formated_date = today.strftime("%d %b %y")
now = datetime.datetime.now()


def wish():
    current_hour = now.hour
    if 5 <= current_hour < 12:
        gm_dlg = random.choice(good_morningdlg)
        speak(gm_dlg)
    elif 12 <= current_hour < 18:
        ga_dlg = random.choice(good_afternoondlg)
        speak(ga_dlg)
    elif 18 <= current_hour < 21:
        ge_dlg = random.choice(good_eveningdlg)
        speak(ge_dlg)
    else:
        gn_dlg = random.choice(good_nightdlg)
        speak(gn_dlg)