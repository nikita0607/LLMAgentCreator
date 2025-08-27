# 1. Билд-стейдж
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install --frozen-lockfile

COPY . .
RUN npm run build

# 2. Продакшн-стейдж
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# Устанавливаем только production-зависимости
COPY package*.json ./
RUN npm install --omit=dev --frozen-lockfile

# Копируем собранный Next.js
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.mjs ./next.config.mjs
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000

CMD ["npm", "start"]