# backend/services/reminder_service.py
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models.models import Reminder, Project, Devlog, Task
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReminderService:
    def __init__(self):
        self.db = SessionLocal()
    
    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()
    
    def get_due_reminders(self) -> List[Reminder]:
        """Get all reminders that are due and haven't been sent"""
        now = datetime.utcnow()
        return self.db.query(Reminder).filter(
            Reminder.due_date <= now,
            Reminder.sent == False
        ).all()
    
    def mark_reminder_sent(self, reminder_id: int):
        """Mark a reminder as sent"""
        reminder = self.db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if reminder:
            reminder.sent = True
            self.db.commit()
            logger.info(f"Marked reminder {reminder_id} as sent")
    
    def send_notification(self, reminder: Reminder) -> bool:
        """Send notification for a reminder (placeholder for actual implementation)"""
        try:
            # For now, just log the reminder
            logger.info(f"🔔 REMINDER DUE: {reminder.message}")
            logger.info(f"📅 Due date: {reminder.due_date}")
            
            # Here you could integrate with:
            # - Email notifications
            # - Push notifications
            # - Slack/Discord webhooks
            # - Social media APIs
            
            return True
        except Exception as e:
            logger.error(f"Failed to send notification for reminder {reminder.id}: {e}")
            return False
    
    def auto_generate_progress_reminders(self, project_id: Optional[int] = None):
        """Automatically generate reminders based on project activity"""
        try:
            # Get projects to generate reminders for
            if project_id:
                projects = self.db.query(Project).filter(Project.id == project_id).all()
            else:
                projects = self.db.query(Project).all()
            
            for project in projects:
                # Check if project has recent activity (devlogs, completed tasks)
                recent_activity = self._has_recent_activity(project)
                
                if recent_activity:
                    # Generate reminder for next week
                    next_week = datetime.utcnow() + timedelta(days=7)
                    
                    # Check if reminder already exists for this timeframe
                    existing_reminder = self.db.query(Reminder).filter(
                        Reminder.message.contains(project.title),
                        Reminder.due_date.between(
                            datetime.utcnow() + timedelta(days=6),
                            datetime.utcnow() + timedelta(days=8)
                        ),
                        Reminder.sent == False
                    ).first()
                    
                    if not existing_reminder:
                        reminder_message = f"Share progress update for '{project.title}' project! 🚀"
                        
                        new_reminder = Reminder(
                            message=reminder_message,
                            due_date=next_week,
                            sent=False
                        )
                        
                        self.db.add(new_reminder)
                        self.db.commit()
                        logger.info(f"Auto-generated reminder for project: {project.title}")
                        
        except Exception as e:
            logger.error(f"Error auto-generating reminders: {e}")
    
    def _has_recent_activity(self, project: Project) -> bool:
        """Check if project has recent activity (last 7 days)"""
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Check for recent devlogs
        recent_devlogs = self.db.query(Devlog).filter(
            Devlog.project_id == project.id,
            Devlog.created_at >= week_ago
        ).count()
        
        # Check for recently completed tasks
        recent_completed_tasks = self.db.query(Task).filter(
            Task.project_id == project.id,
            Task.completed == True
        ).count()
        
        return recent_devlogs > 0 or recent_completed_tasks > 0
    
    def generate_social_media_content(self, project: Project) -> str:
        """Generate social media content based on project progress"""
        try:
            # Get recent devlogs
            recent_devlogs = self.db.query(Devlog).filter(
                Devlog.project_id == project.id
            ).order_by(Devlog.created_at.desc()).limit(3).all()
            
            # Get completed tasks count
            completed_tasks = self.db.query(Task).filter(
                Task.project_id == project.id,
                Task.completed == True
            ).count()
            
            total_tasks = self.db.query(Task).filter(
                Task.project_id == project.id
            ).count()
            
            # Generate content
            content_parts = [
                f"🚀 Progress update on '{project.title}'!",
                f"✅ {completed_tasks}/{total_tasks} tasks completed"
            ]
            
            if recent_devlogs:
                content_parts.append("\n📝 Recent work:")
                for devlog in recent_devlogs[:2]:  # Show last 2 entries
                    # Truncate long entries
                    entry = devlog.entry_text[:100] + "..." if len(devlog.entry_text) > 100 else devlog.entry_text
                    content_parts.append(f"• {entry}")
            
            content_parts.extend([
                "\n#coding #productivity #buildinpublic",
                f"#{project.title.lower().replace(' ', '')}"
            ])
            
            return "\n".join(content_parts)
            
        except Exception as e:
            logger.error(f"Error generating social media content: {e}")
            return f"Working on '{project.title}' project! 🚀 #coding #buildinpublic"
    
    async def process_due_reminders(self):
        """Process all due reminders"""
        try:
            due_reminders = self.get_due_reminders()
            
            for reminder in due_reminders:
                success = self.send_notification(reminder)
                if success:
                    self.mark_reminder_sent(reminder.id)
                    
            if due_reminders:
                logger.info(f"Processed {len(due_reminders)} due reminders")
                
        except Exception as e:
            logger.error(f"Error processing due reminders: {e}")
    
    async def auto_generate_weekly_reminders(self):
        """Generate weekly reminders for active projects"""
        try:
            self.auto_generate_progress_reminders()
            logger.info("Auto-generated weekly reminders")
        except Exception as e:
            logger.error(f"Error auto-generating weekly reminders: {e}")

# Global service instance
reminder_service = ReminderService()
