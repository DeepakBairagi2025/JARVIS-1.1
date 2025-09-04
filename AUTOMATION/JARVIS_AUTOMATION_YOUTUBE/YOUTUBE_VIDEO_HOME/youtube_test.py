import speech_recognition as sr
import pyttsx3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time
import re
import os
import json
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver import ActionChains
import difflib
from io import BytesIO
try:
    from PIL import Image
    import pytesseract
    # Configure tesseract.exe path on Windows if available
    try:
        possible_paths = [
            os.environ.get('TESSERACT_PATH', ''),
            r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
            r"C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe",
        ]
        for p in possible_paths:
            if p and os.path.exists(p):
                pytesseract.pytesseract.tesseract_cmd = p
                break
    except Exception:
        pass
    TESSERACT_AVAILABLE = True
except Exception:
    TESSERACT_AVAILABLE = False

# Imports from modularized packages
from core.speech import speak
from core.stt import listen_command as core_listen_command
from core.driver_attach import (
    create_driver as core_create_driver,
    ensure_attached as core_ensure_attached,
    switch_to_youtube_tab as core_switch_to_youtube_tab,
    get_driver,
)
from util.text_norm import (
    normalize_title as util_normalize_title,
    ascii_projection as util_ascii_projection,
    devnagari_projection as util_devnagari_projection,
    normalize_number_words as util_normalize_number_words,
    parse_video_index as util_parse_video_index,
    extract_title_from_command as util_extract_title_from_command,
)
from youtube.initial_data import match_and_open_by_initial_data as y_match_and_open_by_initial_data
from youtube.actions import (
    click_home as y_click_home,
    click_history as y_click_history,
    click_watch_later as y_click_watch_later,
    find_and_click_video_by_title as y_find_and_click_video_by_title,
    search_and_click_title as y_search_and_click_title,
    ocr_find_and_click_video as y_ocr_find_and_click_video,
)

# Debug flag to trace matching and scrolling decisions
DEBUG = True

# Initialize recognizer (kept for compatibility in this file)
recognizer = sr.Recognizer()

## Driver handled by core.driver_attach
driver = core_create_driver()
# Keep a local reference for legacy code paths
driver = get_driver()

def ensure_attached() -> bool:
    return core_ensure_attached()

def switch_to_youtube_tab():
    return core_switch_to_youtube_tab()

def click_history() -> bool:
    """Open YouTube History via sidebar if available, else direct navigation."""
    try:
        wait = WebDriverWait(driver, 8)
        el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[title='History']")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
        try:
            el.click()
        except Exception:
            driver.execute_script("arguments[0].click();", el)
        return True
    except Exception:
        pass
    try:
        driver.get("https://www.youtube.com/feed/history")
        return True
    except Exception:
        return False

def click_watch_later() -> bool:
    """Open YouTube Watch Later via sidebar if available, else direct navigation."""
    try:
        wait = WebDriverWait(driver, 8)
        el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[title='Watch later']")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
        try:
            el.click()
        except Exception:
            driver.execute_script("arguments[0].click();", el)
        return True
    except Exception:
        pass
    try:
        driver.get("https://www.youtube.com/playlist?list=WL")
        return True
    except Exception:
        return False

from youtube.initial_data import get_yt_initial_data as get_yt_initial_data

from youtube.initial_data import iter_all_video_renderers as iter_all_video_renderers

from youtube.initial_data import extract_title_from_renderer as extract_title_from_renderer

from youtube.initial_data import get_initial_feed_candidates as get_initial_feed_candidates

def match_and_open_by_initial_data(spoken_title: str) -> bool:
    return y_match_and_open_by_initial_data(spoken_title)

