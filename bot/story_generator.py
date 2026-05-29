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
            "Write a dramatic first-person story about a social conflict — "
            "someone in a difficult situation where they question if they did the right thing. "
            "Make it feel very real and relatable. Include clear emotion and a satisfying ending. "
            "Around 300-350 words. Natural spoken style, no Reddit jargon or abbreviations."
        ),
    },
    {
        "genre": "revenge",
        "prompt": (
            "Write a satisfying first-person story where someone gets clever payback "
            "against a rude boss, neighbor, or customer. The revenge should be smart, not violent. "
            "Around 300-350 words. Natural spoken style."
        ),
    },
    {
        "genre": "confession",
        "prompt": (
            "Write a dramatic first-person confession — something the narrator kept secret for years. "
            "Make it emotional and gripping with a surprising twist or revelation. "
            "Around 300-350 words. Natural spoken style."
        ),
    },
    {
        "genre": "horror",
        "prompt": (
            "Write a short creepy first-person horror or supernatural experience story. "
            "It should feel like something that really happened. Build tension slowly, "
            "end on something chilling. Around 300-350 words. No gore."
        ),
    },
    {
        "genre": "wholesome",
        "prompt": (
            "Write a heartwarming first-person story about an unexpected act of kindness "
            "or a surprising positive moment that genuinely changed someone's perspective. "
            "Around 300-350 words. Natural spoken style."
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
                    "You are a master storyteller for YouTube Shorts narration. "
                    "Write gripping, emotional stories that hook the viewer in the first sentence. "
                    "Write naturally as if speaking out loud. No hashtags, no labels, no titles — "
                    "just the story itself."
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
