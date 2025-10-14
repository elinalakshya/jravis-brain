FROM python:3.12-slim
WORKDIR /app

# Install static wkhtmltopdf binary (Render-safe)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential ca-certificates fontconfig libjpeg62-turbo libpng16-16 libx11-6 libxcb1 libxext6 libxrender1 xfonts-base xfonts-75dpi && \
    curl -L -o /usr/local/bin/wkhtmltopdf https://github.com/LakshyaAI/wkhtmltopdf-static/releases/download/v0.12.6/wkhtmltopdf-linux-amd64 && \
    chmod +x /usr/local/bin/wkhtmltopdf && \
    wkhtmltopdf --version && \
    rm -rf /var/lib/apt/lists/*

COPY . .
RUN pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
EXPOSE 10001
CMD ["gunicorn", "jravis_brain:app", "--bind", "0.0.0.0:10001"]
