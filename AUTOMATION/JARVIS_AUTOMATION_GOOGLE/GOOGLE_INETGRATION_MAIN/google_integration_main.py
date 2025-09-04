from AUTOMATION.JARVIS_AUTOMATION_GOOGLE.OPEN_WEBSITE.open_website import *
from AUTOMATION.JARVIS_AUTOMATION_GOOGLE.SCROLL_AUTOMATION.scroll_automation import *
from AUTOMATION.JARVIS_AUTOMATION_GOOGLE.SEARCH_IN_GOOGLE.search_in_google import *
from AUTOMATION.JARVIS_AUTOMATION_GOOGLE.TAB_AUTOMATION.tab_automation import *
from AUTOMATION.COMMON_AUTOMATION.COMMON_OPEN.open import *

def google_cmd(text):
    # Handle specific browser 'open ...' commands first
    if "open new tab" in text:
        open_new_tab()
    elif "open private window" in text:
        open_private_window()
    elif "open browser menu" in text:
        open_browser_menu()
    elif "open history" in text:
        open_history()
    elif "open bookmarks" in text:
        open_bookmarks()
    elif "open dev tools" in text:
        open_dev_tools()
    elif ("close tab" in text) or ("close this tab" in text) or ("close current tab" in text) or ("close active tab" in text):
        close_tab()
    # Generic 'open' last, to avoid Windows search being triggered for specific commands
    elif "open" in text:
        if "website" in text or "site" in text:
            text = text.replace("open", "")
            text = text.replace("website", "")
            text = text.replace("site", "")
            text = text.strip()
            openweb(text)
        else:
            text = text.replace("open","")
            text = text.strip()
            if text == "":
                pass
            else:
                open(text)
    elif "scroll up" in text:
        scroll_up()

    elif "scroll down" in text:
        scroll_down()

    elif "scroll to top" in text:
        scroll_to_top()

    elif "scroll to bottom" in text:
        scroll_to_bottom()

    elif text.endswith("search in google") or text.endswith("search in google"):
        text = text.replace("search in google", "")
        text = text.replace("search on google", "")
        search_google(text)

    elif "close tab" in text:
        close_tab()

    elif "open browser menu" in text:
        open_browser_menu()

    elif "zoom in" in text:
        zoom_in()

    elif "zoom out" in text:
        zoom_out()

    elif "refresh page" in text:
        refresh_page()

    elif "switch to next tab" in text:
        switch_to_next_tab()

    elif "switch to previous tab" in text:
        switch_to_previous_tab()

    elif "open history" in text:
        open_history()

    elif "open bookmarks" in text:
        open_bookmarks()

    elif "go back" in text:
        go_back()

    elif "go forward" in text:
        go_forward()

    elif "open dev tools" in text:
        open_dev_tools()

    elif "toggle full screen" in text:
        toggle_full_screen()

    elif "open private window" in text:
        open_private_window()

    elif "open new tab" in text:
        open_new_tab()

    else:
        pass