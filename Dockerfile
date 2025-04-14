# Встановлюємо залежності
RUN apt-get update && apt-get install -y libpq-dev supervisor

# Встановлюємо бібліотеки Python
RUN pip install --upgrade pip
RUN pip install psycopg2-binary

# Створюємо директорію для програми
WORKDIR /app

# Копіюємо файли бота
COPY . /app

# Встановлюємо залежності
RUN pip install -r requirements.txt

# Копіюємо конфігурацію для supervisor
COPY supervisord.conf /etc/supervisord.conf

# Запускаємо supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
