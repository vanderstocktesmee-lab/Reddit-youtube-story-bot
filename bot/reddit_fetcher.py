import praw
import os
import random


def fetch_story(subreddits: list[str]) -> dict:
    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent="youtube-story-bot/1.0",
    )

    random.shuffle(subreddits)

    for subreddit_name in subreddits:
        for time_filter in ["day", "week"]:
            posts = list(
                reddit.subreddit(subreddit_name).top(
                    time_filter=time_filter, limit=30
                )
            )
            valid = [
                p
                for p in posts
                if p.selftext
                and not p.stickied
                and 400 <= len(p.selftext.split()) <= 3000
            ]
            if valid:
                post = random.choice(valid[:8])
                return {
                    "title": post.title,
                    "text": post.selftext,
                    "subreddit": subreddit_name,
                    "score": post.score,
                }

    raise RuntimeError("No suitable Reddit post found across all subreddits.")
