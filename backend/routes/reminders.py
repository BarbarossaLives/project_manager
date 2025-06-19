# backend/routes/reminders.py
from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from backend.models import models
from backend.dependencies import get_db
from backend.services.reminder_service import reminder_service
from typing import Optional

router = APIRouter()

@router.post("/reminders/create")
def create_reminder(
    message: str = Form(...),
    due_date: str = Form(...),
    db: Session = Depends(get_db)
):
    parsed_due = datetime.fromisoformat(due_date)
    reminder = models.Reminder(message=message, due_date=parsed_due)
    db.add(reminder)
    db.commit()
    return RedirectResponse("/", status_code=303)

@router.post("/reminders/auto-generate")
def auto_generate_reminders(
    project_id: Optional[int] = Form(None)
):
    """Manually trigger auto-generation of reminders"""
    try:
        reminder_service.auto_generate_progress_reminders(project_id)
        return JSONResponse({"status": "success", "message": "Auto-generated reminders created"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reminders/generate-content/{project_id}")
def generate_social_content(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Generate social media content for a project"""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    content = reminder_service.generate_social_media_content(project)
    return JSONResponse({"content": content})

@router.post("/reminders/quick-create/{project_id}")
def quick_create_reminder(
    project_id: int,
    days_ahead: int = Form(7),
    db: Session = Depends(get_db)
):
    """Quickly create a reminder for a project"""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Create reminder
    due_date = datetime.now() + timedelta(days=days_ahead)

    reminder = models.Reminder(
        message=f"Share update: {project.title}",
        due_date=due_date,
        sent=False
    )

    db.add(reminder)
    db.commit()

    return RedirectResponse("/", status_code=303)

@router.delete("/reminders/{reminder_id}")
def delete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db)
):
    """Delete a reminder"""
    reminder = db.query(models.Reminder).filter(models.Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    db.delete(reminder)
    db.commit()
    return JSONResponse({"status": "success", "message": "Reminder deleted"})
