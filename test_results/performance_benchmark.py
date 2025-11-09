#!/usr/bin/env python
"""
Performance Benchmark Test for Agent Scheduling API
Tests response time and validates functionality without database conflicts
"""

import time
import json
from datetime import datetime
import subprocess
import sys

def run_performance_test():
    """Run performance tests using real API calls"""
    
    print("🚀 Agent Scheduling API - Performance Benchmark")
    print("=" * 60)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🖥️  Platform: Windows with Django {get_django_version()}")
    print()
    
    # Test scenarios
    scenarios = [
        {
            'name': 'Single Day - Single Agent',
            'url': 'http://127.0.0.1:8000/api/available-timeslots/?start_date=2024-11-01&end_date=2024-11-01&agent_id=1',
            'expected_max_time': 0.5
        },
        {
            'name': '3 Days - Single Agent', 
            'url': 'http://127.0.0.1:8000/api/available-timeslots/?start_date=2024-11-01&end_date=2024-11-03&agent_id=1',
            'expected_max_time': 1.0
        },
        {
            'name': '3 Days - All Agents',
            'url': 'http://127.0.0.1:8000/api/available-timeslots/?start_date=2024-11-01&end_date=2024-11-03',
            'expected_max_time': 1.5
        },
        {
            'name': '1 Week - All Agents',
            'url': 'http://127.0.0.1:8000/api/available-timeslots/?start_date=2024-11-01&end_date=2024-11-07',
            'expected_max_time': 2.0
        }
    ]
    
    results = []
    
    for scenario in scenarios:
        print(f"📊 Testing: {scenario['name']}")
        
        # Use curl for reliable HTTP testing
        start_time = time.time()
        try:
            result = subprocess.run([
                'curl', '-s', '-w', '%{http_code},%{time_total}', 
                '-o', 'temp_response.json', scenario['url']
            ], capture_output=True, text=True, timeout=10)
            
            end_time = time.time()
            
            if result.returncode == 0:
                # Parse curl output: "status_code,time_total"
                status_code, curl_time = result.stdout.strip().split(',')
                response_time = float(curl_time)
                
                if status_code == '200':
                    # Read response to get slot count
                    try:
                        with open('temp_response.json', 'r') as f:
                            data = json.load(f)
                        total_slots = data.get('total_slots', 0)
                        
                        print(f"   ✅ Response Time: {response_time:.3f}s")
                        print(f"   📈 Total Slots: {total_slots}")
                        
                        if response_time <= scenario['expected_max_time']:
                            print(f"   🎯 PASS - Within {scenario['expected_max_time']}s limit")
                            status = "PASS"
                        else:
                            print(f"   ⚠️  SLOW - Exceeded {scenario['expected_max_time']}s limit")
                            status = "SLOW"
                        
                        results.append({
                            'scenario': scenario['name'],
                            'response_time': response_time,
                            'total_slots': total_slots,
                            'status': status
                        })
                        
                    except (json.JSONDecodeError, FileNotFoundError):
                        print(f"   ❌ ERROR - Could not parse response")
                        results.append({'scenario': scenario['name'], 'status': 'ERROR'})
                else:
                    print(f"   ❌ ERROR - HTTP {status_code}")
                    results.append({'scenario': scenario['name'], 'status': f'HTTP_{status_code}'})
            else:
                print(f"   ❌ ERROR - Curl failed: {result.stderr}")
                results.append({'scenario': scenario['name'], 'status': 'CURL_ERROR'})
                
        except subprocess.TimeoutExpired:
            print(f"   ❌ ERROR - Request timeout (>10s)")
            results.append({'scenario': scenario['name'], 'status': 'TIMEOUT'})
        except Exception as e:
            print(f"   ❌ ERROR - {str(e)}")
            results.append({'scenario': scenario['name'], 'status': 'EXCEPTION'})
        
        print()
    
    # Summary
    print("=" * 60)
    print("📈 PERFORMANCE SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r.get('status') == 'PASS')
    total = len([r for r in results if 'response_time' in r])
    
    if total > 0:
        avg_time = sum(r['response_time'] for r in results if 'response_time' in r) / total
        print(f"✅ Tests Passed: {passed}/{len(results)}")
        print(f"⚡ Average Response Time: {avg_time:.3f}s")
        print(f"🎯 Performance Rating: {'EXCELLENT' if avg_time < 0.5 else 'GOOD' if avg_time < 1.0 else 'ACCEPTABLE'}")
    else:
        print("❌ No successful tests - ensure Django server is running")
    
    return results

def get_django_version():
    """Get Django version"""
    try:
        result = subprocess.run(['pipenv', 'run', 'python', '-c', 
                               'import django; print(django.get_version())'], 
                              capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else "Unknown"
    except:
        return "Unknown"

def save_results(results):
    """Save results to file"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'test_results/performance_results_{timestamp}.json'
    
    with open(filename, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'test_type': 'Performance Benchmark',
            'results': results,
            'summary': {
                'total_tests': len(results),
                'passed_tests': sum(1 for r in results if r.get('status') == 'PASS'),
                'django_version': get_django_version()
            }
        }, f, indent=2)
    
    print(f"📁 Results saved to: {filename}")

if __name__ == "__main__":
    print("⚠️  NOTE: Ensure Django development server is running on port 8000")
    print("   Run: pipenv run python manage.py runserver")
    print()
    
    try:
        results = run_performance_test()
        save_results(results)
        
        # Cleanup
        try:
            import os
            os.remove('temp_response.json')
        except:
            pass
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")