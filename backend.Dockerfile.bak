# Use lightweight Python 3.11 base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirement files first for dependency caching
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend files (server.py, etc.)
COPY . ./

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Expose port for Render
EXPOSE 8000

# Start JRAVIS backend
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]

