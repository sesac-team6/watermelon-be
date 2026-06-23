from datetime import date

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app


class FakeResult:
    def mappings(self) -> "FakeResult":
        return self

    def all(self) -> list[dict[str, object]]:
        return [
            {"id": 1, "date": date(2026, 6, 22), "price": 12000},
            {"id": 2, "date": date(2026, 6, 23), "price": 12500},
        ]


class FakeSession:
    def __init__(self) -> None:
        self.statement = ""
        self.params: dict[str, date] = {}

    def execute(self, statement: object, params: dict[str, date]) -> FakeResult:
        self.statement = str(statement)
        self.params = params
        return FakeResult()


fake_session = FakeSession()


def override_get_db() -> FakeSession:
    return fake_session


client = TestClient(app)


def test_get_weekly_prices() -> None:
    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.get("/api/v1/prices", params={"date": "2026-06-22"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "date": "2026-06-22", "price": 12000},
        {"id": 2, "date": "2026-06-23", "price": 12500},
    ]
    assert 'FROM prices' in fake_session.statement
    assert '"date" >= :start_date' in fake_session.statement
    assert '"date" < :end_date' in fake_session.statement
    assert fake_session.params == {
        "start_date": date(2026, 6, 22),
        "end_date": date(2026, 6, 29),
    }


def test_get_weekly_prices_requires_valid_date() -> None:
    response = client.get("/api/v1/prices", params={"date": "not-a-date"})

    assert response.status_code == 422
