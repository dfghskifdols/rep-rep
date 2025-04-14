# Встановлюємо залежності
FROM python:3.10-slim

RUN apt-get update && apt-get install -y libpq-dev supervisor

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Створюємо директорію для логів
RUN mkdir -p /app/logs

# Копіюємо supervisord.conf
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

