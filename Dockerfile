FROM python:3.10-slim

RUN apt-get update && apt-get install -y ntpdate

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip && pip install -r requirements.txt

# Синхронізація часу перед запуском юзербота
CMD ntpdate time.google.com && python userbot.py
