from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import datetime, date, time, timedelta
from unittest.mock import patch
import json

from .models import Agent, AgentSettings, Appointment, CalendarEvent
from .views import AvailableTimeslotsAPIView


class AgentModelTests(TestCase):
    """Test Agent model functionality"""
    
    def setUp(self):
        self.agent = Agent.objects.create(
            id=1,
            full_name="Dr. Alice Smith",
            email="alice@example.com",
            active=True
        )
    
    def test_agent_str_representation(self):
        """Test Agent string representation"""
        self.assertEqual(str(self.agent), "Dr. Alice Smith")
    
    def test_active_agents_queryset(self):
        """Test filtering for active agents"""
        # Create inactive agent
        Agent.objects.create(
            id=2, full_name="Dr. Inactive", email="inactive@example.com", active=False
        )
        
        active_agents = Agent.objects.filter(active=True)
        self.assertEqual(active_agents.count(), 1)
        self.assertEqual(active_agents.first().full_name, "Dr. Alice Smith")


class AgentSettingsModelTests(TestCase):
    """Test AgentSettings model"""
    
    def setUp(self):
        self.agent = Agent.objects.create(
            id=1, full_name="Dr. Test", email="test@example.com", active=True
        )
        self.settings = AgentSettings.objects.create(
            agent_id=1, daily_caps=2, weekly_caps=5
        )
    
    def test_agent_settings_relationship(self):
        """Test relationship with Agent"""
        self.assertEqual(self.settings.agent_id, self.agent.id)
    
    def test_capacity_values(self):
        """Test capacity values are stored correctly"""
        self.assertEqual(self.settings.daily_caps, 2)
        self.assertEqual(self.settings.weekly_caps, 5)