def open_best_from_search(query: str) -> bool:
    """Navigate to the YouTube search results for the query, harvest titles/hrefs, and open best match."""
    q = (query or '').strip()
    if not q:
        return False
    try:
        from urllib.parse import quote_plus
        url = f"https://www.youtube.com/results?search_query={quote_plus(q)}"
        driver.get(url)
        # Try ytInitialData first
        time.sleep(0.7)
        data = get_yt_initial_data()
        cands = []
        if data:
            for vr in iter_all_video_renderers(data):
                vid = vr.get('videoId')
                title = extract_title_from_renderer(vr)
                if vid and title:
                    cands.append({'title': title, 'videoId': vid, 'href': f"https://www.youtube.com/watch?v={vid}"})
        # Fallback to DOM on results page
        if not cands:
            try:
                els = driver.find_elements(By.CSS_SELECTOR, "ytd-video-renderer a#video-title, a#video-title")
            except Exception:
                els = []
            for el in els[:40]:
                try:
                    if not el.is_displayed():
                        continue
                    # Resolve the anchor and href from the surrounding card to avoid missing href on title elements
                    href = ''
                    try:
                        info = driver.execute_script(
                            """
                            const e = arguments[0];
                            const card = e.closest('ytd-rich-item-renderer') || e.closest('ytd-rich-grid-media') || e.closest('ytd-video-renderer') || e;
                            const a = (card && card.querySelector('a#video-title, a#video-title-link, a[href*=\"watch\"]')) || e.closest('a[href*=\"watch\"]');
                            return a ? a.href || a.getAttribute('href') || '' : '';
                            """,
                            el,
                        )
                        href = (info or '').strip()
                    except Exception:
                        pass
                    if not href:
                        href = el.get_attribute('href') or ''
                    title = (el.get_attribute('title') or el.text or '').strip()
                    if not title:
                        title = driver.execute_script("return arguments[0].innerText || '';", el) or ''
                        title = str(title).strip()
                    if not title:
                        continue
                    vid = None
                    if 'watch' in href:
                        m = re.search(r"[?&]v=([\w-]{6,})", href)
                        if m:
                            vid = m.group(1)
                    cands.append({'title': title, 'videoId': vid, 'href': href or None})
                except Exception:
                    continue
        if DEBUG:
            print(f"[YouTube][Search] candidates: {len(cands)}")
        if not cands:
            return False
        # Reuse scoring with the same normalization rules
        wn = normalize_number_words(normalize_title(q))
        wa = ascii_projection(wn)
        ranked = []
        for c in cands:
            tl = c['title'].lower()
            tl_norm = normalize_title(normalize_number_words(tl))
            tl_ascii = ascii_projection(tl)
            ratio = difflib.SequenceMatcher(None, tl_norm, wn).ratio()
            wtoks = set(wn.split())
            ttoks = set(tl_norm.split())
            jacc = len(wtoks & ttoks) / max(1, len(wtoks | ttoks))
            score = max(ratio, jacc)
            if wn and wn in tl_norm:
                score = max(score, 0.92)
            if wa and wa in tl_ascii:
                score = max(score, 0.90)
            ranked.append((score, c))
        ranked.sort(reverse=True, key=lambda x: x[0])
        if DEBUG and ranked:
            print("[YouTube][Search] top:", [(f"{s:.3f}", r['title'][:80]) for s, r in ranked[:3]])
        if not ranked:
            return False
        best = ranked[0][1]
        url = best.get('href') or (best.get('videoId') and f"https://www.youtube.com/watch?v={best['videoId']}")
        if not url:
            return False
        if url.startswith('/'):
            url = 'https://www.youtube.com' + url
        driver.get(url)
        speak(f"Playing {best['title']}")
        return True
    except Exception:
        return False

from youtube.dom import get_visible_home_candidates as get_visible_home_candidates

def search_and_click_title(title: str) -> bool:
    """Use YouTube search to find and click a video by title.
    Returns True if a confident match was clicked.
    """
    try:
        wait = WebDriverWait(driver, 10)
        # Focus search box
        box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input#search")))
        driver.execute_script("arguments[0].value='';", box)
        box.clear()
        box.send_keys(title)
        # Click search button
        try:
            btn = driver.find_element(By.CSS_SELECTOR, "button#search-icon-legacy")
            driver.execute_script("arguments[0].click();", btn)
        except Exception:
            box.submit()
        # Wait results
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-video-renderer a#video-title")))
        # Reuse title matching on results page
        return find_and_click_video_by_title(wait, title, max_scrolls=1)
    except Exception:
        return False
    return False

def ocr_get_text_boxes():
    """Return list of OCR boxes from current viewport screenshot using pytesseract.
    Each item: {text, left, top, width, height, conf}
    """
    if not TESSERACT_AVAILABLE:
        return []
    try:
        png = driver.get_screenshot_as_png()
        img = Image.open(BytesIO(png))
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        boxes = []
        n = len(data.get('text', []))
        for i in range(n):
            txt = (data['text'][i] or '').strip()
            try:
                conf = float(data['conf'][i])
            except Exception:
                conf = -1.0
            if txt and conf >= 60 and len(txt) >= 3:
                boxes.append({
                    'text': txt,
                    'left': data['left'][i],
                    'top': data['top'][i],
                    'width': data['width'][i],
                    'height': data['height'][i],
                    'conf': conf,
                })
        return boxes
    except Exception:
        return []

def ocr_find_and_click_video(title: str) -> bool:
    """OCR fallback: detect visible text, pick the best matching line, then map to a clickable video element.
    Returns True if clicked.
    """
    if not TESSERACT_AVAILABLE:
        return False
    boxes = ocr_get_text_boxes()
    if not boxes:
        return False
    wanted = title.strip().lower()
    # Choose best OCR line
    best = None
    best_ratio = 0.0
    for b in boxes:
        t = b['text'].lower()
        r = difflib.SequenceMatcher(None, t, wanted).ratio()
        if wanted in t:
            r = max(r, 0.9)
        if r > best_ratio:
            best_ratio = r
            best = b
    if not best or best_ratio < 0.65:
        return False
    best_text = best['text']
    # Map to DOM anchor candidates and click the closest textual match
    try:
        candidates = driver.find_elements(By.CSS_SELECTOR, "ytd-video-renderer a#video-title, ytd-rich-item-renderer a#video-title, a#video-title, a[href*='watch']")
    except Exception:
        candidates = []
    best_el = None
    best_el_ratio = 0.0
    for el in candidates:
        try:
            if not el.is_displayed():
                continue
            txt = (el.get_attribute('title') or el.text or '').strip()
            if not txt:
                continue
            r1 = difflib.SequenceMatcher(None, txt.lower(), best_text.lower()).ratio()
            r2 = difflib.SequenceMatcher(None, txt.lower(), wanted).ratio()
            r = max(r1, r2)
            if wanted in txt.lower() or best_text.lower() in txt.lower():
                r = max(r, 0.9)
            if r > best_el_ratio:
                best_el_ratio = r
                best_el = el
        except Exception:
            continue
    if best_el and best_el_ratio >= 0.7:
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", best_el)
            try:
                best_el.click()
            except Exception:
                driver.execute_script("arguments[0].click();", best_el)
            speak(f"Playing {best_text}")
            return True
        except Exception:
            return False
    return False

