
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from config import CHANNELS

SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"]

def get_auth_for_channel(channel_id):
    ch = CHANNELS.get(channel_id)
    if not ch:
        print(f"❌ Channel {channel_id} not found!")
        return

    client_secret = ch['client_secret']
    token_file = ch['token_file']

    if not os.path.exists(client_secret):
        print(f"❌ {client_secret} file not found! Please upload it first.")
        return

    print(f"\n🔐 Authorizing for {ch['name']}...")
    flow = InstalledAppFlow.from_client_secrets_file(client_secret, SCOPES)
    
    # Use console flow for Colab
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    print(f"\n1. এই লিঙ্কে ক্লিক করুন: \n{auth_url}")
    print("\n2. আপনার YouTube একাউন্ট দিয়ে লগইন করে 'Allow' দিন।")
    code = input("\n3. ব্রাউজার থেকে পাওয়া Authorization Code এখানে পেস্ট করুন: ")
    
    try:
        flow.fetch_token(code=code)
        creds = flow.credentials
        with open(token_file, "wb") as f:
            pickle.dump(creds, f)
        print(f"✅ Authorization সফল! {token_file} সেভ হয়েছে।")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("--- YouTube AI Automation Colab Auth Helper ---")
    print("১. channel_1")
    print("২. channel_2")
    print("৩. channel_3")
    choice = input("\nকোন চ্যানেলের জন্য অথরাইজ করবেন? (১/২/৩): ")
    
    mapping = {"1": "channel_1", "2": "channel_2", "3": "channel_3", "১": "channel_1", "২": "channel_2", "৩": "channel_3"}
    channel_id = mapping.get(choice)
    
    if channel_id:
        get_auth_for_channel(channel_id)
    else:
        print("❌ ভুল ইনপুট!")
