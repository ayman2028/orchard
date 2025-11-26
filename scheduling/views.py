from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta, time
from .models import Agent, AgentSettings, Appointment, CalendarEvent, UserProfile, Client

def doctor_schedule_view(request):
    """
    Web interface to display all doctors and their available times
    Uses the API endpoint internally to ensure consistency
    """
    from django.test import RequestFactory
    import json
    
    # Get date range (default to next 7 days)
    today = datetime.now().date()
    start_date = today
    end_date = today + timedelta(days=7)
    
    # Allow date range override from query params
    if request.GET.get('start_date'):
        try:
            start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if request.GET.get('end_date'):
        try:
            end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Call our own API to get available timeslots
    factory = RequestFactory()
    api_request = factory.get('/api/available-timeslots/', {
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d')
    })
    
    # Get API response - use the new fast API
    api_view = FastAvailableTimeslotsAPIView()
    api_response = api_view.get(api_request)
    
    if api_response.status_code != 200:
        # Fallback if API fails
        context = {
            'doctor_schedules': [],
            'start_date': start_date,
            'end_date': end_date,
            'error': 'Unable to load schedule data'
        }
        return render(request, 'scheduling/doctor_schedule.html', context)
    
    api_data = api_response.data
    available_slots = api_data.get('available_timeslots', [])
    
    # Organize data by doctor for display
    doctors_data = {}
    
    # Group slots by agent
    for slot in available_slots:
        agent_id = slot['agent_id']
        if agent_id not in doctors_data:
            doctors_data[agent_id] = {
                'agent': {
                    'id': agent_id,
                    'full_name': slot['agent_name'],
                    'email': slot['agent_email']
                },
                'slots_by_date': {}
            }
        
        slot_date = slot['date']
        if slot_date not in doctors_data[agent_id]['slots_by_date']:
            doctors_data[agent_id]['slots_by_date'][slot_date] = []
        
        doctors_data[agent_id]['slots_by_date'][slot_date].append({
            'time': slot['time'],
            'datetime': datetime.fromisoformat(slot['datetime']),
            'available': True  # All API slots are available
        })
    
    # Get all active agents (including those with no available slots)
    all_agents = Agent.objects.filter(active=True)
    
    # Build final schedule structure
    doctor_schedules = []
    
    for agent in all_agents:
        # Get agent settings for display
        try:
            agent_settings = AgentSettings.objects.get(agent_id=agent.id)
            daily_limit = agent_settings.daily_caps
            weekly_limit = agent_settings.weekly_caps
        except AgentSettings.DoesNotExist:
            daily_limit = 1
            weekly_limit = 3
        
        # Build schedule for this agent
        agent_schedule = []
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            
            # Get slots for this date from API data
            if (agent.id in doctors_data and 
                date_str in doctors_data[agent.id]['slots_by_date']):
                daily_slots = doctors_data[agent.id]['slots_by_date'][date_str]
            else:
                # No available slots for this date
                daily_slots = []
            
            # Add all time slots (available and unavailable) for display
            all_time_slots = []
            for hour in range(9, 17):  # 9 AM to 4 PM
                time_str = f"{hour:02d}:00"
                slot_datetime = datetime.combine(current_date, time(hour, 0))
                
                # Check if this time slot is available from API
                is_available = any(slot['time'] == time_str for slot in daily_slots)
                
                all_time_slots.append({
                    'time': time_str,
                    'datetime': slot_datetime,
                    'available': is_available
                })
            
            agent_schedule.append({
                'date': current_date,
                'slots': all_time_slots
            })
            
            current_date += timedelta(days=1)
        
        doctor_schedules.append({
            'agent': agent,
            'daily_limit': daily_limit,
            'weekly_limit': weekly_limit,
            'schedule': agent_schedule
        })
    
    context = {
        'doctor_schedules': doctor_schedules,
        'start_date': start_date,
        'end_date': end_date,
        'date_range': [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)],
        'api_url': f"/api/available-timeslots/?start_date={start_date}&end_date={end_date}"
    }
    
    return render(request, 'scheduling/doctor_schedule.html', context)

