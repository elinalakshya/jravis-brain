#!/usr/bin/env bash
set -euo pipefail

echo "🧹 Updating apt and installing wkhtmltopdf (if available)..."
apt-get update -y
apt-get install -y --no-install-recommends wkhtmltopdf ca-certificates curl || true

echo "⬆️ Upgrading pip and installing wheel/setuptools..."
python -m pip install --upgrade pip setuptools wheel

echo "📦 Installing Python dependencies..."
python -m pip install -r requirements.txt

# If playwright is in requirements, install browsers (safe no-op if not)
if python -c "import importlib,sys; sys.exit(0 if importlib.util.find_spec('playwright') else 1)"; then
  echo "🌐 Installing Playwright browsers..."
  python -m playwright install --with-deps chromium || true
fi

echo "✅ Build script finished."
