from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

import app_final
from app_final import app, reset_storage

client = TestClient(app)


# очищаем перед каждым тестом, чтобы тесты не зависели друг от друга
@pytest.fixture(autouse=True)
def clean_storage():
    reset_storage()


# чтобы не повторть тело запроса в каждом тесте
def create_deadline(title="Lab", course="python", due_date=None, **extra):
    if due_date is None:
        due_date = date.today() + timedelta(days=1)
    payload = {"title": title, "course": course, "due_date": str(due_date), **extra}
    return client.post("/deadlines", json=payload)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version():
    response = client.get("/version") #из самого приложения чтоб без переменных окружения тестить
    assert response.status_code == 200
    assert response.json() == {
        "name": app_final.APP_NAME,
        "version": app_final.APP_VERSION,
    }


# проверка 201
def test_create_and_get_deadline():
    created = create_deadline(title="Lab 1", course="Python", notes="сдать в PDF")
    assert created.status_code == 201
    body = created.json()
    assert body["id"] == 1
    assert body["course"] == "python"
    assert body["done"] is False
    assert body["notes"] == "сдать в PDF"

    fetched = client.get("/deadlines/1")
    assert fetched.status_code == 200
    assert fetched.json() == body


def test_list_filter_by_course():
    create_deadline(title="a", course="python")
    create_deadline(title="b", course="sql")
    create_deadline(title="c", course="Python")

    response = client.get("/deadlines", params={"course": "PYTHON"})
    assert response.status_code == 200
    assert [d["title"] for d in response.json()] == ["a", "c"]

    assert client.get("/deadlines", params={"course": "none"}).json() == []


def test_list_sorted_by_due_date():
    today = date.today() # сегодня чтоб тест не ломался со временем
    create_deadline(title="late", due_date=today + timedelta(days=10))
    create_deadline(title="early", due_date=today + timedelta(days=1))
    create_deadline(title="middle", due_date=today + timedelta(days=5))

    response = client.get("/deadlines")
    assert [d["title"] for d in response.json()] == ["early", "middle", "late"]

def test_upcoming_window():
    today = date.today()
    create_deadline(title="past", due_date=today - timedelta(days=1))
    create_deadline(title="today", due_date=today)
    create_deadline(title="edge", due_date=today + timedelta(days=7))
    create_deadline(title="far", due_date=today + timedelta(days=8))
    done = create_deadline(title="done", due_date=today + timedelta(days=2)).json()
    client.patch(f"/deadlines/{done['id']}/done")

    response = client.get("/deadlines/upcoming", params={"days": 7})
    assert response.status_code == 200
    assert [d["title"] for d in response.json()] == ["today", "edge"]


def test_mark_done():
    deadline_id = create_deadline().json()["id"]

    response = client.patch(f"/deadlines/{deadline_id}/done")
    assert response.status_code == 200
    assert response.json()["done"] is True

    assert client.get(f"/deadlines/{deadline_id}").json()["done"] is True
    assert len(client.get("/deadlines", params={"done": True}).json()) == 1
    assert client.get("/deadlines", params={"done": False}).json() == []


def test_get_missing_returns_404():
    for response in (client.get("/deadlines/42"), client.patch("/deadlines/42/done")):
        assert response.status_code == 404
        assert response.json() == {"detail": "Deadline not found"}


def test_validation_errors_422():
    today = str(date.today())
    assert create_deadline(title="").status_code == 422
    assert create_deadline(title="x" * 201).status_code == 422
    assert create_deadline(course="").status_code == 422
    assert create_deadline(due_date="not-a-date").status_code == 422
    assert client.post("/deadlines", json={"course": "x", "due_date": today}).status_code == 422
    assert client.get("/deadlines/upcoming", params={"days": 0}).status_code == 422
    assert client.get("/deadlines/upcoming", params={"days": 366}).status_code == 422
