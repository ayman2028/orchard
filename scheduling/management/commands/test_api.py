from django.core.management.base import BaseCommand
from django.test import Client
import json

class Command(BaseCommand):
    help = 'Test the available timeslots API'

    def handle(self, *args, **options):
        self.stdout.write("🚀 Testing Agent Scheduling API")
        self.stdout.write("=" * 50)

        # Test the API
        client = Client()
        response = client.get('/api/available-timeslots/?start_date=2024-11-01&end_date=2024-11-03&agent_id=1')

        self.stdout.write(f'📊 HTTP Status: {response.status_code}')

        if response.status_code == 200:
            data = json.loads(response.content)
            self.stdout.write('✅ API Response successful!')
            self.stdout.write(f'📅 Date range: {data.get("start_date")} to {data.get("end_date")}')
            self.stdout.write(f'👤 Agent ID: {data.get("agent_id")}')
            self.stdout.write(f'🎯 Total available slots: {data.get("total_slots")}')
            
            # Check slots
            slots = data.get('available_timeslots', [])
            if slots:
                self.stdout.write('\n📝 Sample slots:')
                for i, slot in enumerate(slots[:3]):  # First 3 slots
                    self.stdout.write(f'   {i+1}. {slot["date"]} at {slot["time"]} - Agent: {slot["agent_name"]}')
                
                if len(slots) > 3:
                    self.stdout.write(f'   ... and {len(slots) - 3} more slots')
                
                # Show slots by date
                slots_by_date = {}
                for slot in slots:
                    date = slot['date']
                    slots_by_date[date] = slots_by_date.get(date, 0) + 1
                
                self.stdout.write('\n📊 Slots per date:')
                for date, count in sorted(slots_by_date.items()):
                    self.stdout.write(f'   📅 {date}: {count} slots')
            
            self.stdout.write('\n🎉 API is working with dynamic agent settings!')
            
            # Verify expected behavior
            if data.get('total_slots', 0) > 0:
                self.stdout.write('✅ Slots generated successfully')
            else:
                self.stdout.write('⚠️  No slots found - this might indicate capacity limits or conflicts')
                
        else:
            self.stdout.write(f'❌ Error: HTTP {response.status_code}')
            try:
                error_data = json.loads(response.content)
                self.stdout.write(f'💥 Error details: {error_data}')
            except:
                self.stdout.write(f'💥 Raw error: {response.content.decode()}')