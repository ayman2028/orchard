from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    """
    Extends Django's User model to distinguish between agents and clients
    """
    USER_TYPE_CHOICES = [
        ('agent', 'Agent'),
        ('client', 'Client'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} ({self.user_type})"
    
    class Meta:
        db_table = 'user_profiles'


class Client(models.Model):
    """
    Client-specific data linked to User account
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile')
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"
    
    class Meta:
        db_table = 'clients'


class Agent(models.Model):
    """
    Agent model mapping to existing 'agents' table
    Now also links to Django User for authentication
    """
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='agent_profile')
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    active = models.BooleanField()
    
    class Meta:
        managed = True  # Temporarily set to True to create migration for user field
        db_table = 'agents'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class AgentSettings(models.Model):
    """
    Agent settings model mapping to existing 'agent_settings' table
    Contains scheduling constraints like daily/weekly caps
    """
    agent_id = models.IntegerField(primary_key=True)
    daily_caps = models.IntegerField()
    weekly_caps = models.IntegerField()
    
    class Meta:
        managed = False
        db_table = 'agent_settings'
    
    def __str__(self):
        return f"Agent {self.agent_id}: {self.daily_caps}/day, {self.weekly_caps}/week"

class Appointment(models.Model):
    """
    Appointment model mapping to existing 'appointments' table
    """
    id = models.AutoField(primary_key=True)
    agent_id = models.IntegerField()
    client_name = models.CharField(max_length=255)
    appointment_time = models.DateTimeField()
    status = models.CharField(max_length=255)
    
    class Meta:
        managed = False
        db_table = 'appointments'
    
    def __str__(self):
        return f"{self.client_name} with Agent {self.agent_id} at {self.appointment_time}"

class CalendarEvent(models.Model):
    """
    Calendar event model mapping to existing 'calendar_events' table
    Represents blocked time periods for agents
    """
    id = models.AutoField(primary_key=True)
    agent_id = models.IntegerField()
    event_name = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    
    class Meta:
        managed = False
        db_table = 'calendar_events'
    
    def __str__(self):
        return f"{self.event_name} for Agent {self.agent_id}: {self.start_time} - {self.end_time}"


class AvailableTimeslot(models.Model):
    """
    Pre-computed available timeslots for faster API responses
    
    This table is populated by a management command and queried by the API
    for high-performance timeslot retrieval (vs computing on every request).
    """
    agent_id = models.IntegerField(db_index=True)
    agent_name = models.CharField(max_length=200)
    agent_email = models.EmailField()
    
    # Date and time fields for efficient querying
    date = models.DateField(db_index=True)  # For date range filtering
    time = models.TimeField()  # Time portion (e.g., 14:30)
    datetime = models.DateTimeField(db_index=True)  # Full datetime
    end_datetime = models.DateTimeField()
    duration_minutes = models.IntegerField(default=60)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'available_timeslots'
        indexes = [
            models.Index(fields=['agent_id', 'date']),
            models.Index(fields=['datetime']),
        ]
        # Ensure no duplicate slots
        unique_together = ['agent_id', 'datetime']
    
    def __str__(self):
        return f"Agent {self.agent_id} - {self.datetime.strftime('%Y-%m-%d %H:%M')}"
