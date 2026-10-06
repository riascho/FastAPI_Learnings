from fastapi.testclient import TestClient

# from main import app

# client = TestClient(app)

# We're using conftest.py's fixtures (client) as parameters directly. This uses the Testclient with the test database as setup in conftest.py


def test_health(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_get_all_tasks(client: TestClient):
    response = client.get("/tasks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 3


def test_get_task(client: TestClient):
    response = client.get("/tasks/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_create_task(client: TestClient):
    payload = {"title": "Pick Up Dry Cleaning"}
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    new_id = response.json()["id"]
    assert isinstance(new_id, int)
    assert response.json()["done"] is False
    new_task_from_db = client.get(f"/tasks/{new_id}")
    assert response.json() == new_task_from_db.json()


def test_update_task(client: TestClient):
    def get_task_1():
        task = client.get("/tasks/1")
        return task.json()

    assert get_task_1()["done"] is False
    payload = {"title": "Do Laundry", "done": True}
    response = client.put("/tasks/1", json=payload)
    assert response.status_code == 200
    assert get_task_1()["done"] is True


def test_delete_task(client: TestClient):
    def get_all_tasks():
        tasks = client.get("/tasks")
        return tasks.json()

    assert len(get_all_tasks()) == 3
    response = client.delete("/tasks/3")
    assert response.status_code == 204
    assert response.content == b""
    # .content is the raw bytes exactly as they came off the wire
    assert response.text == ""
    # .text is those bytes decoded to a string using the response's charset
    assert len(get_all_tasks()) == 2


def test_get_missing_task_returns_404(client: TestClient):
    response = client.get("/tasks/999")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_get_task_invalid_id_returns_422(client: TestClient):
    response = client.get("/tasks/abc")
    assert response.status_code == 422


def test_filter_by_done(client: TestClient):
    response = client.get("/tasks", params={"done": True})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert [t["done"] for t in response.json()] == [True]


def test_search_is_case_insensitive(client: TestClient):
    response1 = client.get("/tasks", params={"search": "LAUNDRY"})
    response2 = client.get("/tasks", params={"search": "laundry"})
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert len(response1.json()) > 0
    assert len(response2.json()) > 0
    assert "laundry" in response1.json()[0]["title"].lower()
    assert response1.json() == response2.json()
