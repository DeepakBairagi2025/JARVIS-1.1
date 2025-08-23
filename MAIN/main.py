from BRAIN.MAIN_BRAIN.BRAIN.brain import *
from AUTOMATION.MAIN_INTEGRATION._integration_automation import *
from FUNCTION.MAIN_FUNCTION_INTEGRATION.function_integration import *

while True:
    text = listen().lower()
    Automation(text)
    Function_cmd(text)
    if "jarvis" in text:
        response = brain_cmd(text)
        speak(response)
    else:
        pass