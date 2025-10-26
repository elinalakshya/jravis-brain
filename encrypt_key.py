from cryptography.fernet import Fernet
import os

# Load existing secret key from environment (Render)
key = os.getenv("SECRET_KEY")
if not key:
    raise SystemExit("❌ SECRET_KEY not found in environment. Go to Render > Environment and add it first.")

cipher = Fernet(key.encode())

# 🔹 Paste your real Printify API key here (the one starting with e_ or p_)
api = "e_your_real_printify_key_here"

enc = cipher.encrypt(api.encode()).decode()
print("\n✅ COPY THIS → PRINTIFY_TOKEN_ENC=" + enc)
