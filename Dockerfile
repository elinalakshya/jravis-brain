# ==================================================
# Universal Render-safe Dockerfile for JRAVIS + VA Bot modules
# ==================================================

FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_ROOT_USER_ACTION=ignore

WORKDIR /app

# --------------------------
# Install wkhtmltopdf safely from Debian Bookworm repos
# --------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    wkhtmltopdf curl wget gnupg ca-certificates \
    fontconfig libjpeg62-turbo libpng16-16 libxrender1 libxext6 \
    libx11-6 xfonts-base xfonts-75dpi && \
    wkhtmltopdf --version && \
    rm -rf /var/lib/apt/lists/*

# --------------------------
# Copy app code
# --------------------------
COPY . .

# --------------------------
# Install Python dependencies
# --------------------------
RUN pip install --upgrade pip setuptools wheel && \
    pip install Flask==3.0.3 APScheduler==3.10.4 PyYAML==6.0.2 gunicorn==23.0.0 \
        pdfkit==1.0.0 PyPDF2==3.0.1 reportlab==4.2.2 openai==1.51.0 \
        requests==2.32.3 pytz==2024.1 rich==13.7.1

# --------------------------
# Expose and run with Gunicorn
# (Each app must have app = Flask(__name__) defined)
# --------------------------
EXPOSE 8080
CMD gunicorn app:app --bind 0.0.0.0:$PORT
