FROM python:3.12-slim
WORKDIR /app

# ---- Install wkhtmltopdf safely ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl xz-utils fontconfig libjpeg62-turbo libpng16-16 libxrender1 libxext6 libx11-6 \
    xfonts-base xfonts-75dpi ca-certificates && \
    curl -L -o /tmp/wkhtmltox.deb https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.buster_amd64.deb && \
    dpkg -i /tmp/wkhtmltox.deb || apt-get -f install -y && \
    wkhtmltopdf --version && \
    rm -rf /tmp/wkhtmltox.deb /var/lib/apt/lists/*

COPY . .
RUN pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
EXPOSE 10001
CMD ["gunicorn", "jravis_brain:app", "--bind", "0.0.0.0:10001"]
