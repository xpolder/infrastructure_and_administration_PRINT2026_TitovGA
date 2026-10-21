import os
from fastapi import FastAPI

# переменные окружения, дублируются в макет .env.example
APP_NAME = os.getenv("APP_NAME", "Deadline Tracker API")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

app = FastAPI(title=APP_NAME, version=APP_VERSION)


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
