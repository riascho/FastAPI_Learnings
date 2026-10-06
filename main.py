from fastapi import FastAPI

from database import init_db
from routers import health, tasks

app = FastAPI()
app.include_router(tasks.router)
app.include_router(health.router)

init_db()
