import os, subprocess, time
from cryptography.fernet import Fernet


def auto_encrypt_and_push():
    print("🔐 Starting JRAVIS auto-encrypt + push...")

    # 1️⃣ Load or create secret key
    key_path = "secret.key"
    if not os.path.exists(key_path):
        key = Fernet.generate_key()
        with open(key_path, "wb") as f:
            f.write(key)
        print("✅ secret.key created.")
    else:
        with open(key_path, "rb") as f:
            key = f.read()

    cipher = Fernet(key)

    # 2️⃣ Encrypt Printify key (or any other keys)
    api_key = os.getenv("PRINTIFY_API_KEY", "").strip()
    if not api_key:
        api_key = input(
            "Enter your Printify API key (starts with e_ or p_): ").strip()

    enc = cipher.encrypt(api_key.encode()).decode()
    print("\n✅ New encrypted key:\nPRINTIFY_TOKEN_ENC=" + enc)

    # 3️⃣ Save to .env
    with open(".env", "w") as f:
        f.write(f"PRINTIFY_TOKEN_ENC={enc}\n")

    # 4️⃣ Git commit + push automatically
    print("\n📦 Committing and pushing to GitHub...")
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", "Auto encrypt & push update"],
                   check=False)
    subprocess.run(["git", "push"], check=True)

    print("\n🚀 Done! Render will auto-deploy shortly.")
    time.sleep(2)


if __name__ == "__main__":
    auto_encrypt_and_push()
