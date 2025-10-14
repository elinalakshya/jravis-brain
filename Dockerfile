FROM python:3.12-slim
WORKDIR /app

# Install system deps + wkhtmltopdf binary
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential ca-certificates fontconfig libfreetype6 libjpeg62-turbo libpng16-16 libx11-6 libxcb1 libxext6 libxrender1 xfonts-base xfonts-75dpi && \
    curl -L -o /tmp/wkhtmltopdf.deb https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.bookworm_amd64.deb && \
    apt install -y /tmp/wkhtmltopdf.deb && \
    rm -rf /var/lib/apt/lists/* /tmp/wkhtmltopdf.deb

COPY . .
RUN pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
EXPOSE 10001
CMD ["gunicorn", "jravis_brain:app", "--bind", "0.0.0.0:10001"]

# Install essential system dependencies + wkhtmltopdf
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential ca-certificates fontconfig libfreetype6 libjpeg62-turbo libpng16-16 libx11-6 libxcb1 libxext6 libxrender1 xfonts-base xfonts-75dpi && \
    curl -L -o /tmp/wkhtmltopdf.deb https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.bookworm_amd64.deb && \
    apt install -y /tmp/wkhtmltopdf.deb && \
    rm -rf /var/lib/apt/lists/* /tmp/wkhtmltopdf.deb


