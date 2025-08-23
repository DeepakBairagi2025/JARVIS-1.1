import requests  # pip intall requests

from FUNCTION.JARVIS_SPEAK.speak import speak
from FUNCTION.OFFLINE_VOICE.speak2 import fspeak

def is_online(url="http://www.google.com", timeout=5):
    try:
        # Try to make a GET request to the specified URL
        response = requests.get(url, timeout=10)
        # If the response status code is in the success range (200-299)
        return response.status_code >= 200 and response.status_code < 300
    except requests.ConnectionError:
        return False


# Example usage
def internet_status():
    if is_online():
        speak("YES SIR ! I AM READY AND ONLINE")
    else:
        print("HEY THERE SIR ! I AM FRIDAY, SORRY BUT JARVIS IS CURRENTLY NOT ONLINE")


