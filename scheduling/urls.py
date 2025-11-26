from django.urls import path
from .views import (
    AvailableTimeslotsAPIView, 
    FastAvailableTimeslotsAPIView, 
    doctor_schedule_view,
    AgentSignupAPIView,
    ClientSignupAPIView,
    agent_signup_page,
    client_signup_page
)

urlpatterns = [
    # Fast pre-computed table API (now the default!)
    path('available-timeslots/', FastAvailableTimeslotsAPIView.as_view(), name='available-timeslots'),
    
    # Original compute-on-demand API (for comparison/fallback)
    path('available-timeslots-original/', AvailableTimeslotsAPIView.as_view(), name='available-timeslots-original'),
    
    # Web interface
    path('schedule/', doctor_schedule_view, name='doctor-schedule'),
    
    # Authentication APIs (JSON endpoints)
    path('signup/agent/', AgentSignupAPIView.as_view(), name='agent-signup-api'),
    path('signup/client/', ClientSignupAPIView.as_view(), name='client-signup-api'),
    
    # HTML Signup Pages (render forms that call the APIs above)
    path('signup/agent/form/', agent_signup_page, name='agent-signup-page'),
    path('signup/client/form/', client_signup_page, name='client-signup-page'),
]