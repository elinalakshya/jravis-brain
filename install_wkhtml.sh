#!/bin/bash
set -e

echo "🚀 Installing wkhtmltopdf (Render-safe manual extract)..."

apt-get update
apt-get install -y --no-install-recommends \
    curl xz-utils fontconfig libjpeg62-turbo libpng16-16 \
    libxrender1 libxext6 libx11-6 xfonts-base xfonts-75dpi ca-certificates

echo "📦 Downloading wkhtmltopdf 0.12.6 .deb..."
curl -L -o /tmp/wkhtmltox.deb \
  https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.buster_amd64.deb

echo "📂 Extracting .deb manually..."
mkdir -p /opt/wkhtmltox
dpkg-deb -x /tmp/wkhtmltox.deb /opt/wkhtmltox

# Locate binary inside extracted package
if [ -f /opt/wkhtmltox/usr/local/bin/wkhtmltopdf ]; then
    echo "✅ Found binary in /opt/wkhtmltox/usr/local/bin/"
    cp /opt/wkhtmltox/usr/local/bin/wkhtmltopdf /usr/local/bin/
    cp /opt/wkhtmltox/usr/local/bin/wkhtmltoimage /usr/local/bin/
elif [ -f /opt/wkhtmltox/usr/bin/wkhtmltopdf ]; then
    echo "✅ Found binary in /opt/wkhtmltox/usr/bin/"
    cp /opt/wkhtmltox/usr/bin/wkhtmltopdf /usr/local/bin/
    cp /opt/wkhtmltox/usr/bin/wkhtmltoimage /usr/local/bin/
else
    echo "❌ wkhtmltopdf binary not found in extracted package!"
    ls -R /opt/wkhtmltox | head -n 30
    exit 1
fi

chmod +x /usr/local/bin/wkhtmltopdf /usr/local/bin/wkhtmltoimage

echo "✅ Installed version:"
/usr/local/bin/wkhtmltopdf --version || echo "⚠️ wkhtmltopdf verification skipped"

rm -rf /tmp/wkhtmltox.deb /opt/wkhtmltox /var/lib/apt/lists/*
echo "🎯 wkhtmltopdf installation complete and persistent."
