from django.apps import AppConfig


class SchedulingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scheduling'
    
    def ready(self):
        """Import signal handlers when Django starts"""
        import scheduling.signals
        
        # Auto-populate timeslots on server start for immediate availability
        self._populate_timeslots_if_empty()
    
    def _populate_timeslots_if_empty(self):
        """Populate timeslots table if it's empty (one-time setup)"""
        from .models import AvailableTimeslot
        from django.core.management import call_command
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Check if table is empty
            if not AvailableTimeslot.objects.exists():
                logger.info("📊 Timeslots table is empty. Populating...")
                call_command('populate_timeslots', days=30, verbosity=1)
                logger.info("✅ Timeslots populated successfully!")
            else:
                logger.info("📊 Timeslots table already contains data")
        except Exception as e:
            logger.error(f"❌ Failed to auto-populate timeslots: {str(e)}")
