from fastapi import FastAPI

from app.db.database import Base, engine
from app.routers import (
    Auth_router,
    Health_check,
    Research_project,
    Research_task,
    Users_router,
)

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(Health_check)
app.include_router(Auth_router)
app.include_router(Users_router)
app.include_router(Research_project)
app.include_router(Research_task)
