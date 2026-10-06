import sqlite3

import pytest
from fastapi.testclient import TestClient

from database import create_schema, get_db
from main import app


@pytest.fixture  # the test_db fixture can be called by any test as a simple parameter "test_db" and will be whatever is defined here (a connection in this case)
def test_db():  # build a throw-away database in sql memory (destroyed after connection closed)
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    create_schema(conn)
    conn.executemany(
        "INSERT INTO tasks (title, done) VALUES (?, ?);",
        [
            ("Do Laundry", 0),
            ("Call Accountant", 0),
            ("Go Groceries Shopping", 1),
        ],
    )
    conn.commit()
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture
def client(test_db):
    def override_get_db():  # dependency override function needed for FastAPI
        yield test_db  # hands test_db to the route

    # dict on my app for dependencies (Depends) -> FastAPI will look there first to resolve get_db and here uses the test_db instead
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
