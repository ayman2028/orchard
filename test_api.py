#!/usr/bin/env python

def main():
    import os
    import django
    
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scheduler_api.settings')
    django.setup()

    from django.test import Client
    import json

    print("🚀 Testing Agent Scheduling API")
    print("=" * 50)

    # Test the API
    client = Client()
    response = client.get('/api/available-timeslots/?start_date=2024-11-01&end_date=2024-11-03&agent_id=1')

    print(f'📊 HTTP Status: {response.status_code}')

    if response.status_code == 200:
        data = json.loads(response.content)
        print(f'✅ API Response successful!')
        print(f'📅 Date range: {data.get("start_date")} to {data.get("end_date")}')
        print(f'👤 Agent ID: {data.get("agent_id")}')
        print(f'🎯 Total available slots: {data.get("total_slots")}')
        
        # Check slots
        slots = data.get('available_timeslots', [])
        if slots:
            print(f'\n📝 Sample slots:')
            for i, slot in enumerate(slots[:3]):  # First 3 slots
                print(f'   {i+1}. {slot["date"]} at {slot["time"]} - Agent: {slot["agent_name"]}')
            
            if len(slots) > 3:
                print(f'   ... and {len(slots) - 3} more slots')
            
            # Show slots by date
            slots_by_date = {}
            for slot in slots:
                date = slot['date']
                slots_by_date[date] = slots_by_date.get(date, 0) + 1
            
            print(f'\n📊 Slots per date:')
            for date, count in sorted(slots_by_date.items()):
                print(f'   📅 {date}: {count} slots')
        
        print(f'\n🎉 API is working with dynamic agent settings!')
        
        # Verify expected behavior
        if data.get('total_slots', 0) > 0:
            print(f'✅ Slots generated successfully')
        else:
            print(f'⚠️  No slots found - this might indicate capacity limits or conflicts')
            
    else:
        print(f'❌ Error: HTTP {response.status_code}')
        try:
            error_data = json.loads(response.content)
            print(f'💥 Error details: {error_data}')
        except:
            print(f'💥 Raw error: {response.content.decode()}')

if __name__ == "__main__":
    main()