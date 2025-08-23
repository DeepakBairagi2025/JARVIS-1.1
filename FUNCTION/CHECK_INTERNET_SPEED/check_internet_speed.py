import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from FUNCTION.JARVIS_SPEAK.speak import speak


def get_internet_speed():
    try:
        # Set the path to your ChromeDriver executable
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_driver_path = r'C:\Users\Deepak Bairagi\Desktop\JARVIS 1.1\DATA\JARVIS_DRIVER\chromedriver.exe'

        # Initialize Chrome browser
        service = ChromeService(chrome_driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Open the website
        driver.get("https://fast.com/")
        speak("Checking your Internet speed")
        time.sleep(15)

        # Wait for the speed test to complete (adjust the timeout as needed)
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "speed-value")))

        # Find the element with the speed value
        speed_element = driver.find_element(By.ID, "speed-value")

        # Get the text value from the elemen
        speed_value = speed_element.text

        return speed_value
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        # Close the browser window
        if driver:
            driver.quit()


def check_internet_speed():
    speed_result = get_internet_speed()

    if speed_result is not None:
        speak(f"Sir, your internet speed is: {speed_result} Mbps")
    else:
        speak("Could not retrieve internet speed.")

