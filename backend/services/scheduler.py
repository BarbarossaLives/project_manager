# backend/services/scheduler.py
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from backend.services.reminder_service import reminder_service

logger = logging.getLogger(__name__)

class BackgroundScheduler:
    def __init__(self):
        self.running = False
        self.tasks = []
    
    async def start(self):
        """Start the background scheduler"""
        if self.running:
            return
            
        self.running = True
        logger.info("🚀 Starting background scheduler...")
        
        # Start background tasks
        self.tasks = [
            asyncio.create_task(self._reminder_checker()),
            asyncio.create_task(self._weekly_reminder_generator()),
        ]
        
        logger.info("✅ Background scheduler started")
    
    async def stop(self):
        """Stop the background scheduler"""
        if not self.running:
            return
            
        self.running = False
        logger.info("🛑 Stopping background scheduler...")
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
            
        # Wait for tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()
        
        logger.info("✅ Background scheduler stopped")
    
    async def _reminder_checker(self):
        """Check for due reminders every minute"""
        while self.running:
            try:
                await reminder_service.process_due_reminders()
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in reminder checker: {e}")
                await asyncio.sleep(60)
    
    async def _weekly_reminder_generator(self):
        """Generate weekly reminders every day at 9 AM"""
        while self.running:
            try:
                now = datetime.now()
                
                # Check if it's 9 AM (or close to it)
                if now.hour == 9 and now.minute < 5:
                    await reminder_service.auto_generate_weekly_reminders()
                    # Sleep for 6 hours to avoid running multiple times
                    await asyncio.sleep(6 * 60 * 60)
                else:
                    # Check every 5 minutes
                    await asyncio.sleep(5 * 60)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in weekly reminder generator: {e}")
                await asyncio.sleep(5 * 60)

# Global scheduler instance
scheduler = BackgroundScheduler()
