import os
import random

import edge_tts

# Warm, soft, human-sounding voices. A random one is picked per run so the
# channel varies but every voice has a gentle, cosy tone (soft male / soft female).
VOICES = [
    "en-US-AvaNeural",      # soft, warm female
    "en-US-EmmaNeural",     # gentle, friendly female
    "en-GB-SoniaNeural",    # soft British female
    "en-US-AndrewNeural",   # warm, soft male
    "en-GB-RyanNeural",     # soft British male
    "en-US-BrianNeural",    # warm, casual male
]

_env_voice = os.getenv("TTS_VOICE", "random")
VOICE = random.choice(VOICES) if _env_voice in ("", "random") else _env_voice
RATE = os.getenv("TTS_RATE", "+4%")     # gentle pace = warmer feel
PITCH = os.getenv("TTS_PITCH", "-2Hz")  # slightly lower = softer/warmer


async def generate_tts(text: str, voice: str | None = None) -> tuple[str, list[dict]]:
    audio_path = "/tmp/narration.mp3"
    communicate = edge_tts.Communicate(text, voice or VOICE, rate=RATE, pitch=PITCH)

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
