import os
import re

import anthropic
from dotenv import load_dotenv

from atlas_voice import speak, speak_sentences
from atlas_ears import listen

load_dotenv()  # reads the .env file in this folder into environment variables
client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API"))

SYSTEM_PROMPT = """You are Atlas, the AI assistant for this home.
Personality: warm, polite and charismatic, with gentle dry wit. A small clever remark now and then, never goofy, never sarcastic toward the user.
The user's name is Jaden. Usually address him by first name; occasionally "sir".

Your replies are spoken aloud by a text-to-speech voice, so:
- Keep answers short: one or two sentences unless asked for more detail.
- Never use markdown, bullet points, emoji, or symbols.
- Write numbers, times and units the way they're spoken, for example "seventy-two degrees", not "72°F".
You cannot control any devices yet. If asked to, say so politely."""

history = []  # the conversation so far, so Atlas remembers context


# A sentence ends with . ! or ? followed by a space
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def ask_atlas(user_text):
    """Stream Atlas's reply from Claude, handing back one sentence at a time."""
    history.append({"role": "user", "content": user_text})
    buffer = ""  # text received but not yet a full sentence

    with client.messages.stream(
        model="claude-haiku-5-5",             # cheapest current Claude model
        max_tokens=1024,                      # spoken replies are short
        output_config={"effort": "low"},      # quicker replies for casual chat
        system=SYSTEM_PROMPT,
        messages=history,
    ) as stream:
        for chunk in stream.text_stream:
            buffer += chunk
            parts = SENTENCE_END.split(buffer)
            # Every part except the last is a finished sentence
            for sentence in parts[:-1]:
                if sentence.strip():
                    yield sentence.strip()
            buffer = parts[-1]  # the unfinished leftover waits for more text

        final = stream.get_final_message()

    history.append({"role": "assistant", "content": final.content})

    if final.stop_reason == "refusal":
        yield "I'm afraid I can't help with that one."
    elif buffer.strip():
        yield buffer.strip()  # the last sentence (it has no space after it)


if __name__ == "__main__":
    print("Atlas is online. Type a message, or press Enter on an empty line to talk.")
    print("Say or type 'quit' to exit.")
    speak("Good evening, Jaden. Atlas is online.")

    while True:
        user_text = input("\nYou: ").strip()

        if not user_text:                  # empty line means: listen instead
            user_text = listen()
            if not user_text:
                print("(I didn't catch anything. Try again.)")
                continue
            print(f"You said: {user_text}")

        if user_text.lower().strip(".!? ") in ("quit", "exit"):
            speak("Very good. I'll be here if you need me.")
            break

        try:
            print("Atlas: ", end="", flush=True)
            speak_sentences(
                ask_atlas(user_text),
                on_start=lambda sentence: print(sentence, end=" ", flush=True),
            )
            print()
        except anthropic.AuthenticationError:
            print("Your API key is missing or wrong. Check CLAUDE_API in your .env file.")
            break
        except anthropic.APIConnectionError:
            print("Couldn't reach the API. Check your internet connection.")
            continue