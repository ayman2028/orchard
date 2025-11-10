"""
Django management command to populate the available_timeslots table

Usage:
    python manage.py populate_timeslots
    python manage.py populate_timeslots --days 60
    python manage.py populate_timeslots --agent-id 1
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from scheduling.models import Agent, AgentSettings, Appointment, CalendarEvent, AvailableTimeslot
from datetime import datetime, date, time, timedelta
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Populate the available_timeslots table for fast API responses'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days ahead to generate slots (default: 30)'
        )
        parser.add_argument(
            '--agent-id',
            type=int,
            help='Populate slots for a specific agent only'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing timeslots before generating new ones'
        )

    def handle(self, *args, **options):
        start_time = timezone.now()
        
        if options['clear']:
            self.stdout.write("Clearing existing timeslots...")
            AvailableTimeslot.objects.all().delete()
        
        if options['agent_id']:
            # Populate for specific agent
            try:
                agent = Agent.objects.get(id=options['agent_id'], active=True)
                self.stdout.write(f"Generating slots for Agent {agent.id} ({agent.first_name} {agent.last_name})")
                
                stats = self._generate_slots_for_agent(agent, options['days'])
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Generated {stats['slots_created']} slots for Agent {agent.id}"
                    )
                )
                
            except Agent.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"❌ Agent with ID {options['agent_id']} not found or inactive")
                )
        else:
            # Populate for all agents
            active_agents = Agent.objects.filter(active=True)
            self.stdout.write(f"Generating slots for {active_agents.count()} active agents ({options['days']} days ahead)")
            
            total_slots = 0
            for agent in active_agents:
                try:
                    stats = self._generate_slots_for_agent(agent, options['days'])
                    total_slots += stats['slots_created']
                    self.stdout.write(f"  ✅ Agent {agent.id}: {stats['slots_created']} slots")
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"  ❌ Agent {agent.id}: {str(e)}")
                    )
            
            execution_time = (timezone.now() - start_time).total_seconds()
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n🎉 Generated {total_slots} total slots in {execution_time:.2f} seconds"
                )
            )
    
    def _generate_slots_for_agent(self, agent, days_ahead):
        """Generate available timeslots for a specific agent"""
        start_date = date.today()
        end_date = start_date + timedelta(days=days_ahead)
        
        # Get agent settings
        try:
            agent_settings = AgentSettings.objects.get(agent_id=agent.id)
        except AgentSettings.DoesNotExist:
            # Default settings if none exist
            agent_settings = type('obj', (object,), {'daily_caps': 1, 'weekly_caps': 3})()
        
        # Get existing appointments for capacity calculation
        appointments = Appointment.objects.filter(
            agent_id=agent.id,
            appointment_time__date__range=[start_date, end_date],
            status__in=['scheduled', 'confirmed']
        ).values_list('appointment_time__date', flat=True)
        
        # Get calendar events for conflict detection
        calendar_events = CalendarEvent.objects.filter(
            agent_id=agent.id,
            start_time__date__range=[start_date, end_date]
        )
        
        # Clear existing slots for this agent in the date range
        AvailableTimeslot.objects.filter(
            agent_id=agent.id,
            date__range=[start_date, end_date]
        ).delete()
        
        slots_to_create = []
        current_date = start_date
        
        while current_date <= end_date:
            # Check capacity constraints
            if self._date_passes_capacity_constraints(agent.id, current_date, appointments, agent_settings):
                # Generate daily slots
                daily_slots = self._generate_daily_slots(agent, current_date)
                
                # Filter by conflicts
                available_slots = self._filter_by_conflicts(daily_slots, calendar_events, appointments)
                
                # Convert to model instances
                for slot_data in available_slots:
                    slot = AvailableTimeslot(
                        agent_id=slot_data['agent_id'],
                        agent_name=slot_data['agent_name'],
                        agent_email=slot_data['agent_email'],
                        date=datetime.fromisoformat(slot_data['date']).date(),
                        time=datetime.fromisoformat(slot_data['datetime']).time(),
                        datetime=datetime.fromisoformat(slot_data['datetime']),
                        end_datetime=datetime.fromisoformat(slot_data['end_datetime']),
                        duration_minutes=slot_data['duration_minutes']
                    )
                    slots_to_create.append(slot)
            
            current_date += timedelta(days=1)
        
        # Bulk create for performance
        with transaction.atomic():
            AvailableTimeslot.objects.bulk_create(slots_to_create, batch_size=100)
        
        return {
            'agent_id': agent.id,
            'slots_created': len(slots_to_create)
        }
    
    def _date_passes_capacity_constraints(self, agent_id, check_date, appointment_dates, agent_settings):
        """Check if a date passes daily and weekly capacity constraints"""
        # Count appointments on this specific date
        daily_count = sum(1 for appt_date in appointment_dates if appt_date == check_date)
        if daily_count >= agent_settings.daily_caps:
            return False
        
        # Count appointments in the week containing this date
        week_start = self._get_monday_of_week(check_date)
        week_end = week_start + timedelta(days=6)
        weekly_count = sum(1 for appt_date in appointment_dates 
                          if week_start <= appt_date <= week_end)
        if weekly_count >= agent_settings.weekly_caps:
            return False
        
        return True
    
    def _generate_daily_slots(self, agent, date_obj):
        """Generate all possible timeslots for an agent on a specific date"""
        slots = []
        start_time = time(9, 0)   # 9:00 AM
        end_time = time(17, 0)    # 5:00 PM
        
        current_slot_time = datetime.combine(date_obj, start_time)
        end_datetime = datetime.combine(date_obj, end_time)
        
        while current_slot_time < end_datetime:
            appointment_end = current_slot_time + timedelta(minutes=60)
            
            if appointment_end <= end_datetime:
                slots.append({
                    'agent_id': agent.id,
                    'agent_name': f"{agent.first_name} {agent.last_name}",
                    'agent_email': agent.email,
                    'date': date_obj.isoformat(),
                    'time': current_slot_time.strftime('%H:%M'),
                    'datetime': current_slot_time.isoformat(),
                    'end_datetime': appointment_end.isoformat(),
                    'duration_minutes': 60
                })
            
            current_slot_time += timedelta(minutes=30)
        
        return slots
    
    def _filter_by_conflicts(self, slots, calendar_events, appointment_dates):
        """Filter slots that conflict with existing appointments or calendar events"""
        available_slots = []
        
        for slot in slots:
            slot_start = datetime.fromisoformat(slot['datetime'])
            slot_end = datetime.fromisoformat(slot['end_datetime'])
            
            # Check appointment conflicts
            slot_date = slot_start.date()
            if slot_date in appointment_dates:
                continue
            
            # Check calendar event conflicts
            has_calendar_conflict = False
            for event in calendar_events:
                if self._times_overlap(slot_start, slot_end, event.start_time, event.end_time):
                    has_calendar_conflict = True
                    break
            
            if not has_calendar_conflict:
                available_slots.append(slot)
        
        return available_slots
    
    def _times_overlap(self, start1, end1, start2, end2):
        """Check if two time periods overlap"""
        return start1 < end2 and start2 < end1
    
    def _get_monday_of_week(self, date_obj):
        """Get the Monday of the week containing the given date"""
        days_since_monday = date_obj.weekday()
        monday = date_obj - timedelta(days=days_since_monday)
        return monday