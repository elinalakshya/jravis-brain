# vabot/login_runner.py
import os
import json
from requests_oauthlib import OAuth2Session

# --- YouTube ---
YT_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
YT_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")
YT_SCOPE = ["https://www.googleapis.com/auth/youtube.readonly"]
YT_REDIRECT_URI = "http://localhost/callback"  # dummy, we won't actually open it

# --- Printify ---
PF_CLIENT_ID = os.getenv("PRINTIFY_CLIENT_ID")
PF_CLIENT_SECRET = os.getenv("PRINTIFY_CLIENT_SECRET")
PF_SCOPE = ["read:shops", "read:orders"]
PF_REDIRECT_URI = "http://localhost/callback"  # dummy


def youtube_login():
    oauth = OAuth2Session(YT_CLIENT_ID,
                          scope=YT_SCOPE,
                          redirect_uri=YT_REDIRECT_URI)
    auth_url, state = oauth.authorization_url(
        "https://accounts.google.com/o/oauth2/auth",
        access_type="offline",
        prompt="consent")
    print("\n🔑 YouTube Login URL:\n", auth_url)
    code = input("\nPaste the 'code=' value from the redirect URL here: ")
    token = oauth.fetch_token("https://oauth2.googleapis.com/token",
                              client_secret=YT_CLIENT_SECRET,
                              code=code)
    with open("youtube_token.json", "w") as f:
        json.dump(token, f, indent=2)
    print("✅ YouTube token saved to youtube_token.json")


def printify_login():
    oauth = OAuth2Session(PF_CLIENT_ID,
                          scope=PF_SCOPE,
                          redirect_uri=PF_REDIRECT_URI)
    auth_url, state = oauth.authorization_url(
        "https://auth.printify.com/oauth/authorize")
    print("\n🔑 Printify Login URL:\n", auth_url)
    code = input("\nPaste the 'code=' value from the redirect URL here: ")
    token = oauth.fetch_token("https://auth.printify.com/oauth/token",
                              client_secret=PF_CLIENT_SECRET,
                              code=code)
    with open("printify_token.json", "w") as f:
        json.dump(token, f, indent=2)
    print("✅ Printify token saved to printify_token.json")


if __name__ == "__main__":
    print("---- YOUTUBE LOGIN ----")
    youtube_login()
    print("\n---- PRINTIFY LOGIN ----")
    printify_login()
