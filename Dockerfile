# Use Python 3.10
FROM python:3.10-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080
CMD ["python", "main.py"]

# ---- Base image ----
FROM python:3.12-slim

# ---- System dependencies ----
RUN apt-get update && apt-get install -y \
    wkhtmltopdf curl git \
 && rm -rf /var/lib/apt/lists/*

# ---- App setup ----
WORKDIR /app
COPY . /app

RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt
RUN python -m playwright install --with-deps chromium

# ---- Runtime ----
ENV PORT=10000
CMD ["gunicorn", "jravis_dashboard_v5:app", "--bind", "0.0.0.0:10000"]