def parse_video_index(command: str) -> int:
    """Return 1-based index parsed from phrases like 'video 2', 'second video', 'open third', etc. 0 if none."""
    words = command.lower().replace("-", " ").split()
    # Map common ordinal/cardinal words
    word_to_num = {
        "one": 1, "first": 1, "1st": 1,
        "two": 2, "second": 2, "2nd": 2,
        "three": 3, "third": 3, "3rd": 3,
        "four": 4, "fourth": 4, "4th": 4,
        "five": 5, "fifth": 5, "5th": 5,
        "six": 6, "sixth": 6, "6th": 6,
        "seven": 7, "seventh": 7, "7th": 7,
        "eight": 8, "eighth": 8, "8th": 8,
        "nine": 9, "ninth": 9, "9th": 9,
        "ten": 10, "tenth": 10, "10th": 10,
    }
    # 1) look for explicit pattern: 'video <n>'
    for i, w in enumerate(words[:-1]):
        if w == "video":
            nxt = words[i+1]
            if nxt.isdigit():
                return int(nxt)
            if nxt in word_to_num:
                return word_to_num[nxt]
    # 2) look for standalone ordinals/cardinals
    for w in words:
        if w.isdigit():
            return int(w)
        if w in word_to_num:
            return word_to_num[w]
    return 0

from youtube.dom import get_home_video_elements as get_home_video_elements

from youtube.dom import get_video_title_elements as get_video_title_elements

def load_until_index(wait: WebDriverWait, desired_index: int, max_scrolls: int = 8):
    """Scrolls the page to load more videos until desired index is available or max_scrolls reached.
    Returns the list of elements currently available.
    """
    last_len = 0
    for _ in range(max_scrolls):
        elements = get_home_video_elements(wait)
        if len(elements) >= desired_index and desired_index > 0:
            return elements
        # if not enough yet, scroll down to load more
        driver.execute_script("window.scrollBy(0, Math.max(600, window.innerHeight));")
        time.sleep(0.6)
        # Break if no growth in elements to avoid infinite loop
        if len(elements) == last_len:
            break
        last_len = len(elements)
    return get_home_video_elements(wait)

def extract_title_from_command(command: str) -> str:
    """Try to extract a video title phrase from the spoken command.
    Looks for quotes first, else takes words after play/open/click/watch.
    """
    cmd = command.strip().lower()
    # 1) If user spoke quotes: play "never gonna give you up"
    if '"' in command:
        parts = command.split('"')
        if len(parts) >= 3:
            return parts[1].strip()
    if "'" in command:
        parts = command.split("'")
        if len(parts) >= 3:
            return parts[1].strip()
    # 2) Take text after keywords
    keywords = ["play", "open", "click", "watch", "search"]
    for kw in keywords:
        if kw in cmd:
            after = command.lower().split(kw, 1)[1]
            # Remove common suffix words
            for rm in ["the", "video", "on youtube", "on you tube"]:
                after = after.replace(rm, "")
            title = after.strip(" :,-")
            # If looks like a pure number, it's not a title
            if title and not title.replace(" ", "").isdigit():
                return title
    return ""

