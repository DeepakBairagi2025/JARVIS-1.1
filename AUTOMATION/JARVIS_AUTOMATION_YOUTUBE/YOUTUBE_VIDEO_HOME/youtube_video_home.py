# Monolithic YouTube automation script
# Consolidated from core/, util/, youtube/ modules and youtube_test.py
# Runs standalone and auto-opens YouTube on start

import os
import re
import json
import time
import difflib
from io import BytesIO

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
)

# Optional OCR imports
try:
    from PIL import Image  # type: ignore
    import pytesseract  # type: ignore
    TESSERACT_AVAILABLE = True
except Exception:
    TESSERACT_AVAILABLE = False

# TTS
import pyttsx3

# STT
import speech_recognition as sr


# =============================
# Global flags
# =============================
DEBUG = True


# =============================
# TTS
# =============================
_engine = pyttsx3.init()

def speak(text: str) -> None:
    try:
        _engine.say(text)
        _engine.runAndWait()
    except Exception:
        if DEBUG:
            print(f"[TTS] Failed to speak: {text}")


# =============================
# STT
# =============================
_recognizer = sr.Recognizer()

def listen_command() -> str:
    try:
        with sr.Microphone() as source:
            print("Listening...")
            _recognizer.adjust_for_ambient_noise(source)
            audio = _recognizer.listen(source)
            try:
                command = _recognizer.recognize_google(audio).lower()
                print(f"You said: {command}")
                return command
            except sr.UnknownValueError:
                speak("Sorry, I did not understand")
                return ""
            except sr.RequestError:
                speak("Speech service error")
                return ""
    except Exception as e:
        if DEBUG:
            print(f"[STT] Microphone/listen error: {e}")
        return ""


# =============================
# WebDriver attach/launch
# =============================
BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, os.pardir))
DRIVER_PATH = os.path.join(PROJECT_ROOT, "DATA", "JARVIS_DRIVER", "chromedriver.exe")
_driver = None

def build_options(debugger_address: str | None = None):
    opts = webdriver.ChromeOptions()
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-infobars")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"]) 
    opts.add_experimental_option("useAutomationExtension", False)
    if debugger_address:
        opts.add_experimental_option("debuggerAddress", debugger_address)
    return opts

def attach_existing_chrome():
    addresses = []
    env_addr = os.environ.get("DEBUGGER_ADDRESS", "").strip()
    if env_addr:
        addresses.append(env_addr)
    for port in (9222, 9223, 9333):
        addresses.append(f"127.0.0.1:{port}")
        addresses.append(f"localhost:{port}")
    for addr in addresses:
        try:
            opts = build_options(debugger_address=addr)
            if os.path.isfile(DRIVER_PATH):
                svc = Service(DRIVER_PATH)
                drv = webdriver.Chrome(service=svc, options=opts)
            else:
                drv = webdriver.Chrome(options=opts)
            _ = drv.window_handles
            if DEBUG:
                print(f"[YouTube] Attached to Chrome at {addr}")
            return drv
        except Exception:
            continue
    return None

def launch_new_chrome():
    try:
        opts = build_options()
        if os.path.isfile(DRIVER_PATH):
            svc = Service(DRIVER_PATH)
            drv = webdriver.Chrome(service=svc, options=opts)
        else:
            drv = webdriver.Chrome(options=opts)
        if DEBUG:
            print("[YouTube] Launched new Chrome instance")
        return drv
    except Exception as e:
        if DEBUG:
            print(f"[YouTube] Launch Chrome failed: {e}")
        return None

def ensure_attached() -> bool:
    global _driver
    try:
        if _driver is not None:
            _ = _driver.window_handles
            return True
    except Exception:
        pass
    try:
        _driver = attach_existing_chrome()
        if _driver is None:
            _driver = launch_new_chrome()
        return _driver is not None
    except Exception:
        return False

def get_driver():
    global _driver
    if ensure_attached():
        return _driver
    return None


# =============================
# Text normalization utilities
# =============================

def normalize_title(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^\w]+", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def ascii_projection(t: str) -> str:
    t = (t or "").lower()
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def devnagari_projection(t: str) -> str:
    t = re.sub(r"[^\u0900-\u097F ]+", " ", (t or ""))
    return re.sub(r"\s+", " ", t).strip()

