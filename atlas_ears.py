import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from openwakeword.model import Model
from openwakeword.utils import download_models

SAMPLE_RATE = 16000  # Whisper expects 16,000 samples per second

# --- Load the model once, when this file is imported ---
model = WhisperModel("base.en", device="cpu", compute_type="int8")

# --- Wake word: load once, when this file is imported ---
WAKE_THRESHOLD = 0.5  # raise if it false-triggers, lower if it misses you
download_models()     # makes sure openWakeWord's helper models are there
wake_model = Model(wakeword_models=["hey_atlas.onnx"], inference_framework="onnx")


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


def wait_for_wake_word():
    """Wait (forever if needed) until someone says 'Hey Atlas'."""
    wake_model.reset()  # forget any audio left over from last time
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=1280) as stream:
        while True:
            audio, _ = stream.read(1280)            # next 80 ms of sound
            scores = wake_model.predict(audio[:, 0])
            if max(scores.values()) > WAKE_THRESHOLD:
                return                              # heard it, so stop waiting


def listen():
    """Record the user's voice and return what they said as text."""
    return transcribe(record_until_enter())


# --- Only runs when you execute this file directly, for testing ---
if __name__ == "__main__":
    input("Press Enter to start recording...")
    print(f"You said: {listen()!r}")