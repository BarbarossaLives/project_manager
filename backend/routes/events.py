# backend/routes/events.py
from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
from backend.models import models, schemas
from backend.dependencies import get_db
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/events/create")
def create_event(
    title: str = Form(...),
    description: str = Form(""),
    start_date: str = Form(...),  # YYYY-MM-DD
    start_time: str = Form("09:00"),  # HH:MM
    end_time: str = Form(""),  # HH:MM (optional)
    all_day: Optional[str] = Form(None),  # Checkbox value
    location: str = Form(""),
    event_type: str = Form("personal"),
    priority: str = Form("medium"),
    project_id: Optional[str] = Form(None),  # Handle empty string
    task_id: Optional[str] = Form(None),  # Handle empty string
    recurring: Optional[str] = Form(None),  # Checkbox value
    recurrence_pattern: str = Form(""),
    db: Session = Depends(get_db)
):
    """Create a new event"""
    try:
        logger.info(f"Creating event: title={title}, start_date={start_date}, all_day={all_day}")

        # Convert checkbox values to boolean
        is_all_day = all_day is not None and all_day.lower() in ['on', 'true', '1']
        is_recurring = recurring is not None and recurring.lower() in ['on', 'true', '1']

        # Convert project_id and task_id to integers or None
        project_id_int = None
        if project_id and project_id.strip() and project_id != "":
            try:
                project_id_int = int(project_id)
            except ValueError:
                pass

        task_id_int = None
        if task_id and task_id.strip() and task_id != "":
            try:
                task_id_int = int(task_id)
            except ValueError:
                pass

        # Parse start datetime
        if is_all_day:
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            end_datetime = start_datetime + timedelta(days=1) - timedelta(seconds=1)
        else:
            start_datetime_str = f"{start_date} {start_time}"
            start_datetime = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M")

            if end_time and end_time.strip():
                end_datetime_str = f"{start_date} {end_time}"
                end_datetime = datetime.strptime(end_datetime_str, "%Y-%m-%d %H:%M")
            else:
                end_datetime = start_datetime + timedelta(hours=1)  # Default 1 hour duration

        # Create event
        event = models.Event(
            title=title,
            description=description if description.strip() else None,
            start_time=start_datetime,
            end_time=end_datetime,
            all_day=is_all_day,
            location=location if location.strip() else None,
            event_type=event_type,
            priority=priority,
            project_id=project_id_int,
            task_id=task_id_int,
            recurring=is_recurring,
            recurrence_pattern=recurrence_pattern if recurrence_pattern.strip() else None
        )
        
        db.add(event)
        db.commit()

        logger.info(f"Event created successfully: {event.id}")
        return RedirectResponse("/", status_code=303)

    except ValueError as e:
        logger.error(f"Date/time format error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid date/time format: {e}")
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create event: {e}")