def normalize_number_words(t: str) -> str:
    words = {
        'zero': '0','one': '1','two': '2','three': '3','four': '4','five': '5','six': '6','seven': '7','eight': '8','nine': '9','ten': '10',
        'eleven': '11','twelve': '12','thirteen': '13','fourteen': '14','fifteen': '15','sixteen': '16','seventeen': '17','eighteen': '18','nineteen': '19','twenty': '20'
    }
    def rep(m):
        w = m.group(0)
        return words.get(w, w)
    t = re.sub(r"\b(zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)\b", rep, (t or ""))
    t = re.sub(r"\bepisode\b", "ep", t)
    return t

def parse_video_index(command: str) -> int:
    words = (command or "").lower().replace("-", " ").split()
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
    for i, w in enumerate(words[:-1]):
        if w == "video":
            nxt = words[i+1]
            if nxt.isdigit():
                return int(nxt)
            if nxt in word_to_num:
                return word_to_num[nxt]
    for w in words:
        if w.isdigit():
            return int(w)
        if w in word_to_num:
            return word_to_num[w]
    return 0

def extract_title_from_command(command: str) -> str:
    cmd = (command or "").strip().lower()
    if '"' in command:
        parts = command.split('"')
        if len(parts) >= 3:
            return parts[1].strip()
    if "'" in command:
        parts = command.split("'")
        if len(parts) >= 3:
            return parts[1].strip()
    keywords = ["play", "open", "click", "watch", "search"]
    for kw in keywords:
        if kw in cmd:
            after = command.lower().split(kw, 1)[1]
            for rm in ["the", "video", "on youtube", "on you tube"]:
                after = after.replace(rm, "")
            title = after.strip(" :,-")
            if title and not title.replace(" ", "").isdigit():
                return title
    return ""


# =============================
# DOM helpers
# =============================

def get_home_video_elements(wait: WebDriverWait):
    drv = get_driver()
    if not drv:
        return []
    try:
        wait.until(lambda d: True)
    except Exception:
        pass
    selectors = [
        "ytd-rich-grid-media a#video-title",
        "ytd-rich-item-renderer a#video-title",
        "a#video-title-link",
        "ytd-rich-item-renderer a#thumbnail[href*='watch']",
        "a#thumbnail[href*='watch']",
    ]
    elements = []
    seen = set()
    for sel in selectors:
        try:
            els = drv.find_elements(By.CSS_SELECTOR, sel)
        except Exception:
            continue
        for el in els:
            try:
                if not el.is_displayed():
                    continue
                key = el.get_attribute("href") or el.get_attribute("id") or str(el.id)
                if key in seen:
                    continue
                ancestor_html = drv.execute_script("return arguments[0].closest('ytd-rich-shelf-renderer')?.outerHTML || '';", el)
                if ancestor_html and 'shorts' in ancestor_html.lower():
                    continue
                seen.add(key)
                elements.append(el)
            except Exception:
                continue
    return elements


def get_video_title_elements(wait: WebDriverWait):
    drv = get_driver()
    if not drv:
        return []
    pairs = []
    selectors = [
        "ytd-rich-grid-media a#video-title",
        "ytd-rich-item-renderer a#video-title",
        "a#video-title-link",
        "ytd-rich-item-renderer a#thumbnail[href*='watch']",
        "a#thumbnail[href*='watch']",
        "ytd-video-renderer a#video-title",
    ]
    seen = set()
    for sel in selectors:
        try:
            els = drv.find_elements(By.CSS_SELECTOR, sel)
        except Exception:
            continue
        for el in els:
            try:
                if not el.is_displayed():
                    continue
                key = el.get_attribute("href") or el.get_attribute("id") or str(el.id)
                if key in seen:
                    continue
                ancestor_html = drv.execute_script("return arguments[0].closest('ytd-rich-shelf-renderer')?.outerHTML || '';", el)
                if ancestor_html and 'shorts' in ancestor_html.lower():
                    continue
                title = (el.get_attribute("title") or el.text or "").strip()
                if not title:
                    title = drv.execute_script(
                        "return (arguments[0].closest('ytd-rich-item-renderer') || arguments[0].closest('ytd-rich-grid-media') || arguments[0].closest('ytd-video-renderer'))?.querySelector('#video-title')?.innerText || '';",
                        el,
                    ).strip()
                if title:
                    seen.add(key)
                    pairs.append((el, title))
            except Exception:
                continue
    return pairs


