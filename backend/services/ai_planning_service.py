# backend/services/ai_planning_service.py
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models.models import Project, Task, Devlog, TimeLog
from ai import ollama_ai

logger = logging.getLogger(__name__)

class AIProjectPlanningService:
    def __init__(self):
        self.db = SessionLocal()
    
    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()
    
    def create_project_plan(self, project_description: str, project_title: str = None) -> Dict[str, Any]:
        """Generate a comprehensive project plan using AI"""
        try:
            if not ollama_ai.is_available():
                return {"error": "AI service not available. Please ensure Ollama is running."}

            system_prompt = """You are an expert project manager. You MUST respond with valid JSON only.
            Do not include any text before or after the JSON. Start your response with { and end with }."""

            prompt = f"""Create a project plan for: "{project_title or 'New Project'}"

Description: {project_description}

Respond with ONLY this JSON structure (no other text):
{{
    "project_title": "Clear project title",
    "project_description": "Enhanced description",
    "estimated_duration_weeks": 4,
    "difficulty_level": "intermediate",
    "tasks": [
        {{
            "title": "Setup Development Environment",
            "description": "Install tools and configure workspace",
            "estimated_hours": 4,
            "priority": "high",
            "dependencies": [],
            "skills_required": ["development"],
            "deliverables": ["configured environment"]
        }},
        {{
            "title": "Create Basic Structure",
            "description": "Set up project foundation",
            "estimated_hours": 8,
            "priority": "high",
            "dependencies": ["Setup Development Environment"],
            "skills_required": ["architecture"],
            "deliverables": ["project structure"]
        }}
    ],
    "milestones": [
        {{
            "name": "Project Setup Complete",
            "description": "Development environment ready",
            "week": 1,
            "tasks_included": ["Setup Development Environment"]
        }}
    ],
    "risks": [
        {{
            "risk": "Technical complexity higher than expected",
            "impact": "medium",
            "mitigation": "Break down complex tasks further"
        }}
    ],
    "recommendations": [
        "Start with a simple prototype",
        "Plan regular progress reviews"
    ]
}}"""

            response = ollama_ai.generate_response(prompt, system_prompt)

            # Clean the response - remove any non-JSON content
            response = response.strip()

            # Try to extract JSON if there's extra text
            if not response.startswith('{'):
                # Look for JSON in the response
                start_idx = response.find('{')
                end_idx = response.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    response = response[start_idx:end_idx+1]

            # Try to parse JSON response
            try:
                plan_data = json.loads(response)

                # Validate required fields and provide defaults
                plan_data = self._validate_and_fix_plan_data(plan_data, project_title, project_description)
                return plan_data

            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed: {e}")
                logger.error(f"Raw response: {response[:500]}...")

                # Return a fallback plan
                return self._create_fallback_plan(project_title, project_description)

        except Exception as e:
            logger.error(f"Error creating project plan: {e}")
            return {"error": f"Failed to create project plan: {str(e)}"}

    def _validate_and_fix_plan_data(self, plan_data: dict, project_title: str, project_description: str) -> dict:
        """Validate and fix plan data structure"""
        # Ensure required fields exist
        plan_data.setdefault("project_title", project_title or "New Project")
        plan_data.setdefault("project_description", project_description)
        plan_data.setdefault("estimated_duration_weeks", 4)
        plan_data.setdefault("difficulty_level", "intermediate")
        plan_data.setdefault("tasks", [])
        plan_data.setdefault("milestones", [])
        plan_data.setdefault("risks", [])
        plan_data.setdefault("recommendations", [])

        # Validate tasks structure
        for i, task in enumerate(plan_data["tasks"]):
            task.setdefault("title", f"Task {i+1}")
            task.setdefault("description", "Task description")
            task.setdefault("estimated_hours", 4)
            task.setdefault("priority", "medium")
            task.setdefault("dependencies", [])
            task.setdefault("skills_required", [])
            task.setdefault("deliverables", [])

        return plan_data

    def _create_fallback_plan(self, project_title: str, project_description: str) -> dict:
        """Create a basic fallback plan when AI fails"""
        return {
            "project_title": project_title or "New Project",
            "project_description": project_description,
            "estimated_duration_weeks": 4,
            "difficulty_level": "intermediate",
            "tasks": [
                {
                    "title": "Project Planning",
                    "description": "Define project scope and requirements",
                    "estimated_hours": 8,
                    "priority": "high",
                    "dependencies": [],
                    "skills_required": ["planning"],
                    "deliverables": ["project plan"]
                },
                {
                    "title": "Setup Development Environment",
                    "description": "Configure tools and workspace",
                    "estimated_hours": 4,
                    "priority": "high",
                    "dependencies": ["Project Planning"],
                    "skills_required": ["development"],
                    "deliverables": ["development environment"]
                },
                {
                    "title": "Implementation Phase 1",
                    "description": "Begin core development work",
                    "estimated_hours": 16,
                    "priority": "high",
                    "dependencies": ["Setup Development Environment"],
                    "skills_required": ["development"],
                    "deliverables": ["initial implementation"]
                },
                {
                    "title": "Testing and Review",
                    "description": "Test functionality and review progress",
                    "estimated_hours": 8,
                    "priority": "medium",
                    "dependencies": ["Implementation Phase 1"],
                    "skills_required": ["testing"],
                    "deliverables": ["test results"]
                }
            ],
            "milestones": [
                {
                    "name": "Project Setup Complete",
                    "description": "Planning and environment ready",
                    "week": 1,
                    "tasks_included": ["Project Planning", "Setup Development Environment"]
                },
                {
                    "name": "First Implementation",
                    "description": "Core functionality implemented",
                    "week": 3,
                    "tasks_included": ["Implementation Phase 1"]
                }
            ],
            "risks": [
                {
                    "risk": "Scope creep during development",
                    "impact": "medium",
                    "mitigation": "Regular scope reviews and clear requirements"
                },
                {
                    "risk": "Technical challenges",
                    "impact": "medium",
                    "mitigation": "Research and prototyping before full implementation"
                }
            ],
            "recommendations": [
                "Start with a minimal viable version",
                "Plan regular progress reviews",
                "Document decisions and learnings",
                "Test early and often"
            ]
        }
    
    def analyze_project_progress(self, project_id: int) -> Dict[str, Any]:
        """Analyze current project progress and suggest adjustments"""
        try:
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"error": "Project not found"}
            
            if not ollama_ai.is_available():
                return {"error": "AI service not available"}
            
            # Gather project data
            tasks = self.db.query(Task).filter(Task.project_id == project_id).all()
            devlogs = self.db.query(Devlog).filter(Devlog.project_id == project_id).order_by(Devlog.created_at.desc()).limit(10).all()
            time_logs = self.db.query(TimeLog).join(Task).filter(Task.project_id == project_id).all()
            
            # Calculate metrics
            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t.completed])
            overdue_tasks = len([t for t in tasks if t.deadline and t.deadline < datetime.now() and not t.completed])
            total_time_logged = sum([tl.duration_minutes for tl in time_logs])
            
            # Prepare context for AI
            project_context = {
                "project_title": project.title,
                "project_description": project.description,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "completion_percentage": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                "overdue_tasks": overdue_tasks,
                "total_hours_logged": total_time_logged / 60,
                "recent_devlogs": [{"date": dl.created_at.strftime("%Y-%m-%d"), "entry": dl.entry_text} for dl in devlogs],
                "task_details": [{"title": t.title, "completed": t.completed, "deadline": t.deadline.isoformat() if t.deadline else None} for t in tasks]
            }
            
            system_prompt = """You are an expert project manager. You MUST respond with valid JSON only.
            Do not include any text before or after the JSON. Start your response with { and end with }."""

            prompt = f"""Analyze this project and respond with ONLY this JSON structure:

Project Data: {json.dumps(project_context, indent=2)}

{{
    "overall_health": "good",
    "progress_analysis": "Project is progressing well with {project_context['completion_percentage']:.1f}% completion",
    "schedule_status": "on_track",
    "bottlenecks": ["example bottleneck"],
    "recommendations": [
        {{
            "type": "immediate",
            "action": "Focus on completing overdue tasks",
            "reason": "To maintain project timeline",
            "priority": "high"
        }}
    ],
    "schedule_adjustments": [
        {{
            "task": "Example Task",
            "current_deadline": "2024-01-01",
            "suggested_deadline": "2024-01-15",
            "reason": "Additional time needed for quality"
        }}
    ],
    "next_steps": ["Complete current tasks", "Review progress", "Plan next phase"]
}}"""

            response = ollama_ai.generate_response(prompt, system_prompt)

            # Clean the response
            response = response.strip()
            if not response.startswith('{'):
                start_idx = response.find('{')
                end_idx = response.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    response = response[start_idx:end_idx+1]

            try:
                analysis = json.loads(response)

                # Validate and provide defaults
                analysis.setdefault("overall_health", "good")
                analysis.setdefault("progress_analysis", f"Project is {project_context['completion_percentage']:.1f}% complete")
                analysis.setdefault("schedule_status", "on_track")
                analysis.setdefault("bottlenecks", [])
                analysis.setdefault("recommendations", [])
                analysis.setdefault("schedule_adjustments", [])
                analysis.setdefault("next_steps", ["Continue with current tasks"])

                return analysis
            except json.JSONDecodeError:
                # Return a basic analysis based on the data
                return {
                    "overall_health": "good" if project_context['completion_percentage'] > 50 else "concerning",
                    "progress_analysis": f"Project is {project_context['completion_percentage']:.1f}% complete with {project_context['overdue_tasks']} overdue tasks",
                    "schedule_status": "on_track" if project_context['overdue_tasks'] == 0 else "slightly_behind",
                    "bottlenecks": ["Overdue tasks"] if project_context['overdue_tasks'] > 0 else [],
                    "recommendations": [
                        {
                            "type": "immediate",
                            "action": "Focus on completing overdue tasks" if project_context['overdue_tasks'] > 0 else "Continue current progress",
                            "reason": "To maintain project timeline",
                            "priority": "high" if project_context['overdue_tasks'] > 0 else "medium"
                        }
                    ],
                    "schedule_adjustments": [],
                    "next_steps": ["Complete current tasks", "Review progress regularly"]
                }
                
        except Exception as e:
            logger.error(f"Error analyzing project progress: {e}")
            return {"error": f"Failed to analyze project: {str(e)}"}
    
    def suggest_task_breakdown(self, task_description: str, project_context: str = "") -> Dict[str, Any]:
        """Break down a complex task into smaller, manageable subtasks"""
        try:
            if not ollama_ai.is_available():
                return {"error": "AI service not available"}

            system_prompt = """You are an expert at task breakdown. You MUST respond with valid JSON only.
            Do not include any text before or after the JSON. Start your response with { and end with }."""

            prompt = f"""Break down this task into subtasks. Respond with ONLY this JSON structure:

Task: {task_description}
Context: {project_context}

{{
    "original_task": "{task_description}",
    "estimated_total_hours": 12,
    "subtasks": [
        {{
            "title": "Research and Planning",
            "description": "Understand requirements and plan approach",
            "estimated_hours": 2,
            "order": 1,
            "dependencies": [],
            "skills_needed": ["analysis"],
            "acceptance_criteria": ["Requirements documented", "Plan created"]
        }},
        {{
            "title": "Implementation",
            "description": "Build the main functionality",
            "estimated_hours": 8,
            "order": 2,
            "dependencies": ["Research and Planning"],
            "skills_needed": ["development"],
            "acceptance_criteria": ["Feature working", "Code reviewed"]
        }},
        {{
            "title": "Testing and Documentation",
            "description": "Test the implementation and document",
            "estimated_hours": 2,
            "order": 3,
            "dependencies": ["Implementation"],
            "skills_needed": ["testing"],
            "acceptance_criteria": ["Tests pass", "Documentation complete"]
        }}
    ],
    "notes": "Consider breaking down further if any subtask exceeds 8 hours"
}}"""

            response = ollama_ai.generate_response(prompt, system_prompt)

            # Clean the response
            response = response.strip()
            if not response.startswith('{'):
                start_idx = response.find('{')
                end_idx = response.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    response = response[start_idx:end_idx+1]

            try:
                breakdown = json.loads(response)

                # Validate and provide defaults
                breakdown.setdefault("original_task", task_description)
                breakdown.setdefault("estimated_total_hours", 8)
                breakdown.setdefault("subtasks", [])
                breakdown.setdefault("notes", "")

                # Validate subtasks
                for i, subtask in enumerate(breakdown["subtasks"]):
                    subtask.setdefault("title", f"Subtask {i+1}")
                    subtask.setdefault("description", "Subtask description")
                    subtask.setdefault("estimated_hours", 2)
                    subtask.setdefault("order", i+1)
                    subtask.setdefault("dependencies", [])
                    subtask.setdefault("skills_needed", [])
                    subtask.setdefault("acceptance_criteria", [])

                return breakdown

            except json.JSONDecodeError:
                # Return a basic breakdown
                return {
                    "original_task": task_description,
                    "estimated_total_hours": 8,
                    "subtasks": [
                        {
                            "title": "Research and Planning",
                            "description": "Understand requirements and plan approach",
                            "estimated_hours": 2,
                            "order": 1,
                            "dependencies": [],
                            "skills_needed": ["analysis"],
                            "acceptance_criteria": ["Requirements clear", "Plan documented"]
                        },
                        {
                            "title": "Implementation",
                            "description": "Execute the main work",
                            "estimated_hours": 4,
                            "order": 2,
                            "dependencies": ["Research and Planning"],
                            "skills_needed": ["implementation"],
                            "acceptance_criteria": ["Work completed", "Quality checked"]
                        },
                        {
                            "title": "Review and Finalize",
                            "description": "Review work and finalize",
                            "estimated_hours": 2,
                            "order": 3,
                            "dependencies": ["Implementation"],
                            "skills_needed": ["review"],
                            "acceptance_criteria": ["Review complete", "Task finalized"]
                        }
                    ],
                    "notes": "Basic task breakdown - consider customizing based on specific requirements"
                }
                
        except Exception as e:
            logger.error(f"Error breaking down task: {e}")
            return {"error": f"Failed to break down task: {str(e)}"}
    
    def auto_adjust_schedule(self, project_id: int, delay_reason: str = "") -> Dict[str, Any]:
        """Automatically adjust project schedule based on current progress and delays"""
        try:
            # First analyze the project
            analysis = self.analyze_project_progress(project_id)
            
            if "error" in analysis:
                return analysis
            
            # Get project and tasks
            project = self.db.query(Project).filter(Project.id == project_id).first()
            tasks = self.db.query(Task).filter(Task.project_id == project_id).all()
            
            # Apply AI-suggested schedule adjustments
            adjustments_made = []
            
            if "schedule_adjustments" in analysis:
                for adjustment in analysis["schedule_adjustments"]:
                    task_title = adjustment.get("task")
                    new_deadline = adjustment.get("suggested_deadline")
                    reason = adjustment.get("reason")
                    
                    # Find matching task
                    matching_task = next((t for t in tasks if t.title == task_title), None)
                    
                    if matching_task and new_deadline:
                        try:
                            new_deadline_dt = datetime.fromisoformat(new_deadline)
                            old_deadline = matching_task.deadline
                            matching_task.deadline = new_deadline_dt
                            
                            adjustments_made.append({
                                "task": task_title,
                                "old_deadline": old_deadline.isoformat() if old_deadline else None,
                                "new_deadline": new_deadline,
                                "reason": reason
                            })
                        except ValueError:
                            logger.warning(f"Invalid date format for task {task_title}: {new_deadline}")
            
            # Commit changes
            if adjustments_made:
                self.db.commit()
            
            return {
                "success": True,
                "adjustments_made": adjustments_made,
                "analysis": analysis,
                "delay_reason": delay_reason
            }
            
        except Exception as e:
            logger.error(f"Error auto-adjusting schedule: {e}")
            return {"error": f"Failed to adjust schedule: {str(e)}"}

# Global service instance
ai_planning_service = AIProjectPlanningService()