@router.get("/events/", response_model=List[schemas.Event])
def get_events(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get events, optionally filtered by date range"""
    query = db.query(models.Event)
    
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(models.Event.start_time >= start_dt)
    
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        query = query.filter(models.Event.start_time < end_dt)
    
    return query.order_by(models.Event.start_time).all()

@router.get("/events/today")
def get_today_events(db: Session = Depends(get_db)):
    """Get today's events"""
    today = date.today()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = start_of_day + timedelta(days=1)
    
    events = db.query(models.Event).filter(
        models.Event.start_time >= start_of_day,
        models.Event.start_time < end_of_day
    ).order_by(models.Event.start_time).all()
    
    return JSONResponse({
        "date": today.isoformat(),
        "events": [
            {
                "id": event.id,
                "title": event.title,
                "description": event.description,
                "start_time": event.start_time.strftime("%H:%M"),
                "end_time": event.end_time.strftime("%H:%M") if event.end_time else None,
                "all_day": event.all_day,
                "location": event.location,
                "event_type": event.event_type,
                "priority": event.priority,
                "completed": event.completed,
                "project_title": event.project.title if event.project else None,
                "task_title": event.task.title if event.task else None
            } for event in events
        ]
    })

@router.get("/schedule/daily/{date_str}")
def get_daily_schedule(date_str: str, db: Session = Depends(get_db)):
    """Get complete daily schedule including events and tasks"""
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = start_of_day + timedelta(days=1)
        
        # Get events for the day
        events = db.query(models.Event).filter(
            models.Event.start_time >= start_of_day,
            models.Event.start_time < end_of_day
        ).order_by(models.Event.start_time).all()
        
        # Get tasks with deadlines on this day
        tasks_due = db.query(models.Task).filter(
            models.Task.deadline.isnot(None),
            models.Task.deadline >= start_of_day,
            models.Task.deadline < end_of_day,
            models.Task.completed == False
        ).order_by(models.Task.deadline).all()

        # Get overdue tasks (deadline before today)
        overdue_tasks = db.query(models.Task).filter(
            models.Task.deadline.isnot(None),
            models.Task.deadline < start_of_day,
            models.Task.completed == False
        ).order_by(models.Task.deadline).all()

        # Get all incomplete tasks (for project steps view)
        all_incomplete_tasks = db.query(models.Task).filter(
            models.Task.completed == False
        ).order_by(models.Task.project_id, models.Task.order_index).all()

        # Get completed tasks for today (to show progress)
        completed_today = db.query(models.Task).filter(
            models.Task.completed == True,
            models.Task.updated_at.isnot(None),
            models.Task.updated_at >= start_of_day,
            models.Task.updated_at < end_of_day
        ).order_by(models.Task.updated_at).all()
        
        # Combine into schedule items
        schedule_items = []
        
        # Add events
        for event in events:
            schedule_items.append({
                "type": "event",
                "id": event.id,
                "title": event.title,
                "description": event.description,
                "start_time": event.start_time.strftime("%H:%M") if not event.all_day else "All Day",
                "end_time": event.end_time.strftime("%H:%M") if event.end_time and not event.all_day else None,
                "all_day": event.all_day,
                "location": event.location,
                "priority": event.priority,
                "event_type": event.event_type,
                "completed": event.completed,
                "project_title": getattr(event.project, 'title', None) if event.project else None,
                "sort_time": event.start_time
            })
        
        # Add tasks due today
        for task in tasks_due:
            schedule_items.append({
                "type": "task_due",
                "id": task.id,
                "title": f"📋 {task.title}",
                "description": task.description,
                "start_time": task.deadline.strftime("%H:%M") if task.deadline else "No time",
                "end_time": None,
                "all_day": False,
                "location": None,
                "priority": task.priority,
                "event_type": "deadline",
                "completed": task.completed,
                "project_title": getattr(task.project, 'title', None) if task.project else None,
                "sort_time": task.deadline or start_of_day
            })
        
        # Sort all items by time
        schedule_items.sort(key=lambda x: x["sort_time"])
        
        # Remove sort_time from response
        for item in schedule_items:
            del item["sort_time"]
        
        return JSONResponse({
            "date": target_date.isoformat(),
            "day_name": target_date.strftime("%A"),
            "schedule_items": schedule_items,
            "overdue_tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "deadline": task.deadline.strftime("%Y-%m-%d %H:%M") if task.deadline else None,
                    "project_title": getattr(task.project, 'title', None) if task.project else None,
                    "priority": task.priority
                } for task in overdue_tasks
            ],
            "project_tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "project_title": getattr(task.project, 'title', None) if task.project else "No Project",
                    "project_id": task.project_id,
                    "priority": task.priority,
                    "estimated_hours": task.estimated_hours,
                    "ai_generated": task.ai_generated,
                    "order_index": task.order_index
                } for task in all_incomplete_tasks
            ],
            "completed_today": [
                {
                    "id": task.id,
                    "title": task.title,
                    "project_title": getattr(task.project, 'title', None) if task.project else "No Project",
                    "completed_at": task.updated_at.strftime("%H:%M")
                } for task in completed_today
            ],
            "summary": {
                "total_events": len(events),
                "total_tasks_due": len(tasks_due),
                "total_overdue": len(overdue_tasks),
                "total_project_tasks": len(all_incomplete_tasks),
                "completed_today": len(completed_today),
                "high_priority_items": len([item for item in schedule_items if item["priority"] == "high"])
            }
        })
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get daily schedule: {e}")

@router.post("/events/{event_id}/complete")
def complete_event(event_id: int, db: Session = Depends(get_db)):
    """Mark an event as completed"""
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    event.completed = True
    db.commit()
    
    return JSONResponse({"success": True, "message": "Event marked as completed"})

