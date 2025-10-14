#!/bin/bash
set -e

echo "🚀 Installing wkhtmltopdf (Render-safe universal installer)..."

apt-get update
apt-get install -y --no-install-recommends \
    curl xz-utils fontconfig libjpeg62-turbo libpng16-16 \
    libxrender1 libxext6 libx11-6 xfonts-base xfonts-75dpi ca-certificates

echo "📦 Downloading wkhtmltopdf 0.12.6 .deb..."
curl -L -o /tmp/wkhtmltox.deb \
  https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.buster_amd64.deb

echo "🔧 Installing .deb package..."
dpkg -i /tmp/wkhtmltox.deb || apt-get -f install -y

echo "✅ Installed version:"
wkhtmltopdf --version

rm -rf /tmp/wkhtmltox.deb /var/lib/apt/lists/*
echo "🎯 wkhtmltopdf installation complete."
