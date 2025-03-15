# Foodgram

Foodgram - это веб-приложение для публикации рецептов.
Пользователи могут добавлять рецепты, подписываться на других авторов,
добавлять рецепты в избранное и формировать список покупок.

## Технологии

- Backend: Python 3, Django, Django REST Framework (DRF)
- База данных: PostgreSQL
- Контейнеризация: Docker, Docker Compose
- Веб-сервер: Nginx
- Gunicorn: для запуска Django-приложения в продакшене
- DevOps: Yandex Cloud (VPS), GitHub Actions

## Установка и запуск проекта

### 1. Клонирование репозитория

Подключитесь к серверу по SSH и выполните:
```
git clone https://github.com/maashuup/foodgram.git
```

### 2. Настройка переменных окружения

Создайте `.env` файл в корневой директории `foodgram` и добавьте в него:
```env
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=False
ALLOWED_HOSTS=<домен>,<server_ip>
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
DB_HOST=db
DB_PORT=5432
```

## 3. Автоматическое развертывание через GitHub Actions

Проект настроен на автоматический деплой через GitHub Actions.
При `git push` в репозиторий код автоматически обновляется на сервере и
перезапускаются контейнеры.

Для этого необходимо:
3.1. **Добавить в репозиторий GitHub Secrets:**
   - `HOST` – IP-адрес сервера
   - `USER` – Пользователь для подключения по SSH
   - `SSH_KEY` – SSH-ключ для деплоя
   - `DOCKER_USERNAME` – Логин Docker Hub
   - `DOCKER_PASSWORD` – Пароль Docker Hub
   - `SSH_PASSPHRASE` -	Парольная фраза для SSH-ключа
   - `TELEGRAM_TO` - ID пользователя, куда отправляются уведомления о деплое
   - `TELEGRAM_TOKEN` - Токен бота Telegram, который отправляет уведомления о
                        статусе деплоя.

3.2. **После внесения изменений в код выполнить `git push`** 
    Проект будет обновлен автоматически.
