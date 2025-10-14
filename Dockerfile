# ==================================================
# JRAVIS Dashboard v5 — Render-safe Unified Deployment
# ==================================================

FROM python:3.12-slim

# Environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_ROOT_USER_ACTION=ignore

WORKDIR /app

# --------------------------
# Install system dependencies (wkhtmltopdf included)
# --------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl xz-utils fontconfig libjpeg62-turbo libpng16-16 libxrender1 \
    libxext6 libx11-6 xfonts-base xfonts-75dpi ca-certificates && \
    curl -L -o /tmp/wkhtmltox.tar.xz \
      https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox-0.12.6-1.amd64.tar.xz && \
    mkdir -p /opt/wkhtmltox && \
    tar -xf /tmp/wkhtmltox.tar.xz -C /opt/wkhtmltox --strip-components=1 && \
    ln -s /opt/wkhtmltox/bin/wkhtmltopdf /usr/local/bin/wkhtmltopdf && \
    ln -s /opt/wkhtmltox/bin/wkhtmltoimage /usr/local/bin/wkhtmltoimage && \
    wkhtmltopdf --version && \
    rm -rf /tmp/wkhtmltox.tar.xz /var/lib/apt/lists/*

# --------------------------
# Install Python dependencies
# --------------------------
COPY jravis_brain/requirements.txt ./jravis_brain/
COPY jravis_dashboard_v5/requirements.txt ./jravis_dashboard_v5/
COPY mission_bridge/requirements.txt ./mission_bridge/
COPY va_bot_connector/requirements.txt ./va_bot_connector/
COPY vaboat_dashboard/requirements.txt ./vaboat_dashboard/
COPY income_system_bundle/requirements.txt ./income_system_bundle/

RUN pip install --upgrade pip setuptools wheel && \
    pip install -r jravis_brain/requirements.txt || true && \
    pip install -r jravis_dashboard_v5/requirements.txt || true && \
    pip install -r mission_bridge/requirements.txt || true && \
    pip install -r va_bot_connector/requirements.txt || true && \
    pip install -r vaboat_dashboard/requirements.txt || true && \
    pip install -r income_system_bundle/requirements.txt || true && \
    pip install Flask==3.0.3 APScheduler==3.10.4 PyYAML==6.0.2 gunicorn==23.0.0 \
        pdfkit==1.0.0 PyPDF2==3.0.1 reportlab==4.2.2 openai==1.51.0 \
        requests==2.32.3 pytz==2024.1 rich==13.7.1

# --------------------------
# Copy all source code
# --------------------------
COPY . .

# --------------------------
# Expose and run
# --------------------------
EXPOSE 8080
CMD gunicorn jravis_dashboard_v5:app --bind 0.0.0.0:$PORT
