"""
YouTube upload for Claim Defend Advocacy episodes, using the YouTube Data API v3.

One-time setup (do this in your Google account, not here):
    1. Go to https://console.cloud.google.com/ and create a project
       (e.g. "Claim Defend Advocacy").
    2. APIs & Services > Library > enable "YouTube Data API v3".
    3. APIs & Services > OAuth consent screen > configure as "External",
       add your own Google account as a test user (keeps the app in
       Testing mode, which is fine for personal use).
    4. APIs & Services > Credentials > Create Credentials > OAuth client ID
       > Application type "Desktop app". Download the JSON.
    5. Save the downloaded file as client_secret.json in this scripts/
       directory (it's already covered by .gitignore — never commit it).

Required pip packages (added to requirements.txt):
    google-auth-oauthlib
    google-api-python-client

First run opens a browser for you to authorize the app against your own
YouTube channel. A token.json is cached afterward so you won't be prompted
every time (token.json is also gitignored).

Usage:
    python scripts/youtube_upload.py path/to/episode1.mp4 \\
        --title "The Roof Damage Trap: Why Your Initial Inspection is a Lie" \\
        --description "..." \\
        --tags "roof insurance claim,property damage,public adjuster"
"""

import argparse
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRET_FILE = os.path.join(SCRIPT_DIR, "client_secret.json")
TOKEN_FILE = os.path.join(SCRIPT_DIR, "token.json")
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_authenticated_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRET_FILE):
                raise RuntimeError(
                    f"Missing {CLIENT_SECRET_FILE}. Download OAuth client "
                    "credentials from Google Cloud Console and save them there."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token_file:
            token_file.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def upload_video(video_path, title, description, tags, privacy_status="public"):
    if not os.path.exists(video_path):
        raise FileNotFoundError(video_path)

    youtube = get_authenticated_service()

    body = {
        "snippet": {
            "title": f"Claim Defend Podcast - {title}",
            "description": description,
            "tags": tags,
            "categoryId": "27",  # Education
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/*")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[..] Upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"[OK] Uploaded. Video ID: {video_id} (https://youtu.be/{video_id})")
    return video_id


def main():
    parser = argparse.ArgumentParser(description="Upload an episode to YouTube.")
    parser.add_argument("video_path", help="Path to the video file")
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument(
        "--privacy",
        default="public",
        choices=["private", "unlisted", "public"],
        help="Defaults to public",
    )
    args = parser.parse_args()

    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    upload_video(args.video_path, args.title, args.description, tags, args.privacy)


if __name__ == "__main__":
    main()
