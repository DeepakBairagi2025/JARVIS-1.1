import requests
import json
from FUNCTION.JARVIS_SPEAK.speak import speak


def get_tempreature_openweathermap(city):
    api_key = "57750a40690b5a50f53cc755c386cfbc"
    endpoint = "http://api.openweathermap.org/data/2.5/weather"

    # Send GET request to API endpoint
    response = requests.get(endpoint, params={'q': city, 'appid': api_key, 'units': 'metric'})

    # Check if the request was successful
    if response.status_code == 200:
        # parse JSON respone
        data = json.loads(response.text)

        # check if 'main' key is present
        if 'main' in data:
            # Extract temperature in Celsius
            temperature_celesius = data['main']['temp']
            return temperature_celesius
        else:
            print("Error: 'main' key not found in API response")
    else:
        print(f"Error: Unable to fetch data from API. Status code: {response.status_code}")

    return None

def Temp():
    city = "Delhi", "New Delhi"

    # get temperature using OpenWeatherMap API
    temperature_celesius = get_tempreature_openweathermap(city)

    if temperature_celesius is not None:
        speak(f"The weather in {city} is {temperature_celesius}°C.")
    else:
        print("Temperature data not available.")