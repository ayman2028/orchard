import requests
import json

print("🚀 Testing Agent Scheduling API")
print("=" * 50)

try:
    url = "http://127.0.0.1:8000/api/available-timeslots/"
    params = {
        'start_date': '2024-11-01',
        'end_date': '2024-11-03', 
        'agent_id': '1'
    }
    
    print(f"📡 Calling: {url}")
    print(f"📋 Parameters: {params}")
    print()
    
    response = requests.get(url, params=params)
    
    print(f"📊 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"✅ Success!")
        print(f"📅 Date Range: {data.get('start_date')} to {data.get('end_date')}")
        print(f"👤 Agent ID: {data.get('agent_id')}")
        print(f"🎯 Total Available Slots: {data.get('total_slots')}")
        print()
        
        # Show first few slots
        slots = data.get('available_timeslots', [])
        if slots:
            print("📝 Sample Available Slots:")
            for i, slot in enumerate(slots[:5]):  # Show first 5 slots
                print(f"   {i+1}. {slot['date']} at {slot['time']} - Agent: {slot['agent_name']}")
            
            if len(slots) > 5:
                print(f"   ... and {len(slots) - 5} more slots")
            
            # Group by date
            print(f"\n📊 Slots by Date:")
            date_counts = {}
            for slot in slots:
                date = slot['date']
                date_counts[date] = date_counts.get(date, 0) + 1
            
            for date, count in sorted(date_counts.items()):
                print(f"   📅 {date}: {count} slots")
        
        print(f"\n🎉 API is working correctly with dynamic agent settings!")
        
    else:
        print(f"❌ Error: {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error details: {error_data}")
        except:
            print(f"Raw response: {response.text}")
            
except requests.exceptions.ConnectionError:
    print("❌ Connection Error: Make sure Django server is running on http://127.0.0.1:8000")
except Exception as e:
    print(f"❌ Unexpected error: {e}")