#!/usr/bin/env python3
import os, subprocess, sys

PROJECT_ID = input("Enter GCP PROJECT_ID: ").strip()
REGION     = "asia-south1"  # Mumbai
EMAIL      = input("Sender Gmail (EMAIL): ").strip()
APP_PASS   = input("Gmail App Password (APP_PASS): ").strip()
PAYPAL     = input("PayPal Email (PAYPAL_EMAIL): ").strip()

IMAGE = f"{REGION}-docker.pkg.dev/{PROJECT_ID}/va-bot/va-bot:latest"

def run(cmd):
    print("➤", " ".join(cmd))
    subprocess.run(cmd, check=True)

# 1. Config
run(["gcloud", "config", "set", "project", PROJECT_ID])
run(["gcloud", "config", "set", "run/region", REGION])

# 2. Enable services
run(["gcloud", "services", "enable",
     "run.googleapis.com","cloudbuild.googleapis.com",
     "artifactregistry.googleapis.com","cloudscheduler.googleapis.com",
     "secretmanager.googleapis.com"])

# 3. Secrets
for name, val in [("EMAIL", EMAIL), ("APP_PASS", APP_PASS), ("PAYPAL_EMAIL", PAYPAL)]:
    try:
        run(["bash","-c", f"echo -n '{val}' | gcloud secrets create {name} --data-file=-"])
    except:
        run(["bash","-c", f"echo -n '{val}' | gcloud secrets versions add {name} --data-file=-"])

# 4. Artifact Registry
run(["gcloud","artifacts","repositories","create","va-bot",
     "--repository-format=docker","--location",REGION],
    )

# 5. Build & Push
run(["gcloud","builds","submit","--tag",IMAGE])

print("✅ Setup complete. Cloud Run Job creation next step needs Cloud Shell (with run jobs).")
