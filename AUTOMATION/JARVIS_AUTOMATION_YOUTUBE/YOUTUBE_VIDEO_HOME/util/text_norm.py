import re
import difflib

DEBUG = True


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
