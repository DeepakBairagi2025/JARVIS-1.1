import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

# Debug flag
DEBUG = True

# Driver path resolution
BASE_DIR = os.path.dirname(__file__)
# project root is YOUTUBE_VIDEO_HOME/, chromedriver expected under DATA/JARVIS_DRIVER
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, os.pardir))
DRIVER_PATH = os.path.join(PROJECT_ROOT, "DATA", "JARVIS_DRIVER", "chromedriver.exe")

# Global driver instance
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
    """Try to attach to an existing Chrome instance with remote debugging enabled."""
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


def create_driver():
    global _driver
    _driver = attach_existing_chrome()
    return _driver


def ensure_attached() -> bool:
    """Ensure global driver is attached and usable."""
    global _driver
    try:
        if _driver is not None:
            _ = _driver.window_handles
            return True
    except Exception:
        pass
    try:
        _driver = attach_existing_chrome()
        return _driver is not None
    except Exception:
        return False


def get_driver():
    """Return an attached webdriver instance or None."""
    global _driver
    if ensure_attached():
        return _driver
    return None


def switch_to_youtube_tab() -> bool:
    drv = get_driver()
    if not drv:
        return False
    try:
        for handle in drv.window_handles:
            try:
                drv.switch_to.window(handle)
                url = (drv.current_url or "").lower()
            except Exception:
                continue
            if "youtube.com" in url:
                return True
    except Exception:
        return False
    return False
