import random

import requests

from bot.story_generator import MODEL, SATISFYING_BG, _split_hook, client

# Text-heavy story subreddits, mapped to the genres the rest of the bot understands.
REDDIT_SUBS = [
    ("AmItheAsshole", "aita"),
    ("tifu", "confession"),
    ("pettyrevenge", "revenge"),
    ("ProRevenge", "revenge"),
    ("confession", "confession"),
    ("nosleep", "horror"),
    ("entitledparents", "revenge"),
    ("relationship_advice", "aita"),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) reddit-story-bot/1.0",
}

CLEANUP_SYSTEM = (
    "You turn a real Reddit post into a warm, natural first-person narration for a short video. "
    "Keep the real story, the real situation and the key details. The VERY FIRST line must be a punchy "
    "hook or question that grabs attention. Then tell the story conversationally, the way someone actually "
    "talks: vary sentence length, use commas, ellipses (...) and dashes for natural pauses, use contractions, "
    "let real emotion show. Remove Reddit jargon, usernames, 'EDIT:'/'UPDATE:' notes, links, and ANY slurs or "
    "explicit content (keep it advertiser-friendly). Keep it about 200-320 words. "
    "Output ONLY the spoken words: no hashtags, no emojis, no labels."
)


def _fetch_raw_post():
    sub, genre = random.choice(REDDIT_SUBS)
    r = requests.get(
        f"https://www.reddit.com/r/{sub}/top.json",
        headers=HEADERS,
        params={"t": "month", "limit": 50},
        timeout=20,
    )
    r.raise_for_status()
    children = r.json().get("data", {}).get("children", [])

    candidates = []
    for c in children:
        d = c.get("data", {})
        text = (d.get("selftext") or "").strip()
        title = (d.get("title") or "").strip()
        if d.get("over_18") or d.get("stickied"):
            continue
        if text in ("", "[removed]", "[deleted]"):
            continue
        if not (400 <= len(text) <= 4000) or not title:
            continue
        candidates.append((title, text))

    if not candidates:
        return None
    title, text = random.choice(candidates)
    return genre, title, text


def fetch_reddit_story():
    """Return a story dict based on a real Reddit post, or None if it can't be fetched."""
    try:
        result = _fetch_raw_post()
    except Exception:
        return None
    if not result:
        return None

    genre, title, text = result
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": CLEANUP_SYSTEM},
                {"role": "user", "content": f"Title: {title}\n\n{text[:3000]}"},
            ],
            max_tokens=600,
        )
    except Exception:
        return None

    raw = resp.choices[0].message.content.strip()
    hook, body = _split_hook(raw)
    return {
        "narration": (hook + " " + body).strip(),
        "hook": hook,
        "genre": genre,
        "bg_query": random.choice(SATISFYING_BG),
        "source": "reddit",
    }
