FROM python:3.12-slim
WORKDIR /app

# Install wkhtmltopdf from official PPA (Render-safe)
RUN apt-get update && \
    apt-get install -y --no-install-recommends software-properties-common && \
    add-apt-repository ppa:somesh/wkhtmltopdf && \
    apt-get update && \
    apt-get install -y --no-install-recommends wkhtmltopdf fontconfig libfreetype6 libjpeg62-turbo libpng16-16 libx11-6 libxcb1 libxext6 libxrender1 xfonts-base xfonts-75dpi && \
    rm -rf /var/lib/apt/lists/*

COPY . .
RUN pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
EXPOSE 10001
CMD ["gunicorn", "jravis_brain:app", "--bind", "0.0.0.0:10001"]
