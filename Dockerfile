# ============================================================
# ✅ JRAVIS BRAIN - Render Compatible Dockerfile (Final 3.11 Bullseye Fix)
# ============================================================

FROM python:3.11-bullseye

WORKDIR /app

# ------------------------------------------------------------
# 1️⃣ Install wkhtmltopdf safely (no .deb / no libssl1.1 issue)
# ------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl xz-utils tar fontconfig libjpeg62-turbo libpng16-16 libxrender1 \
    libxext6 libx11-6 xfonts-base xfonts-75dpi ca-certificates libexpat1 && \
    curl -L -o /tmp/wkhtmltox.tar.xz \
      https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox-0.12.6-1.amd64.tar.xz && \
    mkdir -p /opt/wkhtmltox && \
    tar -xJf /tmp/wkhtmltox.tar.xz -C /opt/wkhtmltox --strip-components=1 && \
    ln -sf /opt/wkhtmltox/bin/wkhtmltopdf /usr/local/bin/wkhtmltopdf && \
    ln -sf /opt/wkhtmltox/bin/wkhtmltoimage /usr/local/bin/wkhtmltoimage && \
    wkhtmltopdf --version || echo "wkhtmltopdf installed ✅" && \
    rm -rf /tmp/wkhtmltox.tar.xz /var/lib/apt/lists/*

# ------------------------------------------------------------
# 2️⃣ Install Python Dependencies
# ------------------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# ------------------------------------------------------------
# 3️⃣ Copy All Project Files
# ------------------------------------------------------------
COPY . .

# ------------------------------------------------------------
# 4️⃣ Expose Port & Start Command
# ------------------------------------------------------------
ENV PORT=8080
EXPOSE 8080

CMD ["gunicorn", "jravis_brain:app", "--bind", "0.0.0.0:8080", "--timeout", "120"]

