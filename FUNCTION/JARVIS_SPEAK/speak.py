import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

chrome_options = Options()
chrome_options.add_argument("--headless") # Run in headless mode (without opening a browser window)

# Specify the path to your Chrome driver executable


chrome_driver_path = r'C:\Users\Deepak Bairagi\Desktop\JARVIS 1.1\DATA\JARVIS_DRIVER\chromedriver.exe'

# Create a Service object with the specified executable path
chrome_service = Service(chrome_driver_path)

# Create a Chrome driver instance with the specified options and service
driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

# Navigate to the website
driver.get("https://tts.5e7en.me/")


def speak(text):

    # Wait for the element to be clickable
    element_to_click = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, "//*[@id='text']"))
    )

    # Perform the click action
    element_to_click.click()

    # Input text into the element
    text_to_input = text
    element_to_click.send_keys(text_to_input)
    print(text_to_input)

    # Calculate sleep duration based on sentence length
    sleep_duration = min(0.2 + len(text) // 150, 150) # Minimum sleep in 3 seconds, maximum is 10 seconds

    # Wait for the button to be clickable
    button_to_click = WebDriverWait(driver, 3).until(
        EC.element_to_be_clickable((By.XPATH, "//*[@id='button']"))
    )

    # Perform the click action
    button_to_click.click()

    # Sleep fir dynamically calculated duration
    time.sleep(sleep_duration)

    # Clear the text box for the next sentence
    element_to_click.clear()

    
""" 
import pyttsx3

def speak(text):
    engine = pyttsx3.init()
    #pitch=180
    rate=180
    volume=1
    voice_id = engine.getProperty('voices')

    if voice_id:
        voices = engine.getProperty('voices')
        try:
            engine.setProperty('voice', voices[1].id)
        except IndexError:
            print("Voice ID not found. Using the default voice.")

    # Set properties (adjust as needed)
    engine.setProperty('rate', rate) # Speed of speech
    engine.setProperty('volume', volume) # Volume (0.0 to 1.0)
   # engine.setProperty('pitch', pitch) # Pitch level (0-100)

    # Real-time speaking
    print(text)
    engine.say(text)
    engine.runAndWait() """