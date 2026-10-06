# bridging between the web part of the app and the background services (e.g. storage)

import sqlite3

from fastapi import Depends, HTTPException, status

from database import get_db, row_to_task

# from storage import find_task


def check_task_exists(task_id: int, db: sqlite3.Connection = Depends(get_db)):  # noqa: B008
    # task = find_task(task_id)

    row = db.execute("SELECT * FROM tasks WHERE id = ?", [task_id]).fetchone()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"task id {task_id} not found!",
        )
    return row_to_task(row)
