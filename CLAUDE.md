# Atlas Voice Assistant

The voice assistant for a home automation system that may eventually be sold as a product. The planned product line is mmWave door sensors, a doorbell camera (logic mostly built, in `../door-greeter`), an outdoor camera, this smart speaker, and later a hub. Smart home control (lights, Matter) comes later.

The assistant is named **Atlas**: a warm, polite, charismatic British male voice in the "AI butler" style. The brain is the Claude API.

## How to work with the user

- **Teach one step at a time.** The user is learning and asked explicitly not to get the whole tutorial at once. Give one step, explain *why* it matters, give copy-paste commands and code, and end with a clear "done when…" check. Wait for the user to confirm before moving on.
- Explain errors in plain language: what they mean, then the fix.
- The user runs the commands themselves; this is a tutorial, not a "do it for me" project. **Never edit code, create files or install packages unless the user explicitly asks for that specific piece.** Permission for one step doesn't carry over to the next, and "let's move on to step N" means teach it.

## Ground rules

- **No training or cloning on JARVIS / Paul Bettany audio**, not even for the private prototype. Anything trained on it can never ship. The goal is an original voice in the same *archetype*.
- Stay on voices and models that are commercially licensable. Kokoro is Apache-2.0. Check licenses before adding any model (many cloning models have non-commercial weights; the newer Piper is GPL-3.0).

## Environment

- macOS, Python 3.14 from the python.org installer, virtual environment in `.venv/` (`source .venv/bin/activate`).
- Python 3.14 from python.org didn't ship with SSL certificates, which broke downloads. Fixed with `sudo "/Applications/Python 3.14/Install Certificates.command"`.
- Packages are listed in `requirements.txt` (`pip install -r requirements.txt`). The `.venv` was rebuilt after the project folder was renamed from `custom-voice-assistant`; a venv hard-codes its path, so recreate it if the folder moves.
- `.env` (holds `CLAUDE_API`) and the model files are gitignored, so a fresh clone needs them added by hand.
- Model files in the project root, not committed: `kokoro-v1.0.onnx`, `voices-v1.0.bin` (from the thewh1teagle/kokoro-onnx GitHub releases, `model-files-v1.0`), and the custom wake word `hey_atlas.onnx` (plus `hey_atlas.tflite`, unused on the Mac). The wake-word model can't be re-downloaded, so the user keeps a backup outside git.
- Run the programs from the project folder: models are loaded by relative path.
- Target speaker hardware will probably be Linux (e.g. Raspberry Pi). Avoid Mac-only tools like `afplay` in real code; use `sounddevice`.

## Decisions so far

| Decision | Choice | Why |
|---|---|---|
| Text-to-speech engine | **Kokoro** (`kokoro-onnx`) | Much more natural than Piper, runs offline, Apache-2.0 license |
| Rejected | Piper `en_GB-alan-medium` | Sounded dark, robotic and eerie |
| Atlas voice | **40% `bm_fable` + 60% `bm_lewis`**, speed **1.2**, `lang="en-gb"` | User's favorite after tuning. Blending also makes it less generic than one stock voice. Speed was first tuned to 0.9; the user later sped it up to 1.2 on purpose |
| Brain | Claude API, **`claude-haiku-5-5`** with effort `low` (`chat_atlas.py`) | The user chose the cheapest model. The key is in `.env` as `CLAUDE_API`, loaded with `python-dotenv` |
| Replies | Streamed from the API, split into sentences, played back to back | Atlas starts talking after the first sentence instead of the whole reply |
| Speech-to-text | **`faster-whisper`**, model `base.en`, CPU, `int8`, `vad_filter=True` (`atlas_ears.py`) | Runs locally (private, no per-use cost), MIT license, small enough for a Pi. `small.en` is the upgrade if accuracy is lacking |
| Name pronunciation | Pronunciation dictionary that swaps text before synthesis: `"Jaden" → "Jayden"` | The engine misreads "Jaden". "Jayden" and "Jaiden" both work |
| Wake word | **openWakeWord** (`openwakeword==0.6.0`, `inference_framework="onnx"`), custom phrase **"hey atlas"**, threshold **0.5** | Free, offline, Apache-2.0 code. Porcupine's free tier reportedly ended June 30, 2026. "Hey Atlas" (3 syllables) false-triggers less than "Atlas" alone. Offline check: "Hey Atlas" in three Kokoro voices scored 0.60–0.78; "at last", "atlas" alone and plain "hey" scored 0.001 |
| Wake-word license | **Prototype only for now** | openWakeWord's ready-made models are CC BY-NC-SA, and the training notebook's data is marked non-commercial. Must retrain on commercially licensed data before shipping (see Later) |

## Files

