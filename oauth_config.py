#!/usr/bin/env python3
# oauth_config.py — Google OAuth Configuration for Desktop App
# এটি Desktop App-এর জন্য Google OAuth সেটআপ করে

import os
import json
import pickle
import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# OAuth Scopes
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]

# Client Configuration (Load from environment variables)
CLIENT_CONFIG = {
    "installed": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
        "project_id": os.getenv("GOOGLE_PROJECT_ID", "yotutube-automation"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
        "redirect_uris": ["http://localhost"]
    }
}

# Validate credentials
if not CLIENT_CONFIG["installed"]["client_id"] or not CLIENT_CONFIG["installed"]["client_secret"]:
    raise ValueError(
        "❌ Google OAuth credentials not found!\n"
        "Please set environment variables:\n"
        "  - GOOGLE_CLIENT_ID\n"
        "  - GOOGLE_CLIENT_SECRET\n\n"
        "Or create a .env file with these values."
    )

TOKEN_PICKLE_FILE = "token.pickle"

def get_authenticated_service():
    """
    Google OAuth সেটআপ করে এবং authenticated YouTube service রিটার্ন করে।
    প্রথমবার চালালে ব্রাউজার খুলবে এবং আপনাকে Google দিয়ে লগইন করতে বলবে।
    """
    creds = None

    # যদি token.pickle ফাইল থাকে, সেটা ব্যবহার করো
    if os.path.exists(TOKEN_PICKLE_FILE):
        with open(TOKEN_PICKLE_FILE, 'rb') as token:
            creds = pickle.load(token)

    # যদি credentials না থাকে বা invalid থাকে, নতুন করে authenticate করো
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Token refresh করছি...")
            creds.refresh(Request())
        else:
            print("🔐 Google দিয়ে প্রথমবার লগইন করছি...")
            print("⏳ ব্রাউজার খুলবে — আপনার YouTube চ্যানেল দিয়ে লগইন করুন।\n")
            
            flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)
            creds = flow.run_local_server(port=0)

        # Token সেভ করো পরবর্তী ব্যবহারের জন্য
        with open(TOKEN_PICKLE_FILE, 'wb') as token:
            pickle.dump(creds, token)
        print("✅ Token সেভ হয়েছে!\n")

    return creds


def test_oauth():
    """OAuth সেটআপ টেস্ট করো।"""
    print("🧪 Google OAuth টেস্ট করছি...\n")
    try:
        creds = get_authenticated_service()
        print(f"✅ OAuth সফল!")
        print(f"📧 Email: {creds.token}")
        return True
    except Exception as e:
        print(f"❌ OAuth Error: {e}")
        return False


if __name__ == "__main__":
    test_oauth()