def get_visible_home_candidates():
    drv = get_driver()
    if not drv:
        return []
    sels = [
        "ytd-rich-grid-media a#video-title, ytd-rich-item-renderer a#video-title, a#video-title",
        "ytd-rich-grid-media a[href*='watch'], ytd-rich-item-renderer a[href*='watch']",
    ]
    seen = set()
    out = []
    for sel in sels:
        try:
            els = drv.find_elements(By.CSS_SELECTOR, sel)
        except Exception:
            continue
        for el in els:
            try:
                if not el.is_displayed():
                    continue
                try:
                    is_ad = drv.execute_script(
                        """
                        const e = arguments[0];
                        const ad = e.closest('ytd-ad-slot-renderer') || e.closest('ytd-promoted-video-renderer');
                        if (ad) return true;
                        const row = e.closest('ytd-rich-item-renderer');
                        if (row) {
                          const lab = row.querySelector('#badge-style-type-ad, ytd-badge-supported-renderer[icon][type="BADGE_STYLE_TYPE_AD"]');
                          if (lab) return true;
                          const s = row.innerText || '';
                          if (/\bSponsored\b/i.test(s)) return true;
                        }
                        return false;
                        """,
                        el,
                    )
                    if is_ad:
                        continue
                except Exception:
                    pass
                href = el.get_attribute('href') or ''
                js = (
                    "const e=arguments[0];"
                    "const card=e.closest('ytd-rich-item-renderer')||e.closest('ytd-rich-grid-media')||e.closest('ytd-video-renderer')||null;"
                    "let t='';"
                    "if(card){const tEl=card.querySelector('#video-title'); if(tEl){t=tEl.getAttribute('title')||tEl.textContent||'';}}"
                    "if(!t){t=e.getAttribute('title')||e.getAttribute('aria-label')||e.textContent||'';}"
                    "t=t.trim(); return t;"
                )
                title = drv.execute_script(js, el) or ''
                title = str(title).strip()
                if not title:
                    continue
                title = re.sub(r"\b\d+\s*(hours?|hour|hrs?|minutes?|minute|min)\b.*$", "", title, flags=re.IGNORECASE).strip()
                title = re.sub(r"\b\d+\s*(घंटे|घंटा|मिनट|सेकंड)\b.*$", "", title).strip()
                if re.match(r"^\s*\d{1,2}:\d{2}(?::\d{2})?\s*$", title):
                    continue
                key = href or title
                if key in seen:
                    continue
                seen.add(key)
                vid = None
                if 'watch' in href:
                    m = re.search(r"[?&]v=([\w-]{6,})", href)
                    if m:
                        vid = m.group(1)
                out.append({'title': title, 'videoId': vid, 'href': href or None, 'source': 'dom'})
            except Exception:
                continue
    if DEBUG and out:
        try:
            print("[YouTube] Visible titles (sample):", [c['title'] for c in out[:6]])
        except Exception:
            pass
    return out


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
                from selenium.webdriver import ActionChains
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


# =============================
# ytInitialData helpers
# =============================

def get_yt_initial_data():
    drv = get_driver()
    if not drv:
        return None
    try:
        data_str = drv.execute_script(
            """
            try {
              const w = window;
              const pick = () => {
                if (w.ytInitialData) return w.ytInitialData;
                if (w.ytcfg && typeof w.ytcfg.get === 'function') {
                  const d = w.ytcfg.get('INITIAL_DATA');
                  if (d) return d;
                }
                if (w.yt && w.yt.config_ && w.yt.config_.INITIAL_DATA) return w.yt.config_.INITIAL_DATA;
                return null;
              };
              const d = pick();
              return d ? JSON.stringify(d) : null;
            } catch (e) { return null; }
            """
        )
        if not data_str:
            return None
        return json.loads(data_str)
    except Exception:
        return None


def iter_all_video_renderers(initial_data):
    def walk(node):
        if isinstance(node, dict):
            for key in ('videoRenderer', 'gridVideoRenderer', 'compactVideoRenderer'):
                if key in node and isinstance(node[key], dict):
                    yield node[key]
            for v in node.values():
                yield from walk(v)
        elif isinstance(node, list):
            for item in node:
                yield from walk(item)
    try:
        yield from walk(initial_data)
    except Exception:
        return


