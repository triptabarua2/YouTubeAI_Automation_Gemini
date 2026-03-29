# modules/youtube_uploader.py
# YouTube Data API দিয়ে video upload করে

import os
import sys
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import YOUTUBE_CLIENT_SECRET_FILE, VIDEO_CATEGORY_ID, CHANNEL_LANGUAGE

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube"]
TOKEN_FILE = "youtube_token.pickle"


def get_youtube_service():
    """YouTube API connection তৈরি করে"""
    creds = None

    # পুরনো token আছে কিনা দেখা
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)

    # Token নেই বা expire হয়েছে
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                YOUTUBE_CLIENT_SECRET_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)

    return build("youtube", "v3", credentials=creds)


def upload_video(video_path: str, thumbnail_path: str, script_data: dict) -> str:
    """
    Video YouTube-এ upload করে।
    Returns: Video URL
    """
    print(f"\n📤 YouTube-এ upload হচ্ছে...")

    youtube = get_youtube_service()

    # Video metadata
    body = {
        "snippet": {
            "title": script_data["title"],
            "description": script_data["description"],
            "tags": script_data["tags"],
            "categoryId": VIDEO_CATEGORY_ID,
            "defaultLanguage": CHANNEL_LANGUAGE,
            "defaultAudioLanguage": CHANNEL_LANGUAGE,
        },
        "status": {
            "privacyStatus": "private",  # প্রথমে private রাখি, approve করলে public করবে
            "selfDeclaredMadeForKids": False,
        }
    }

    # Upload
    media = MediaFileUpload(
        video_path,
        chunksize=1024 * 1024,  # 1MB chunks
        resumable=True,
        mimetype="video/mp4"
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            print(f"  📤 Upload: {progress}%")

    video_id = response["id"]
    print(f"  ✅ Upload সম্পন্ন! Video ID: {video_id}")

    # Thumbnail set করা
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
            print(f"  ✅ Thumbnail set হয়েছে")
        except Exception as e:
            print(f"  ⚠️ Thumbnail error: {e}")

    video_url = f"https://youtube.com/watch?v={video_id}"
    print(f"\n🎉 Video live: {video_url}")
    print(f"⚠️  এখন private আছে। দেখে approve করলে Public করুন।")
    return video_url


def make_video_public(video_id: str):
    """Video public করে"""
    youtube = get_youtube_service()
    youtube.videos().update(
        part="status",
        body={
            "id": video_id,
            "status": {"privacyStatus": "public"}
        }
    ).execute()
    print(f"✅ Video public হয়েছে!")
