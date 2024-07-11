FROM python:3.11.9-slim

ENV TZ="Asia/Kolkata"

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "gunicorn", "--bind", "0.0.0.0:8000", "wsgi:app" ]