import os
import random

from openai import OpenAI

client = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
)
MODEL = "llama-3.3-70b-versatile"

STORY_TYPES = [
    {
        "genre": "aita",
        "prompt": (
            "Write a viral Reddit AITA-style story. The VERY FIRST line must be a punchy "
            "title written as a question, like: 'Am I wrong for kicking my sister out of my wedding?' "
            "Then on a new line, tell the full first-person story with vivid, specific, realistic details "
            "(real names, ages, exact things people said) about a tense social conflict where the "
            "listener has to pick a side. End with the narrator asking 'So... am I really the bad guy here?' "
            "Around 260-320 words. Sound like a real person talking, not formal writing."
        ),
    },
    {
        "genre": "revenge",
        "prompt": (
            "Write a viral Reddit petty-revenge story. The VERY FIRST line must be an irresistible hook, "
            "like: 'My boss tried to steal my bonus, so I made sure he lost everything.' "
            "Then on a new line, tell the satisfying first-person story with specific, clever, non-violent payback "
            "against a rude boss, neighbor, or customer. Build it up and end on the exact moment of triumph. "
            "Around 260-320 words. Sound like a real person talking."
        ),
    },
    {
        "genre": "confession",
        "prompt": (
            "Write a viral Reddit confession story. The VERY FIRST line must be a gripping hook, "
            "like: 'I've never told anyone this, but I know what really happened to my brother.' "
            "Then on a new line, reveal a secret the narrator kept for years, with rising tension and "
            "a surprising emotional twist at the end. Around 260-320 words. Sound like a real person talking."
        ),
    },
    {
        "genre": "horror",
        "prompt": (
            "Write a viral Reddit true-scary-story (nosleep style). The VERY FIRST line must be a chilling hook, "
            "like: 'I still can't explain what was standing at the end of my bed that night.' "
            "Then on a new line, build slow dread with realistic, mundane details that turn wrong, "
            "and end on a final line that gives the listener chills. No gore. "
            "Around 260-320 words. Sound like a real person nervously recounting it."
        ),
    },
    {
        "genre": "wholesome",
        "prompt": (
            "Write a viral Reddit wholesome story. The VERY FIRST line must be a warm hook, "
            "like: 'I was at the lowest point of my life when a complete stranger changed everything.' "
            "Then on a new line, tell an uplifting first-person story with a genuinely touching payoff. "
            "Around 260-320 words. Sound like a real person sharing something that moved them."
        ),
    },
]

BG_QUERIES = {
    "aita": "city night rain window",
    "revenge": "office hallway empty",
    "confession": "dark road night driving",
    "horror": "dark forest fog night",
    "wholesome": "golden hour park bench",
}


def generate_story() -> dict:
    story_type = random.choice(STORY_TYPES)

    story_resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You write viral Reddit-style stories for YouTube Shorts narration. "
                    "Your number one job is the HOOK: the first sentence must make the viewer unable to scroll away. "
                    "Write in first person as a real person sharing their own story — conversational, specific, "
                    "and emotional, never formal or generic. Use concrete details that make it feel 100% real. "
                    "Build tension and pay it off with a satisfying, shocking, or moving ending. "
                    "Output ONLY the spoken words: no hashtags, no emojis, no stage directions, no labels like 'Title:'."
                ),
            },
            {"role": "user", "content": story_type["prompt"]},
        ],
        max_tokens=600,
    )
    narration = story_resp.choices[0].message.content.strip()

    FIXED_TITLE = "DONT CHECK THE SOUND!!"
    FIXED_DESCRIPTION = (
        "#shorts #viral #story #reddit #fyp #foryou #trending #storytime "
        "#satisfying #interesting #scary #confession #revenge #relatable #omg"
    )

    return {
        "narration": narration,
        "title": FIXED_TITLE,
        "description": FIXED_DESCRIPTION,
        "tags": ["shorts", "viral", "story", "reddit", "fyp", "foryou", "trending",
                 "storytime", "satisfying", "interesting", "scary", "confession",
                 "revenge", "relatable", "omg"],
        "genre": story_type["genre"],
        "bg_query": BG_QUERIES.get(story_type["genre"], "cinematic nature landscape"),
    }
