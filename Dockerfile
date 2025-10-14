# ✅ Install wkhtmltopdf safely (no .deb, no libssl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl xz-utils tar fontconfig libjpeg62-turbo libpng16-16 libxrender1 \
    libxext6 libx11-6 xfonts-base xfonts-75dpi ca-certificates && \
    curl -L -o /tmp/wkhtmltox.tar.xz \
      https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox-0.12.6-1.amd64.tar.xz && \
    mkdir -p /opt/wkhtmltox && \
    tar -xJf /tmp/wkhtmltox.tar.xz -C /opt/wkhtmltox --strip-components=1 && \
    ln -sf /opt/wkhtmltox/bin/wkhtmltopdf /usr/local/bin/wkhtmltopdf && \
    ln -sf /opt/wkhtmltox/bin/wkhtmltoimage /usr/local/bin/wkhtmltoimage && \
    wkhtmltopdf --version || echo "wkhtmltopdf installed ✅" && \
    rm -rf /tmp/wkhtmltox.tar.xz /var/lib/apt/lists/*

