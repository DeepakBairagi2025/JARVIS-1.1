import speech_recognition as sr
from core.speech import speak

_recognizer = sr.Recognizer()


def listen_command() -> str:
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
