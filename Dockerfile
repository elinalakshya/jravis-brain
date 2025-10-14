FROM python:3.12-slim
WORKDIR /app

# Install wkhtmltopdf safely
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl xfonts-base xfonts-75dpi libjpeg62-turbo fontconfig libxrender1 libxext6 libx11-6 ca-certificates && \
    curl -L -o /tmp/wkhtmltox.tar.xz https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox-0.12.6-1.alpine3.17-amd64.tar.xz && \
    mkdir -p /opt/wkhtmltox && \
    tar -xf /tmp/wkhtmltox.tar.xz -C /opt/wkhtmltox --strip-components=1 && \
    ln -s /opt/wkhtmltox/bin/wkhtmltopdf /usr/local/bin/wkhtmltopdf && \
    ln -s /opt/wkhtmltox/bin/wkhtmltoimage /usr/local/bin/wkhtmltoimage && \
    wkhtmltopdf --version && \
    rm -rf /tmp/wkhtmltox.tar.xz /var/lib/apt/lists/*

COPY . .
RUN pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
EXPOSE 10001
CMD ["gunicorn", "jravis_brain:app", "--bind", "0.0.0.0:10001"]
