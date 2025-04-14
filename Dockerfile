# Встановлюємо базовий образ
FROM python:3.10-slim

# Встановлюємо необхідні пакети для PostgreSQL
RUN apt-get update && apt-get install -y libpq-dev

# Встановлюємо робочу директорію
WORKDIR /app

# Копіюємо код проекту в контейнер
COPY . /app

# Оновлюємо pip і встановлюємо залежності
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Запускаємо скрипт бота
CMD ["python", "mtrepo.py"]
