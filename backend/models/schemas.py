# backend/models/schemas.py

from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class TaskBase(BaseModel):
    title: str
    deadline: Optional[datetime] = None
    completed: Optional[bool] = False

class TaskCreate(TaskBase):
    project_id: int

class Task(TaskBase):
    id: int
    project_id: int

    model_config = ConfigDict(from_attributes=True)

class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = ""

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: int
    created_at: datetime
    tasks: List[Task] = []

    model_config = ConfigDict(from_attributes=True)