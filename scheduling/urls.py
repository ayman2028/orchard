from django.urls import path
from .views import AvailableTimeslotsAPIView, FastAvailableTimeslotsAPIView, doctor_schedule_view

urlpatterns = [
    # Fast pre-computed table API (now the default!)
    path('available-timeslots/', FastAvailableTimeslotsAPIView.as_view(), name='available-timeslots'),
    
    # Original compute-on-demand API (for comparison/fallback)
    path('available-timeslots-original/', AvailableTimeslotsAPIView.as_view(), name='available-timeslots-original'),
    
    # Web interface
    path('schedule/', doctor_schedule_view, name='doctor-schedule'),
]