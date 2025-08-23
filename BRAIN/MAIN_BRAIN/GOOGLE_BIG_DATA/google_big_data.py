# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.support.wait import WebDriverWait
# from bs4 import BeautifulSoup
# import re
#
# def search_and_extract(text):
#     chrome_options = Options()
#
#     # run in true headless background
#     chrome_options.add_argument("--headless")
#     chrome_options.add_argument("--disable-gpu")
#     chrome_options.add_argument("--window-size=1920,1080")
#
#     # DISABLE images, CSS, fonts to speed up network loads
#     chrome_prefs = {
#         "profile.managed_default_content_settings.images": 2,
#         "profile.managed_default_content_settings.stylesheets": 2,
#         "profile.managed_default_content_settings.fonts": 2
#     }
#     chrome_options.add_experimental_option("prefs", chrome_prefs)
#
#     # STEALTH flags (unchanged)
#     chrome_options.add_argument("--disable-blink-features=AutomationControlled")
#     chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
#     chrome_options.add_experimental_option("useAutomationExtension", False)
#     chrome_options.add_argument(
#         "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
#     )
#
#     # EAGER load stops at DOMContentLoaded, not full load
#     chrome_options.set_capability("pageLoadStrategy", "eager")
#
#     service = Service(r"C:\Users\Deepak Bairagi\Desktop\JARVIS 1.1\DATA\JARVIS_DRIVER\chromedriver.exe")
#     driver = webdriver.Chrome(service=service, options=chrome_options)
#
#     # shorter implicit wait
#     driver.implicitly_wait(10)
#
#     try:
#         # 1) Google search + cookie consent
#         driver.get("https://www.google.com")
#         try:
#             btn = WebDriverWait(driver, 3).until(
#                 EC.element_to_be_clickable((By.XPATH, "//button[.='I agree' or .='Accept all']"))
#             )
#             btn.click()
#         except:
#             pass
#
#         # 2) Type & submit query
#         box = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.NAME, "q")))
#         box.clear()
#         box.send_keys(text, Keys.RETURN)
#
#         # 3) Grab the first result link immediately when it appears
#         link = WebDriverWait(driver, 7).until(
#             EC.presence_of_element_located((By.CSS_SELECTOR, "div.yuRUbf a"))
#         )
#         first_link = link.get_attribute("href")
#
#         # 4) Navigate there (stops at DOMContentLoaded)
#         driver.get(first_link)
#
#         # 5) Wait only for the first <p> tag to show up—should be quick under eager strategy
#         WebDriverWait(driver, 7).until(EC.presence_of_element_located((By.TAG_NAME, "p")))
#
#         # 6) Scrape the first few paragraphs
#         soup = BeautifulSoup(driver.page_source, "html.parser")
#         paras = [p.get_text(strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]
#         text_all = " ".join(paras) if paras else driver.find_element(By.TAG_NAME, "body").text
#
#         # return first 9 sentences
#         sentences = re.split(r'(?<=[.!?])\s+', text_all)
#         return " ".join(sentences[:9])
#
#     except Exception as e:
#         print("An error occurred:", repr(e))
#         return ""
#     finally:
#         driver.quit()
#
#
# def summarize_text(text, sentences_count=5):
#     from sumy.parsers.plaintext import PlaintextParser
#     from sumy.nlp.tokenizers import Tokenizer
#     from sumy.summarizers.lsa import LsaSummarizer
#
#     parser = PlaintextParser.from_string(text, Tokenizer("english"))
#     summarizer = LsaSummarizer()
#     summary = summarizer(parser.document, sentences_count)
#     return " ".join(str(s) for s in summary)
#
# def summary(text):
#     return summarize_text(text)
#
# def deep_search(text):
#     x = text
#     y = search_and_extract(x)
#     x = summary(y)
#     return x

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

        # Find multiple search results for longer response
        all_results = []
        selectors = ['.VwiC3b', '.s3v9rd', '.IsZvec', 'div.g', '[data-ved]']
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements[:3]:  # Get first 3 results
                    text = element.text.strip()
                    if text and len(text) > 20:
                        all_results.append(text)
                if all_results:
                    break
            except:
                continue

        if not all_results:
            return "Could not extract data from search results."

        # Combine results and clean
        combined_text = ' '.join(all_results)
        combined_text = combined_text.replace("Featured snippet from the web", "")
        combined_text = combined_text.replace("About this result", "")
        combined_text = combined_text.replace("People also ask", "")

        # Split into sentences and take more for 9 lines
        sentences = re.split(r'(?<=[.!?])\s+', combined_text)
        meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        result_text = '. '.join(meaningful_sentences[:15])  # More sentences for longer response
        if not result_text.endswith('.'):
            result_text += '.'

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


# result = deep_search("What is machine learning")
# print(result)