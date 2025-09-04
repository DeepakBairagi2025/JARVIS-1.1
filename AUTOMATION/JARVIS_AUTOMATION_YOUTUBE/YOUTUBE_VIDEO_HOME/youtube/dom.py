import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from core.driver_attach import get_driver

DEBUG = True

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
