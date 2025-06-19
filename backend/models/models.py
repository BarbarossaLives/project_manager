# backend/models/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.database import Base
from datetime import datetime
from sqlalchemy import Time, Float


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    title = Column(String, index=True)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    tasks = relationship("Task", back_populates="project")
    attachments = relationship("Attachment", back_populates="project")  # ✅ FIXED HERE


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    deadline = Column(DateTime, nullable=True)
    completed = Column(Boolean, default=False)
    project_id = Column(Integer, ForeignKey("projects.id"))

    # AI Planning fields
    estimated_hours = Column(Float, nullable=True)
    priority = Column(String, default="medium")  # high, medium, low
    ai_generated = Column(Boolean, default=False)
    parent_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    order_index = Column(Integer, default=0)
    skills_required = Column(JSON, nullable=True)  # List of required skills
    dependencies = Column(JSON, nullable=True)  # List of task dependencies

    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    project = relationship("Project", back_populates="tasks")
    attachments = relationship("Attachment", back_populates="task")

    # Self-referential relationship for subtasks
    subtasks = relationship("Task", backref="parent_task", remote_side=[id])



class TimeLog(Base):
    __tablename__ = "timelogs"
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    duration_minutes = Column(Float, default=0.0)

    task = relationship("Task", backref="timelogs")

class Devlog(Base):
    __tablename__ = "devlogs"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    entry_text = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", backref="devlogs")

class Reminder(Base):
    __tablename__ = "reminders"
    id = Column(Integer, primary_key=True)
    message = Column(String)
    due_date = Column(DateTime)
    sent = Column(Boolean, default=False)


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True)
    filename = Column(String)
    filepath = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)

    task = relationship("Task", back_populates="attachments")
    project = relationship("Project", back_populates="attachments")  # ✅ FIXED HERE


class ProjectPlan(Base):
    __tablename__ = "project_plans"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    ai_generated = Column(Boolean, default=True)
    plan_data = Column(JSON)  # Store the full AI-generated plan
    estimated_duration_weeks = Column(Integer)
    difficulty_level = Column(String)  # beginner, intermediate, advanced
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    project = relationship("Project", backref="plans")


class ProjectMilestone(Base):
    __tablename__ = "project_milestones"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    name = Column(String)
    description = Column(Text)
    target_week = Column(Integer)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    project = relationship("Project", backref="milestones")


class ProjectRisk(Base):
    __tablename__ = "project_risks"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    risk_description = Column(Text)
    impact_level = Column(String)  # high, medium, low
    mitigation_strategy = Column(Text)
    status = Column(String, default="active")  # active, mitigated, occurred
    created_at = Column(DateTime, default=datetime.now)

    project = relationship("Project", backref="risks")


class ScheduleAdjustment(Base):
    __tablename__ = "schedule_adjustments"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    adjustment_reason = Column(Text)
    old_deadline = Column(DateTime, nullable=True)
    new_deadline = Column(DateTime, nullable=True)
    ai_suggested = Column(Boolean, default=True)
    applied = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

    project = relationship("Project", backref="schedule_adjustments")
    task = relationship("Task", backref="schedule_adjustments")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime, nullable=True)
    all_day = Column(Boolean, default=False)
    location = Column(String, nullable=True)
    event_type = Column(String, default="personal")  # personal, meeting, deadline, etc.
    priority = Column(String, default="medium")  # high, medium, low
    completed = Column(Boolean, default=False)

    # Optional project association
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)

    # Recurrence fields
    recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String, nullable=True)  # daily, weekly, monthly
    recurrence_end = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    project = relationship("Project", backref="events")
    task = relationship("Task", backref="events")
