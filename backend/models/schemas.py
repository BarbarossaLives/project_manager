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

class DevlogBase(BaseModel):
    project_id: int
    entry_text: str

class DevlogCreate(DevlogBase): pass

class Devlog(DevlogBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ReminderBase(BaseModel):
    message: str
    due_date: datetime

class ReminderCreate(ReminderBase): pass

class Reminder(ReminderBase):
    id: int
    sent: bool

    model_config = ConfigDict(from_attributes=True)

class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    all_day: Optional[bool] = False
    location: Optional[str] = None
    event_type: Optional[str] = "personal"
    priority: Optional[str] = "medium"
    project_id: Optional[int] = None
    task_id: Optional[int] = None
    recurring: Optional[bool] = False
    recurrence_pattern: Optional[str] = None
    recurrence_end: Optional[datetime] = None

class EventCreate(EventBase):
    pass

class Event(EventBase):
    id: int
    completed: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)