import glob
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
from PIL import Image, ImageDraw, ImageFilter, ImageFont

PEXELS_KEY = os.environ["PEXELS_API_KEY"]
WIDTH, HEIGHT = 1080, 1920
FPS = 30

SUBREDDITS = {
    "aita": "r/AmItheAsshole",
    "revenge": "r/pettyrevenge",
    "confession": "r/confessions",
    "horror": "r/nosleep",
    "wholesome": "r/MadeMeSmile",
}

FALLBACK_BG = ["satisfying", "abstract motion", "nature aerial"]

# Warm, soft subtitle colours (picked once per run, consistent within one video).
SUB_COLORS = [
    (255, 248, 236),  # warm cream
    (255, 226, 184),  # soft amber
    (255, 206, 184),  # soft peach
    (212, 240, 222),  # soft sage
]
SUB_COLOR = random.choice(SUB_COLORS)


_FONT_CACHE = {}


def _font(bold: bool = True, size: int = 48) -> ImageFont.FreeTypeFont:
    key = (bold, size)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    # Prefer warm, rounded fonts; fall back to whatever is installed.
    bold_names = ["Comfortaa-Bold.ttf", "Quicksand-Bold.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"]
    reg_names = ["Comfortaa-Regular.ttf", "Quicksand-Regular.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"]
    chosen = None
    for name in (bold_names if bold else reg_names):
        hits = glob.glob(f"/usr/share/fonts/**/{name}", recursive=True)
        if hits:
            chosen = hits[0]
            break
    font = ImageFont.truetype(chosen, size) if chosen else ImageFont.load_default()
    _FONT_CACHE[key] = font
    return font


