from AUTOMATION.COMMON_AUTOMATION.COMMON_INTEGRATION.common_integration import *
from AUTOMATION.JARVIS_AUTOMATION_GOOGLE.GOOGLE_INETGRATION_MAIN.google_integration_main import *
from AUTOMATION.JARVIS_AUTOMATION_BATTERY.BATTERY_INTEGRATION_MAIN.battery_integration_main import *
from AUTOMATION.JARVIS_AUTOMATION_YOUTUBE.INTEGRATION_MAIN.integration_main import *

def Automation(text):
    youtube_cmd(text)
    google_cmd(text)
    battery_cmd(text)
    common_cmd(text)

