from django.urls import path
from .views import AvailableTimeslotsAPIView

urlpatterns = [
    path('available-timeslots/', AvailableTimeslotsAPIView.as_view(), name='available-timeslots'),
]