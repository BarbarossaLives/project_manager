# backend/routes/uploads.py
from fastapi import APIRouter, UploadFile, File, Form, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import shutil
import os
from backend.models import models
from backend.dependencies import get_db

UPLOAD_DIR = "uploads"

router = APIRouter()

@router.post("/upload/")
def upload_attachment(
    file: UploadFile = File(...),
    task_id: int = Form(None),
    project_id: int = Form(None),
    db: Session = Depends(get_db)
):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    attachment = models.Attachment(
        filename=file.filename,
        filepath=file_path,
        task_id=task_id,
        project_id=project_id
    )
    db.add(attachment)
    db.commit()
    return RedirectResponse("/", status_code=303)
