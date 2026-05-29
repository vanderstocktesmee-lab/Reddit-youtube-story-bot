import os
import random
import textwrap

import numpy as np
import requests
from moviepy.editor import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
    concatenate_videoclips,
)
from PIL import Image, ImageDraw, ImageFont

PEXELS_KEY = os.environ["PEXELS_API_KEY"]
WIDTH, HEIGHT = 1080, 1920
FPS = 30

GENRE_QUERIES = {
    "aita": "city night rain",
    "revenge": "office hallway empty",
    "confession": "dark road night driving",
    "horror": "dark forest fog night",
    "wholesome": "golden hour park bench",
}


def _download_background(query_or_genre: str) -> str:
    query = GENRE_QUERIES.get(query_or_genre, query_or_genre or "nature landscape cinematic")
    headers = {"Authorization": PEXELS_KEY}

    for orientation in ["portrait", "landscape"]:
        r = requests.get(
            "https://api.pexels.com/videos/search",
            headers=headers,
            params={"query": query, "per_page": 15, "orientation": orientation},
            timeout=30,
        )
        videos = r.json().get("videos", [])
        if videos:
            break

    if not videos:
        raise RuntimeError("No background videos found on Pexels.")

    video = random.choice(videos[:10])
    files = sorted(video["video_files"], key=lambda f: f.get("height", 0), reverse=True)
    url = files[0]["link"]

    path = "/tmp/background.mp4"
    with requests.get(url, stream=True, timeout=60) as r:
        with open(path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
    return path


def _make_subtitle_image(words: list[str]) -> np.ndarray:
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    text = " ".join(words).upper()
    wrapped = textwrap.fill(text, width=18)

    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    font = None
    for fp in font_paths:
        if os.path.exists(fp):
            font = ImageFont.truetype(fp, 85)
            break
    if font is None:
        font = ImageFont.load_default()

    lines = wrapped.split("\n")
    line_height = 95
    total_h = line_height * len(lines)
    y_start = int(HEIGHT * 0.68) - total_h // 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (WIDTH - w) // 2
        draw.text((x + 3, y_start + 3), line, font=font, fill=(0, 0, 0, 220))
        draw.text((x, y_start), line, font=font, fill=(255, 230, 0, 255))
        y_start += line_height

    return np.array(img)


def _build_subtitle_clips(word_boundaries: list[dict], duration: float) -> list:
    clips = []
    chunk_size = 4
    for i in range(0, len(word_boundaries), chunk_size):
        chunk = word_boundaries[i : i + chunk_size]
        words = [w["word"] for w in chunk]
        start = chunk[0]["start"]
        end = chunk[-1]["end"] + 0.05
        end = min(end, duration)
        if end <= start:
            continue
        frame = _make_subtitle_image(words)
        clip = (
            ImageClip(frame, ismask=False)
            .set_start(start)
            .set_duration(end - start)
        )
        clips.append(clip)
    return clips


def create_video(audio_path: str, word_boundaries: list[dict], metadata: dict) -> str:
    output_path = "/tmp/output.mp4"
    audio = AudioFileClip(audio_path)
    duration = audio.duration

    bg_path = _download_background(metadata.get("bg_query") or metadata.get("genre", ""))
    bg = VideoFileClip(bg_path, audio=False)

    if bg.duration < duration:
        loops = int(duration / bg.duration) + 1
        bg = concatenate_videoclips([bg] * loops)
    bg = bg.subclip(0, duration)

    bw, bh = bg.size
    target_ratio = WIDTH / HEIGHT
    if bw / bh > target_ratio:
        new_w = int(bh * target_ratio)
        bg = bg.crop(x_center=bw // 2, width=new_w)
    else:
        new_h = int(bw / target_ratio)
        bg = bg.crop(y_center=bh // 2, height=new_h)
    bg = bg.resize((WIDTH, HEIGHT))

    dim = ColorClip((WIDTH, HEIGHT), color=(0, 0, 0)).set_opacity(0.45).set_duration(duration)
    subtitle_clips = _build_subtitle_clips(word_boundaries, duration)

    final = CompositeVideoClip(
        [bg, dim] + subtitle_clips,
        size=(WIDTH, HEIGHT),
    ).set_audio(audio)

    final.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=4,
        logger=None,
    )
    return output_path
