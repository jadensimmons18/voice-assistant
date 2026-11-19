import sounddevice as sd
from openwakeword.model import Model
from openwakeword.utils import download_models

download_models()  # makes sure openWakeWord's helper models are there (only slow the first time)
model = Model(wakeword_models=["hey_atlas.onnx"], inference_framework="onnx")  # our custom-trained model

CHUNK = 1280   # 80 milliseconds of audio at 16,000 samples per second
cooldown = 0   # stops one "hey atlas" from being counted several times

print("Say 'Hey Atlas'... (press Ctrl+C to stop)")
with sd.InputStream(samplerate=16000, channels=1, dtype="int16", blocksize=CHUNK) as stream:
    while True:
        audio, _ = stream.read(CHUNK)         # wait for the next 80 ms of sound
        scores = model.predict(audio[:, 0])   # how sure is it that it heard the word?
        score = max(scores.values())

        if cooldown > 0:
            cooldown -= 1
        elif score > 0.5:
            print(f"Heard it! (confidence {score:.2f})")
            cooldown = 25                     # ignore the next ~2 seconds
