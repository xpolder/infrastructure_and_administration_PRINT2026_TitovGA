import os
from datetime import date

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

# переменные окружения, дублируются в макет .env.example
APP_NAME = os.getenv("APP_NAME", "Deadline Tracker API")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

app = FastAPI(title=APP_NAME, version=APP_VERSION)


class DeadlineCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    course: str = Field(min_length=1, max_length=50)
    due_date: date
    notes: str | None = Field(default=None, max_length=500)
    
    @field_validator("course")
    @classmethod
    def lowercase_course(cls, value: str) -> str:
        return value.lower()


# это отдаём клиенту: поля создания плюс id и признак выполнения
class Deadline(DeadlineCreate):
    id: int
    done: bool = False


# хранилище в памяти, пропадет после перезапуска
deadlines: dict[int, Deadline] = {}
next_id = 1


# сброс состояния чтобы тесты они не зависели друг от друга
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


# REVIEW: 201 Created; id выдаётся автоинкрементом, новый дедлайн всегда не выполнен
@app.post("/deadlines", response_model=Deadline, status_code=201)
def create_deadline(payload: DeadlineCreate):
    global next_id
    deadline = Deadline(id=next_id, **payload.model_dump())
    deadlines[deadline.id] = deadline
    next_id += 1
    return deadline


@app.get("/deadlines/{deadline_id}", response_model=Deadline)
def get_deadline(deadline_id: int):
    deadline = deadlines.get(deadline_id)
    if deadline is None:
        raise HTTPException(status_code=404, detail="Deadline not found")
    return deadline
