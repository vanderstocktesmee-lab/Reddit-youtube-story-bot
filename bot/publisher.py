import os

import requests

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPO = os.environ["GITHUB_REPOSITORY"]
MAKE_WEBHOOK_URL = os.environ["MAKE_WEBHOOK_URL"]
RUN_ID = os.environ.get("GITHUB_RUN_ID", "local")


def publish_video(video_path: str, title: str, description: str, tags: list) -> str:
    api = f"https://api.github.com/repos/{GITHUB_REPO}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    r = requests.post(
        f"{api}/releases",
        headers=headers,
        json={"tag_name": f"video-{RUN_ID}", "name": title[:100], "body": description},
        timeout=30,
    )
    r.raise_for_status()
    upload_url = r.json()["upload_url"].split("{")[0]

    with open(video_path, "rb") as f:
        r = requests.post(
            f"{upload_url}?name=video.mp4",
            headers={**headers, "Content-Type": "video/mp4"},
            data=f,
            timeout=180,
        )
    r.raise_for_status()
    video_url = r.json()["browser_download_url"]

    requests.post(
        MAKE_WEBHOOK_URL,
        json={
            "video_url": video_url,
            "title": title,
            "description": description,
            "tags": ",".join(tags),
        },
        timeout=30,
    )

    return video_url
