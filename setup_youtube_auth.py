"""
Run this script ONCE on your PC to get your YouTube credentials.
After running, copy the printed JSON into GitHub Secrets as YOUTUBE_CREDENTIALS.

Requirements:
    pip install google-auth-oauthlib google-api-python-client

Steps:
    1. Go to https://console.cloud.google.com/
    2. Create a new project (or use existing)
    3. Enable "YouTube Data API v3"
    4. Go to "Credentials" -> "Create Credentials" -> "OAuth 2.0 Client ID"
    5. Choose "Desktop app"
    6. Download the JSON file and save it as client_secrets.json next to this script
    7. Run: python setup_youtube_auth.py
    8. A browser will open — log in with the YouTube channel's Google account
    9. Copy the printed JSON and paste it into GitHub -> Settings -> Secrets -> YOUTUBE_CREDENTIALS
"""

import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
creds = flow.run_local_server(port=0)

output = {
    "token": creds.token,
    "refresh_token": creds.refresh_token,
    "client_id": creds.client_id,
    "client_secret": creds.client_secret,
}

print("\n" + "=" * 60)
print("COPY THIS INTO GITHUB SECRET 'YOUTUBE_CREDENTIALS':")
print("=" * 60)
print(json.dumps(output, indent=2))
print("=" * 60 + "\n")
