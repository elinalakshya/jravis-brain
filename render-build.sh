#!/usr/bin/env bash
set -e

# Clean start
apt-get update -y
apt-get install -y wkhtmltopdf
pip install --upgrade pip setuptools wheel

# Fresh environment
python --version
pip install -r requirements.txt
python -m playwright install --with-deps chromium
