# Django Setup Steps for Agent Scheduling API

## What We Just Accomplished

### 1. Repository Setup
- Already had a Git repository initialized 
- Repository name: `orchard` (owner: ayman2028)
- Working on branch: `main`

### 2. Python Environment Configuration
- Configured Python virtual environment using `venv`
- Python Version: 3.13.5
- Virtual environment location: `D:\ONEDRIVE\orchard-take-home\.venv\`
- Python executable path: `D:\ONEDRIVE\orchard-take-home\.venv\Scripts\python.exe`

### 3. Package Installation
Installed the following Python packages:
- **Django (5.2.8)** - Main web framework
- **djangorestframework (3.16.1)** - For building REST APIs
- **python-decouple (3.8)** - For configuration management

### 4. Django Project Structure Created
- Created main Django project: `scheduler_api`
- Created Django app: `scheduling`
- Generated `manage.py` file for project management

### 5. Current Project Structure
```
d:\ONEDRIVE\orchard-take-home\
├── .git/                          # Git repository
├── .venv/                         # Python virtual environment
├── manage.py                      # Django management script
├── scheduler_api/                 # Main Django project directory
├── scheduling/                    # Django app for scheduling logic
├── scheduling.db                  # SQLite database (provided)
├── README.md                      # Assignment instructions
├── scheduling-interface.png       # Reference UI image
└── Orchard Engineering - Interview Prep.pdf
```

### 6. Next Steps Needed
1. **Configure Django settings** - Add our app to INSTALLED_APPS, configure database
2. **Examine the SQLite database** - Understand the schema for agents, appointments, etc.
3. **Create Django models** - Map the existing database tables to Django models
4. **Build the API endpoint** - Create views and URLs for available timeslots
5. **Add business logic** - Implement scheduling constraints (60min appointments, 30min buffer, working hours, etc.)
6. **Write tests** - Create test suite for the scheduling logic
7. **Generate sample output** - Create JSON output for dates 6/15 to 6/28

### 7. Key Assignment Requirements to Implement
- **API Input**: start_date, end_date
- **API Output**: JSON list of available timeslots
- **Constraints**:
  - 60-minute appointments
  - 30-minute buffer before/after appointments
  - Working hours: 9:00 AM - 5:00 PM
  - 30-minute time increments
  - No double-booking
  - Respect daily/weekly appointment caps
  - No scheduling over existing appointments

### 8. PowerShell Notes
- Had to use `python` command directly (virtual environment was already active)
- PowerShell execution policy prevented running `.venv\Scripts\Activate.ps1`
- Django installation and project creation completed successfully

## Database Analysis & API Design Approach

### 9. Database Schema Discovered
After examining `scheduling.db`, found these key tables:
- **agents** - Agent info (id, names, email, phone, active status)
- **agent_settings** - Scheduling constraints (daily_caps: 1/day, weekly_caps: 3/week)
- **appointments** - Existing bookings (agent_id, client_name, appointment_time, status)
- **calendar_events** - Blocked time slots (agent_id, event_name, start_time, end_time)

### 10. API-First Development Strategy
**Primary Focus**: Build `/api/available-timeslots/` endpoint
- Input: `start_date`, `end_date` query parameters
- Output: JSON array of available appointment slots
- Implements all business constraints

### 11. Algorithm Logic
```
For each agent (active only):
  For each date in range:
    For each 30-min time slot (9:00 AM - 4:00 PM):
      Check if 60-min appointment + 30-min buffer fits
      Check conflicts with appointments/calendar_events  
      Check daily cap (1/day) and weekly cap (3/week)
      If available → add to results
```

### 12. Implementation Steps Refined
1. **Configure Django** - Update settings.py, add 'scheduling' to INSTALLED_APPS
2. **Create Models** - Map existing DB tables to Django models (unmanaged)
3. **Build Algorithm** - Implement scheduling logic in views.py
4. **Create API View** - Django REST Framework view for endpoint
5. **Configure URLs** - Set up routing for `/api/available-timeslots/`
6. **Test & Validate** - Create test suite, generate sample JSON output

### 13. Sample API Response Format
```json
{
  "start_date": "2025-06-15",
  "end_date": "2025-06-28",
  "available_timeslots": [
    {
      "agent_id": 1,
      "agent_name": "Claudia Failli",
      "date": "2025-06-15",
      "time": "09:00",
      "datetime": "2025-06-15T09:00:00",
      "duration_minutes": 60,
      "available": true
    }
  ],
  "total_slots": 245
}
```

### 14. Key Business Rules Identified
- Appointments: 60 minutes long
- Buffer: 30 minutes before/after each appointment
- Working hours: 9:00 AM - 5:00 PM (last appointment starts at 4:00 PM)
- Time increments: 30-minute slots (9:00, 9:30, 10:00, etc.)
- Agent caps: 1 appointment/day, 3 appointments/week
- Conflicts: Avoid existing appointments AND calendar events
- Agent filter: Only include active agents