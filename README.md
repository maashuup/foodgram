# Данные для проверки

ip: 84.201.143.252
https://maashuup.zapto.org/
email: admin@example.com
password: Practicum123!

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
- DevOps: Yandex Cloud, GitHub Actions

## Установка и запуск проекта

### 1. Клонирование репозитория

Подключитесь к серверу по SSH и выполните:
```
git clone https://github.com/maashuup/foodgram.git
```

### 2. Настройка переменных окружения

Создайте `.env` файл в корневой директории `foodgram` и добавьте в него:
```env
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=django
DB_HOST=db
DB_PORT=
SECRET_KEY=
DEBUG=False
ALLOWED_HOSTS=
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
