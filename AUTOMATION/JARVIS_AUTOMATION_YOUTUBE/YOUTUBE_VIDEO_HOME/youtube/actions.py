import re
import time
import difflib
from io import BytesIO
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, StaleElementReferenceException

try:
    from PIL import Image
    import pytesseract
    TESSERACT_AVAILABLE = True
except Exception:
    TESSERACT_AVAILABLE = False

from core.driver_attach import get_driver
from core.speech import speak
from util.text_norm import (
    normalize_title,
    ascii_projection,
    devnagari_projection,
    normalize_number_words,
)
from youtube.dom import get_home_video_elements, get_video_title_elements, click_video_element

DEBUG = True


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


# OCR utilities

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
    from selenium.webdriver.common.by import By
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
