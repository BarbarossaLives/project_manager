# backend/routes/devlogs.py
from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from backend.models import models, schemas
from backend.dependencies import get_db

router = APIRouter()

@router.post("/devlogs/create")
def create_devlog(
    project_id: int = Form(...),
    entry_text: str = Form(...),
    db: Session = Depends(get_db)
):
    log = models.Devlog(project_id=project_id, entry_text=entry_text)
    db.add(log)
    db.commit()
    return RedirectResponse("/", status_code=303)
