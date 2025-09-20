import os
import subprocess


def run(cmd):
    print("➤ " + " ".join(cmd))
    subprocess.run(cmd, check=True)


# Read from environment variables
PROJECT_ID = os.getenv("PROJECT_ID", "lakshya-phase1")
EMAIL = os.getenv("EMAIL")
APP_PASS = os.getenv("APP_PASS")
PAYPAL_EMAIL = os.getenv("PAYPAL_EMAIL")

if not EMAIL or not APP_PASS or not PAYPAL_EMAIL:
    raise ValueError(
        "❌ Missing EMAIL, APP_PASS, or PAYPAL_EMAIL in environment variables!")

# Configure gcloud project & region
run(["gcloud", "config", "set", "project", PROJECT_ID])
run(["gcloud", "config", "set", "run/region", "asia-south1"])

# Enable necessary APIs
run([
    "gcloud", "services", "enable", "run.googleapis.com",
    "cloudbuild.googleapis.com", "artifactregistry.googleapis.com",
    "cloudscheduler.googleapis.com", "secretmanager.googleapis.com"
])

print("✅ Setup complete. Ready for deployment.")
