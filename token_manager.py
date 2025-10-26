"""
token_manager.py — Final Production Version
Handles encryption, decryption, and secure loading of API tokens for JRAVIS/VA Bot.
"""

import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv("/home/runner/workspace/.env")

# ==============================================================
# 1. Load environment variables from available dotenv files
# ==============================================================

# Preferred file order
DOTENV_PATHS = [
    os.path.join(os.getcwd(), ".env"),
    os.path.join(os.getcwd(), ".envfile"),
    os.path.join(os.getcwd(), "env_test"),
]

loaded_paths = []
for path in DOTENV_PATHS:
    if os.path.isfile(path):
        load_dotenv(dotenv_path=path, override=False)
        loaded_paths.append(path)

# Also call load_dotenv() to capture Replit Secrets (environment injection)
load_dotenv(override=False)

# ==============================================================
# 2. Diagnostics helper (non-sensitive)
# ==============================================================


def print_diagnostics():
    print("\n[TokenManager Diagnostics]")
    if loaded_paths:
        print("Loaded dotenv from:", ", ".join(loaded_paths))
    else:
        print("No dotenv file auto-loaded from standard paths.")

    keys_to_check = [
        "MESHY_TOKEN_ENC",
        "PRINTIFY_TOKEN_ENC",
        "YOUTUBE_TOKEN_ENC",
    ]
    for key in keys_to_check:
        val = os.getenv(key)
        if val:
            print(f"  - {key}: present (len={len(val)})")
        else:
            print(f"  - {key}: MISSING")
    print("[End diagnostics]\n")


# ==============================================================
# 3. Key file handling (secret.key)
# ==============================================================

KEY_FILE = "secret.key"


def generate_key():
    """Generate and save a new Fernet encryption key."""
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)
        print("[TokenManager] New encryption key created.")
    else:
        print(f"[TokenManager] Key already exists at {KEY_FILE}")


def load_key():
    env_key = os.getenv("SECRET_KEY")
    if env_key:
        return env_key.encode()
    if os.path.exists("secret.key"):
        with open("secret.key", "rb") as f:
            return f.read()

    raise FileNotFoundError(
        "[TokenManager] secret.key not found. Run generate_key() first.")

    raise FileNotFoundError(
        "[TokenManager] secret.key not found. Run generate_key() first.")


# ==============================================================
# 4. Encryption / Decryption
# ==============================================================


def encrypt_token(token: str) -> str:
    """Encrypt a plain API key string."""
    cipher = Fernet(load_key())
    return cipher.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt an encrypted API key string."""
    cipher = Fernet(load_key())
    return cipher.decrypt(encrypted_token.encode()).decode()


# ==============================================================
# 5. Token Retrieval
# ==============================================================


def get_token(service_name: str) -> str:
    """
    Retrieve and decrypt the API token for a given service.
    Example:
        get_token("printify")
        get_token("meshy")
        get_token("youtube")
    """
    env_key = f"{service_name.upper()}_TOKEN_ENC"
    encrypted_value = os.getenv(env_key)
    if not encrypted_value:
        raise ValueError(
            f"[TokenManager] No encrypted token found for {service_name}.")
    try:
        return decrypt_token(encrypted_value)
    except Exception as e:
        raise ValueError(
            f"[TokenManager] Decryption error for {service_name}: {e}")


# ==============================================================
# 6. Diagnostics auto-run
# ==============================================================

if __name__ == "__main__":
    print_diagnostics()
    print("[TokenManager] Ready for encryption/decryption operations.")
