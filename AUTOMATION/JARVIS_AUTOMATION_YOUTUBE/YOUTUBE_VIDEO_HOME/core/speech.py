import pyttsx3

# Text-to-Speech engine singleton
_engine = pyttsx3.init()


def speak(text: str) -> None:
    _engine.say(text)
    _engine.runAndWait()
