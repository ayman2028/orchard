"""
Django signals to automatically update timeslots when relevant data changes

This ensures the available_timeslots table stays current without manual intervention.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.management import call_command
from .models import Appointment, CalendarEvent, AgentSettings
import logging

logger = logging.getLogger(__name__)


@receiver([post_save, post_delete], sender=Appointment)
def update_timeslots_on_appointment_change(sender, instance, **kwargs):
    """
    Update available timeslots when appointments are created/modified/deleted
    """
    try:
        # Get the affected date
        affected_date = instance.appointment_time.date()
        
        # Regenerate timeslots for this agent for the affected week
        call_command('populate_timeslots', 
                    agent_id=instance.agent_id,
                    days=7,  # Regenerate the week containing this appointment
                    verbosity=0)
        
        logger.info(f"Updated timeslots for Agent {instance.agent_id} due to appointment change on {affected_date}")
        
    except Exception as e:
        logger.error(f"Failed to update timeslots after appointment change: {str(e)}")


@receiver([post_save, post_delete], sender=CalendarEvent)
def update_timeslots_on_calendar_change(sender, instance, **kwargs):
    """
    Update available timeslots when calendar events are created/modified/deleted
    """
    try:
        # Get the affected date range
        start_date = instance.start_time.date()
        end_date = instance.end_time.date()
        
        # Calculate how many days to regenerate
        days_affected = (end_date - start_date).days + 7  # Include buffer
        
        call_command('populate_timeslots',
                    agent_id=instance.agent_id,
                    days=days_affected,
                    verbosity=0)
        
        logger.info(f"Updated timeslots for Agent {instance.agent_id} due to calendar event change")
        
    except Exception as e:
        logger.error(f"Failed to update timeslots after calendar event change: {str(e)}")


@receiver(post_save, sender=AgentSettings)
def update_timeslots_on_settings_change(sender, instance, **kwargs):
    """
    Update available timeslots when agent capacity settings change
    """
    try:
        # Settings changes affect future availability, regenerate next 30 days
        call_command('populate_timeslots',
                    agent_id=instance.agent_id,
                    days=30,
                    verbosity=0)
        
        logger.info(f"Updated timeslots for Agent {instance.agent_id} due to settings change")
        
    except Exception as e:
        logger.error(f"Failed to update timeslots after settings change: {str(e)}")