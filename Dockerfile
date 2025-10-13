# Dockerfile - deterministic build with Python 3.12 slim
FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PORT=10000
WORKDIR /app

# system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    wkhtmltopdf ca-certificates curl build-essential \
 && rm -rf /var/lib/apt/lists/*

# copy app
COPY . /app

# pip
RUN python -m pip install --upgrade pip setuptools wheel
RUN python -m pip install -r requirements.txt

# optional playwright browsers (if playwright used)
RUN python -m playwright install --with-deps chromium || true

EXPOSE 10000
CMD ["gunicorn", "jravis_dashboard_v5:app", "--bind", "0.0.0.0:10000"]