def extract_title_from_renderer(vr: dict) -> str:
    t = vr.get('title', {})
    txt = t.get('simpleText')
    if txt:
        return str(txt).strip()
    runs = t.get('runs') or []
    if runs and isinstance(runs, list):
        return ' '.join([str(r.get('text', '')).strip() for r in runs if r and r.get('text')]).strip()
    acc = vr.get('accessibility', {}).get('accessibilityData', {}).get('label')
    if acc:
        return str(acc).strip()
    return ''


def get_initial_feed_candidates(max_wait_sec: float = 2.5, poll: float = 0.25):
    drv = get_driver()
    if not drv:
        return []
    deadline = time.time() + max_wait_sec
    seen = set()
    best_out = []
    while time.time() < deadline:
        out = []
        data = get_yt_initial_data()
        if data:
            for vr in iter_all_video_renderers(data):
                try:
                    vid = vr.get('videoId')
                    if not vid or vid in seen:
                        continue
                    title = extract_title_from_renderer(vr)
                    if not title:
                        continue
                    if 'shorts' in json.dumps(vr).lower():
                        continue
                    seen.add(vid)
                    out.append({'videoId': vid, 'title': title})
                except Exception:
                    continue
        if out:
            best_out = out
            break
        time.sleep(poll)
    if DEBUG:
        print(f"[YouTube] Initial feed candidates: {len(best_out)}")
    return best_out


def match_and_open_by_initial_data(spoken_title: str) -> bool:
    drv = get_driver()
    if not drv:
        return False
    spoken = (spoken_title or '').strip()
    if not spoken:
        return False
    wanted_norm = normalize_title(spoken)
    candidates = get_initial_feed_candidates()
    if not candidates:
        # Fallback: harvest visible anchors on Home without scrolling
        candidates = get_visible_home_candidates()
        if DEBUG:
            print(f"[YouTube] Visible DOM candidates: {len(candidates)}")
        if not candidates:
            return False
    wanted_norm = normalize_number_words(wanted_norm)
    ranked = []
    for c in candidates:
        t = c['title']
        tl = t.lower()
        tl_norm = normalize_title(normalize_number_words(tl))
        tl_ascii = ascii_projection(tl)
        tl_dev = devnagari_projection(t)
        wanted_ascii = ascii_projection(wanted_norm)
        wanted_dev = devnagari_projection(spoken)
        ratio = difflib.SequenceMatcher(None, tl_norm, wanted_norm).ratio()
        wtoks = set(wanted_norm.split())
        ttoks = set(tl_norm.split())
        jacc = len(wtoks & ttoks) / max(1, len(wtoks | ttoks))
        score = max(ratio, jacc)
        if wanted_norm and wanted_norm in tl_norm:
            score = max(score, 0.92)
        if wanted_ascii and wanted_ascii in tl_ascii:
            score = max(score, 0.90)
        if wanted_dev and tl_dev:
            dtoks = set(tl_dev.split())
            wtoks_dev = set(wanted_dev.split())
            if dtoks and wtoks_dev:
                dj = len(dtoks & wtoks_dev) / max(1, len(dtoks | wtoks_dev))
                if dj >= 0.25:
                    score = max(score, 0.88)
        if c.get('source') == 'dom':
            score += 0.02
        ranked.append((score, c))
    ranked.sort(reverse=True, key=lambda x: x[0])
    best = ranked[0][1] if ranked else None
    best_score = ranked[0][0] if ranked else 0.0
    second_score = ranked[1][0] if len(ranked) > 1 else 0.0
    dom_best = None
    for s, c in ranked[:6]:
        if c.get('source') == 'dom':
            dom_best = (s, c)
            break
    if dom_best and (best is not None) and (dom_best[0] >= best_score - 0.05):
        best_score, best = dom_best
    if DEBUG and ranked:
        try:
            top3 = [(f"{s:.3f}", r['title'][:80]) for s, r in ranked[:3]]
            print("[YouTube] Top matches:", top3)
        except Exception:
            pass
        print(f"[YouTube] Best initial-data match: score={best_score:.3f} title={best['title'][:120]}")
    ascii_best = ascii_projection(best['title']) if best else ''
    is_dom = bool(best and best.get('source') == 'dom')
    if best and (
        best_score >= 0.60
        or normalize_title(best['title']) == wanted_norm
        or (wanted_norm in normalize_title(best['title']))
        or (ascii_projection(wanted_norm) and ascii_projection(wanted_norm) in ascii_best)
        or (best_score >= 0.40 and (best_score - second_score) >= 0.12)
        or (is_dom and best_score >= 0.33)
    ):
        try:
            if best.get('videoId'):
                url = f"https://www.youtube.com/watch?v={best['videoId']}"
            else:
                url = best.get('href')
            if not url:
                return False
            if url.startswith('/'):
                url = 'https://www.youtube.com' + url
            if DEBUG:
                print(f"[YouTube] Navigating to: {url}")
            drv.get(url)
            speak(f"Playing {best['title']}")
            return True
        except Exception:
            return False
    return False