- `atlas_voice.py`: **the voice module.** Loads Kokoro once, defines `ATLAS_VOICE` and `ATLAS_SPEED`, has a `PRONUNCIATIONS` dict plus `fix_pronunciation()`, `speak(text)` plays audio through `sounddevice`, and `speak_sentences(sentences, on_start)` plays a stream of sentences gaplessly (it builds the next sentence's audio while the current one plays). Everything else should call these.
- `atlas_ears.py`: **the listening module.** Loads Whisper and the wake-word model once. `wait_for_wake_word()` reads the mic in 1280-sample (80 ms) `int16` chunks and returns when the score passes `WAKE_THRESHOLD` (it calls `wake_model.reset()` first so the last trigger can't repeat). `record_until_enter()` records the mic (16 kHz mono, `float32`) through an `InputStream` callback until Enter, `transcribe(audio)` returns text, and `listen()` does both. Only one function has the mic open at a time.
- `chat_atlas.py`: the main program. Holds the system prompt and `history`; `ask_atlas()` is a generator that yields one sentence at a time from the streamed reply. Loop: wait for "Hey Atlas" → `speak("Yes?")` → `listen()` → answer. Typing was removed in step 9; saying "quit" exits.
- `test_wake.py`: standalone wake-word tester that prints the confidence on each trigger. Useful for tuning the threshold.
- `voice-brief.md`: the voice spec (name, personality, accent, pace). **Incomplete on purpose; paused until the product is closer to launch.** Remaining gaps: the example lines are empty, the only reference voice is JARVIS (add 2–3 others), "quirky" needs defining (dry wit vs playful), and which British accent.
- `.gitignore` should include `.venv/`, `*.onnx`, `*.tflite`, `*.bin`, `*.wav` (the models are about 400 MB).

## Roadmap

### Done
1. ✅ **Got text-to-speech working on the Mac.** Installed Piper and heard a stock British voice. Learned that a voice = model file + config.
2. ✅ **Wrote the voice brief** (partially; see above). The user wants warm, polite, charismatic and natural, and never robotic, dark or eerie.
3. ✅ **Compared text-to-speech engines.** Kokoro beat Piper by a wide margin; the favorite was `bm_fable`.
4. ✅ **Tuned the voice.** Settled on the Fable/Lewis 40/60 mix at speed 0.9 and fixed the pronunciation of the user's name.
5. ✅ **Built `speak()` in `atlas_voice.py`.**
6. ✅ **Connected the brain.** `chat_atlas.py`: typed question → Claude (`claude-haiku-5-5`) with Atlas's system prompt → `speak()`. Confirmed working 2026-11-13.
7. ✅ **Made it feel instant.** Streamed the reply, split it into sentences, and removed the gaps by making the next sentence's audio while the current one plays (gaps went from about 1.5 s to about 5 ms).

8. ✅ **Speech-to-text** with `faster-whisper`. Built `atlas_ears.py` (`listen()` records until Enter, then transcribes) and connected it to `chat_atlas.py`: an empty line means talk instead of type, and the quit check strips Whisper's punctuation (`"Quit."`). Confirmed working 2026-11-16.
9. ✅ **Wake word.** Tested the pipeline with the ready-made "hey mycroft" (`test_wake.py`), trained a custom "hey atlas" model in openWakeWord's official Colab notebook (`automatic_model_training_simple`), then wired `wait_for_wake_word()` into `chat_atlas.py`. Confirmed working 2026-11-19. The notebook (from 2023) needed these fixes, which will be needed again for any retrain:
   - Set the Colab runtime to an **older runtime version** (Python 3.12 or earlier) with a **T4 GPU**. `piper-phonemize` has no Python 3.13 wheels.
   - Cell 2: AudioSet moved from `data/bal_train09.tar` (404) to `data/bal_train/09.parquet`. Replaced the block with code that downloads the parquet via `hf_hub_download`, decodes each clip with `soundfile`, resamples to 16 kHz and writes `audioset_16k/*.wav`.
   - Cell 2: changed `!pip install onnx2tf` to `!pip install onnx2tf --no-deps`. The latest onnx2tf pins `numpy==2.2.6`, which swapped numpy mid-cell and caused a restart loop and an `ImportError: cannot import name '_center'`.
   - Training was killed (shown as `^C`) at exactly step 7,497 of 10,000. At 75% of steps validation starts, and `train.py` line 879 feeds the whole 11-hour false-positive set as one batch, which runs out of free-Colab RAM. Fix before cell 3: `!sed -i 's/batch_size=len(X_val_fp_labels)/batch_size=4096/' openwakeword/openwakeword/train.py`. This gives the same result because false positives are summed across batches.
   - Never click "Restart session" while a cell is running: it cuts off the remaining downloads. A restart also wipes variables (`target_word` from cell 1), so rerun cell 1 afterward. The `if not os.path.exists(...)` checks skip half-made folders, so delete them (`rm -rf`) before retrying.
   - Note: openwakeword.com is a third-party paid service (credits) and isn't affiliated with the openWakeWord author as far as we could tell. It was considered as an alternative.

### Next
10. 🔄 **Full loop.** Wake word → listen → transcribe → think → speak. Conversation memory already exists (`history`). The missing piece is end-of-speech detection, so the user doesn't press Enter to stop recording.
11. **Audio polish and hardware.** Light EQ, compression and short reverb (e.g. `pedalboard`), tuned on the real speaker hardware; port to the target device.

### Later / when it becomes a product
- Smart home control through LLM tool calling (lights, Matter, door sensors, cameras), integrated with the hub and doorbell.
- **Retrain the wake word on commercially licensed data.** The current `hey_atlas.onnx` is prototype-only. The plan the user liked: write their own trainer. Generate positives with Kokoro (Apache-2.0), using random voice blends to get many synthetic speakers. Use negatives and background noise only from datasets that allow commercial use. Train just the small classifier on top of openWakeWord's frozen melspectrogram and embedding models.
- A per-user pronunciation setup screen so each customer can fix how Atlas says their name (extends `PRONUNCIATIONS`).
- **Custom voice from a voice actor.** Finish the voice brief, hire an actor with a written contract granting AI training and commercial use, record 1–2 hours of clean audio (LJSpeech format), and fine-tune on a rented GPU. Until then, the Kokoro blend is a legally shippable voice, though not exclusive to Atlas.