def find_and_click_video_by_title(wait: WebDriverWait, wanted_title: str, max_scrolls: int = 3) -> bool:
    """Scroll and fuzzy-match against visible video titles, click best match if confident.
    Returns True if clicked.
    """
    wanted = wanted_title.strip()
    if not wanted:
        return False
    wanted_norm = normalize_title(wanted)
    for step in range(max_scrolls):
        pairs = get_video_title_elements(wait)
        if not pairs:
            # nothing on page; scroll a bit and retry
            driver.execute_script("window.scrollBy(0, Math.max(600, window.innerHeight));")
            time.sleep(0.4)
            continue
        # Fast path: if an EXACT or strong substring match is visible on screen, click it immediately without scrolling
        wanted_norm = normalize_title(wanted)
        viewport_h = driver.execute_script("return window.innerHeight;")
        for el, t in pairs:
            try:
                rect = driver.execute_script("const r=arguments[0].getBoundingClientRect(); return {top:r.top,bottom:r.bottom};", el)
                if not rect:
                    continue
                top = rect.get('top', 9999)
                bottom = rect.get('bottom', -9999)
                visible = (bottom > 0) and (top < (viewport_h * 1.05 if viewport_h else 10000))
                if not visible:
                    continue
                tl_norm = normalize_title((t or '').lower())
                if tl_norm == wanted_norm or wanted_norm in tl_norm:
                    if DEBUG:
                        print(f"[YouTube] Fast-path click: '{t}' matches '{wanted_title}'")
                    if click_video_element(el):
                        speak(f"Playing {t}")
                        return True
            except Exception:
                continue
        # Build candidate list
        candidates = []
        center = viewport_h / 2 if viewport_h else 400
        for el, t in pairs:
            try:
                rect = driver.execute_script("const r=arguments[0].getBoundingClientRect(); return {top:r.top,bottom:r.bottom};", el)
                top = rect.get('top', 9999) if rect else 9999
                near = abs(top - center)
                tl = t.lower()
                tl_norm = normalize_title(tl)
                ratio = difflib.SequenceMatcher(None, tl_norm, wanted_norm).ratio()
                substring = (wanted_norm in tl_norm)
                # Token-Jaccard to be robust against truncation/ellipsis
                wtoks = set(wanted_norm.split())
                ttoks = set(tl_norm.split())
                jacc = len(wtoks & ttoks) / max(1, len(wtoks | ttoks))
                if substring:
                    ratio = max(ratio, 0.9)
                score = max(ratio, jacc)
                bottom = rect.get('bottom', -9999) if rect else -9999
                visible = (bottom > 0) and (top < (viewport_h * 1.05 if viewport_h else 10000))
                candidates.append((visible, substring, score, -near, el, t))
            except Exception:
                continue
        # First, try clicking among VISIBLE items only without scrolling
        vis_candidates = [c for c in candidates if c[0]]
        vis_candidates.sort(reverse=True)  # (visible, substring, score, -near,...)
        if DEBUG:
            print("[YouTube] Visible candidates:")
            for _vis, is_sub, score, _near, _el, ttl in vis_candidates[:8]:
                print(f"  vis score={score:.3f} sub={is_sub} title={ttl[:80]}")
        for idx, (_vis, is_sub, score, _near, el, title_text) in enumerate(vis_candidates[:6]):
            try:
                if not is_sub and score < 0.75:
                    # too weak to trust; skip this try group
                    continue
                if click_video_element(el):
                    speak(f"Playing {title_text}")
                    return True
            except Exception:
                continue
        # If nothing clicked and this is the first pass, do NOT scroll yet; try top-ranked overall once
        if step == 0:
            candidates.sort(reverse=True)
            if DEBUG:
                print("[YouTube] Top overall candidates (no scroll):")
                for _vis, is_sub, score, _near, _el, ttl in candidates[:5]:
                    print(f"  any score={score:.3f} sub={is_sub} title={ttl[:80]}")
            for idx, (_vis, is_sub, score, _near, el, title_text) in enumerate(candidates[:3]):
                try:
                    if not is_sub and score < 0.80:
                        continue
                    if click_video_element(el):
                        speak(f"Playing {title_text}")
                        return True
                except Exception:
                    continue
        # Only scroll if there are no strong visible candidates
        strong_vis_exists = any((is_sub or score >= 0.9) for _vis, is_sub, score, _near, _el, _ttl in vis_candidates)
        if not strong_vis_exists:
            if DEBUG:
                print("[YouTube] No strong visible match, scrolling a bit...")
            driver.execute_script("window.scrollBy(0, Math.max(600, window.innerHeight));")
            time.sleep(0.5)
        else:
            if DEBUG:
                print("[YouTube] Strong visible candidates exist but click failed; not scrolling further.")
            break
    return False

