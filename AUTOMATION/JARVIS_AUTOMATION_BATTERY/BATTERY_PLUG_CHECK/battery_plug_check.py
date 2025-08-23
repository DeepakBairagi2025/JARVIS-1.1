import random
import psutil
from DATA.JARVIS_DLG_DATASET.DLG import plug_in, plug_out
from FUNCTION.JARVIS_SPEAK.speak import speak


def check_plugin_status():
    battery = psutil.sensors_battery()
    previous_state = battery.power_plugged

    # Only announce when the state actually changes
    while True:
        battery = psutil.sensors_battery()

        if battery.power_plugged != previous_state:
            if battery.power_plugged:
                random_low = random.choice(plug_in)
                speak(random_low)
            else:
                random_low = random.choice(plug_out)
                speak(random_low)
            previous_state = battery.power_plugged

        # Check agian after a minute
        #time.sleep(5)

previous_state = None
plug_in1 = ["charage is plugged check confirm", "battery is charging that means charger is plugged"]
plug_out2 = ["charage status unplugged", "battery is not charging that means charger is not plugged"]

def check_plugin_status1():
    global previous_state # Use the global variables

    battery = psutil.sensors_battery()
    #previous_state = battery.power_plugged

    if battery.power_plugged != previous_state:
        if battery.power_plugged:
            random_low = random.choice(plug_in1)
            speak(random_low)
        else:
            random_low = random.choice(plug_out2)
            speak(random_low)
        previous_state = battery.power_plugged