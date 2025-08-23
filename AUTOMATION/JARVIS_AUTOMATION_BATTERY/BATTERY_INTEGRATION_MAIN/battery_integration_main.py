from AUTOMATION.JARVIS_AUTOMATION_BATTERY.BATTERY_ALERT.battery_alert import *
from AUTOMATION.JARVIS_AUTOMATION_BATTERY.BATTERY_PLUG_CHECK.battery_plug_check import check_plugin_status1
from AUTOMATION.JARVIS_AUTOMATION_BATTERY.CHECK_BATTERY_PERSENTAGE.check_battery_persentage import battery_persentage


def battery_cmd(text):
    if "check battery percentage" in text or "battery percentage check karo" in text or "battery kitni hai" in text:
        battery_persentage()
    elif "check plug" in text or "check battery plug" in text:
        check_plugin_status1()
    elif "give me the battery alert" in text or "battery alert" in text:
        battery_alert1()
    else:
        pass

#text = "check plug"
#battery_cmd(text)
#time.sleep(10)