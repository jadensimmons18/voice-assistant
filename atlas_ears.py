import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from openwakeword.model import Model
from openwakeword.utils import download_models

SAMPLE_RATE = 16000  # Whisper expects 16,000 samples per second

# --- End-of-speech detection (tuned from test_loudness.py) ---
SPEECH_THRESHOLD = 0.005   # louder than this = talking (silence ~0.0008, talking ~0.02-0.05)
SILENCE_TO_STOP = 1.0      # seconds of quiet after talking that means "done"
NO_SPEECH_TIMEOUT = 5.0    # give up if no talking starts within this many seconds
MAX_RECORDING = 15.0       # never record longer than this
CHUNK_SECONDS = 0.1        # check loudness every 100 ms

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


def record_until_silence():
    """Record until the user stops talking. Returns the audio, or an empty array if they never spoke."""
    chunk_size = int(SAMPLE_RATE * CHUNK_SECONDS)   # 1,600 samples = 100 ms
    chunks = []
    heard_speech = False
    quiet_time = 0.0

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32", blocksize=chunk_size) as stream:
        while True:
            audio, _ = stream.read(chunk_size)
            chunks.append(audio[:, 0])
            elapsed = len(chunks) * CHUNK_SECONDS

            loudness = np.sqrt(np.mean(audio[:, 0] ** 2))   # RMS, same as test_loudness.py
            if loudness > SPEECH_THRESHOLD:
                heard_speech = True
                quiet_time = 0.0                           # talking: reset the quiet timer
            else:
                quiet_time += CHUNK_SECONDS                # quiet: count it

            if heard_speech and quiet_time >= SILENCE_TO_STOP:
                break                                      # talked, then went quiet: done
            if not heard_speech and elapsed >= NO_SPEECH_TIMEOUT:
                return np.zeros(0, dtype="float32")        # never started talking
            if elapsed >= MAX_RECORDING:
                break                                      # safety limit

    return np.concatenate(chunks)


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
    """Record until the user stops talking, then return what they said as text."""
    audio = record_until_silence()
    if len(audio) == 0:
        return ""            # they never started talking, so don't bother Whisper
    return transcribe(audio)


# --- Only runs when you execute this file directly, for testing ---
if __name__ == "__main__":
    print("Start talking (it stops by itself when you go quiet)...")
    audio = record_until_silence()
    print(f"Recorded {len(audio) / SAMPLE_RATE:.1f} seconds")
    if len(audio):
        print(f"You said: {transcribe(audio)!r}")