# Entity Relationship Diagram - Agent Scheduling System

## Visual Database Schema

```
┌─────────────────┐    ┌──────────────────┐
│     AGENTS      │────│  AGENT_SETTINGS  │
├─────────────────┤ 1:1├──────────────────┤
│🔑 id (PK)       │    │🔑 agent_id (PK)  │
│  first_name     │    │  daily_caps      │
│  last_name      │    │  weekly_caps     │
│  email          │    └──────────────────┘
│  phone          │
│  active         │
└─────────────────┘
         │ 1
         │
         │ N
┌─────────────────┐    ┌──────────────────┐
│  APPOINTMENTS   │    │ CALENDAR_EVENTS  │
├─────────────────┤    ├──────────────────┤
│🔑 id (PK)       │    │🔑 id (PK)        │
│🔗 agent_id (FK) │    │🔗 agent_id (FK)  │
│  client_name    │    │  event_name      │
│  appointment_time│   │  start_time      │
│  status         │    │  end_time        │
└─────────────────┘    └──────────────────┘
```

## API Flow Visualization

```
HTTP Request
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Django API Layer                            │
├─────────────────────────────────────────────────────────────────┤
│ GET /api/available-timeslots/?start_date=X&end_date=Y          │
│                                                                 │
│ 1. Validate date parameters                                     │
│ 2. Query database for agents, appointments, events             │
│ 3. Apply scheduling algorithm                                   │
│ 4. Format JSON response                                         │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼ Queries
┌─────────────────────────────────────────────────────────────────┐
│                   Data Access Layer                            │
├─────────────────────────────────────────────────────────────────┤
│ Django Models (ORM)                                             │
│ ├─ Agent.objects.filter(active=True)                           │
│ ├─ Appointment.objects.filter(date_range)                      │
│ ├─ CalendarEvent.objects.filter(date_range)                    │
│ └─ AgentSettings.objects.all()                                 │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼ SQL Queries
┌─────────────────────────────────────────────────────────────────┐
│                    SQLite Database                              │
│                    (scheduling.db)                              │
└─────────────────────────────────────────────────────────────────┘
```

## Business Logic Flow

```
Start: Date Range Input
     │
     ▼
┌─────────────────┐
│ Get Active      │ ──→ agents table (active=True)
│ Agents          │
└─────────────────┘
     │
     ▼
┌─────────────────┐     ┌─────────────────┐
│ Generate All    │ ──→ │ Time Slots      │
│ Possible        │     │ 9:00, 9:30,     │
│ Time Slots      │     │ 10:00... 16:00  │
└─────────────────┘     └─────────────────┘
     │
     ▼
┌─────────────────┐     ┌─────────────────┐
│ Filter Out      │ ──→ │ appointments +  │
│ Conflicts       │     │ calendar_events │
└─────────────────┘     └─────────────────┘
     │
     ▼
┌─────────────────┐     ┌─────────────────┐
│ Apply Buffer    │ ──→ │ 30min before/   │
│ Rules           │     │ after conflicts │
└─────────────────┘     └─────────────────┘
     │
     ▼
┌─────────────────┐     ┌─────────────────┐
│ Check Daily/    │ ──→ │ agent_settings  │
│ Weekly Caps     │     │ daily_caps=1    │
└─────────────────┘     │ weekly_caps=3   │
     │                  └─────────────────┘
     ▼
┌─────────────────┐
│ Return Available│ ──→ JSON Response
│ Timeslots       │
└─────────────────┘
```

## Data Record Counts
- 👥 Agents: 4 records
- ⚙️  Agent Settings: 4 records  
- 📅 Appointments: 53 records
- 🚫 Calendar Events: 517 records

## Key Constraints
- 🕘 Working Hours: 9:00 AM - 5:00 PM
- ⏱️  Appointment Duration: 60 minutes
- 🚗 Buffer Time: 30 minutes before/after
- 📊 Daily Cap: 1 appointment per agent per day
- 📈 Weekly Cap: 3 appointments per agent per week
- 🎯 Time Increments: 30-minute slots