import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "tasks.db"  # relative path anchored to this file


def get_connection():
    conn = sqlite3.connect(
        DB_PATH,  # opens and if absent creates the file
        check_same_thread=False,  # FastAPI runs endpoints in a thread pool, so any thread may handle the request not just the thread that created the connection ('same thread')
    )
    conn.row_factory = sqlite3.Row  # allows access by column names (e.g. row["title"])
    return conn


def create_schema(conn: sqlite3.Connection):
    conn.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    done INTEGER NOT NULL DEFAULT 0);
    """)


def init_db():
    conn = get_connection()
    create_schema(conn)
    row = conn.execute(
        "SELECT COUNT(*) AS count FROM tasks;"
    ).fetchone()  # execute() returns a cursor / fetchone() returns row object, using row factory the column name will be what we give it in the query ("count")
    count = row["count"]  # and hence we can access the column by name
    if count == 0:
        conn.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?);",
            [
                ("Task1", 0),
                ("Task2", 1),
            ],
        )
    conn.commit()
    conn.close()


def get_db():
    conn = get_connection()
    try:
        yield conn  # returns connection to who ever called this function, but will come back after to finish here
    finally:  # runs also if an Exception was raised! (important, because we want to close the connection even on errors)
        conn.close()


def row_to_task(row):
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}
