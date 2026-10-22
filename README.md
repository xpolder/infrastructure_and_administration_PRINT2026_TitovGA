# Deadline Tracker API

[![CI](https://github.com/xpolder/infrastructure_and_administration_PRINT2026_TitovGA/actions/workflows/ci.yml/badge.svg)](https://github.com/xpolder/infrastructure_and_administration_PRINT2026_TitovGA/actions/workflows/ci.yml)

Итоговый проект по курсу «Инфраструктура и администрирование»: сервис на FastAPI — студент записывает туда дедлайны по своим курсам.

## Для кого сервис

Нужно студентам чтобы трекать дедлайны: добавлять дедлайны по курсам, фильтровать их, можно отметить что сделано, что горит, надо сделать в ближ N дней и так далее.

Данные лежат в памяти. БД не добавлял — после перезапуска всё пропадает. 

## Инструкции по установке

Нужен Python 3.12 (в CI используем)

Создание виртуального окуржения и включаем его:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Зависимости:

```bash
pip install -r requirements-dev.txt
```

Копируем настройки в `.env`:

```bash
cp .env.example .env
```

## Запуск для разработки

С автоперезагрузкой при изменении кода:

```bash
uvicorn app_final:app --reload --env-file .env
```

Сервис на http://127.0.0.1:8000, дока чтобы попробовать руками http://127.0.0.1:8000/docs.

## Обычный запуск


```bash
uvicorn app_final:app --host 0.0.0.0 --port 8000 --env-file .env
```

## Тесты

```bash
python -m pytest -v
```

9 тестов, они проверяют все маршруты, фильтры, 404 и ошибки валидации

## Переменные окружения

| Переменная | По умолчанию | Что делает |
|---|---|---|
| `APP_NAME` | `Deadline Tracker API` | название сервиса, видно в `/` и `/version` |
| `APP_VERSION` | `1.0.0` | версия, видна в `/version` |
| `LOG_LEVEL` | `INFO` | уровень логов (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `UPCOMING_DAYS_DEFAULT` | `7` | сколько дней вперёд смотрит `/deadlines/upcoming`, если `days` не указан |

## Маршруты

| Метод | Путь | Что делает |
|---|---|---|
| GET | `/` | название сервиса и ссылка на документацию |
| GET | `/health` | проверка, что сервис жив |
| GET | `/version` | название и версия |
| POST | `/deadlines` | создать дедлайн (201) |
| GET | `/deadlines` | список, можно фильтровать `?course=...` и `?done=true/false`, отсортирован по дате |
| GET | `/deadlines/upcoming` | невыполненные дедлайны на ближайшие `?days=N` дней (от 1 до 365) |
| GET | `/deadlines/{id}` | один дедлайн, 404 если такого нет |
| PATCH | `/deadlines/{id}/done` | отметить выполненным, 404 если такого нет |

Примеры (дату в `due_date` поменять на свою, чтобы попала в ближайшие дни):

```bash
curl -X POST http://127.0.0.1:8000/deadlines \
  -H "Content-Type: application/json" \
  -d '{"title": "Лабораторная 1", "course": "Python", "due_date": "2026-10-30", "notes": "сдать в PDF"}'
```

```bash
curl "http://127.0.0.1:8000/deadlines/upcoming?days=14"
```

Название курса всегда храним в нижнем регистре

## Диагностика

Проверка на живость:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/version
```

Первая команда возвращает `{"status":"ok"}`, вторая — название и версию.

Логи пишутся прямо в терминал, где запущен сервис. При старте там будет строка `Starting Deadline Tracker API v1.0.0`, на каждый запрос строка вида `GET /health -> 200 (1.0 ms)`. Ещё пишутся создание дедлайна, отметка «выполнено» и предупреждение, когда дедлайн не найден.
Если надо больше логов то можно поставить `LOG_LEVEL=DEBUG` в `.env` и сделать рестарт сервиса.
## CI

В `.github/workflows/ci.yml` настроен GitHub Actions. Он запускается на каждый push и pull request: ставит Python 3.12, зависимости, гоняет `python -m pytest -v`, а если тесты прошли, сохраняет artifact `deadline-tracker-app` (сам сервис, зависимости, README и пример настроек).

Результаты запусков: вкладка **Actions** в репозитории. Artifact скачивается со страницы нужного запуска, раздел **Artifacts** внизу страницы. Если тесты упали, artifact не создаётся.
