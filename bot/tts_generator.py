import asyncio
import os
import edge_tts

VOICE = os.getenv("TTS_VOICE", "en-US-AndrewNeural")
RATE = os.getenv("TTS_RATE", "+15%")


async def generate_tts(text: str) -> tuple[str, list[dict]]:
    audio_path = "/tmp/narration.mp3"
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE)

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
