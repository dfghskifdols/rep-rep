# Встановлюємо базовий образ
FROM python:3.10-slim

# Встановлюємо необхідні пакети
RUN apt-get update && apt-get install -y libpq-dev supervisor

# Встановлюємо робочу директорію
WORKDIR /app

# Копіюємо код проекту в контейнер
COPY . /app

# Оновлюємо pip і встановлюємо залежності
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Створюємо директорію для логів
RUN mkdir -p /app/logs

# Копіюємо конфігурацію для Supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Команда для запуску Supervisor
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

