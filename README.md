# ASPEX Booking API

Backend-сервис для бронирования столов в ресторане на FastAPI + PostgreSQL + SQLAlchemy + Alembic + JWT + Redis + Celery.

## Статус по `TASK.md`

Реализовано:
- `Auth`: `POST /auth/register`, `POST /auth/login`, JWT на 1 час.
- Защита бизнес-эндпоинтов через JWT.
- `Tables`: `GET /tables/available` с учетом времени, гостей, занятости и фиксированного слота 2 часа.
- `Bookings`: создание, просмотр своих активных/будущих, изменение, отмена с дедлайном 1 час.
- Асинхронные эндпоинты и асинхронный SQLAlchemy.
- Alembic-миграции.
- Celery-задача отправки уведомления о созданной брони.
- Redis-кэширование доступности столов.
- Swagger/OpenAPI (`/docs`).
- ER-диаграмма в `docs/er-diagram.md`.
- Dockerfile и Docker Compose.
- Unit/integration-тесты на `pytest`.
- Структурированное JSON-логирование.
- Метрики Prometheus (`/metrics`).

Добавлено как опциональные улучшения:
- Админский CRUD столов через API.
- Система ролей `user/admin`.
- Prometheus + Grafana в compose-стеке.

## Роли и администрирование

### Модель ролей
- У пользователя есть поле `role` со значениями `user` или `admin`.
- По умолчанию роль — `user`.
- При регистрации роль `admin` назначается, если email входит в `ADMIN_EMAILS`.

### `ADMIN_EMAILS`
- Переменная окружения с CSV-списком email, например:
  - `ADMIN_EMAILS=admin@gmail.com,owner@company.com`
- Сравнение email выполняется в lower-case.

### Admin CRUD столов
- `GET /admin/tables/` — список всех столов.
- `POST /admin/tables/` — создать стол.
- `PATCH /admin/tables/{table_id}` — изменить стол.
- `DELETE /admin/tables/{table_id}` — удалить стол.
- Доступ только у пользователей с ролью `admin` (иначе `403`).

## Архитектура

- `app/models` — ORM-модели.
- `app/schemas` — pydantic-схемы запросов/ответов.
- `app/repositories` — слой доступа к данным.
- `app/services` — бизнес-логика.
- `app/api` — роутеры и зависимости FastAPI.
- `app/tasks` — Celery-задачи.
- `alembic` — миграции.
- `infra` — конфиги Prometheus/Grafana.
- `docs/er-diagram.md` — ER-диаграмма.

## Локальный запуск (без Docker Compose)

1. Установить зависимости:

```bash
poetry install
```

2. Применить миграции:

```bash
poetry run alembic upgrade head
```

3. Запустить API:

```bash
poetry run uvicorn app.main:app --reload
```

4. Запустить Celery worker (в отдельном терминале):

```bash
poetry run celery -A app.tasks.celery_app.celery_app worker --loglevel=INFO
```

## Запуск через Docker Compose

1. Подготовить env-файл:

```bash
cp .env.compose-example .env.compose
```

2. Запустить стек:

```bash
docker compose up --build
```

Сервисы:
- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Prometheus metrics endpoint приложения: `http://localhost:8000/metrics`
- Prometheus UI: `http://localhost:9090`
- Grafana UI: `http://localhost:3000`
- RabbitMQ UI: `http://localhost:15673`

## Grafana: как использовать

1. Открыть `http://localhost:3000`.
2. Войти под учеткой из `.env.compose`:
   - `GRAFANA_ADMIN_USER`
   - `GRAFANA_ADMIN_PASSWORD`
3. Data source Prometheus подключается автоматически.
4. Дашборд `ASPEX API Overview` загружается автоматически из provisioning.
5. Для появления данных выполните несколько запросов к API и обновите дашборд.

## Тесты

```bash
poetry run pytest -q
```

## Основные переменные окружения

- `DATABASE_URL`, `DATABASE_SYNC_URL` — подключения к PostgreSQL.
- `SECRET_KEY`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES` — JWT.
- `ADMIN_EMAILS` — список email администраторов.
- `REDIS_URL` — Redis.
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` — Celery.
- `CACHE_TTL_SECONDS` — TTL кэша доступности столов.
- `BOOKING_SLOT_HOURS` — длительность слота.
- `CANCEL_DEADLINE_MINUTES` — дедлайн отмены.
- `WORKDAY_START_HOUR`, `WORKDAY_END_HOUR` — рабочее окно.
- `RESTAURANT_TIMEZONE` — таймзона бизнес-логики.
- `GRAFANA_ADMIN_USER`, `GRAFANA_ADMIN_PASSWORD` — вход в Grafana.

## ER-диаграмма

- `docs/er-diagram.md`
