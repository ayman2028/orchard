from django.urls import path
from .views import AvailableTimeslotsAPIView, doctor_schedule_view

urlpatterns = [
    path('available-timeslots/', AvailableTimeslotsAPIView.as_view(), name='available-timeslots'),
    path('schedule/', doctor_schedule_view, name='doctor-schedule'),
]