# === VA Bot Receiver Dockerfile ===
FROM python:3.11-slim

# Working directory
WORKDIR /app

# Copy requirements first for caching
COPY vabot_receiver/requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY vabot_receiver/ ./

# Expose Render port
EXPOSE 8000

# Start FastAPI server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
