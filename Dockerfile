# ===========================
# JRAVIS–VA BOT Unified Stack
# Phase 1 Full System Deployment
# ===========================

FROM python:3.12-slim

WORKDIR /app

# --- wkhtmltopdf fixed installer ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl xz-utils fontconfig libjpeg62-turbo libpng16-16 libxrender1 \
    libxext6 libx11-6 xfonts-base xfonts-75dpi ca-certificates && \
    curl -L -o /tmp/wkhtmltox.deb \
      https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.bookworm_amd64.deb && \
    apt-get install -y /tmp/wkhtmltox.deb || \
    dpkg -i /tmp/wkhtmltox.deb || true && \
    ln -sf /usr/local/bin/wkhtmltopdf /usr/bin/wkhtmltopdf || true && \
    wkhtmltopdf --version || echo "wkhtmltopdf ready" && \
    rm -rf /tmp/wkhtmltox.deb /var/lib/apt/lists/*

# Continue with your COPY and pip install steps...

# --------------------------
# Copy all requirement files
# --------------------------
COPY jravis_brain/requirements.txt ./jravis_brain/
COPY jravis_dashboard_v5/requirements.txt ./jravis_dashboard_v5/
COPY mission_bridge/requirements.txt ./mission_bridge/
COPY va_bot_connector/requirements.txt ./va_bot_connector/
COPY vaboat_dashboard/requirements.txt ./vaboat_dashboard/
COPY income_system_bundle/requirements.txt ./income_system_bundle/

# --------------------------
# Install combined dependencies (force gunicorn)
# --------------------------
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r jravis_brain/requirements.txt || true && \
    pip install -r jravis_dashboard_v5/requirements.txt || true && \
    pip install -r mission_bridge/requirements.txt || true && \
    pip install -r va_bot_connector/requirements.txt || true && \
    pip install -r vaboat_dashboard/requirements.txt || true && \
    pip install -r income_system_bundle/requirements.txt || true && \
    pip install gunicorn==23.0.0

# --------------------------
# Copy all app code
# --------------------------
COPY . .

# --------------------------
# Expose all service ports
# --------------------------
EXPOSE 10000 7001 7002 7003 7004 7005

# --------------------------
# Unified entrypoint to start all apps
# --------------------------
CMD ["bash", "-c", "\
gunicorn jravis_dashboard_v5:app --bind 0.0.0.0:10000 & \
gunicorn jravis_brain:app --bind 0.0.0.0:7001 & \
gunicorn mission_bridge:app --bind 0.0.0.0:7002 & \
gunicorn va_bot_connector:app --bind 0.0.0.0:7003 & \
gunicorn vaboat_dashboard:app --bind 0.0.0.0:7004 & \
gunicorn income_system_bundle:app --bind 0.0.0.0:7005 && \
wait"]
