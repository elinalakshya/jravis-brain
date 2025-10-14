# ==== Base Dockerfile for all JRAVIS + VA BOT services ====
FROM python:3.12-slim

WORKDIR /app

# Install essential system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wkhtmltopdf curl build-essential ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy code
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Default to JRAVIS Dashboard (Render overrides per service)
EXPOSE 10000
CMD ["gunicorn", "jravis_dashboard_v5:app", "--bind", "0.0.0.0:10000"]
