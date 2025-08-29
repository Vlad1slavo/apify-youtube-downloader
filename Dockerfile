# Використовуємо офіційний базовий образ Apify для Python 3.11
FROM apify/actor-python:3.11

# Потрібен root-доступ для встановлення системних пакетів
USER root

# Встановлюємо ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Повертаємося до користувача apify для запуску актора
USER apify

# Копіюємо файли актора в контейнер
COPY --chown=apify:apify . /home/apify/actor

# Змінюємо робочу директорію
WORKDIR /home/apify/actor

# Встановлюємо залежності Python
RUN pip install --no-cache-dir -r requirements.txt

# Встановлюємо команду для запуску контейнера
CMD ["python3", "-m", "main"]
