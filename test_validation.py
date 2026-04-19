import requests
import json

BASE_URL = "http://127.0.0.1:5000"

print("="*70)
print("VALIDATION: Flask Endpoint Testing")
print("="*70)

# Test 1
print("\nTest 1: 'Show threat detection results'")
try:
    r = requests.post(f"{BASE_URL}/api/files/bot/message", 
                      json={"message": "Show threat detection results"}, timeout=5)
    print(f"Status: {r.status_code}")
    data = r.json()
    if "agent_actions" in data:
        print("✓ agent_actions found")
        print(f"Actions: {data['agent_actions']}")
    else:
        print("✗ No agent_actions")
except Exception as e:
    print(f"Error: {e}")

# Test 2  
print("\nTest 2: 'Bulk archive old files'")
try:
    r = requests.post(f"{BASE_URL}/api/files/bot/message",
                      json={"message": "Bulk archive old files"}, timeout=5)
    print(f"Status: {r.status_code}")
    data = r.json()
    if "agent_actions" in data:
        print("✓ agent_actions found")
        print(f"Actions: {data['agent_actions']}")
    else:
        print("✗ No agent_actions")
except Exception as e:
    print(f"Error: {e}")
