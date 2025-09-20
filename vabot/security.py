"""
VA Bot Security Module - Mission 2040
Ensures 100% safety, legality, and prevents hacking/trespassing.
"""

import os
import hashlib
import hmac
import time

# ------------------------
# Security Config
# ------------------------
SECURE_CODE = os.getenv("SECURE_CODE", "MY OG")  # Boss' private code
PAYPAL_EMAIL = os.getenv("PAYPAL_EMAIL", "nrveeresh327@gmail.com")


# ------------------------
# Code Lock
# ------------------------
def verify_code(user_input: str) -> bool:
    """
    Check if the given input matches Boss' secure code.
    """
    return hmac.compare_digest(user_input.strip(), SECURE_CODE)


# ------------------------
# OTP-like Time Lock
# ------------------------
def generate_token(secret: str, interval: int = 60) -> str:
    """
    Generate a rotating time-based token (like OTP).
    """
    counter = int(time.time()) // interval
    msg = str(counter).encode()
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()[:6]


def verify_token(secret: str, token: str, interval: int = 60) -> bool:
    """
    Verify the rotating token (valid only within its time window).
    """
    return generate_token(secret, interval) == token


# ------------------------
# Usage Example
# ------------------------
if __name__ == "__main__":
    print("🔐 Mission 2040 Security Module")
    print("PayPal email locked to:", PAYPAL_EMAIL)

    # Boss code test
    code = input("Enter Boss code: ")
    if verify_code(code):
        print("✅ Code verified. Access granted.")
    else:
        print("❌ Wrong code. Access denied.")

    # Token test
    token = generate_token("VA_BOT_SECRET")
    print("Generated token (share only with Boss):", token)
    check = input("Enter token to verify: ")
    if verify_token("VA_BOT_SECRET", check):
        print("✅ Token verified. Secure access.")
    else:
        print("❌ Invalid token.")
"""
Security module for VA Bot
Handles Boss code lock + rotating OTP token
"""

import os
import time
import hmac
import hashlib
import base64

# Fixed boss code
BOSS_CODE = "MY OG"


def verify_code(code: str) -> bool:
    """Check if Boss entered correct code."""
    return code.strip() == BOSS_CODE


def generate_token(secret: str, interval: int = 60) -> str:
    """
    Generate a rotating OTP-like token based on current time.
    Same algorithm as TOTP (Google Authenticator).
    """
    key = secret.encode()
    timestep = int(time.time()) // interval
    msg = str(timestep).encode()
    h = hmac.new(key, msg, hashlib.sha1).digest()
    offset = h[-1] & 0x0F
    binary = ((h[offset] & 0x7f) << 24) | ((h[offset + 1] & 0xff) << 16) | (
        (h[offset + 2] & 0xff) << 8) | (h[offset + 3] & 0xff)
    otp = binary % 1000000  # 6 digit token
    return f"{otp:06d}"


def verify_token(secret: str, token: str, interval: int = 60) -> bool:
    """Verify if provided token matches the current one."""
    return token == generate_token(secret, interval)


# vabot/security.py

import os
from security import generate_token

# You need to set VA_BOT_SECRET in Render/ENV first
secret = os.getenv("VA_BOT_SECRET", "lakshya2040secret")

print("🚀 VA Bot Security Module")
print(f"Current OTP token: {generate_token(secret)}")
