# API организационной структуры

Тестовое приложение на **FastAPI + SQLAlchemy + PostgreSQL** для управления деревом подразделений и сотрудниками.

## Что реализовано

- Модель `Department` с самоссылкой (`parent_id`) для построения дерева.
- Модель `Employee` с привязкой к подразделению (`department_id`).
- Валидации входных данных через Pydantic.
- Ограничения целостности на уровне БД:
  - каскадное удаление дочерних подразделений;
  - каскадное удаление сотрудников при удалении подразделения;
  - уникальность имени подразделения в рамках одного родителя (`(parent_id, name)`).
- Миграции через Alembic.
- Docker/Docker Compose для запуска.
- Тесты на `pytest`.

## Структура проекта

```text
app/
  api/            # роуты и DI
  core/           # конфиг и подключение к БД
  models/         # SQLAlchemy ORM модели
  repositories/   # доступ к данным
  schemas/        # Pydantic схемы
  services/       # бизнес-логика
alembic/          # миграции
tests/            # тесты API
```

## Запуск через Docker Compose

```bash
docker-compose up --build
```

После запуска:

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Остановка:

```bash
docker-compose down
```

С очисткой данных Postgres:

```bash
docker-compose down -v
```

## Переменные окружения

Основная переменная:

- `DATABASE_URL` (по умолчанию в приложении):
  `postgresql+asyncpg://postgres:postgres@db:5432/org_structure`

## Миграции

Миграции выполняются автоматически при старте API-контейнера (`alembic upgrade head`).

Ручной запуск:

```bash
alembic upgrade head
```

## Тесты

```bash
pytest -q
```

Тесты используют SQLite in-memory и проверяют ключевую бизнес-логику API.

## API

Базовый префикс: `/departments`

### 1) Создать подразделение

`POST /departments/`

```json
{
  "name": "Engineering",
  "parent_id": null
}
```

### 2) Создать сотрудника

`POST /departments/{id}/employees/`

```json
{
  "full_name": "Alice Johnson",
  "position": "Backend Engineer",
  "hired_at": "2024-05-20"
}
```

### 3) Получить подразделение (детали + сотрудники + поддерево)

`GET /departments/{id}?depth=1&include_employees=true`

- `depth` — глубина вложенности (1..5)
- `include_employees` — включать ли сотрудников

### 4) Обновить подразделение

`PATCH /departments/{id}`

```json
{
  "name": "Platform",
  "parent_id": 2
}
```

### 5) Удалить подразделение

`DELETE /departments/{id}?mode=cascade`

или

`DELETE /departments/{id}?mode=reassign&reassign_to_department_id=10`

- `cascade` — удалить подразделение, его поддерево и сотрудников;
- `reassign` — перевести сотрудников удаляемого поддерева в `reassign_to_department_id`, затем удалить подразделение.

## Бизнес-правила

- Нельзя создать сотрудника в несуществующем подразделении (`404`).
- Поля `name`, `full_name`, `position`:
  - обязательны;
  - длина `1..200`;
  - пробелы по краям обрезаются.
- Нельзя сделать подразделение родителем самого себя.
- Нельзя создать цикл в дереве (переместить узел в своё поддерево) — `409`.
- Имена подразделений уникальны в пределах одного `parent_id`.
