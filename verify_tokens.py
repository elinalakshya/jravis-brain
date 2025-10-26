from token_manager import get_token
import requests


def verify_meshy():
    try:
        token = get_token("meshy")
        # Dummy test endpoint – replace with a real one if needed
        r = requests.get("https://api.meshy.ai/v1/user",
                         headers={"Authorization": f"Bearer {token}"})
        print("✅ Meshy connection:", r.status_code, r.reason)
    except Exception as e:
        print("❌ Meshy error:", e)


def verify_printify():
    try:
        token = get_token("printify")
        r = requests.get("https://api.printify.com/v1/shops.json",
                         headers={"Authorization": f"Bearer {token}"})
        print("✅ Printify connection:", r.status_code, r.reason)
    except Exception as e:
        print("❌ Printify error:", e)


def verify_youtube():
    try:
        token = get_token("youtube")
        # Using a harmless YouTube API call
        r = requests.get(
            f"https://www.googleapis.com/youtube/v3/channels?part=id&mine=true&access_token={token}"
        )
        print("✅ YouTube connection:", r.status_code, r.reason)
    except Exception as e:
        print("❌ YouTube error:", e)


if __name__ == "__main__":
    print("\n🔐 Phase 2 Token Verification — JRAVIS Live Mode\n")
    verify_meshy()
    verify_printify()
    verify_youtube()
    print("\n✅ Verification complete.")
