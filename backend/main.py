# backend/main.py
from fastapi import FastAPI
# backend/main.py

from fastapi import FastAPI
from backend.database import engine
from backend.models import models
from backend.routes import projects, tasks

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.include_router(projects.router)
app.include_router(tasks.router)

@app.get("/")
def read_root():
    return {"message": "Project Tracker API is running"}