@router.post("/tasks/{task_id}/complete")
def complete_task(task_id: int, db: Session = Depends(get_db)):
    """Mark a task as completed"""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.completed = True
    db.commit()

    logger.info(f"Task {task_id} marked as completed")
    return JSONResponse({"success": True, "message": "Task marked as completed"})

@router.post("/tasks/{task_id}/uncomplete")
def uncomplete_task(task_id: int, db: Session = Depends(get_db)):
    """Mark a task as not completed"""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.completed = False
    db.commit()

    logger.info(f"Task {task_id} marked as not completed")
    return JSONResponse({"success": True, "message": "Task marked as not completed"})

@router.get("/projects/{project_id}/tasks")
def get_project_tasks(project_id: int, db: Session = Depends(get_db)):
    """Get all tasks for a specific project"""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    tasks = db.query(models.Task).filter(
        models.Task.project_id == project_id
    ).order_by(models.Task.order_index, models.Task.id).all()

    return JSONResponse({
        "project": {
            "id": project.id,
            "title": project.title,
            "description": project.description
        },
        "tasks": [
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "completed": task.completed,
                "priority": task.priority,
                "estimated_hours": task.estimated_hours,
                "ai_generated": task.ai_generated,
                "order_index": task.order_index,
                "deadline": task.deadline.isoformat() if task.deadline else None,
                "parent_task_id": task.parent_task_id
            } for task in tasks
        ],
        "progress": {
            "total_tasks": len(tasks),
            "completed_tasks": len([t for t in tasks if t.completed]),
            "completion_percentage": (len([t for t in tasks if t.completed]) / len(tasks) * 100) if tasks else 0
        }
    })

@router.get("/schedule/project-steps")
def get_all_project_steps(db: Session = Depends(get_db)):
    """Get all project steps organized by project"""
    projects = db.query(models.Project).all()

    project_steps = []
    for project in projects:
        tasks = db.query(models.Task).filter(
            models.Task.project_id == project.id
        ).order_by(models.Task.order_index, models.Task.id).all()

        if tasks:  # Only include projects that have tasks
            project_steps.append({
                "project": {
                    "id": project.id,
                    "title": project.title,
                    "description": project.description
                },
                "tasks": [
                    {
                        "id": task.id,
                        "title": task.title,
                        "description": task.description,
                        "completed": task.completed,
                        "priority": task.priority,
                        "estimated_hours": task.estimated_hours,
                        "ai_generated": task.ai_generated,
                        "deadline": task.deadline.isoformat() if task.deadline else None,
                        "parent_task_id": task.parent_task_id
                    } for task in tasks
                ],
                "progress": {
                    "total_tasks": len(tasks),
                    "completed_tasks": len([t for t in tasks if t.completed]),
                    "completion_percentage": (len([t for t in tasks if t.completed]) / len(tasks) * 100) if tasks else 0
                }
            })

    return JSONResponse({
        "project_steps": project_steps,
        "summary": {
            "total_projects": len(project_steps),
            "total_tasks": sum([p["progress"]["total_tasks"] for p in project_steps]),
            "total_completed": sum([p["progress"]["completed_tasks"] for p in project_steps])
        }
    })

@router.delete("/events/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    """Delete an event"""
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    db.delete(event)
    db.commit()

    return JSONResponse({"success": True, "message": "Event deleted"})

@router.get("/schedule/week/{date_str}")
def get_weekly_schedule(date_str: str, db: Session = Depends(get_db)):
    """Get weekly schedule starting from the given date"""
    try:
        start_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        # Get the Monday of the week containing start_date
        monday = start_date - timedelta(days=start_date.weekday())
        
        weekly_schedule = []
        
        for i in range(7):  # 7 days in a week
            current_date = monday + timedelta(days=i)
            daily_response = get_daily_schedule(current_date.strftime("%Y-%m-%d"), db)
            daily_data = daily_response.body.decode() if hasattr(daily_response, 'body') else daily_response
            
            if isinstance(daily_data, str):
                import json
                daily_data = json.loads(daily_data)
            
            weekly_schedule.append(daily_data)
        
        return JSONResponse({
            "week_start": monday.isoformat(),
            "week_end": (monday + timedelta(days=6)).isoformat(),
            "days": weekly_schedule
        })
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get weekly schedule: {e}")
