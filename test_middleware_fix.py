#!/usr/bin/env python3
"""Quick test to verify middleware fix"""

import requests
import json

BASE_URL = "http://localhost:8000/auth"

# Login to get token
print("1. Logging in...")
login_response = requests.post(
    f"{BASE_URL}/login/",
    json={"username": "user_test", "password": "testpass123"}
)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.status_code}")
    exit(1)

token = login_response.json()["access"]
headers = {"Authorization": f"Bearer {token}"}

print("✓ Login successful\n")

# Test previously blocked endpoints
endpoints = [
    ("GET", "/auth/my-subscription/", "My Subscription Status"),
    ("GET", "/auth/payment/history/", "Payment History"),
    ("POST", "/auth/subscription/cancel/", "Cancel Subscription"),
]

print("Testing previously blocked endpoints:\n")
print("=" * 70)

for method, endpoint, name in endpoints:
    print(f"\nTesting: {name}")
    print(f"Endpoint: {method} {endpoint}")

    if method == "GET":
        response = requests.get(f"http://localhost:8000{endpoint}", headers=headers)
    else:
        response = requests.post(f"http://localhost:8000{endpoint}", headers=headers)

    # Check if it's NOT blocked by middleware (403 with subscription required message)
    if response.status_code == 403:
        data = response.json()
        if "Subscription required" in data.get("message", "") or "Active subscription required" in data.get("message", ""):
            print(f"❌ STILL BLOCKED by middleware")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {json.dumps(data, indent=2)}")
        else:
            print(f"⚠️  403 response (but not from middleware)")
            print(f"   Response: {json.dumps(data, indent=2)}")
    elif response.status_code == 404:
        print(f"✓ NOT BLOCKED (404 - endpoint accessible, no subscription found - EXPECTED)")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    elif response.status_code == 200:
        print(f"✓ NOT BLOCKED (200 - endpoint accessible)")
        data = response.json()
        if "status" in data:
            print(f"   Subscription status: {data.get('status')}")
    else:
        print(f"✓ NOT BLOCKED (Status: {response.status_code} - endpoint accessible)")
        try:
            print(f"   Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"   Response: {response.text[:200]}")

print("\n" + "=" * 70)
print("\n✅ Middleware fix verification complete!")
print("\nSummary:")
print("- If endpoints return 404 or 200, the middleware is no longer blocking them")
print("- If endpoints return 403 with 'Subscription required', middleware is still blocking")
