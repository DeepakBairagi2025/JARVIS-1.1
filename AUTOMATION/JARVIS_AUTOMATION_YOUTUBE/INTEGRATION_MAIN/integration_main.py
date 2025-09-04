import random
from AUTOMATION.JARVIS_AUTOMATION_YOUTUBE.ANOTHER_AUTOMATION_IN_YOUTUBE.Another_Automation_in_youtube import *
from AUTOMATION.JARVIS_AUTOMATION_YOUTUBE.CAPTION_IN_VIDEO.caption_in_video import *
from AUTOMATION.JARVIS_AUTOMATION_YOUTUBE.MANUAL_SEARCH_IN_YOUTUBE.manual_search_in_youtube import search_manual
from AUTOMATION.JARVIS_AUTOMATION_YOUTUBE.PLAY_MUSIC_IN_YOUTUBE.play_music_in_youtube import play_music_on_youtube
from AUTOMATION.JARVIS_AUTOMATION_YOUTUBE.PLAY_PAUSE_VIDEO_IN_YOUTUBE.play_pause_video_in_youtube import stop, play
from AUTOMATION.JARVIS_AUTOMATION_YOUTUBE.SEARCH_IN_YOUTUBE.search_in_youtube import youtube_search
from DATA.JARVIS_DLG_DATASET.DLG import x, q, x1, x2
from FUNCTION.JARVIS_LISTEN.listen import listen
from FUNCTION.JARVIS_SPEAK.speak import speak
from ...JARVIS_AUTOMATION_GOOGLE.OPEN_WEBSITE.open_website import openweb


def youtube_cmd(text):
    if "open youtube website" in text:
        openweb("youtube")
    elif text in x:
        a = random.choice(q)
        speak(a)
        text = listen().lower()
        play_music_on_youtube(text)

    elif text in x1:
        stop()
    elif text in x2:
        play()
    elif text == "increase volume":
        volume_up()
    elif text == "decrease volume":
        volume_down()
    elif text == "seek forward":
        seek_forward()

    elif text == "seek backward":
        seek_backward()

    elif text == "seek forward 10 seconds":
        seek_forward_10s()

    elif text == "seek backward 10 seconds":
        seek_backward_10s()

    elif text == "seek backward frame":
        seek_backward_frame()

    elif text == "seek forward frame":
        seek_forward_frame()

    elif text == "seel to beginning":
        seek_to_beginning()

    elif text == "seek end":
        seek_to_end()

    elif text == "seek to previous chapter":
        seek_to_previous_chapter()

    elif text == "seek to next chapter":
        seek_to_next_chapter()

    elif text == "decrease playback speed":
        decrease_playback_speed()

    elif text == "increase playback speed":
        increase_playback_speed()

    elif text == "move to next video ":
        move_to_next_video()

    elif text == "move to previous video ":
        move_to_previous_video()

    elif text == "toggle subtitles":
        toggle_subtitles()

    elif text == "increase font size":
        increase_font_size()

    elif text == "decrease font size":
        decrease_font_size()

    elif text == "rotate text opacity":
        rotate_text_opacity()

    elif text == "rotate window opacity":
        rotate_window_opacity()

    elif text == "pan up":
        pan_up()

    elif text == "pan down":
        pan_down()

    elif text == "pan left":
        pan_left()

    elif text == "pan right":
        pan_right()

    elif text == "zoom in":
        zoom_in()

    elif text == "zoom out":
        zoom_out()

    elif text == "go to search box":
        go_to_search_box()

    elif text == "toggle play pause":
        toggle_play_pause()

    elif text == "toggle mute unmute":
        toggle_mute_unmute()

    elif text == "toggle full screen":
        toggle_full_screen()

    elif text == "seek to specific point":
        seek_to_specific_point()

    elif text == "toggle theater mode":
        toggle_theater_mode()

    elif text == "toggle miniplayer mode":
        toggle_miniplayer_mode()

    elif text == "exit full screen":
        exit_full_screen()

    elif text == "toggle party mode":
        toggle_party_mode()

    elif text == "navigate forward":
        navigate_forward()

    elif text == "navigate backward":
        navigate_backward()

    elif ("search in youtube" in text) or ("search on youtube" in text):
        # Extract query by removing trigger phrases anywhere in the text
        text = text.replace("search in youtube", "")
        text = text.replace("search on youtube", "")
        # Also remove a leading 'search ' if spoken like 'search <query> on youtube'
        if text.startswith("search "):
            text = text[7:]
        text = text.strip()
        youtube_search(text)

    elif ("search in current youtube window" in text) or ("search on current youtube window" in text) or ("search current youtube window" in text):
        # Extract query by removing trigger phrases and trimming
        text = text.replace("search in current youtube window", "")
        text = text.replace("search on current youtube window", "")
        text = text.replace("search current youtube window", "")
        if text.startswith("search "):
            text = text[7:]
        text = text.strip()
        search_manual(text)

    else:
        pass

