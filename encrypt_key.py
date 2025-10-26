from cryptography.fernet import Fernet
import os

key = os.getenv("SECRET_KEY").encode()
cipher = Fernet(key)

# 🔹 Paste your real Printify API key between quotes below:
api = "p_your_real_printify_api_key_here"

enc = cipher.encrypt(api.encode()).decode()
print("\n✅ COPY THIS → PRINTIFY_TOKEN_ENC=" + enc)