# =============================
# High-level actions
# =============================

def click_history() -> bool:
    drv = get_driver()
    if not drv:
        return False
    try:
        wait = WebDriverWait(drv, 8)
        el = wait.until(lambda d: d.find_element(By.CSS_SELECTOR, "a[title='History']"))
        drv.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
        try:
            el.click()
        except Exception:
            drv.execute_script("arguments[0].click();", el)
        return True
    except Exception:
        pass
    try:
        drv.get("https://www.youtube.com/feed/history")
        return True
    except Exception:
        return False


def click_watch_later() -> bool:
    drv = get_driver()
    if not drv:
        return False
    try:
        wait = WebDriverWait(drv, 8)
        el = wait.until(lambda d: d.find_element(By.CSS_SELECTOR, "a[title='Watch later']"))
        drv.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
        try:
            el.click()
        except Exception:
            drv.execute_script("arguments[0].click();", el)
        return True
    except Exception:
        pass
    try:
        drv.get("https://www.youtube.com/playlist?list=WL")
        return True
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


def find_and_click_video_by_title(wait: WebDriverWait, wanted_title: str, max_scrolls: int = 3) -> bool:
    drv = get_driver()
    if not drv:
        return False
    wanted = (wanted_title or '').strip()
    if not wanted:
        return False
    wanted_norm = normalize_title(wanted)
    for step in range(max_scrolls):
        pairs = get_video_title_elements(wait)
        if not pairs:
            drv.execute_script("window.scrollBy(0, Math.max(600, window.innerHeight));")
            time.sleep(0.4)
            continue
        wanted_norm = normalize_title(wanted)
        viewport_h = drv.execute_script("return window.innerHeight;")
        for el, t in pairs:
            try:
                rect = drv.execute_script("const r=arguments[0].getBoundingClientRect(); return {top:r.top,bottom:r.bottom};", el)
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
        candidates = []
        center = viewport_h / 2 if viewport_h else 400
        for el, t in pairs:
            try:
                rect = drv.execute_script("const r=arguments[0].getBoundingClientRect(); return {top:r.top,bottom:r.bottom};", el)
                top = rect.get('top', 9999) if rect else 9999
                near = abs(top - center)
                tl = t.lower()
                tl_norm = normalize_title(tl)
                ratio = difflib.SequenceMatcher(None, tl_norm, wanted_norm).ratio()
                substring = (wanted_norm in tl_norm)
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
        vis_candidates = [c for c in candidates if c[0]]
        vis_candidates.sort(reverse=True)
        if DEBUG:
            print("[YouTube] Visible candidates:")
            for _vis, is_sub, score, _near, _el, ttl in vis_candidates[:8]:
                print(f"  vis score={score:.3f} sub={is_sub} title={ttl[:80]}")
        for idx, (_vis, is_sub, score, _near, el, title_text) in enumerate(vis_candidates[:6]):
            try:
                if not is_sub and score < 0.75:
                    continue
                if click_video_element(el):
                    speak(f"Playing {title_text}")
                    return True
            except Exception:
                continue
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
        strong_vis_exists = any((is_sub or score >= 0.9) for _vis, is_sub, score, _near, _el, _ttl in vis_candidates)
        if not strong_vis_exists:
            if DEBUG:
                print("[YouTube] No strong visible match, scrolling a bit...")
            drv.execute_script("window.scrollBy(0, Math.max(600, window.innerHeight));")
            time.sleep(0.5)
        else:
            if DEBUG:
                print("[YouTube] Strong visible candidates exist but click failed; not scrolling further.")
            break
    return False