class AvailableTimeslotsAPITests(APITestCase):
    """Test the main API endpoint"""
    
    def setUp(self):
        """Set up test data before each test"""
        # Create test agents
        self.agent1 = Agent.objects.create(
            id=1, full_name="Dr. Alice Smith", email="alice@example.com", active=True
        )
        self.agent2 = Agent.objects.create(
            id=2, full_name="Dr. Bob Jones", email="bob@example.com", active=True
        )
        self.inactive_agent = Agent.objects.create(
            id=3, full_name="Dr. Inactive", email="inactive@example.com", active=False
        )
        
        # Create agent settings with different capacities
        AgentSettings.objects.create(agent_id=1, daily_caps=1, weekly_caps=3)
        AgentSettings.objects.create(agent_id=2, daily_caps=2, weekly_caps=5)
        # No settings for inactive_agent (tests fallback)
        
        self.url = '/api/available-timeslots/'
    
    # ========================================================================
    # PARAMETER VALIDATION TESTS
    # ========================================================================
    
    def test_missing_start_date_returns_400(self):
        """Test API returns 400 when start_date parameter is missing"""
        response = self.client.get(self.url, {'end_date': '2024-11-03'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('start_date', response.data['error'])
    
    def test_missing_end_date_returns_400(self):
        """Test API returns 400 when end_date parameter is missing"""
        response = self.client.get(self.url, {'start_date': '2024-11-01'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('end_date', response.data['error'])
    
    def test_invalid_date_format_returns_400(self):
        """Test API returns 400 for invalid date format"""
        response = self.client.get(self.url, {
            'start_date': '2024-13-01',  # Invalid month
            'end_date': '2024-11-03'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid date format', response.data['error'])
    
    def test_end_before_start_returns_400(self):
        """Test API returns 400 when end_date is before start_date"""
        response = self.client.get(self.url, {
            'start_date': '2024-11-03',
            'end_date': '2024-11-01'  # Before start_date
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('start_date must be before', response.data['error'])
    
    # ========================================================================
    # SUCCESSFUL RESPONSE TESTS
    # ========================================================================
    
    def test_valid_request_returns_200(self):
        """Test API returns 200 for valid parameters"""
        response = self.client.get(self.url, {
            'start_date': '2024-11-01',
            'end_date': '2024-11-03'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_response_structure(self):
        """Test response contains all required fields"""
        response = self.client.get(self.url, {
            'start_date': '2024-11-01',
            'end_date': '2024-11-03'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check top-level response structure
        required_fields = ['start_date', 'end_date', 'agent_id', 'available_timeslots', 'total_slots', 'generated_at']
        for field in required_fields:
            self.assertIn(field, response.data)
        
        # Check timeslot structure if any slots exist
        if response.data['available_timeslots']:
            slot = response.data['available_timeslots'][0]
            slot_fields = ['agent_id', 'agent_name', 'agent_email', 'date', 'time', 'datetime', 'end_datetime', 'duration_minutes']
            for field in slot_fields:
                self.assertIn(field, slot)
    
    def test_timeslot_structure_details(self):
        """Test individual timeslot field values"""
        response = self.client.get(self.url, {
            'start_date': '2024-11-01',
            'end_date': '2024-11-01',
            'agent_id': '1'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        if response.data['available_timeslots']:
            slot = response.data['available_timeslots'][0]
            
            # Check data types and formats
            self.assertIsInstance(slot['agent_id'], int)
            self.assertEqual(slot['agent_name'], 'Dr. Alice Smith')
            self.assertEqual(slot['agent_email'], 'alice@example.com')
            self.assertEqual(slot['duration_minutes'], 60)
            
            # Check date format (ISO format)
            self.assertEqual(slot['date'], '2024-11-01')
            
            # Check time format (HH:MM)
            self.assertRegex(slot['time'], r'^\d{2}:\d{2}$')
    
    # ========================================================================
    # AGENT FILTERING TESTS
    # ========================================================================
    
    def test_specific_agent_filtering(self):
        """Test filtering results to specific agent"""
        response = self.client.get(self.url, {
            'start_date': '2024-11-01',
            'end_date': '2024-11-01',
            'agent_id': '1'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['agent_id'], '1')
        
        # All slots should be for agent 1
        for slot in response.data['available_timeslots']:
            self.assertEqual(slot['agent_id'], 1)
            self.assertEqual(slot['agent_name'], 'Dr. Alice Smith')
    
    def test_all_agents_when_no_agent_id(self):
        """Test returns slots for all active agents when no agent_id specified"""
        response = self.client.get(self.url, {
            'start_date': '2024-11-01',
            'end_date': '2024-11-01'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['agent_id'])
        
        # Should have slots from both active agents
        agent_ids_in_response = set(slot['agent_id'] for slot in response.data['available_timeslots'])
        self.assertIn(1, agent_ids_in_response)  # Agent 1
        self.assertIn(2, agent_ids_in_response)  # Agent 2
        self.assertNotIn(3, agent_ids_in_response)  # Inactive agent should not appear
    
    def test_inactive_agent_excluded(self):
        """Test inactive agents don't appear in results"""
        response = self.client.get(self.url, {
            'start_date': '2024-11-01',
            'end_date': '2024-11-01',
            'agent_id': str(self.inactive_agent.id)
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['available_timeslots']), 0)
    
    def test_nonexistent_agent_returns_empty(self):
        """Test querying nonexistent agent returns empty results"""
        response = self.client.get(self.url, {
            'start_date': '2024-11-01',
            'end_date': '2024-11-01',
            'agent_id': '999'  # Nonexistent agent
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['available_timeslots']), 0)


class SchedulingAlgorithmTests(TestCase):
    """Test core scheduling algorithm components"""
    
    def setUp(self):
        """Set up test data"""
        self.agent = Agent.objects.create(
            id=1, full_name="Dr. Test", email="test@example.com", active=True
        )
        AgentSettings.objects.create(agent_id=1, daily_caps=1, weekly_caps=3)
        self.view = AvailableTimeslotsAPIView()
    
    def test_daily_time_slots_count(self):
        """Test correct number of daily time slots generated"""
        slots = self.view.generate_daily_time_slots(self.agent, date(2024, 11, 1))
        
        # 9:00 AM to 5:00 PM, 30-minute increments, 60-minute appointments
        # Should be 15 slots: 9:00, 9:30, 10:00, ..., 4:00 (last slot that fits)
        self.assertEqual(len(slots), 15)
    
    def test_slot_timing_accuracy(self):
        """Test slot times are correctly calculated"""
        slots = self.view.generate_daily_time_slots(self.agent, date(2024, 11, 1))
        
        # First slot should start at 9:00 AM
        self.assertEqual(slots[0]['time'], '09:00')
        self.assertEqual(slots[0]['datetime'], '2024-11-01T09:00:00')
        self.assertEqual(slots[0]['end_datetime'], '2024-11-01T10:00:00')
        
        # Second slot should start at 9:30 AM
        self.assertEqual(slots[1]['time'], '09:30')
        self.assertEqual(slots[1]['datetime'], '2024-11-01T09:30:00')
        
        # Last slot should start at 4:00 PM (to fit 60-min appointment before 5:00 PM)
        self.assertEqual(slots[-1]['time'], '16:00')
        self.assertEqual(slots[-1]['end_datetime'], '2024-11-01T17:00:00')
    
    def test_working_hours_boundaries(self):
        """Test slots respect 9AM-5PM boundaries"""
        slots = self.view.generate_daily_time_slots(self.agent, date(2024, 11, 1))
        
        # All slots should start at or after 9:00 AM
        for slot in slots:
            slot_time = datetime.fromisoformat(slot['datetime']).time()
            self.assertGreaterEqual(slot_time, time(9, 0))
        
        # All slots should end at or before 5:00 PM
        for slot in slots:
            end_time = datetime.fromisoformat(slot['end_datetime']).time()
            self.assertLessEqual(end_time, time(17, 0))
    
    def test_60_minute_appointment_duration(self):
        """Test each appointment is exactly 60 minutes"""
        slots = self.view.generate_daily_time_slots(self.agent, date(2024, 11, 1))
        
        for slot in slots:
            self.assertEqual(slot['duration_minutes'], 60)
            
            # Verify actual duration matches
            start_time = datetime.fromisoformat(slot['datetime'])
            end_time = datetime.fromisoformat(slot['end_datetime'])
            duration = end_time - start_time
            self.assertEqual(duration, timedelta(minutes=60))
    
    def test_monday_of_week_calculation(self):
        """Test get_monday_of_week utility function"""
        # Test various days of week
        friday_nov_1 = date(2024, 11, 1)  # Friday
        monday = self.view.get_monday_of_week(friday_nov_1)
        self.assertEqual(monday, date(2024, 10, 28))  # Previous Monday
        
        # Test Monday itself
        monday_nov_4 = date(2024, 11, 4)  # Monday
        monday = self.view.get_monday_of_week(monday_nov_4)
        self.assertEqual(monday, date(2024, 11, 4))  # Same day
        
        # Test Sunday (end of week)
        sunday_nov_3 = date(2024, 11, 3)  # Sunday
        monday = self.view.get_monday_of_week(sunday_nov_3)
        self.assertEqual(monday, date(2024, 10, 28))  # Previous Monday
    
    def test_times_overlap_function(self):
        """Test times_overlap utility function accuracy"""
        # Test overlapping times
        start1 = datetime(2024, 11, 1, 9, 0)
        end1 = datetime(2024, 11, 1, 10, 0)
        start2 = datetime(2024, 11, 1, 9, 30)
        end2 = datetime(2024, 11, 1, 10, 30)
        
        self.assertTrue(self.view.times_overlap(start1, end1, start2, end2))
        
        # Test non-overlapping times
        start3 = datetime(2024, 11, 1, 10, 0)
        end3 = datetime(2024, 11, 1, 11, 0)
        
        self.assertFalse(self.view.times_overlap(start1, end1, start3, end3))
        
        # Test adjacent times (should not overlap)
        self.assertFalse(self.view.times_overlap(
            datetime(2024, 11, 1, 9, 0), datetime(2024, 11, 1, 10, 0),
            datetime(2024, 11, 1, 10, 0), datetime(2024, 11, 1, 11, 0)
        ))


class CapacityLimitsTests(APITestCase):
    """Test dynamic capacity constraint enforcement"""
    
    def setUp(self):
        """Set up test data"""
        # Create agents with different capacity limits
        self.agent1 = Agent.objects.create(
            id=1, full_name="Dr. Low Capacity", email="low@example.com", active=True
        )
        self.agent2 = Agent.objects.create(
            id=2, full_name="Dr. High Capacity", email="high@example.com", active=True
        )
        
        # Different capacity settings
        AgentSettings.objects.create(agent_id=1, daily_caps=1, weekly_caps=2)  # Low capacity
        AgentSettings.objects.create(agent_id=2, daily_caps=3, weekly_caps=6)  # High capacity
        
        self.url = '/api/available-timeslots/'
    
    def test_daily_capacity_respected(self):
        """Test daily capacity limits are enforced"""
        # Create appointment for low-capacity agent (daily_caps=1)
        Appointment.objects.create(
            agent_id=1,
            client_name="Test Client",
            appointment_time=datetime(2024, 11, 1, 10, 0),
            status="scheduled"
        )
        
        response = self.client.get(self.url, {
            'start_date': '2024-11-01',
            'end_date': '2024-11-01',
            'agent_id': '1'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Agent 1 should have no available slots on Nov 1 (reached daily cap)
        self.assertEqual(len(response.data['available_timeslots']), 0)
    
    def test_different_agent_capacities(self):
        """Test agents with different capacity limits"""
        # Give each agent 1 appointment on same day
        Appointment.objects.create(
            agent_id=1, client_name="Client 1",
            appointment_time=datetime(2024, 11, 1, 10, 0), status="scheduled"
        )
        Appointment.objects.create(
            agent_id=2, client_name="Client 2",
            appointment_time=datetime(2024, 11, 1, 11, 0), status="scheduled"
        )
        
        # Agent 1 should have 0 slots (reached daily limit of 1)
        response1 = self.client.get(self.url, {
            'start_date': '2024-11-01', 'end_date': '2024-11-01', 'agent_id': '1'
        })
        self.assertEqual(len(response1.data['available_timeslots']), 0)
        
        # Agent 2 should still have slots (daily limit of 3, only used 1)
        response2 = self.client.get(self.url, {
            'start_date': '2024-11-01', 'end_date': '2024-11-01', 'agent_id': '2'
        })
        self.assertGreater(len(response2.data['available_timeslots']), 0)
    
    def test_weekly_capacity_enforcement(self):
        """Test weekly capacity limits are enforced"""
        # Create 2 appointments for agent 1 (weekly_caps=2) in same week
        monday = date(2024, 11, 4)  # Monday of a week
        tuesday = date(2024, 11, 5)  # Tuesday same week
        
        Appointment.objects.create(
            agent_id=1, client_name="Client Mon",
            appointment_time=datetime.combine(monday, time(10, 0)), status="scheduled"
        )
        Appointment.objects.create(
            agent_id=1, client_name="Client Tue",
            appointment_time=datetime.combine(tuesday, time(10, 0)), status="scheduled"
        )
        
        # Request slots for Wednesday same week - should be none (weekly cap reached)
        response = self.client.get(self.url, {
            'start_date': '2024-11-06',  # Wednesday
            'end_date': '2024-11-06',
            'agent_id': '1'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['available_timeslots']), 0)
    
    def test_fallback_default_settings(self):
        """Test default settings when AgentSettings missing"""
        # Create agent without AgentSettings
        agent_no_settings = Agent.objects.create(
            id=3, full_name="Dr. No Settings", email="nosettings@example.com", active=True
        )
        
        response = self.client.get(self.url, {
            'start_date': '2024-11-01',
            'end_date': '2024-11-01',
            'agent_id': str(agent_no_settings.id)
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should still generate slots using fallback defaults
        self.assertGreater(len(response.data['available_timeslots']), 0)


class ConflictDetectionTests(APITestCase):
    """Test appointment and calendar event conflict detection"""
    
    def setUp(self):
        """Set up test data"""
        self.agent = Agent.objects.create(
            id=1, full_name="Dr. Test", email="test@example.com", active=True
        )
        AgentSettings.objects.create(agent_id=1, daily_caps=5, weekly_caps=20)  # High caps to focus on conflicts
        
        self.url = '/api/available-timeslots/'
    
    def test_appointment_conflict_with_buffer(self):
        """Test 30-minute buffer prevents appointment conflicts"""
        # Create appointment at 10:00 AM (10:00-11:00)
        Appointment.objects.create(
            agent_id=1,
            client_name="Test Client",
            appointment_time=datetime(2024, 11, 1, 10, 0),
            status="scheduled"
        )
        
        response = self.client.get(self.url, {
            'start_date': '2024-11-01',
            'end_date': '2024-11-01',
            'agent_id': '1'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that slots conflicting with 30-min buffer are excluded
        slot_times = [slot['time'] for slot in response.data['available_timeslots']]
        
        # These slots should be excluded due to buffer:
        # 9:30 (9:30-10:30 conflicts with 10:00-11:00 + buffer)
        # 10:00 (10:00-11:00 conflicts directly)  
        # 10:30 (10:30-11:30 conflicts with 10:00-11:00 + buffer)
        self.assertNotIn('09:30', slot_times)
        self.assertNotIn('10:00', slot_times)
        self.assertNotIn('10:30', slot_times)
        
        # These should be available (outside buffer range)
        self.assertIn('09:00', slot_times)  # 9:00-10:00, ends before buffer
        self.assertIn('11:00', slot_times)  # 11:00-12:00, starts after buffer
    
    def test_calendar_event_direct_overlap_only(self):
        """Test calendar events block slots with direct overlap only (no buffer)"""
        # Create calendar event 10:00-11:00 AM
        CalendarEvent.objects.create(
            agent_id=1,
            event_name="Team Meeting",
            start_time=datetime(2024, 11, 1, 10, 0),
            end_time=datetime(2024, 11, 1, 11, 0)
        )
        
        response = self.client.get(self.url, {
            'start_date': '2024-11-01',
            'end_date': '2024-11-01',
            'agent_id': '1'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        slot_times = [slot['time'] for slot in response.data['available_timeslots']]
        
        # These slots should be excluded (direct overlap with calendar event):
        # 10:00 (10:00-11:00 overlaps with 10:00-11:00)
        # 10:30 (10:30-11:30 overlaps with 10:00-11:00)
        self.assertNotIn('10:00', slot_times)
        self.assertNotIn('10:30', slot_times)
        
        # These should be available (no buffer for calendar events):
        self.assertIn('09:30', slot_times)  # 9:30-10:30 only partially overlaps
        self.assertIn('11:00', slot_times)  # 11:00-12:00 starts when event ends
    
    def test_multiple_conflicts(self):
        """Test handling multiple conflicting appointments and events"""
        # Create appointment at 10:00
        Appointment.objects.create(
            agent_id=1, client_name="Client 1",
            appointment_time=datetime(2024, 11, 1, 10, 0), status="scheduled"
        )
        
        # Create calendar event at 2:00 PM
        CalendarEvent.objects.create(
            agent_id=1, event_name="Meeting",
            start_time=datetime(2024, 11, 1, 14, 0),
            end_time=datetime(2024, 11, 1, 15, 0)
        )
        
        response = self.client.get(self.url, {
            'start_date': '2024-11-01',
            'end_date': '2024-11-01',
            'agent_id': '1'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        slot_times = [slot['time'] for slot in response.data['available_timeslots']]
        
        # Should exclude slots around 10:00 AM appointment (with buffer)
        self.assertNotIn('09:30', slot_times)
        self.assertNotIn('10:00', slot_times)
        self.assertNotIn('10:30', slot_times)
        
        # Should exclude slots overlapping 2:00 PM event (no buffer)
        self.assertNotIn('14:00', slot_times)
        self.assertNotIn('14:30', slot_times)
        
        # Should have available slots in other time periods
        self.assertIn('09:00', slot_times)
        self.assertIn('11:00', slot_times)
        self.assertIn('13:30', slot_times)  # Just before calendar event
        self.assertIn('15:00', slot_times)  # Just after calendar event
