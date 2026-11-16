import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000  # Whisper expects 16,000 samples per second

# --- Load the model once, when this file is imported ---
model = WhisperModel("base.en", device="cpu", compute_type="int8")


def record_until_enter():
    """Record from the microphone until the user presses Enter."""
    chunks = []

    def save_chunk(indata, frames, time, status):
        chunks.append(indata.copy())  # sounddevice calls this for every new chunk

    # The microphone stays on for everything indented under "with"
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32", callback=save_chunk):
        input("Listening... press Enter when you're done.")

    if not chunks:
        return np.zeros(0, dtype="float32")  # nothing recorded
    return np.concatenate(chunks)[:, 0]  # join the chunks into one recording


def transcribe(audio):
    """Turn recorded audio into text."""
    segments, _ = model.transcribe(
        audio,
        language="en",
        beam_size=1,      # fastest setting; plenty accurate for short questions
        vad_filter=True,  # skip the silent parts
    )
    return " ".join(segment.text.strip() for segment in segments).strip()


def listen():
    """Record the user's voice and return what they said as text."""
    return transcribe(record_until_enter())


# --- Only runs when you execute this file directly, for testing ---
if __name__ == "__main__":
    input("Press Enter to start recording...")
    print(f"You said: {listen()!r}")