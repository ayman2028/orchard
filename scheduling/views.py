from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from .models import Agent, AgentSettings, Appointment, CalendarEvent

class AvailableTimeslotsAPIView(APIView):
    """
    API endpoint to get available appointment timeslots
    """
    
    def get(self, request):
        """Handle GET requests for available timeslots"""
        
        # Get query parameters
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
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
        
        # Test database queries
        try:
            database_info = self.get_database_info(start_date, end_date)
            return Response({
                'message': 'Database connection working!',
                'start_date': start_date_str,
                'end_date': end_date_str,
                'database_info': database_info,
                'status': 'Ready for scheduling algorithm implementation',
                'generated_at': datetime.now().isoformat()
            })
        except Exception as e:
            return Response({
                'error': f'Database connection failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_database_info(self, start_date, end_date):
        """
        Test database connectivity and return summary information
        """
        # Get active agents
        active_agents = Agent.objects.filter(active=True)
        # Get agent settings
        agent_settings = AgentSettings.objects.all()
        # Get appointments in date range
        appointments = Appointment.objects.filter(
            appointment_time__date__range=[start_date, end_date]
        )
        # Get calendar events in date range
        calendar_events = CalendarEvent.objects.filter(
            start_time__date__range=[start_date, end_date]
        )
        
        return {
            'agents': {
                'active_count': active_agents.count(),
                'active_agents': [
                    {
                        'id': agent.id,
                        'name': agent.full_name,
                        'email': agent.email
                    } for agent in active_agents
                ]
            },
            'agent_settings': {
                'total_count': agent_settings.count(),
                'settings': [
                    {
                        'agent_id': setting.agent_id,
                        'daily_caps': setting.daily_caps,
                        'weekly_caps': setting.weekly_caps
                    } for setting in agent_settings
                ]
            },
            'appointments': {
                'count_in_range': appointments.count(),
                'sample_appointments': [
                    {
                        'id': appt.id,
                        'agent_id': appt.agent_id,
                        'client_name': appt.client_name,
                        'appointment_time': appt.appointment_time.isoformat(),
                        'status': appt.status
                    } for appt in appointments[:5]  # Show first 5
                ]
            },
            'calendar_events': {
                'count_in_range': calendar_events.count(),
                'sample_events': [
                    {
                        'id': event.id,
                        'agent_id': event.agent_id,
                        'event_name': event.event_name,
                        'start_time': event.start_time.isoformat(),
                        'end_time': event.end_time.isoformat()
                    } for event in calendar_events[:5]  # Show first 5
                ]
            }
        }
