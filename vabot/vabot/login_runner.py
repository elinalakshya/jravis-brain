# vabot/login_runner.py
import os, json
from requests_oauthlib import OAuth2Session

YT_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
YT_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")
SCOPE = ["https://www.googleapis.com/auth/youtube.readonly"]
REDIRECT_URI = "http://localhost:8080/callback"  # must match Google Console


def youtube_manual_login():
    if not YT_CLIENT_ID or not YT_CLIENT_SECRET:
        print("❌ Missing YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET")
        return

    oauth = OAuth2Session(YT_CLIENT_ID, scope=SCOPE, redirect_uri=REDIRECT_URI)

    # Use the v2 auth endpoint and keep params stable
    auth_url, state = oauth.authorization_url(
        "https://accounts.google.com/o/oauth2/v2/auth",
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true")
    print(
        "\n🔑 Open this URL in your browser, approve access, then copy the FULL redirect URL from the address bar:"
    )
    print(auth_url)

    redirect_full_url = input(
        "\nPaste the FULL redirect URL here (starts with http://localhost:8080/callback?...): "
    ).strip()
    if not redirect_full_url:
        print("❌ No URL provided.")
        return

    # Exchange the code using the full redirect URL (prevents state/redirect mismatches)
    token = oauth.fetch_token("https://oauth2.googleapis.com/token",
                              client_secret=YT_CLIENT_SECRET,
                              authorization_response=redirect_full_url,
                              include_client_id=True)

    with open("youtube_token.json", "w") as f:
        json.dump(token, f, indent=2)
    print("✅ YouTube token saved to youtube_token.json")


if __name__ == "__main__":
    print("---- YOUTUBE LOGIN (manual) ----")
    youtube_manual_login()
    print("\n---- PRINTIFY LOGIN ----")
    print("ℹ️ Printify will be done tomorrow.")
