# backend/main.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend.database import engine
from backend.models import models
from backend.routes import projects, tasks
from backend.dependencies import get_db

from sqlalchemy.orm import Session
from fastapi import Depends

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Configure Jinja2 templates
templates = Jinja2Templates(directory="frontend/templates")

# Include API routes
app.include_router(projects.router)
app.include_router(tasks.router)

# Initialize DB
models.Base.metadata.create_all(bind=engine)

# Serve Home Page
@app.get("/", response_class=HTMLResponse)
def get_home(request: Request, db: Session = Depends(get_db)):
    projects = db.query(models.Project).all()
    return templates.TemplateResponse("index.html", {"request": request, "projects": projects})

@app.post("/projects/create")
async def form_router(request: Request):
    from backend.routes.projects import create_project_form
    return await create_project_form(request)

@app.post("/tasks/create")
async def form_router(request: Request):
    from backend.routes.tasks import create_task_form
    return await create_task_form(request)