def search_and_click_title(title: str) -> bool:
    drv = get_driver()
    if not drv:
        return False
    try:
        wait = WebDriverWait(drv, 10)
        box = wait.until(lambda d: d.find_element(By.CSS_SELECTOR, "input#search"))
        drv.execute_script("arguments[0].value='';", box)
        box.clear()
        box.send_keys(title)
        try:
            btn = drv.find_element(By.CSS_SELECTOR, "button#search-icon-legacy")
            drv.execute_script("arguments[0].click();", btn)
        except Exception:
            box.submit()
        wait.until(lambda d: d.find_element(By.CSS_SELECTOR, "ytd-video-renderer a#video-title"))
        return find_and_click_video_by_title(wait, title, max_scrolls=1)
    except Exception:
        return False


# =============================
# OCR fallback
# =============================

def _ocr_get_text_boxes():
    if not TESSERACT_AVAILABLE:
        return []
    drv = get_driver()
    if not drv:
        return []
    try:
        png = drv.get_screenshot_as_png()
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
    if not TESSERACT_AVAILABLE:
        return False
    boxes = _ocr_get_text_boxes()
    if not boxes:
        return False
    wanted = (title or '').strip().lower()
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
    drv = get_driver()
    if not drv:
        return False
    try:
        candidates = drv.find_elements(By.CSS_SELECTOR, "ytd-video-renderer a#video-title, ytd-rich-item-renderer a#video-title, a#video-title, a[href*='watch']")
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
            drv.execute_script("arguments[0].scrollIntoView({block: 'center'});", best_el)
            try:
                best_el.click()
            except Exception:
                drv.execute_script("arguments[0].click();", best_el)
            speak(f"Playing {best_text}")
            return True
        except Exception:
            return False
    return False


# =============================
# Command execution
# =============================

def execute_command(command: str) -> None:
    cmd = (command or '').strip().lower()
    if not cmd:
        return

    # Simple navigations
    if any(kw in cmd for kw in ["go home", "open home", "youtube home", "home page"]):
        if click_home():
            speak("Opened YouTube Home")
        else:
            speak("Unable to open Home")
        return

    if "history" in cmd:
        if click_history():
            speak("Opened history")
        else:
            speak("Unable to open history")
        return

    if "watch later" in cmd or "watchlater" in cmd:
        if click_watch_later():
            speak("Opened Watch later")
        else:
            speak("Unable to open Watch later")
        return

    # Search
    if "search" in cmd:
        title = extract_title_from_command(command)
        if not title:
            speak("Tell me what to search")
            return
        if search_and_click_title(title):
            return
        if DEBUG:
            print("[YouTube] Search didn't click any result")
        return

    # Play/open video by title on Home
    if any(kw in cmd for kw in ["play", "open", "watch", "click"]):
        title = extract_title_from_command(command)
        if title:
            # Try initial-data first
            if match_and_open_by_initial_data(title):
                return
            # then try visible DOM scan
            drv = get_driver()
            if not drv:
                speak("Driver not ready")
                return
            wait = WebDriverWait(drv, 10)
            if find_and_click_video_by_title(wait, title, max_scrolls=2):
                return
            if TESSERACT_AVAILABLE and ocr_find_and_click_video(title):
                return
            speak("Couldn't find the requested video")
            return

    # Click by index e.g., "open video 3"
    idx = parse_video_index(command)
    if idx > 0:
        drv = get_driver()
        if not drv:
            return
        wait = WebDriverWait(drv, 8)
        pairs = get_video_title_elements(wait)
        if pairs and 1 <= idx <= len(pairs):
            el, t = pairs[idx-1]
            if click_video_element(el):
                speak(f"Playing {t}")
                return
        speak("Couldn't click the requested number")
        return

    if DEBUG:
        print(f"[YouTube] Unrecognized command: {command}")


# =============================
# Main
# =============================
if __name__ == "__main__":
    drv = get_driver()
    if not drv:
        print("[YouTube] Could not start/attach Chrome. Exiting.")
        raise SystemExit(1)

    # Auto open YouTube Home
    try:
        if not (drv.current_url and 'youtube.com' in drv.current_url.lower()):
            drv.get("https://www.youtube.com/")
    except Exception:
        try:
            drv.get("https://www.youtube.com/")
        except Exception:
            pass

    speak("YouTube ready. Say a command or say exit to quit.")

    try:
        while True:
            command = listen_command()
            if not command:
                continue
            if "exit" in command or "quit" in command:
                speak("Exiting now")
                break
            execute_command(command)
    finally:
        try:
            drv.quit()
        except Exception:
            pass
