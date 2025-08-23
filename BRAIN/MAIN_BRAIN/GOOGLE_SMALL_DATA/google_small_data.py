
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def search_brain(text):
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")

        # Add options to avoid detection and CAPTCHA
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # Set the path to your ChromeDriver executable
        chrome_driver_path = r'c:\Users\Deepak Bairagi\Desktop\JARVIS 1.1\DATA\JARVIS_DRIVER\chromedriver.exe'

        chrome_service = Service(chrome_driver_path)
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

        # Execute script to hide automation indicators
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # Open Google in the browser
        driver.get("https://www.google.com")

        # Find the search box using its name attribute value
        search_box = driver.find_element("name", "q")

        # Type the search query
        search_query = text
        search_box.send_keys(search_query)

        # Submit the form
        search_box.send_keys(Keys.RETURN)

        # Wait for search results to load properly
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#search")))

        # Additional wait to ensure content is fully loaded
        time.sleep(3)

        # Find search results with updated selectors
        result_text = ""
        selectors = ['.VwiC3b', '.s3v9rd', '.IsZvec', 'div.g', '[data-ved]']
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.text.strip()
                    if text and len(text) > 20:
                        result_text = text
                        break
                if result_text:
                    break
            except:
                continue

        if not result_text:
            driver.quit()
            return "I couldn't find any search results for that query."

        # Clean and process the text
        result_text = result_text.strip()

        # Remove common Google UI elements
        result_text = result_text.replace("Featured snippet from the web", "")
        result_text = result_text.replace("About this result", "")
        result_text = result_text.replace("People also ask", "")

        # Split into sentences and clean
        sentences = re.split(r'(?<=[.!?])\s+', result_text)

        # Filter out very short sentences and URLs
        meaningful_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if (len(sentence) > 10 and
                    not re.search(r'\b(?:https?://|www\.)\S+\b', sentence) and
                    not sentence.lower().startswith(('›', '...', 'more', 'see', 'view'))):
                meaningful_sentences.append(sentence)

        # Take first 5-6 meaningful sentences for medium responses
        if meaningful_sentences:
            result_text = '. '.join(meaningful_sentences[:5])
            if not result_text.endswith('.'):
                result_text += '.'
        else:
            # Fallback: use raw text but clean it
            result_text = re.sub(r'\s+', ' ', result_text)
            result_text = result_text[:350] + '...' if len(result_text) > 350 else result_text

        # Final check for meaningful content
        if not result_text.strip() or len(result_text.strip()) < 20:
            result_text = "I found search results but couldn't extract meaningful content. Please try a different query."

        driver.quit()
        return result_text

    except Exception as e:
        print("An error occurred:", e)
        if 'driver' in locals():
            driver.quit()
        return "I encountered an error while searching. Please try again."

