# backend/routes/ai_planning.py
from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from backend.models import models
from backend.dependencies import get_db
from backend.services.ai_planning_service import ai_planning_service
from typing import Optional
import json
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/ai/status")
async def ai_status():
    """Check AI service status"""
    try:
        from ai import ollama_ai

        if not ollama_ai.is_available():
            return JSONResponse({
                "status": "unavailable",
                "message": "Ollama service is not running",
                "available": False
            })

        # Test a simple response
        test_response = ollama_ai.generate_response(
            "Respond with exactly: {'test': 'success'}",
            "You must respond with valid JSON only."
        )

        return JSONResponse({
            "status": "available",
            "message": "AI service is working",
            "available": True,
            "test_response": test_response[:100] + "..." if len(test_response) > 100 else test_response
        })

    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": f"AI service error: {str(e)}",
            "available": False
        })

@router.post("/ai/create-project-plan")
async def create_ai_project_plan(
    project_description: str = Form(...),
    project_title: str = Form(""),
    db: Session = Depends(get_db)
):
    """Create a new project with AI-generated plan"""
    try:
        # Generate AI plan
        plan_data = ai_planning_service.create_project_plan(
            project_description, 
            project_title if project_title else None
        )
        
        if "error" in plan_data:
            return JSONResponse(
                status_code=500, 
                content={"error": plan_data["error"]}
            )
        
        # Create project
        project = models.Project(
            title=plan_data.get("project_title", project_title or "AI Generated Project"),
            description=plan_data.get("project_description", project_description)
        )
        db.add(project)
        db.flush()  # Get the project ID
        
        # Save the AI plan
        project_plan = models.ProjectPlan(
            project_id=project.id,
            ai_generated=True,
            plan_data=plan_data,
            estimated_duration_weeks=plan_data.get("estimated_duration_weeks", 4),
            difficulty_level=plan_data.get("difficulty_level", "intermediate")
        )
        db.add(project_plan)
        
        # Create tasks from AI plan
        if "tasks" in plan_data:
            for i, task_data in enumerate(plan_data["tasks"]):
                task = models.Task(
                    title=task_data.get("title", f"Task {i+1}"),
                    description=task_data.get("description", ""),
                    project_id=project.id,
                    estimated_hours=task_data.get("estimated_hours", 4),
                    priority=task_data.get("priority", "medium"),
                    ai_generated=True,
                    order_index=i,
                    skills_required=task_data.get("skills_required", []),
                    dependencies=task_data.get("dependencies", [])
                )
                db.add(task)
        
        # Create milestones
        if "milestones" in plan_data:
            for milestone_data in plan_data["milestones"]:
                milestone = models.ProjectMilestone(
                    project_id=project.id,
                    name=milestone_data.get("name", "Milestone"),
                    description=milestone_data.get("description", ""),
                    target_week=milestone_data.get("week", 1)
                )
                db.add(milestone)
        
        # Create risks
        if "risks" in plan_data:
            for risk_data in plan_data["risks"]:
                risk = models.ProjectRisk(
                    project_id=project.id,
                    risk_description=risk_data.get("risk", ""),
                    impact_level=risk_data.get("impact", "medium"),
                    mitigation_strategy=risk_data.get("mitigation", "")
                )
                db.add(risk)
        
        db.commit()
        
        return JSONResponse({
            "success": True,
            "project_id": project.id,
            "plan_data": plan_data
        })
        
    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to create AI project plan: {str(e)}"}
        )

