import psutil
from FUNCTION.JARVIS_SPEAK.speak import speak


def battery_persentage():
    battery = psutil.sensors_battery()
    percent = int(battery.percent)

    speak(f"the device is running on {percent}% battery power")

