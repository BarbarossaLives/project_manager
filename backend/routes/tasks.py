from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.models import models, schemas
from backend.dependencies import get_db
from typing import List  # Added import for List
from fastapi import APIRouter, Depends, HTTPException, Form


router = APIRouter()

@router.post("/tasks/", response_model=schemas.Task)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    db_task = models.Task(**task.model_dump())  # Changed from .dict() to .model_dump()
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.get("/tasks/", response_model=List[schemas.Task])
def read_tasks(db: Session = Depends(get_db)):
    return db.query(models.Task).all()

@router.post("/tasks/create")
def create_task_form(
    title: str = Form(...),
    project_id: int = Form(...),
    db: Session = Depends(get_db)
):
    new_task = models.Task(title=title, project_id=project_id)
    db.add(new_task)
    db.commit()
    return RedirectResponse("/", status_code=303)
