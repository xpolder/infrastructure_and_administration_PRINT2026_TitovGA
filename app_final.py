import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import date, timedelta

from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, Field

# переменные окружения, дублируются в макет .env.example
APP_NAME = os.getenv("APP_NAME", "Deadline Tracker API")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
UPCOMING_DAYS_DEFAULT = int(os.getenv("UPCOMING_DAYS_DEFAULT", "7"))

# логирование
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("deadline_tracker")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s", APP_NAME, APP_VERSION)
    yield


app = FastAPI(title=APP_NAME, version=APP_VERSION, lifespan=lifespan)


# замеряем время и пишем метод, путь, статус и длительность
@app.middleware("http")
async def log_requests(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "%s %s -> %s (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


class DeadlineCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    course: str = Field(min_length=1, max_length=50)
    due_date: date
    notes: str | None = Field(default=None, max_length=500)


# это отдаём в клиент: поля создания плюс id и признак выполнения
class Deadline(DeadlineCreate):
    id: int
    done: bool = False


# хранилище в памяти, пропадет после перезапуска
deadlines: dict[int, Deadline] = {}
next_id = 1


# сброс состояния чтобы тесты не зависели друг от друга
def reset_storage() -> None:
    global next_id
    deadlines.clear()
    next_id = 1


@app.get("/")
def root():
    return {"service": APP_NAME, "docs": "/docs"}


# проверка живости сервиса — health
@app.get("/health")
def health():
    return {"status": "ok"}


# проверка какая сборка запущена
@app.get("/version")
def version():
    return {"name": APP_NAME, "version": APP_VERSION}


# чтобы новый дедлайн был всегда не выполнен
@app.post("/deadlines", status_code=201)
def create_deadline(payload: DeadlineCreate):
    global next_id
    deadline = Deadline(
        id=next_id,
        title=payload.title,
        course=payload.course.lower(),
        due_date=payload.due_date,
        notes=payload.notes,
    )
    deadlines[deadline.id] = deadline
    next_id += 1
    logger.info(
        "Created deadline id=%s course=%s due=%s",
        deadline.id,
        deadline.course,
        deadline.due_date,
    )
    return deadline


# course приводим к нижнему регистру как и при хранении чтобы матчилось + сортировка по дате
@app.get("/deadlines")
def list_deadlines(course: str | None = None, done: bool | None = None):
    items = list(deadlines.values())
    if course is not None:
        items = [d for d in items if d.course == course.lower()]
    if done is not None:
        items = [d for d in items if d.done == done]
    return sorted(items, key=lambda d: d.due_date)


@app.get("/deadlines/upcoming")
def upcoming_deadlines(days: int = Query(default=UPCOMING_DAYS_DEFAULT, ge=1, le=365)):
    today = date.today()
    last_day = today + timedelta(days=days)
    items = [
        d for d in deadlines.values()
        if not d.done and today <= d.due_date <= last_day
    ]
    return sorted(items, key=lambda d: d.due_date)


@app.get("/deadlines/{deadline_id}")
def get_deadline(deadline_id: int):
    deadline = deadlines.get(deadline_id)
    if deadline is None:
        logger.warning("Deadline id=%s not found", deadline_id)
        raise HTTPException(status_code=404, detail="Deadline not found")
    return deadline


# меняем одно поле существующего ресурса, повторный вызов будет безопасным
@app.patch("/deadlines/{deadline_id}/done")
def mark_done(deadline_id: int):
    deadline = deadlines.get(deadline_id)
    if deadline is None:
        logger.warning("Deadline id=%s not found", deadline_id)
        raise HTTPException(status_code=404, detail="Deadline not found")
    deadline.done = True
    logger.info("Deadline id=%s marked as done", deadline_id)
    return deadline
