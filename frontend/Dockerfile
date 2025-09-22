FROM node:20-alpine

WORKDIR /app

# Копируем package.json и ставим все зависимости (dev тоже нужны, т.к. будет next dev)
COPY package*.json ./
RUN npm install

# Копируем исходники
COPY . .

# Переменные окружения (например, API)
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

EXPOSE 3000

# Запуск dev-сервера
CMD ["npm", "start"]