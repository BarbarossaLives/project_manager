# backend/main.py
from fastapi import FastAPI
from backend.database import engine
from backend.models import models

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Project Tracker API running!"}
