# Frontend Dockerfile

# Build stage
FROM node:18-alpine as build-stage

WORKDIR /app

# Копировать package файлы
COPY package*.json ./

# Установить зависимости
RUN npm ci

# Копировать исходный код
COPY . .

# Build приложение
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Production stage
FROM nginx:alpine

# Копировать build файлы
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Копировать nginx конфигурацию
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose порт
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]