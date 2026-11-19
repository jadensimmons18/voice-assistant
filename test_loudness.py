import numpy as np
import sounddevice as sd

CHUNK = 1600  # 100 milliseconds at 16,000 samples per second

print("Stay quiet for a few seconds, then talk normally. Press Ctrl+C to stop.\n")
with sd.InputStream(samplerate=16000, channels=1, dtype="float32", blocksize=CHUNK) as stream:
    while True:
        audio, _ = stream.read(CHUNK)              # next 100 ms of sound
        rms = np.sqrt(np.mean(audio[:, 0] ** 2))   # how loud was it?
        bar = "#" * min(int(rms * 1000), 60)       # a little bar so you can see it
        print(f"{rms:.4f}  {bar}")
