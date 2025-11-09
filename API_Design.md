# Agent Scheduling API Design

## Database Schema Analysis

### Tables:
1. **agents** - Agent information (id, names, email, phone, active status)
2. **agent_settings** - Scheduling constraints (daily_caps, weekly_caps per agent)  
3. **appointments** - Booked appointments (agent_id, client_name, appointment_time, status)
4. **calendar_events** - Blocked time slots (agent_id, event_name, start_time, end_time)

### Key Insights:
- Agents have daily caps (1 per day) and weekly caps (3 per week)
- Appointments are 1 hour long (based on calendar_events data)
- Calendar events show blocked time including appointments
- Need to respect both existing appointments AND calendar events

## API Endpoint Design

### Primary Endpoint (Required)

#### GET /api/available-timeslots/
**Purpose**: Return all available appointment slots within a date range

**Query Parameters**:
- `start_date` (required): YYYY-MM-DD format
- `end_date` (required): YYYY-MM-DD format
- `agent_id` (optional): Filter by specific agent

**Business Rules**:
- Appointments are 60 minutes long
- 30-minute buffer before/after each appointment
- Working hours: 9:00 AM - 5:00 PM (09:00 - 17:00)
- Return times in 30-minute increments (9:00, 9:30, 10:00, etc.)
- No scheduling over existing appointments or calendar events
- Respect daily caps (1/day) and weekly caps (3/week)
- Only include active agents

**Response Format**:
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
    },
    {
      "agent_id": 1,
      "agent_name": "Claudia Failli", 
      "date": "2025-06-15",
      "time": "09:30",
      "datetime": "2025-06-15T09:30:00",
      "duration_minutes": 60,
      "available": true
    }
  ],
  "total_slots": 245
}
```

### Supporting Endpoints (Optional - for development/testing)

#### GET /api/agents/
- List all active agents with their settings
- Shows daily/weekly caps

#### GET /api/agents/{id}/appointments/
- Show specific agent's appointments and blocked times
- Useful for debugging scheduling logic

#### GET /api/appointments/
- List all appointments (for testing)

## Algorithm Logic

### Available Timeslot Calculation:
1. **Generate time slots**: For each day in range, create 30-min slots from 9:00-17:00
2. **Filter working hours**: Only include slots that allow 60-min appointment (so last slot is 16:00)
3. **Remove conflicts**: Exclude slots that overlap with:
   - Existing appointments
   - Calendar events (blocked time)
   - 30-minute buffer zones
4. **Apply caps**: Check daily (1/day) and weekly (3/week) limits
5. **Agent availability**: Only include active agents

### Pseudocode:
```python
def get_available_timeslots(start_date, end_date, agent_id=None):
    agents = get_active_agents(agent_id)
    all_slots = []
    
    for agent in agents:
        for date in date_range(start_date, end_date):
            # Generate 30-min slots: 9:00, 9:30, 10:00... 16:00
            for slot_time in generate_time_slots(date):
                appointment_end = slot_time + 60_minutes
                
                # Check if slot + 60min + 30min buffer fits in working hours
                if appointment_end + 30_minutes <= 17:00:
                    
                    # Check conflicts with appointments/events
                    if not has_conflict(agent, slot_time, appointment_end):
                        
                        # Check daily/weekly caps
                        if within_caps(agent, date):
                            all_slots.append(create_slot(agent, slot_time))
    
    return all_slots
```

## Implementation Steps

1. **Configure Django settings** - Add scheduling app, configure database
2. **Create Django models** - Map database tables to Django models  
3. **Build the algorithm** - Implement scheduling logic in views.py
4. **Create serializers** - Format JSON output with DRF
5. **Set up URLs** - Configure routing
6. **Write tests** - Test business rules and edge cases
7. **Generate sample output** - Create JSON for 6/15 to 6/28 date range

## Sample Test Cases

- Agent with no conflicts → should show many available slots
- Agent at daily cap → should show no slots for that day
- Agent at weekly cap → should show no slots for rest of week
- Slot with 30min before existing appointment → should be blocked
- Slot ending after 5 PM → should be excluded
- Inactive agent → should not appear in results