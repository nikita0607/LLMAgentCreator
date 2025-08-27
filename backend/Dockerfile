FROM python:3.11-slim

# Устанавливаем системные зависимости
# && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
RUN apt-get update
RUN apt-get install -y \
    libpq-dev gcc python3-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY . .

# Запуск приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]