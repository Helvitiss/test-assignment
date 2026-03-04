# API организационной структуры

Тестовый backend-проект на **FastAPI + SQLAlchemy (async) + PostgreSQL** для управления деревом подразделений и сотрудниками.

## Что реализовано

- CRUD-операции для подразделений в рамках требований тестового задания.
- Создание сотрудников в подразделениях.
- Получение подразделения с поддеревом (`depth`) и сотрудниками (`include_employees`).
- Перемещение подразделения (смена `parent_id`) с защитой от циклов.
- Удаление подразделения в режимах `cascade` и `reassign`.
- Миграции через Alembic.
- Запуск через Docker / docker-compose.
- Базовые тесты на ключевые сценарии.

## Технологии

- Python 3.12
- FastAPI
- SQLAlchemy 2 (async)
- Alembic
- PostgreSQL 16
- Pytest

## Структура проекта

```text
app/
  api/            # роутеры и зависимости
  core/           # конфигурация и подключение к БД
  models/         # SQLAlchemy модели
  repositories/   # слой работы с БД
  schemas/        # Pydantic схемы
  services/       # бизнес-логика
alembic/          # миграции
tests/            # тесты
```

## Быстрый старт

### 1) Запуск в Docker

```bash
docker-compose up --build
```

После старта API доступно по адресу:

- `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

> При запуске контейнера API автоматически выполняется `alembic upgrade head`.

### 2) Остановка

```bash
docker-compose down
```

С удалением томов БД:

```bash
docker-compose down -v
```

## Конфигурация

Приложение использует переменную окружения `DATABASE_URL`.

По умолчанию в коде:

```text
postgresql+asyncpg://postgres:postgres@db:5432/org_structure
```

При запуске через `docker-compose` используется сервис `db` (PostgreSQL).

## Миграции

Внутри контейнера API:

```bash
alembic upgrade head
```

Локально (если запускаете без Docker, и настроен доступ к Postgres):

```bash
alembic upgrade head
```

## Запуск тестов

```bash
pytest -q
```

Тесты используют in-memory SQLite для быстрого прогона.

## Основные эндпоинты

Базовый префикс: `/departments`

### Создать подразделение

`POST /departments/`

```json
{
  "name": "Engineering",
  "parent_id": null
}
```

### Создать сотрудника в подразделении

`POST /departments/{department_id}/employees/`

```json
{
  "full_name": "Alice Johnson",
  "position": "Backend Engineer",
  "hired_at": "2024-05-20"
}
```

### Получить подразделение с деревом

`GET /departments/{department_id}?depth=2&include_employees=true`

- `depth`: 1..5 (по умолчанию 1)
- `include_employees`: `true/false` (по умолчанию `true`)

### Обновить подразделение

`PATCH /departments/{department_id}`

```json
{
  "name": "Platform",
  "parent_id": 2
}
```

### Удалить подразделение

`DELETE /departments/{department_id}?mode=cascade`

или

`DELETE /departments/{department_id}?mode=reassign&reassign_to_department_id=10`

- `cascade`: удалить подразделение и связанные сущности каскадно.
- `reassign`: перевести сотрудников удаляемого подразделения в `reassign_to_department_id`.

## Валидации и ограничения

- `name`, `full_name`, `position`: обязательные, длина `1..200`, пробелы по краям обрезаются.
- Запрещено делать подразделение родителем самого себя.
- Запрещено создавать циклы при переносе подразделения.
- Имя подразделения уникально в рамках одного `parent_id`.
- Нельзя создать сотрудника в несуществующем подразделении.