def normalize_title(s: str) -> str:
    s = s.lower()
    # Keep unicode word characters to support non-Latin scripts, replace others with space
    s = re.sub(r"[^\w]+", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def ascii_projection(t: str) -> str:
    """Project text to ASCII-only tokens to better match mixed Hindi/English cases.
    Keeps a-z, 0-9 and spaces; collapses whitespace.
    """
    t = t.lower()
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def devnagari_projection(t: str) -> str:
    """Keep Devanagari characters and spaces only; collapse whitespace."""
    t = re.sub(r"[^\u0900-\u097F ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def normalize_number_words(t: str) -> str:
    """Convert common English number words to digits to help match S/E queries."""
    words = {
        'zero':'0','one':'1','two':'2','three':'3','four':'4','five':'5','six':'6','seven':'7','eight':'8','nine':'9','ten':'10',
        'eleven':'11','twelve':'12','thirteen':'13','fourteen':'14','fifteen':'15','sixteen':'16','seventeen':'17','eighteen':'18','nineteen':'19','twenty':'20'
    }
    def rep(m):
        w = m.group(0)
        return words.get(w, w)
    t = re.sub(r"\b(zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)\b", rep, t)
    # Normalize common patterns like 'season 3 episode 8' => 'season 3 ep 8'
    t = re.sub(r"\bepisode\b", "ep", t)
    return t

from youtube.dom import click_video_element as click_video_element

def click_home():
    return y_click_home()

def listen_command():
    return core_listen_command()

def execute_command(command):
    try:
        # Ensure we are on a YouTube tab before executing commands
        if not switch_to_youtube_tab():
            speak("I need to attach to your already open Chrome. Please launch Chrome with remote debugging and open YouTube, then try again.")
            if DEBUG:
                print("To start Chrome with remote debugging on Windows:")
                print("  chrome.exe --remote-debugging-port=9222 --user-data-dir=\\temp_chrome_debug")
                print("Then open https://www.youtube.com in that Chrome window.")
            return
        if "home" in command:
            ok = click_home()
            if ok:
                speak("Opened Home")
            else:
                speak("Couldn't open Home page")

        elif "history" in command:
            if y_click_history():
                speak("Opened History")
            else:
                speak("Couldn't open History")

        elif "watch later" in command or "watchlater" in command:
            if y_click_watch_later():
                speak("Opened Watch Later")
            else:
                speak("Couldn't open Watch Later")

        elif "video" in command or any(k in command for k in ["open", "play", "click"]):
            # Prefer title-based selection
            try:
                wait = WebDriverWait(get_driver(), 10)
                title = extract_title_from_command(command)
                if title:
                    # 1) Try ytInitialData-based direct open (no scrolling)
                    opened = match_and_open_by_initial_data(title)
                    if opened:
                        return
                    # 2) Fall back to DOM-based visible match with minimal scrolling
                    clicked = y_find_and_click_video_by_title(wait, title, max_scrolls=3)
                    if not clicked:
                        # Try searching and clicking from results
                        searched = y_search_and_click_title(title)
                        if not searched:
                            # OCR fallback on the current screen
                            ocr_clicked = y_ocr_find_and_click_video(title)
                            if not ocr_clicked:
                                if not TESSERACT_AVAILABLE:
                                    speak("OCR is not available. Please install Tesseract and pytesseract to enable visual detection.")
                                else:
                                    speak("I couldn't find that title.")
                    return
                # Fallback to number-based if user said like "open video 3"
                video_num = util_parse_video_index(command)
                if video_num <= 0:
                    speak("Please say the video title, for example: play 'lofi hip hop mix'.")
                    return
                # numeric fallback
                elements = load_until_index(wait, video_num, max_scrolls=10)
                if 0 < video_num <= len(elements):
                    target = elements[video_num - 1]
                    get_driver().execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
                    try:
                        target.click()
                    except (ElementClickInterceptedException, StaleElementReferenceException):
                        try:
                            ActionChains(get_driver()).move_to_element(target).click().perform()
                        except Exception:
                            get_driver().execute_script("arguments[0].click();", target)
                    speak(f"Playing video {video_num}")
                else:
                    speak("Video number out of range")
            except TimeoutException:
                speak("I couldn't find the videos on the page. Please make sure the Home page is visible.")
            except Exception:
                speak("Could not open the requested video.")
        else:
            speak("Command not recognized")

    except Exception as e:
        print("Error:", e)
        speak("Something went wrong")

# Main loop
while True:
    command = listen_command()
    if "exit" in command or "quit" in command:
        speak("Exiting now")
        break
    execute_command(command)

driver.quit()


def ocr_find_and_click_video(title: str) -> bool:
    """OCR fallback: detect visible text, pick the best matching line, then map to a clickable video element.
    Returns True if clicked.
    """
    if not TESSERACT_AVAILABLE:
        return False
    boxes = ocr_get_text_boxes()
    if not boxes:
        return False
    wanted = title.strip().lower()
    # Choose best OCR line
    best = None
    best_ratio = 0.0
    for b in boxes:
        t = b['text'].lower()
        r = difflib.SequenceMatcher(None, t, wanted).ratio()
        if wanted in t:
            r = max(r, 0.9)
        if r > best_ratio:
            best_ratio = r
            best = b
    if not best or best_ratio < 0.65:
        return False
    best_text = best['text']
    # Map to DOM anchor candidates and click the closest textual match
    try:
        candidates = driver.find_elements(By.CSS_SELECTOR, "ytd-video-renderer a#video-title, ytd-rich-item-renderer a#video-title, a#video-title, a[href*='watch']")
    except Exception:
        candidates = []
    best_el = None
    best_el_ratio = 0.0
    for el in candidates:
        try:
            if not el.is_displayed():
                continue
            txt = (el.get_attribute('title') or el.text or '').strip()
            if not txt:
                continue
            r1 = difflib.SequenceMatcher(None, txt.lower(), best_text.lower()).ratio()
            r2 = difflib.SequenceMatcher(None, txt.lower(), wanted).ratio()
            r = max(r1, r2)
            if wanted in txt.lower() or best_text.lower() in txt.lower():
                r = max(r, 0.9)
            if r > best_el_ratio:
                best_el_ratio = r
                best_el = el
        except Exception:
            continue
    if best_el and best_el_ratio >= 0.7:
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", best_el)
            try:
                best_el.click()
            except Exception:
                driver.execute_script("arguments[0].click();", best_el)
            speak(f"Playing {best_text}")
            return True
        except Exception:
            return False
    return False

def parse_video_index(command: str) -> int:
    """Return 1-based index parsed from phrases like 'video 2', 'second video', 'open third', etc. 0 if none."""
    words = command.lower().replace("-", " ").split()
    # Map common ordinal/cardinal words
    word_to_num = {
        "one": 1, "first": 1, "1st": 1,
        "two": 2, "second": 2, "2nd": 2,
        "three": 3, "third": 3, "3rd": 3,
        "four": 4, "fourth": 4, "4th": 4,
        "five": 5, "fifth": 5, "5th": 5,
        "six": 6, "sixth": 6, "6th": 6,
        "seven": 7, "seventh": 7, "7th": 7,
        "eight": 8, "eighth": 8, "8th": 8,
        "nine": 9, "ninth": 9, "9th": 9,
        "ten": 10, "tenth": 10, "10th": 10,
    }
    # 1) look for explicit pattern: 'video <n>'
    for i, w in enumerate(words[:-1]):
        if w == "video":
            nxt = words[i+1]
            if nxt.isdigit():
                return int(nxt)
            if nxt in word_to_num:
                return word_to_num[nxt]
    # 2) look for standalone ordinals/cardinals
    for w in words:
        if w.isdigit():
            return int(w)
        if w in word_to_num:
            return word_to_num[w]
    return 0

def load_until_index(wait: WebDriverWait, desired_index: int, max_scrolls: int = 8):
    """Scrolls the page to load more videos until desired index is available or max_scrolls reached.
    Returns the list of elements currently available.
    """
    last_len = 0
    for _ in range(max_scrolls):
        elements = get_home_video_elements(wait)
        if len(elements) >= desired_index and desired_index > 0:
            return elements
        # if not enough yet, scroll down to load more
        driver.execute_script("window.scrollBy(0, Math.max(600, window.innerHeight));")
        time.sleep(0.6)
        # Break if no growth in elements to avoid infinite loop
        if len(elements) == last_len:
            break
        last_len = len(elements)
    return get_home_video_elements(wait)

def extract_title_from_command(command: str) -> str:
    """Try to extract a video title phrase from the spoken command.
    Looks for quotes first, else takes words after play/open/click/watch.
    """
    cmd = command.strip().lower()
    # 1) If user spoke quotes: play "never gonna give you up"
    if '"' in command:
        parts = command.split('"')
        if len(parts) >= 3:
            return parts[1].strip()
    if "'" in command:
        parts = command.split("'")
        if len(parts) >= 3:
            return parts[1].strip()
    # 2) Take text after keywords
    keywords = ["play", "open", "click", "watch", "search"]
    for kw in keywords:
        if kw in cmd:
            after = command.lower().split(kw, 1)[1]
            # Remove common suffix words
            for rm in ["the", "video", "on youtube", "on you tube"]:
                after = after.replace(rm, "")
            title = after.strip(" :,-")
            # If looks like a pure number, it's not a title
            if title and not title.replace(" ", "").isdigit():
                return title
    return ""

def find_and_click_video_by_title(wait: WebDriverWait, wanted_title: str, max_scrolls: int = 3) -> bool:
    """Scroll and fuzzy-match against visible video titles, click best match if confident.
    Returns True if clicked.
    """
    wanted = wanted_title.strip()
    if not wanted:
        return False
    wanted_norm = normalize_title(wanted)
    for step in range(max_scrolls):
        pairs = get_video_title_elements(wait)
        if not pairs:
            # nothing on page; scroll a bit and retry
            driver.execute_script("window.scrollBy(0, Math.max(600, window.innerHeight));")
            time.sleep(0.4)
            continue
        # Fast path: if an EXACT or strong substring match is visible on screen, click it immediately without scrolling
        wanted_norm = normalize_title(wanted)
        viewport_h = driver.execute_script("return window.innerHeight;")
        for el, t in pairs:
            try:
                rect = driver.execute_script("const r=arguments[0].getBoundingClientRect(); return {top:r.top,bottom:r.bottom};", el)
                if not rect:
                    continue
                top = rect.get('top', 9999)
                bottom = rect.get('bottom', -9999)
                visible = (bottom > 0) and (top < (viewport_h * 1.05 if viewport_h else 10000))
                if not visible:
                    continue
                tl_norm = normalize_title((t or '').lower())
                if tl_norm == wanted_norm or wanted_norm in tl_norm:
                    if DEBUG:
                        print(f"[YouTube] Fast-path click: '{t}' matches '{wanted_title}'")
                    if click_video_element(el):
                        speak(f"Playing {t}")
                        return True
            except Exception:
                continue
        # Build candidate list
        candidates = []
        center = viewport_h / 2 if viewport_h else 400
        for el, t in pairs:
            try:
                rect = driver.execute_script("const r=arguments[0].getBoundingClientRect(); return {top:r.top,bottom:r.bottom};", el)
                top = rect.get('top', 9999) if rect else 9999
                near = abs(top - center)
                tl = t.lower()
                tl_norm = normalize_title(tl)
                ratio = difflib.SequenceMatcher(None, tl_norm, wanted_norm).ratio()
                substring = (wanted_norm in tl_norm)
                # Token-Jaccard to be robust against truncation/ellipsis
                wtoks = set(wanted_norm.split())
                ttoks = set(tl_norm.split())
                jacc = len(wtoks & ttoks) / max(1, len(wtoks | ttoks))
                if substring:
                    ratio = max(ratio, 0.9)
                score = max(ratio, jacc)
                bottom = rect.get('bottom', -9999) if rect else -9999
                visible = (bottom > 0) and (top < (viewport_h * 1.05 if viewport_h else 10000))
                candidates.append((visible, substring, score, -near, el, t))
            except Exception:
                continue
        # First, try clicking among VISIBLE items only without scrolling
        vis_candidates = [c for c in candidates if c[0]]
        vis_candidates.sort(reverse=True)  # (visible, substring, score, -near,...)
        if DEBUG:
            print("[YouTube] Visible candidates:")
            for _vis, is_sub, score, _near, _el, ttl in vis_candidates[:8]:
                print(f"  vis score={score:.3f} sub={is_sub} title={ttl[:80]}")
        for idx, (_vis, is_sub, score, _near, el, title_text) in enumerate(vis_candidates[:6]):
            try:
                if not is_sub and score < 0.75:
                    # too weak to trust; skip this try group
                    continue
                if click_video_element(el):
                    speak(f"Playing {title_text}")
                    return True
            except Exception:
                continue
        # If nothing clicked and this is the first pass, do NOT scroll yet; try top-ranked overall once
        if step == 0:
            candidates.sort(reverse=True)
            if DEBUG:
                print("[YouTube] Top overall candidates (no scroll):")
                for _vis, is_sub, score, _near, _el, ttl in candidates[:5]:
                    print(f"  any score={score:.3f} sub={is_sub} title={ttl[:80]}")
            for idx, (_vis, is_sub, score, _near, el, title_text) in enumerate(candidates[:3]):
                try:
                    if not is_sub and score < 0.80:
                        continue
                    if click_video_element(el):
                        speak(f"Playing {title_text}")
                        return True
                except Exception:
                    continue
        # Only scroll if there are no strong visible candidates
        strong_vis_exists = any((is_sub or score >= 0.9) for _vis, is_sub, score, _near, _el, _ttl in vis_candidates)
        if not strong_vis_exists:
            if DEBUG:
                print("[YouTube] No strong visible match, scrolling a bit...")
            driver.execute_script("window.scrollBy(0, Math.max(600, window.innerHeight));")
            time.sleep(0.5)
        else:
            if DEBUG:
                print("[YouTube] Strong visible candidates exist but click failed; not scrolling further.")
            break
    return False

def normalize_title(s: str) -> str:
    s = s.lower()
    # Keep unicode word characters to support non-Latin scripts, replace others with space
    s = re.sub(r"[^\w]+", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def ascii_projection(t: str) -> str:
    """Project text to ASCII-only tokens to better match mixed Hindi/English cases.
    Keeps a-z, 0-9 and spaces; collapses whitespace.
    """
    t = t.lower()
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def devnagari_projection(t: str) -> str:
    """Keep Devanagari characters and spaces only; collapse whitespace."""
    t = re.sub(r"[^\u0900-\u097F ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def normalize_number_words(t: str) -> str:
    """Convert common English number words to digits to help match S/E queries."""
    words = {
        'zero':'0','one':'1','two':'2','three':'3','four':'4','five':'5','six':'6','seven':'7','eight':'8','nine':'9','ten':'10',
        'eleven':'11','twelve':'12','thirteen':'13','fourteen':'14','fifteen':'15','sixteen':'16','seventeen':'17','eighteen':'18','nineteen':'19','twenty':'20'
    }
    def rep(m):
        w = m.group(0)
        return words.get(w, w)
    t = re.sub(r"\b(zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)\b", rep, t)
    # Normalize common patterns like 'season 3 episode 8' => 'season 3 ep 8'
    t = re.sub(r"\bepisode\b", "ep", t)
    return t

def click_video_element(el) -> bool:
    drv = get_driver()
    if not drv:
        return False
    try:
        anchor = drv.execute_script(
            """
            const e = arguments[0];
            const card = e.closest('ytd-rich-item-renderer') || e.closest('ytd-rich-grid-media') || e.closest('ytd-video-renderer') || e;
            const a = (card && card.querySelector('a#video-title, a#video-title-link, a[href*="watch"]')) || e.closest('a[href*="watch"]') || e;
            return a;
            """,
            el,
        )
        drv.execute_script("arguments[0].scrollIntoView({block: 'center'});", anchor)
        prev_url = ""
        try:
            prev_url = drv.current_url
        except Exception:
            pass
        clicked = False
        try:
            anchor.click()
            clicked = True
        except Exception:
            try:
                ActionChains(drv).move_to_element(anchor).click().perform()
                clicked = True
            except Exception:
                try:
                    drv.execute_script("arguments[0].click();", anchor)
                    clicked = True
                except Exception:
                    clicked = False
        if not clicked:
            return False
        try:
            WebDriverWait(drv, 6).until(
                lambda d: (
                    'watch' in (d.current_url or '').lower() or
                    len(d.find_elements(By.CSS_SELECTOR, 'ytd-watch-flexy, #movie_player, ytd-player')) > 0
                )
            )
            return True
        except Exception:
            try:
                if prev_url and drv.current_url != prev_url:
                    return True
            except Exception:
                pass
            try:
                href = anchor.get_attribute('href') or ''
                if href and 'watch' in href:
                    drv.get(href)
                    return True
            except Exception:
                pass
            return False
    except Exception:
        return False

def click_home() -> bool:
    drv = get_driver()
    if not drv:
        return False
    try:
        wait = WebDriverWait(drv, 5)
        try:
            logo = wait.until(lambda d: d.find_element(By.CSS_SELECTOR, "a#logo"))
            drv.execute_script("arguments[0].click();", logo)
            return True
        except Exception:
            pass
        try:
            home_link = wait.until(lambda d: d.find_element(By.CSS_SELECTOR, "ytd-guide-entry-renderer a[title='Home'], a[title='Home']"))
            drv.execute_script("arguments[0].scrollIntoView({block: 'center'});", home_link)
            try:
                home_link.click()
            except Exception:
                drv.execute_script("arguments[0].click();", home_link)
            return True
        except Exception:
            pass
    except Exception:
        pass
    try:
        drv.get("https://www.youtube.com/")
        return True
    except Exception:
        return False

def listen_command() -> str:
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
        try:
            command = recognizer.recognize_google(audio).lower()
            print(f"You said: {command}")
            return command
        except sr.UnknownValueError:
            speak("Sorry, I did not understand")
            return ""
        except sr.RequestError:
            speak("Speech service error")
            return ""

def execute_command(command):
    try:
        # Ensure we are on a YouTube tab before executing commands
        if not switch_to_youtube_tab():
            speak("I need to attach to your already open Chrome. Please launch Chrome with remote debugging and open YouTube, then try again.")
            if DEBUG:
                print("To start Chrome with remote debugging on Windows:")
                print("  chrome.exe --remote-debugging-port=9222 --user-data-dir=\\temp_chrome_debug")
                print("Then open https://www.youtube.com in that Chrome window.")
            return
        if "home" in command:
            ok = click_home()
            if ok:
                speak("Opened Home")
            else:
                speak("Couldn't open Home page")

        elif "history" in command:
            if click_history():
                speak("Opened History")
            else:
                speak("Couldn't open History")

        elif "watch later" in command or "watchlater" in command:
            if click_watch_later():
                speak("Opened Watch Later")
            else:
                speak("Couldn't open Watch Later")

        elif "video" in command or any(k in command for k in ["open", "play", "click"]):
            # Prefer title-based selection
            try:
                wait = WebDriverWait(get_driver(), 10)
                title = extract_title_from_command(command)
                if title:
                    # 1) Try ytInitialData-based direct open (no scrolling)
                    opened = match_and_open_by_initial_data(title)
                    if opened:
                        return
                    # 2) Fall back to DOM-based visible match with minimal scrolling
                    clicked = find_and_click_video_by_title(wait, title, max_scrolls=3)
                    if not clicked:
                        # Try searching and clicking from results
                        searched = search_and_click_title(title)
                        if not searched:
                            # OCR fallback on the current screen
                            ocr_clicked = ocr_find_and_click_video(title)
                            if not ocr_clicked:
                                if not TESSERACT_AVAILABLE:
                                    speak("OCR is not available. Please install Tesseract and pytesseract to enable visual detection.")
                                else:
                                    speak("I couldn't find that title.")
                    return
                # Fallback to number-based if user said like "open video 3"
                video_num = parse_video_index(command)
                if video_num <= 0:
                    speak("Please say the video title, for example: play 'lofi hip hop mix'.")
                    return
                # numeric fallback
                elements = load_until_index(wait, video_num, max_scrolls=10)
                if 0 < video_num <= len(elements):
                    target = elements[video_num - 1]
                    get_driver().execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
                    try:
                        target.click()
                    except (ElementClickInterceptedException, StaleElementReferenceException):
                        try:
                            ActionChains(get_driver()).move_to_element(target).click().perform()
                        except Exception:
                            get_driver().execute_script("arguments[0].click();", target)
                    speak(f"Playing video {video_num}")
                else:
                    speak("Video number out of range")
            except TimeoutException:
                speak("I couldn't find the videos on the page. Please make sure the Home page is visible.")
            except Exception:
                speak("Could not open the requested video.")
        else:
            speak("Command not recognized")

    except Exception as e:
        print("Error:", e)
        speak("Something went wrong")

# Main loop
while True:
    command = listen_command()
    if "exit" in command or "quit" in command:
        speak("Exiting now")
        break
    execute_command(command)

driver.quit()
