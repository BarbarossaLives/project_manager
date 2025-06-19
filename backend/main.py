# backend/main.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from backend.database import engine
from backend.models import models
from backend.routes import projects, tasks
from backend.dependencies import get_db
from backend.routes import devlogs, reminders, uploads, ai_planning, events
from backend.models.models import Project, Reminder, Attachment, Event
from backend.services.scheduler import scheduler

from sqlalchemy.orm import Session
from fastapi import Depends

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await scheduler.start()
    yield
    # Shutdown
    await scheduler.stop()

app = FastAPI(lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# Configure Jinja2 templates
templates = Jinja2Templates(directory="frontend/templates")

# Include API routes
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(devlogs.router)
app.include_router(reminders.router)
app.include_router(uploads.router)
app.include_router(ai_planning.router)
app.include_router(events.router)

# Initialize DB
models.Base.metadata.create_all(bind=engine)

# Serve Home Page
@app.get("/", response_class=HTMLResponse)
def get_home(request: Request, db: Session = Depends(get_db)):
    from datetime import date, datetime, timedelta

    projects = db.query(Project).all()
    reminders = db.query(Reminder).all()
    attachments = db.query(Attachment).all()

    # Get today's events and upcoming events
    today = date.today()
    start_of_today = datetime.combine(today, datetime.min.time())
    end_of_week = start_of_today + timedelta(days=7)

    today_events = db.query(Event).filter(
        Event.start_time >= start_of_today,
        Event.start_time < start_of_today + timedelta(days=1)
    ).order_by(Event.start_time).all()

    upcoming_events = db.query(Event).filter(
        Event.start_time >= start_of_today + timedelta(days=1),
        Event.start_time < end_of_week
    ).order_by(Event.start_time).limit(5).all()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "projects": projects,
        "reminders": reminders,
        "attachments": attachments,
        "today_events": today_events,
        "upcoming_events": upcoming_events,
        "today_date": today.isoformat()
    })

@app.post("/projects/create")
async def form_router(request: Request):
    from backend.routes.projects import create_project_form
    return await create_project_form(request)

@app.post("/tasks/create")
async def form_router(request: Request):
    from backend.routes.tasks import create_task_form
    return await create_task_form(request)
