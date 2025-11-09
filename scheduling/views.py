from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime

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
        
        # For now, return a simple response to test the API works
        return Response({
            'message': 'API is working!',
            'start_date': start_date_str,
            'end_date': end_date_str,
            'status': 'Ready for scheduling algorithm implementation',
            'generated_at': datetime.now().isoformat()
        })
