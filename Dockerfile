# ==================================================
# JRAVIS Dashboard v5 — Render-stable deployment (wkhtmltopdf fix)
# ==================================================

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_ROOT_USER_ACTION=ignore

WORKDIR /app

# --------------------------
# Install wkhtmltopdf (Ubuntu Jammy source, fully compatible)
# --------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl wget gnupg ca-certificates software-properties-common \
        fontconfig libjpeg62-turbo libpng16-16 libxrender1 libxext6 \
        libx11-6 xfonts-base xfonts-75dpi && \
    echo "deb http://archive.ubuntu.com/ubuntu/ jammy main universe" > /etc/apt/sources.list.d/jammy.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends wkhtmltopdf && \
    wkhtmltopdf --version && \
    rm -rf /var/lib/apt/lists/*

# --------------------------
# Copy requirements
# --------------------------
COPY jravis_brain/requirements.txt ./jravis_brain/
COPY jravis_dashboard_v5/requirements.txt ./jravis_dashboard_v5/
COPY mission_bridge/requirements.txt ./mission_bridge/
COPY va_bot_connector/requirements.txt ./va_bot_connector/
COPY vaboat_dashboard/requirements.txt ./vaboat_dashboard/
COPY income_system_bundle/requirements.txt ./income_system_bundle/

# --------------------------
# Install Python dependencies
# --------------------------
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
# Expose & Run
# --------------------------
EXPOSE 8080
CMD gunicorn jravis_dashboard_v5:app --bind 0.0.0.0:$PORT
