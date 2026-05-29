import os
import random

import numpy as np
from moviepy.editor import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
    concatenate_audioclips,
    concatenate_videoclips,
)
from PIL import Image, ImageDraw

import edge_tts

from bot.story_generator import (
    MODEL,
    SATISFYING_BG,
    STORY_SETTINGS,
    STORY_TYPES,
    _split_hook,
    client,
)
from bot.tts_generator import PITCH, RATE, VOICES
from bot.video_creator import SUBREDDITS, _download_background, _font

LWIDTH, LHEIGHT = 1920, 1080
FPS = 30

LONG_TITLES = [
    "Reddit Stories That Will Keep You Up At Night",
    "The Most Insane Reddit Stories You'll Ever Hear",
    "Reddit Stories To Listen To Before Bed",
    "Unbelievable Reddit Stories That Actually Happened",
    "Reddit Stories That Went Completely Wrong",
    "The Wildest Reddit Stories Of The Week",
]

LONG_DESCRIPTION = (
    "A compilation of the most gripping Reddit stories, narrated for your enjoyment. "
    "Sit back, relax, and listen.\n\n"
    "#reddit #redditstories #storytime #askreddit #stories #fyp #viral"
)

LONG_TAGS = [
    "reddit", "reddit stories", "storytime", "askreddit", "stories",
    "reddit readings", "compilation", "fyp", "viral", "narration",
]

INTRO_TEXT = (
    "Welcome back to the channel. Today I've got some of the most unbelievable "
    "Reddit stories people have ever shared. Grab a snack, get comfortable, and "
    "make sure you stick around until the end, because the last one is wild."
)
OUTRO_TEXT = (
    "And that's it for today. If you enjoyed these stories, do me a favor and "
    "subscribe, it really helps the channel. I'll see you in the next one."
)


async def _tts_to_file(text: str, voice: str, path: str) -> str:
    communicate = edge_tts.Communicate(text, voice, rate=RATE, pitch=PITCH)
    with open(path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
    return path


def _make_card_landscape(hook: str, genre: str) -> np.ndarray:
    img = Image.new("RGBA", (LWIDTH, LHEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    title_font = _font(bold=True, size=60)
    sub_font = _font(bold=True, size=40)
    meta_font = _font(bold=False, size=32)

    card_w = 1200
    card_x = (LWIDTH - card_w) // 2
    pad = 50
    inner_w = card_w - 2 * pad

    def wrap(text, font, max_w):
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
    title_lh = 74
    header_h = 86
    card_h = pad + header_h + 26 + title_lh * len(title_lines) + pad
    card_y = (LHEIGHT - card_h) // 2

    draw.rounded_rectangle(
        [card_x + 7, card_y + 11, card_x + card_w + 7, card_y + card_h + 11],
        radius=34, fill=(0, 0, 0, 110),
    )
    draw.rounded_rectangle(
        [card_x, card_y, card_x + card_w, card_y + card_h],
        radius=34, fill=(255, 255, 255, 255),
    )

    av_r = 32
    av_cx = card_x + pad + av_r
    av_cy = card_y + pad + av_r
    draw.ellipse(
        [av_cx - av_r, av_cy - av_r, av_cx + av_r, av_cy + av_r],
        fill=(255, 69, 0, 255),
    )

    sub = SUBREDDITS.get(genre, "r/stories")
    tx = av_cx + av_r + 22
    draw.text((tx, card_y + pad - 2), sub, font=sub_font, fill=(20, 20, 20, 255))
    draw.text(
        (tx, card_y + pad + 44),
        "Posted by u/throwaway · now",
        font=meta_font,
        fill=(120, 120, 120, 255),
    )

    ty = card_y + pad + header_h + 26
    for line in title_lines:
        draw.text((card_x + pad, ty), line, font=title_font, fill=(15, 15, 15, 255))
        ty += title_lh

    return np.array(img)


def _generate_stories(num: int) -> list:
    stories = []
    for _ in range(num):
        st = random.choice(STORY_TYPES)
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You write viral Reddit-style stories read aloud in a long compilation video. "
                        "Open with an irresistible hook on the first line, then tell a vivid, specific, "
                        "first-person story with a satisfying or shocking ending. Write the way someone actually "
                        "talks: vary sentence length, use commas, ellipses (...) and dashes for natural pauses, "
                        "use contractions, and let real emotion show, so it sounds spoken, not read. "
                        "Output only the spoken words: no hashtags, no emojis, no labels."
                    ),
                },
                {"role": "user", "content": st["prompt"] + " " + random.choice(STORY_SETTINGS)},
            ],
            max_tokens=600,
        )
        raw = resp.choices[0].message.content.strip()
        hook, body = _split_hook(raw)
        stories.append(
            {
                "hook": hook,
                "text": (hook + " " + body).strip(),
                "genre": st["genre"],
            }
        )
    return stories


async def run_longform() -> tuple:
    num = int(os.getenv("LONG_STORIES", "4"))
    voice = random.choice(VOICES)

    segments = [{"text": INTRO_TEXT, "hook": None, "genre": None}]
    segments += [
        {"text": s["text"], "hook": s["hook"], "genre": s["genre"]}
        for s in _generate_stories(num)
    ]
    segments.append({"text": OUTRO_TEXT, "hook": None, "genre": None})

    audio_clips = []
    timeline = []  # (start, end, segment)
    t = 0.0
    for i, seg in enumerate(segments):
        path = await _tts_to_file(seg["text"], voice, f"/tmp/long_seg_{i}.mp3")
        clip = AudioFileClip(path)
        timeline.append((t, t + clip.duration, seg))
        t += clip.duration
        audio_clips.append(clip)

    full_audio = concatenate_audioclips(audio_clips)
    duration = full_audio.duration

    bg_path = _download_background(random.choice(SATISFYING_BG))
    bg = VideoFileClip(bg_path, audio=False)
    if bg.duration < duration:
        loops = int(duration / bg.duration) + 1
        bg = concatenate_videoclips([bg] * loops)
    bg = bg.subclip(0, duration)

    bw, bh = bg.size
    target_ratio = LWIDTH / LHEIGHT
    if bw / bh > target_ratio:
        bg = bg.crop(x_center=bw // 2, width=int(bh * target_ratio))
    else:
        bg = bg.crop(y_center=bh // 2, height=int(bw / target_ratio))
    bg = bg.resize((LWIDTH, LHEIGHT))

    dim = ColorClip((LWIDTH, LHEIGHT), color=(0, 0, 0)).set_opacity(0.5).set_duration(duration)
    layers = [bg, dim]

    for start, end, seg in timeline:
        if seg["hook"]:
            card = _make_card_landscape(seg["hook"], seg["genre"])
            layers.append(
                ImageClip(card, ismask=False).set_start(start).set_duration(end - start)
            )

    output_path = "/tmp/output.mp4"
    final = CompositeVideoClip(layers, size=(LWIDTH, LHEIGHT)).set_audio(full_audio)
    final.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=4,
        logger=None,
    )

    return output_path, random.choice(LONG_TITLES), LONG_DESCRIPTION, LONG_TAGS
