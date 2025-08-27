FROM python:3.11-slim

# Устанавливаем системные зависимости
# && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
RUN apt-get update

WORKDIR .

# Копируем requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY . ./app

# Запуск приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]