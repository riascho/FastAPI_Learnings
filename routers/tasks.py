import sqlite3

from fastapi import APIRouter, Depends, status

from database import get_db, row_to_task
from dependencies import check_task_exists
from models import Task

# from storage import tasks

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("")
def get_all_tasks(
    limit: int = 10,
    done: bool | None = None,  # not specified should not filter, hence None as default
    search: str | None = None,
    db: sqlite3.Connection = Depends(get_db),  # noqa: B008
):
    # result = tasks

    conditions = []  # used to build up the sql query
    params = []

    if done is not None:  # meaning a filter is applied (query parameter in URL)
        # result = [task for task in result if task["done"] == done]
        conditions.append("done = ?")
        params.append(int(done))  # boolean to int conversion for sql int column

    if search is not None:
        # search = search.lower()
        # result = [task for task in result if search in task["title"].lower()]
        conditions.append("title LIKE ?")
        params.append("%" + search + "%")  # wildcards for fuzzy search

    query_string = "SELECT * FROM tasks"
    if conditions:
        query_string += " WHERE " + " AND ".join(conditions)

    params.append(limit)
    query_string += " LIMIT ?"
    rows = db.execute(query_string, params)
    return [row_to_task(row) for row in rows]


# path parameters as function arguments (must match)
@router.get("/{task_id}")
def get_task(
    task: dict = Depends(check_task_exists),  # noqa: B008
):
    return task


@router.post("", status_code=status.HTTP_201_CREATED)  # default status_code is 200
def create_task(payload: Task, db: sqlite3.Connection = Depends(get_db)):  # noqa: B008
    # Task = type hint to pydantic basemodel
    # new_id = (
    #     max((task["id"] for task in tasks), default=0) + 1
    # )  # creates next id from task list with highest id

    params = [
        payload.title,  # dot notation works for pydantic models
        int(payload.done),
    ]
    query_string = "INSERT INTO tasks (title, done) VALUES (? , ?)"

    entry = db.execute(query_string, params)
    db.commit()
    new_row = db.execute(
        "SELECT * FROM tasks WHERE id = ?", [entry.lastrowid]
    ).fetchone()

    # tasks.append(new_task)
    return row_to_task(new_row)


@router.put("/{task_id}")
def update_task(
    payload: Task,
    task: dict = Depends(check_task_exists),  # noqa: B008 # using FastAPI's Depends feature as default param to provide the value of task directly
    db: sqlite3.Connection = Depends(get_db),  # noqa: B008
):
    query_string = "UPDATE tasks SET title = ?, done = ? WHERE id = ?"
    db.execute(
        query_string,
        [
            payload.title,
            int(
                payload.done
            ),  # be explicit with the boolean/int conversion! - SQL column is an integer
            task["id"],
        ],
    )
    db.commit()
    updated_row = db.execute(
        "SELECT * FROM tasks WHERE id = ?", [task["id"]]
    ).fetchone()
    # task["title"] = payload.title
    # task["done"] = payload.done
    return row_to_task(updated_row)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task: dict = Depends(check_task_exists),  # noqa: B008
    db: sqlite3.Connection = Depends(get_db),  # noqa: B008
):
    db.execute("DELETE FROM tasks WHERE id = ?", [task["id"]])
    db.commit()
    # tasks.remove(task)