def _download_background(query: str) -> str:
    headers = {"Authorization": PEXELS_KEY}
    queries = [query] + [q for q in FALLBACK_BG if q != query]
    videos = []
    for q in queries:
        for orientation in ["portrait", "landscape"]:
            r = requests.get(
                "https://api.pexels.com/videos/search",
                headers=headers,
                params={"query": q, "per_page": 15, "orientation": orientation},
                timeout=30,
            )
            videos = r.json().get("videos", [])
            if videos:
                break
        if videos:
            break

    if not videos:
        raise RuntimeError("No background videos found on Pexels.")

    video = random.choice(videos[:10])
    files = video["video_files"]
    # Prefer ~HD for speed; avoid heavy 4K.
    hd = [f for f in files if 1080 <= f.get("height", 0) <= 2000]
    if hd:
        url = min(hd, key=lambda f: f.get("height", 0))["link"]
    else:
        decent = [f for f in files if f.get("height", 0) >= 720] or files
        url = min(decent, key=lambda f: f.get("height", 0))["link"]

    path = "/tmp/background.mp4"
    with requests.get(url, stream=True, timeout=60) as r:
        with open(path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
    return path


def _make_reddit_card(hook: str, genre: str) -> np.ndarray:
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    title_font = _font(bold=True, size=54)
    sub_font = _font(bold=True, size=36)
    meta_font = _font(bold=False, size=28)

    card_x = 50
    card_w = WIDTH - 2 * card_x
    pad = 44
    inner_w = card_w - 2 * pad

    def wrap(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list:
        lines, cur = [], ""
        for word in text.split():
            test = (cur + " " + word).strip()
            if draw.textlength(test, font=font) <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines

    title_lines = wrap(hook, title_font, inner_w)
    title_lh = 66
    header_h = 78
    card_h = pad + header_h + 24 + title_lh * len(title_lines) + pad
    card_y = int(HEIGHT * 0.20)

    # drop shadow + white card
    draw.rounded_rectangle(
        [card_x + 6, card_y + 10, card_x + card_w + 6, card_y + card_h + 10],
        radius=32, fill=(0, 0, 0, 110),
    )
    draw.rounded_rectangle(
        [card_x, card_y, card_x + card_w, card_y + card_h],
        radius=32, fill=(255, 255, 255, 255),
    )

    # avatar
    av_r = 28
    av_cx = card_x + pad + av_r
    av_cy = card_y + pad + av_r
    draw.ellipse(
        [av_cx - av_r, av_cy - av_r, av_cx + av_r, av_cy + av_r],
        fill=(255, 69, 0, 255),
    )

    sub = SUBREDDITS.get(genre, "r/stories")
    tx = av_cx + av_r + 20
    draw.text((tx, card_y + pad - 2), sub, font=sub_font, fill=(20, 20, 20, 255))
    draw.text(
        (tx, card_y + pad + 40),
        "Posted by u/throwaway · now",
        font=meta_font,
        fill=(120, 120, 120, 255),
    )

    ty = card_y + pad + header_h + 24
    for line in title_lines:
        draw.text((card_x + pad, ty), line, font=title_font, fill=(15, 15, 15, 255))
        ty += title_lh

    return np.array(img)


def _make_subtitle_image(words: list) -> np.ndarray:
    text = " ".join(words)
    wrapped = textwrap.fill(text, width=18)
    font = _font(bold=True, size=80)

    lines = wrapped.split("\n")
    line_height = 94
    total_h = line_height * len(lines)
    y = int(HEIGHT * 0.70) - total_h // 2

    measure = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    placed = []
    for line in lines:
        bbox = measure.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        placed.append((line, (WIDTH - w) // 2, y))
        y += line_height

    # soft blurred shadow = warm glow instead of a hard angular outline
    shadow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    for line, x, ly in placed:
        sdraw.text((x, ly + 4), line, font=font, fill=(0, 0, 0, 190))
    img = shadow.filter(ImageFilter.GaussianBlur(9))

    draw = ImageDraw.Draw(img)
    for line, x, ly in placed:
        draw.text((x, ly), line, font=font, fill=(*SUB_COLOR, 255))

    return np.array(img)


def _build_subtitle_clips(word_boundaries: list, duration: float, chunk_size: int = 3) -> list:
    clips = []
    for i in range(0, len(word_boundaries), chunk_size):
        chunk = word_boundaries[i : i + chunk_size]
        words = [w["word"] for w in chunk]
        start = chunk[0]["start"]
        end = min(chunk[-1]["end"] + 0.05, duration)
        if end <= start:
            continue
        frame = _make_subtitle_image(words)
        clips.append(
            ImageClip(frame, ismask=False).set_start(start).set_duration(end - start)
        )
    return clips


def create_video(audio_path: str, word_boundaries: list, metadata: dict) -> str:
    output_path = "/tmp/output.mp4"
    audio = AudioFileClip(audio_path)
    duration = audio.duration

    if not word_boundaries:
        words = metadata.get("narration", "").split()
        if words:
            per = duration / len(words)
            word_boundaries = [
                {"word": w, "start": i * per, "end": (i + 1) * per}
                for i, w in enumerate(words)
            ]

    # Split off the opening hook so it can be shown as a Reddit card.
    hook = (metadata.get("hook") or "").strip()
    hook_words = min(len(hook.split()), len(word_boundaries)) if hook else 0
    hook_end = word_boundaries[hook_words - 1]["end"] + 0.15 if hook_words else 0.0
    hook_end = min(hook_end, duration)
    body_boundaries = word_boundaries[hook_words:]

    bg_path = _download_background(metadata.get("bg_query") or "satisfying")
    bg = VideoFileClip(bg_path, audio=False)
    if bg.duration < duration:
        loops = int(duration / bg.duration) + 1
        bg = concatenate_videoclips([bg] * loops)
    bg = bg.subclip(0, duration)

    bw, bh = bg.size
    target_ratio = WIDTH / HEIGHT
    if bw / bh > target_ratio:
        bg = bg.crop(x_center=bw // 2, width=int(bh * target_ratio))
    else:
        bg = bg.crop(y_center=bh // 2, height=int(bw / target_ratio))
    bg = bg.resize((WIDTH, HEIGHT))

    dim = ColorClip((WIDTH, HEIGHT), color=(0, 0, 0)).set_opacity(0.35).set_duration(duration)
    layers = [bg, dim]

    if hook and hook_end > 0:
        card = _make_reddit_card(hook, metadata.get("genre", ""))
        layers.append(ImageClip(card, ismask=False).set_start(0).set_duration(hook_end))

    layers += _build_subtitle_clips(body_boundaries, duration)

    final = CompositeVideoClip(layers, size=(WIDTH, HEIGHT)).set_audio(audio)
    final.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="veryfast",
        bitrate="4500k",
        threads=4,
        logger=None,
    )
    return output_path