@router.post("/ai/analyze-project/{project_id}")
async def analyze_project_progress(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Analyze project progress using AI"""
    try:
        analysis = ai_planning_service.analyze_project_progress(project_id)
        return JSONResponse(analysis)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to analyze project: {str(e)}"}
        )

@router.post("/ai/adjust-schedule/{project_id}")
async def auto_adjust_schedule(
    project_id: int,
    delay_reason: str = Form(""),
    db: Session = Depends(get_db)
):
    """Automatically adjust project schedule based on AI analysis"""
    try:
        result = ai_planning_service.auto_adjust_schedule(project_id, delay_reason)
        
        if result.get("success") and result.get("adjustments_made"):
            # Log the schedule adjustments
            for adjustment in result["adjustments_made"]:
                schedule_adj = models.ScheduleAdjustment(
                    project_id=project_id,
                    adjustment_reason=delay_reason or "AI-suggested adjustment",
                    old_deadline=datetime.fromisoformat(adjustment["old_deadline"]) if adjustment["old_deadline"] else None,
                    new_deadline=datetime.fromisoformat(adjustment["new_deadline"]),
                    ai_suggested=True,
                    applied=True
                )
                db.add(schedule_adj)
            
            db.commit()
        
        return JSONResponse(result)
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to adjust schedule: {str(e)}"}
        )

@router.post("/ai/break-down-task")
async def break_down_task(
    task_description: str = Form(...),
    project_context: str = Form(""),
    project_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """Break down a complex task into subtasks using AI"""
    try:
        breakdown = ai_planning_service.suggest_task_breakdown(
            task_description, 
            project_context
        )
        
        if "error" in breakdown:
            return JSONResponse(
                status_code=500,
                content=breakdown
            )
        
        # If project_id is provided, create the subtasks
        if project_id and "subtasks" in breakdown:
            # Create parent task first
            parent_task = models.Task(
                title=breakdown.get("original_task", task_description),
                description=f"Parent task broken down by AI. Total estimated hours: {breakdown.get('estimated_total_hours', 0)}",
                project_id=project_id,
                estimated_hours=breakdown.get("estimated_total_hours", 0),
                ai_generated=True
            )
            db.add(parent_task)
            db.flush()
            
            # Create subtasks
            for subtask_data in breakdown["subtasks"]:
                subtask = models.Task(
                    title=subtask_data.get("title", "Subtask"),
                    description=subtask_data.get("description", ""),
                    project_id=project_id,
                    parent_task_id=parent_task.id,
                    estimated_hours=subtask_data.get("estimated_hours", 1),
                    order_index=subtask_data.get("order", 0),
                    ai_generated=True,
                    skills_required=subtask_data.get("skills_needed", []),
                    dependencies=subtask_data.get("dependencies", [])
                )
                db.add(subtask)
            
            db.commit()
            breakdown["parent_task_id"] = parent_task.id
        
        return JSONResponse(breakdown)
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to break down task: {str(e)}"}
        )

@router.get("/ai/project-insights/{project_id}")
async def get_project_insights(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Get comprehensive AI insights for a project"""
    try:
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get project plan if exists
        project_plan = db.query(models.ProjectPlan).filter(
            models.ProjectPlan.project_id == project_id
        ).first()
        
        # Get milestones
        milestones = db.query(models.ProjectMilestone).filter(
            models.ProjectMilestone.project_id == project_id
        ).all()
        
        # Get risks
        risks = db.query(models.ProjectRisk).filter(
            models.ProjectRisk.project_id == project_id
        ).all()
        
        # Get recent schedule adjustments
        adjustments = db.query(models.ScheduleAdjustment).filter(
            models.ScheduleAdjustment.project_id == project_id
        ).order_by(models.ScheduleAdjustment.created_at.desc()).limit(5).all()
        
        insights = {
            "project": {
                "id": project.id,
                "title": project.title,
                "description": project.description
            },
            "plan": project_plan.plan_data if project_plan else None,
            "milestones": [
                {
                    "name": m.name,
                    "description": m.description,
                    "target_week": m.target_week,
                    "completed": m.completed
                } for m in milestones
            ],
            "risks": [
                {
                    "description": r.risk_description,
                    "impact": r.impact_level,
                    "mitigation": r.mitigation_strategy,
                    "status": r.status
                } for r in risks
            ],
            "recent_adjustments": [
                {
                    "reason": a.adjustment_reason,
                    "old_deadline": a.old_deadline.isoformat() if a.old_deadline else None,
                    "new_deadline": a.new_deadline.isoformat() if a.new_deadline else None,
                    "date": a.created_at.isoformat()
                } for a in adjustments
            ]
        }
        
        return JSONResponse(insights)
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to get project insights: {str(e)}"}
        )
