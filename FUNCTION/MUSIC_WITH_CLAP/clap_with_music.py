import os
import random
import pygame
from pygame import mixer
from FUNCTION.CLAP_DETECTOR.clapd import *

def play_random_music(folder_path):
    music_files = [file for file in os.listdir(folder_path) if file.endswith((".mp3", ".wav", ".ogg"))]

    if not music_files:
        print("No music files found in the specified folder.")
        return

    selected_music = random.choice(music_files)
    music_path = os.path.join(folder_path, selected_music)

    try:
        # Initialize pygame and mixer
        pygame.init()
        mixer.init()

        # Load and play the selected music file in the background
        mixer.music.load(music_path)
        mixer.music.play()

        # Wait for the music to finish (or you can add some delay or user input here)
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10) # Adjust the tick value as needed

        # Stop and quit pygame mixer
        mixer.music.stop()
        mixer.quit()
    except Exception as e:
        print(f"Error playing music: {e}")

def clap_to_music():
    tt = TapTester()
    
    try:
        print("Listening for claps to start music...")
        while True:
            result = tt.listen()
            if result:
                print("Clap detected! Starting music...")
                play_random_music(r"C:\Users\Deepak Bairagi\Desktop\JARVIS 1.1\DATA\MUSIC")
                break
    except KeyboardInterrupt:
        print("Clap detection stopped by user")
    except Exception as e:
        print(f"Error in clap detection: {e}")
    finally:
        tt.stop()


if __name__ == "__main__":
    clap_to_music()