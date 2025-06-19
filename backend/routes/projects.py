from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.models import models, schemas
from backend.dependencies import get_db
from typing import List  # Explicit List import
from fastapi import Form
from fastapi.responses import RedirectResponse

router = APIRouter()

@router.post("/projects/", response_model=schemas.Project)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    db_project = models.Project(**project.model_dump())  # Changed from .dict() to .model_dump()
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/projects/", response_model=List[schemas.Project])
def read_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).all()

@router.post("/projects/create")
def create_project_form(
    title: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db)
):
    new_project = models.Project(title=title, description=description)
    db.add(new_project)
    db.commit()
    return RedirectResponse("/", status_code=303)