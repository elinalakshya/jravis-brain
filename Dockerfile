FROM python:3.12-slim
WORKDIR /app

COPY ../install_wkhtml.sh .
RUN bash install_wkhtml.sh

COPY ../requirements.txt .
RUN pip install --upgrade pip setuptools wheel && pip install -r requirements.txt

COPY . .
EXPOSE 10000
CMD ["gunicorn", "FILENAME:app", "--bind", "0.0.0.0:10000"]
