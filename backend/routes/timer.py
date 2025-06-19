# backend/routes/timer.py
from fastapi import APIRouter, Depends
from backend.models import models
from backend.dependencies import get_db
from sqlalchemy.orm import Session
from datetime import datetime

router = APIRouter()

@router.post("/timer/log")
def log_time(duration_minutes: float, db: Session = Depends(get_db)):
    log = models.TimeLog(duration_minutes=duration_minutes)
    db.add(log)
    db.commit()
    return {"status": "logged"}