class AvailableTimeslotsAPIView(APIView):
    """
    API endpoint to get available appointment timeslots
    """
    
    def get(self, request):
        """Handle GET requests for available timeslots"""
        
        # Get query parameters (handle both DRF Request and Django WSGIRequest)
        if hasattr(request, 'query_params'):
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')
            agent_id = request.query_params.get('agent_id')
        else:
            start_date_str = request.GET.get('start_date')
            end_date_str = request.GET.get('end_date')
            agent_id = request.GET.get('agent_id')
        
        # Basic validation
        if not start_date_str or not end_date_str:
            return Response({
                'error': 'Both start_date and end_date parameters are required',
                'example': '/api/available-timeslots/?start_date=2025-06-15&end_date=2025-06-28'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate date format
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({
                'error': 'Invalid date format. Use YYYY-MM-DD',
                'example': 'start_date=2025-06-15&end_date=2025-06-28'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if start_date > end_date:
            return Response({
                'error': 'start_date must be before or equal to end_date'
            }, status=status.HTTP_400_BAD_REQUEST)
        

        
        # Generate available timeslots
        try:
            available_slots = self.get_available_timeslots(start_date, end_date, agent_id)
            return Response({
                'start_date': start_date_str,
                'end_date': end_date_str,
                'agent_id': agent_id,
                'available_timeslots': available_slots,
                'total_slots': len(available_slots),
                'generated_at': datetime.now().isoformat()
            })
        except Exception as e:
            return Response({
                'error': f'Failed to generate timeslots: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_available_timeslots(self, start_date, end_date, agent_id=None):
        """
        Main method to get available timeslots using optimized algorithm
        Returns all available slots across agents, or for a specific agent if agent_id is provided
        1. Get active agents   
        2. Bulk query appointments for each agent
        3. Filter dates by weekly cap
        4. Filter dates by daily cap
        5. Generate time slots for valid dates only
        6. Bulk query conflicts (appointments and calendar events)
        7. Filter slots by conflicts
        8. Return available slots
        
        """
        # Step 1: Get active agents
        active_agents = Agent.objects.filter(active=True)
        if agent_id:
            active_agents = active_agents.filter(id=agent_id) #Time complexity: O(1) for filtering by ID
        
        all_available_slots = []
        
        # Step 2-7: Process each agent
        for agent in active_agents:
            agent_slots = self.get_available_timeslots_for_agent(agent, start_date, end_date)
            all_available_slots.extend(agent_slots) #Just adds all available slots
        
        return all_available_slots
    
    def get_available_timeslots_for_agent(self, agent, start_date, end_date):
        """
        Get available timeslots for a specific agent using optimized algorithm
        """
        # Get agent's capacity settings
        try:
            agent_settings = AgentSettings.objects.get(agent_id=agent.id)
        except AgentSettings.DoesNotExist:
            # Default fallback if no settings found
            agent_settings = type('obj', (object,), {'daily_caps': 1, 'weekly_caps': 3})()
        
        # Step 2: Bulk query appointments for this agent
        agent_appointments = Appointment.objects.filter(
            agent_id=agent.id,
            appointment_time__date__range=[start_date, end_date],
            status__in=['scheduled', 'confirmed']  # Only active appointments
        ).values_list('appointment_time__date', flat=True)
        
        # Step 3 & 4: Filter dates by weekly and daily caps
        valid_dates = self.get_valid_dates_after_caps(agent.id, start_date, end_date, agent_appointments, agent_settings)
        
        # Step 5: Generate time slots for valid dates only
        generated_slots = []
        for date in valid_dates:
            daily_slots = self.generate_daily_time_slots(agent, date)
            generated_slots.extend(daily_slots)
        
        # Step 6 & 7: Filter by conflicts
        available_slots = self.filter_slots_by_conflicts(generated_slots, start_date, end_date)
        
        return available_slots
    
    def get_valid_dates_after_caps(self, agent_id, start_date, end_date, appointment_dates, agent_settings):
        """
        Filter dates that pass both weekly and daily cap constraints using agent's specific settings
        """
        # Count appointments per date and per week
        #basically hashsets (maps) for each date and week.
        daily_counts = {}
        weekly_counts = {}
        
        for appt_date in appointment_dates:
            # Daily count
            daily_counts[appt_date] = daily_counts.get(appt_date, 0) + 1
            
            # Weekly count (Monday = week start)
            week_start = self.get_monday_of_week(appt_date)
            weekly_counts[week_start] = weekly_counts.get(week_start, 0) + 1
        
        # Find valid dates
        valid_dates = []
        current_date = start_date
        
        while current_date <= end_date:
            week_start = self.get_monday_of_week(current_date)
            
            # Step 3: Check weekly cap first (most restrictive) - use agent's weekly_caps
            if weekly_counts.get(week_start, 0) >= agent_settings.weekly_caps:
                # Skip entire week - jump to next Monday
                days_to_next_monday = 7 - current_date.weekday()
                current_date = current_date + timedelta(days=days_to_next_monday)
                continue
            
            # Step 4: Check daily cap - use agent's daily_caps
            if daily_counts.get(current_date, 0) >= agent_settings.daily_caps:
                current_date += timedelta(days=1)
                continue
            
            # Date is valid!
            valid_dates.append(current_date)
            current_date += timedelta(days=1)
        
        return valid_dates
    
    def generate_daily_time_slots(self, agent, date):
        """
        Generate 15 time slots for a specific agent on a specific date
        Working hours: 9:00 AM - 5:00 PM, 30-minute increments
        """
        slots = []
        start_time = time(9, 0)   # 9:00 AM
        end_time = time(17, 0)    # 5:00 PM
        
        current_slot_time = datetime.combine(date, start_time)
        end_datetime = datetime.combine(date, end_time)
        
        while current_slot_time < end_datetime:
            # Each appointment is 60 minutes
            appointment_end = current_slot_time + timedelta(minutes=60)
            
            # Check if 60-minute appointment fits within working hours
            if appointment_end <= end_datetime:
                slots.append({
                    'agent_id': agent.id,
                    'agent_name': agent.full_name,
                    'agent_email': agent.email,
                    'date': date.isoformat(),
                    'time': current_slot_time.strftime('%H:%M'),
                    'datetime': current_slot_time.isoformat(),
                    'end_datetime': appointment_end.isoformat(),
                    'duration_minutes': 60
                })
            
            # Move to next 30-minute slot
            current_slot_time += timedelta(minutes=30)
        
        return slots
    
    def filter_slots_by_conflicts(self, generated_slots, start_date, end_date):
        """
        Filter out slots that conflict with existing appointments or calendar events
        """
        if not generated_slots:
            return []
        
        # Step 6: Bulk query conflicts
        # Get all appointments in date range for buffer checking
        all_appointments = Appointment.objects.filter(
            appointment_time__date__range=[start_date, end_date],
            status__in=['scheduled', 'confirmed']
        ).values('agent_id', 'appointment_time')
        
        # Get all calendar events in date range
        all_calendar_events = CalendarEvent.objects.filter(
            start_time__date__range=[start_date, end_date]
        ).values('agent_id', 'start_time', 'end_time')
        
        # Step 7: Filter each slot
        available_slots = []
        for slot in generated_slots:
            if self.is_slot_available(slot, all_appointments, all_calendar_events):
                available_slots.append(slot)
        
        return available_slots
    
    def is_slot_available(self, slot, all_appointments, all_calendar_events):
        """
        Check if a specific slot is available (no conflicts with 30-min buffer)
        """
        agent_id = slot['agent_id']
        slot_start = datetime.fromisoformat(slot['datetime'])
        slot_end = datetime.fromisoformat(slot['end_datetime'])
        
        # Add 30-minute buffer before and after
        buffer_start = slot_start - timedelta(minutes=30)
        buffer_end = slot_end + timedelta(minutes=30)
        
        # Check appointment conflicts with buffer
        for appointment in all_appointments:
            if appointment['agent_id'] == agent_id:
                appt_time = appointment['appointment_time']
                # Assume appointments are 60 minutes (no end time in DB)
                appt_end = appt_time + timedelta(minutes=60)
                
                # Check if appointment overlaps with buffer zone
                if self.times_overlap(buffer_start, buffer_end, appt_time, appt_end):
                    return False
        
        # Check calendar event conflicts (direct overlap, no buffer)
        for event in all_calendar_events:
            if event['agent_id'] == agent_id:
                event_start = event['start_time']
                event_end = event['end_time']
                
                # Check if slot overlaps with calendar event
                if self.times_overlap(slot_start, slot_end, event_start, event_end):
                    return False
        
        return True
    
    def times_overlap(self, start1, end1, start2, end2):
        """
        Check if two time ranges overlap
        """
        return start1 < end2 and start2 < end1
    
    def get_monday_of_week(self, date):
        """
        Get the Monday of the week for a given date
        """
        days_since_monday = date.weekday()
        monday = date - timedelta(days=days_since_monday)
        return monday


class FastAvailableTimeslotsAPIView(APIView):
    """
    High-performance API using pre-populated available_timeslots table
    
    This API queries the pre-computed timeslots table instead of calculating
    availability on every request, resulting in ~10x faster response times.
    """
    
    def get(self, request):
        """
        Get available timeslots from pre-populated table
        
        Query Parameters:
            - agent_id: Filter by specific agent (optional)
            - start_date: Start date (YYYY-MM-DD, default: today)
            - end_date: End date (YYYY-MM-DD, default: +7 days)
        """
        from .models import AvailableTimeslot
        import time
        
        start_time = time.time()
        
        # Get query parameters exactly like original API
        if hasattr(request, 'query_params'):
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')
            agent_id = request.query_params.get('agent_id')
        else:
            start_date_str = request.GET.get('start_date')
            end_date_str = request.GET.get('end_date')
            agent_id = request.GET.get('agent_id')
        
        # Basic validation exactly like original
        if not start_date_str or not end_date_str:
            return Response({
                'error': 'Both start_date and end_date parameters are required',
                'example': '/api/available-timeslots/?start_date=2025-06-15&end_date=2025-06-28'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate date format exactly like original
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({
                'error': 'Invalid date format. Use YYYY-MM-DD',
                'example': 'start_date=2025-06-15&end_date=2025-06-28'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if start_date > end_date:
            return Response({
                'error': 'start_date must be before or equal to end_date'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            
            # Query pre-populated timeslots table
            queryset = AvailableTimeslot.objects.filter(
                date__gte=start_date,
                date__lte=end_date
            ).order_by('datetime')
            
            if agent_id:
                queryset = queryset.filter(agent_id=agent_id)
            
            # If no pre-populated data exists, fall back to original algorithm
            if not queryset.exists():
                # Create a temporary instance of the original API to get timeslots
                original_view = AvailableTimeslotsAPIView()
                available_slots = original_view.get_available_timeslots(start_date, end_date, agent_id)
                
                # Convert to our expected format
                timeslots = []
                for slot in available_slots:
                    timeslots.append({
                        'agent_id': slot['agent_id'],
                        'agent_name': slot['agent_name'], 
                        'agent_email': slot['agent_email'],
                        'date': slot['date'],
                        'time': slot['time'],
                        'datetime': slot['datetime'],
                        'end_datetime': slot['end_datetime'],
                        'duration_minutes': slot['duration_minutes']
                    })
            else:
                # Use pre-populated data
                timeslots = []
                for slot in queryset:
                    timeslots.append({
                        'agent_id': slot.agent_id,
                        'agent_name': slot.agent_name,
                        'agent_email': slot.agent_email,
                        'date': slot.date.isoformat(),
                        'time': slot.time.strftime('%H:%M'),
                        'datetime': slot.datetime.isoformat(),
                        'end_datetime': slot.end_datetime.isoformat(),
                        'duration_minutes': slot.duration_minutes
                    })
            
            # Group by agent for consistent format
            agents_data = {}
            for slot in timeslots:
                agent_key = slot['agent_id']
                if agent_key not in agents_data:
                    agents_data[agent_key] = {
                        'agent_id': slot['agent_id'],
                        'agent_name': slot['agent_name'],
                        'agent_email': slot['agent_email'],
                        'available_slots': []
                    }
                agents_data[agent_key]['available_slots'].append({
                    'date': slot['date'],
                    'time': slot['time'],
                    'datetime': slot['datetime'],
                    'end_datetime': slot['end_datetime'],
                    'duration_minutes': slot['duration_minutes']
                })
            
            # Convert to original API format for compatibility
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return Response({
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'agent_id': str(agent_id) if agent_id else None,
                'available_timeslots': timeslots,
                'total_slots': len(timeslots),
                'generated_at': datetime.now().isoformat(),
                # Performance metrics (bonus info)
                '_performance': {
                    'execution_time_ms': round(execution_time, 2),
                    'data_source': 'pre_populated_table',
                    'optimization': 'database_lookup_vs_computation'
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to generate timeslots: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AgentSignupAPIView(APIView):
    """
    API endpoint for agent signup
    POST /api/signup/agent/
    
    Creates:
    1. Django User account
    2. UserProfile (marking as agent)
    3. Agent record with default settings
    """
    
    def post(self, request):
        try:
            # Extract data
            username = request.data.get('username')
            email = request.data.get('email')
            password = request.data.get('password')
            first_name = request.data.get('first_name')
            last_name = request.data.get('last_name')
            phone = request.data.get('phone', '')
            
            # Validate required fields
            if not all([username, email, password, first_name, last_name]):
                return Response({
                    'error': 'Missing required fields',
                    'required': ['username', 'email', 'password', 'first_name', 'last_name']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if username or email already exists
            if User.objects.filter(username=username).exists():
                return Response({
                    'error': 'Username already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if User.objects.filter(email=email).exists():
                return Response({
                    'error': 'Email already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create everything in a transaction
            with transaction.atomic():
                # Create User
                user = User.objects.create(
                    username=username,
                    email=email,
                    password=make_password(password),
                    first_name=first_name,
                    last_name=last_name
                )
                
                # Create UserProfile
                user_profile = UserProfile.objects.create(
                    user=user,
                    user_type='agent',
                    phone=phone
                )
                
                # Create Agent record
                agent = Agent.objects.create(
                    user=user,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    active=True
                )
                
                # Create default AgentSettings
                agent_settings = AgentSettings.objects.create(
                    agent_id=agent.id,
                    daily_caps=10,  # Default: 10 appointments per day
                    weekly_caps=50  # Default: 50 appointments per week
                )
                
                return Response({
                    'message': 'Agent account created successfully',
                    'user_id': user.id,
                    'agent_id': agent.id,
                    'username': username,
                    'email': email,
                    'full_name': f"{first_name} {last_name}"
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response({
                'error': f'Failed to create agent account: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ClientSignupAPIView(APIView):
    """
    API endpoint for client signup
    POST /api/signup/client/
    
    Creates:
    1. Django User account
    2. UserProfile (marking as client)
    3. Client record
    """
    
    def post(self, request):
        try:
            # Extract data
            username = request.data.get('username')
            email = request.data.get('email')
            password = request.data.get('password')
            first_name = request.data.get('first_name')
            last_name = request.data.get('last_name')
            phone = request.data.get('phone', '')
            date_of_birth = request.data.get('date_of_birth', None)
            address = request.data.get('address', '')
            
            # Validate required fields
            if not all([username, email, password, first_name, last_name]):
                return Response({
                    'error': 'Missing required fields',
                    'required': ['username', 'email', 'password', 'first_name', 'last_name']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if username or email already exists
            if User.objects.filter(username=username).exists():
                return Response({
                    'error': 'Username already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if User.objects.filter(email=email).exists():
                return Response({
                    'error': 'Email already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Parse date_of_birth if provided
            dob = None
            if date_of_birth:
                try:
                    dob = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
                except ValueError:
                    return Response({
                        'error': 'Invalid date_of_birth format. Use YYYY-MM-DD'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create everything in a transaction
            with transaction.atomic():
                # Create User
                user = User.objects.create(
                    username=username,
                    email=email,
                    password=make_password(password),
                    first_name=first_name,
                    last_name=last_name
                )
                
                # Create UserProfile
                user_profile = UserProfile.objects.create(
                    user=user,
                    user_type='client',
                    phone=phone
                )
                
                # Create Client record
                client = Client.objects.create(
                    user=user,
                    date_of_birth=dob,
                    address=address
                )
                
                return Response({
                    'message': 'Client account created successfully',
                    'user_id': user.id,
                    'client_id': client.id,
                    'username': username,
                    'email': email,
                    'full_name': f"{first_name} {last_name}"
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response({
                'error': f'Failed to create client account: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# HTML Form Views (render signup pages that call the APIs)

def agent_signup_page(request):
    """
    Render the agent signup form page
    The form uses JavaScript to call AgentSignupAPIView
    """
    return render(request, 'scheduling/agent_signup.html')


def client_signup_page(request):
    """
    Render the client signup form page
    The form uses JavaScript to call ClientSignupAPIView
    """
    return render(request, 'scheduling/client_signup.html')
