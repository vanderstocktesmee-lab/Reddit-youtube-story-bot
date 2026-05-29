import os
import random

import edge_tts

# Microsoft's "Multilingual" HD voices: the most natural and expressive in edge-tts,
# with real intonation and warmth instead of a flat, read-aloud tone.
VOICES = [
    "en-US-AvaMultilingualNeural",     # warm, very natural, expressive female
    "en-US-EmmaMultilingualNeural",    # gentle, expressive female
    "en-US-AndrewMultilingualNeural",  # warm, natural, easygoing male
    "en-US-BrianMultilingualNeural",   # natural, friendly male
]

_env_voice = os.getenv("TTS_VOICE", "random")
VOICE = random.choice(VOICES) if _env_voice in ("", "random") else _env_voice
RATE = os.getenv("TTS_RATE", "+0%")     # natural, unhurried pace
PITCH = os.getenv("TTS_PITCH", "+0Hz")  # keep the voice's own intonation


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
