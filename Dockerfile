FROM python:3.12-slim
WORKDIR /app

# Copy and run wkhtmltopdf installer
COPY install_wkhtml.sh .
RUN bash install_wkhtml.sh

COPY . .
RUN pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
EXPOSE 10001
CMD ["gunicorn", "jravis_brain:app", "--bind", "0.0.0.0:10001"]
