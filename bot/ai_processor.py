import json
import os

from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])
MODEL = "llama-3.3-70b-versatile"


def process_story(story: dict) -> dict:
    narration = _rewrite_for_narration(story)
    metadata = _generate_metadata(story, narration)
    return {
        "narration": narration,
        "title": metadata["title"],
        "description": metadata["description"],
        "tags": metadata["tags"],
        "subreddit": story["subreddit"],
    }


def _rewrite_for_narration(story: dict) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a YouTube narrator. Rewrite the Reddit story below for "
                    "engaging audio narration. Rules: remove all Reddit formatting "
                    "(asterisks, AITA, TL;DR, edit notes, usernames). Use natural "
                    "spoken English. Add dramatic pauses with '...' where appropriate. "
                    "Start with a hook sentence. Keep under 1800 words."
                ),
            },
            {
                "role": "user",
                "content": f"Title: {story['title']}\n\n{story['text']}",
            },
        ],
        max_tokens=2200,
    )
    return resp.choices[0].message.content.strip()


def _generate_metadata(story: dict, narration: str) -> dict:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Generate YouTube metadata. Return ONLY valid JSON with keys: "
                    "title (string, max 90 chars, catchy, no spoilers), "
                    "description (string, 2 paragraphs + hashtags), "
                    "tags (array of 15 strings)."
                ),
            },
            {
                "role": "user",
                "content": f"Story title: {story['title']}\n\nNarration preview: {narration[:600]}",
            },
        ],
        max_tokens=700,
        response_format={"type": "json_object"},
    )
    data = json.loads(resp.choices[0].message.content)
    return {
        "title": str(data.get("title", story["title"]))[:90],
        "description": str(data.get("description", "")),
        "tags": list(data.get("tags", []))[:15],
    }
