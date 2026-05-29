import asyncio

from bot.story_generator import generate_story
from bot.tts_generator import generate_tts
from bot.video_creator import create_video
from bot.publisher import publish_video


async def run():
    print("==> Generating story with AI...")
    story = generate_story()
    print(f"    Genre: {story['genre']} | Title: {story['title']}")

    print("==> Generating TTS narration...")
    audio_path, word_boundaries = await generate_tts(story["narration"])
    print(f"    Words: {len(word_boundaries)}")

    print("==> Creating video...")
    video_path = create_video(audio_path, word_boundaries, story)
    print(f"    Video: {video_path}")

    print("==> Publishing (GitHub Releases + Make.com)...")
    video_url = publish_video(
        video_path,
        story["title"],
        story["description"],
        story["tags"],
    )
    print(f"==> Done! Video URL: {video_url}")


if __name__ == "__main__":
    asyncio.run(run())
