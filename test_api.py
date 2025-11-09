#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scheduler_api.settings')
django.setup()

from scheduling.views import AvailableTimeslotsAPIView
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request
import json

def test_api():
    # Create a test request
    factory = APIRequestFactory()
    django_request = factory.get('/api/available-timeslots/', {
        'start_date': '2024-11-01',
        'end_date': '2024-11-03',
        'agent_id': '1'
    })
    # Wrap it in DRF Request to get query_params
    request = Request(django_request)
    
    # Create view instance and call it
    view = AvailableTimeslotsAPIView()
    response = view.get(request)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Type: {type(response.data)}")
    
    # Print the structure of the response
    if hasattr(response.data, 'keys'):
        print(f"Top-level keys: {list(response.data.keys())}")
        
        # Show some key values
        if 'message' in response.data:
            print(f"Message: {response.data['message']}")
        if 'status' in response.data:
            print(f"Status: {response.data['status']}")
        if 'start_date' in response.data:
            print(f"Start Date: {response.data['start_date']}")
        if 'database_info' in response.data:
            db_info = response.data['database_info']
            print(f"Database Info Keys: {list(db_info.keys()) if isinstance(db_info, dict) else 'Not a dict'}")
    
    # Show formatted JSON (truncated)
    print("\n" + "="*50)
    print("FORMATTED JSON RESPONSE:")
    print("="*50)
    json_str = json.dumps(response.data, indent=2, default=str)
    # Truncate if too long
    if len(json_str) > 2000:
        print(json_str[:2000] + "\n... [TRUNCATED - response is " + str(len(json_str)) + " characters]")
    else:
        print(json_str)

if __name__ == "__main__":
    test_api()