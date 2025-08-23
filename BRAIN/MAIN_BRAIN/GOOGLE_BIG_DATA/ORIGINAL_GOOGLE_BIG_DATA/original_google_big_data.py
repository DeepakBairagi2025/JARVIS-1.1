from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import re
from selenium.webdriver.support.wait import WebDriverWait


def search_and_extract(text):
    try:
        chrome_options = Options()
        # chrome_options.add_argument("--headless")

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

        # Wait for the search results to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#search")))

        # Extract information directly from Google search results page
        webpage_content = driver.page_source

        # Parse the Google search results with BeautifulSoup
        soup = BeautifulSoup(webpage_content, "html.parser")

        # Extract text from search results snippets
        snippets = soup.find_all('span', {'data-ved': True})
        webpage_text = ' '.join([s.get_text().strip() for s in snippets[:5] if len(s.get_text().strip()) > 30])
        
        # If no snippets found, try featured content
        if not webpage_text:
            featured = soup.find('div', {'data-attrid': True})
            if featured:
                webpage_text = featured.get_text().strip()

        # Extract and print the first 8-9 sentences from the webpage text
        sentences = re.split(r'(?<=[.!?])\s', webpage_text)
        result_text = ' '.join(sentences[:9])

        driver.quit()
        return result_text

    except Exception as e:
        print("An error occurred:", e)
        if 'driver' in locals():
            driver.quit()
        return None


from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer


def summarize_text(text, sentences_count=5):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, sentences_count)
    return ' '.join([str(sentence) for sentence in summary])


def summary(text):
    text_to_summarize = text
    summary_result = summarize_text(text_to_summarize)
    return summary_result


def deep_search(text):
    x = text
    y = search_and_extract(x)
    if y is None:
        return "Error: Could not extract data from search results."
    x = summary(y)
    return x


result = deep_search("What is machine learning")
print(result)