import os
import random

import edge_tts

# Natural, human-sounding voices used by top Reddit-story channels.
# A random one is picked per run so the channel doesn't sound templated.
VOICES = [
    "en-US-AndrewNeural",
    "en-US-BrianNeural",
    "en-US-AriaNeural",
    "en-US-JennyNeural",
    "en-US-GuyNeural",
    "en-US-EmmaNeural",
]

_env_voice = os.getenv("TTS_VOICE", "random")
VOICE = random.choice(VOICES) if _env_voice in ("", "random") else _env_voice
RATE = os.getenv("TTS_RATE", "+13%")


async def generate_tts(text: str, voice: str | None = None) -> tuple[str, list[dict]]:
    audio_path = "/tmp/narration.mp3"
    communicate = edge_tts.Communicate(text, voice or VOICE, rate=RATE)

    audio_chunks = []
    word_boundaries = []

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            word_boundaries.append(
                {
                    "word": chunk["text"],
                    "start": chunk["offset"] / 10_000_000,
                    "end": (chunk["offset"] + chunk["duration"]) / 10_000_000,
                }
            )

    with open(audio_path, "wb") as f:
        for chunk in audio_chunks:
            f.write(chunk)

    return audio_path, word_boundaries
