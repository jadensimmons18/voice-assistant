import re
import sounddevice as sd
from kokoro_onnx import Kokoro

# --- Load the model once, when this file is imported ---
kokoro = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")

# --- Atlas's voice: 40% Fable + 60% Lewis ---
ATLAS_VOICE = kokoro.get_voice_style("bm_fable") * 0.4 + kokoro.get_voice_style("bm_lewis") * 0.6
ATLAS_SPEED = 1.2

# --- Pronunciation dictionary: written word -> spelling the engine reads correctly ---
PRONUNCIATIONS = {
    "Jaden": "Jayden",
}


def fix_pronunciation(text):
    """Swap tricky words for spellings the voice engine reads correctly."""
    for word, spoken in PRONUNCIATIONS.items():
        text = re.sub(rf"\b{re.escape(word)}\b", spoken, text, flags=re.IGNORECASE)
    return text


def make_audio(text):
    """Turn text into Atlas's voice audio, without playing it yet."""
    text = fix_pronunciation(text)
    return kokoro.create(text, voice=ATLAS_VOICE, speed=ATLAS_SPEED, lang="en-gb")


def speak(text):
    """Say the text out loud in Atlas's voice."""
    samples, sample_rate = make_audio(text)
    sd.play(samples, sample_rate)
    sd.wait()  # wait until it finishes talking


def speak_sentences(sentences, on_start=None):
    """Say sentences back to back with no gaps.

    sd.play() returns right away and plays in the background, so while one
    sentence is playing we're already making the next sentence's audio.
    on_start(sentence) is called as each sentence begins playing.
    """
    for sentence in sentences:
        samples, sample_rate = make_audio(sentence)  # made while the previous one still plays
        sd.wait()                                    # let the previous sentence finish
        if on_start:
            on_start(sentence)
        sd.play(samples, sample_rate)
    sd.wait()  # let the last sentence finish


# --- Only runs when you execute this file directly, for testing ---
if __name__ == "__main__":
    speak("Welcome back, Jaden. The house is just as you left it.")
    speak("Pardon the interruption. There's someone at the front door.")