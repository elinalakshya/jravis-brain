# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY backend/pyproject.toml ./
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./

ENV PYTHONUNBUFFERED=1

# Uvicorn run
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
