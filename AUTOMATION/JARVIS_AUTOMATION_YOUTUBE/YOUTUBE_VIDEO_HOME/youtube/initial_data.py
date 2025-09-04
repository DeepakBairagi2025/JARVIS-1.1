import json
import re
import time
import difflib
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from core.driver_attach import get_driver
from core.speech import speak
from util.text_norm import (
    normalize_title,
    ascii_projection,
    devnagari_projection,
    normalize_number_words,
)

DEBUG = True


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
        from youtube.dom import get_visible_home_candidates
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
