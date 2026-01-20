#!/usr/bin/env python3
"""
Comprehensive test script for subscription API endpoints
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"
AUTH_URL = f"{BASE_URL}/auth"

# Test credentials
ADMIN_USER = {
    "username": "admin_test",
    "email": "admin@test.com",
    "password": "testpass123",
    "first_name": "Admin",
    "last_name": "Test"
}

REGULAR_USER = {
    "username": "user_test",
    "email": "user@test.com",
    "password": "testpass123",
    "first_name": "Regular",
    "last_name": "User"
}

# Test results storage
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80 + "\n")

def print_test(test_name, passed, message="", response_data=None):
    """Print test result"""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status}: {test_name}")
    if message:
        print(f"   → {message}")
    if response_data and not passed:
        print(f"   → Response: {json.dumps(response_data, indent=6)}")

    if passed:
        test_results["passed"].append(test_name)
    else:
        test_results["failed"].append({"test": test_name, "message": message})

def print_warning(message):
    """Print a warning message"""
    print(f"⚠ WARNING: {message}")
    test_results["warnings"].append(message)

# ============ Test Functions ============

def test_register_user(user_data, is_admin=False):
    """Test user registration"""
    print_section(f"Registering {'Admin' if is_admin else 'Regular'} User")

    response = requests.post(
        f"{AUTH_URL}/register/",
        json={
            "username": user_data["username"],
            "email": user_data["email"],
            "password": user_data["password"],
            "password_confirm": user_data["password"],
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"]
        }
    )

    if response.status_code == 201:
        data = response.json()
        print_test(f"Register {user_data['username']}", True)
        return {
            "access_token": data.get("access"),
            "refresh_token": data.get("refresh"),
            "user": data.get("user")
        }
    else:
        print_test(f"Register {user_data['username']}", False,
                  f"Status: {response.status_code}", response.json())
        return None

def login_user(username, password):
    """Login and get tokens"""
    response = requests.post(
        f"{AUTH_URL}/login/",
        json={"username": username, "password": password}
    )

    if response.status_code == 200:
        data = response.json()
        return {
            "access_token": data.get("access"),
            "refresh_token": data.get("refresh")
        }
    return None

def make_admin(username):
    """Make a user an admin via Django shell"""
    import subprocess
    cmd = f"python3 manage.py shell -c \"from django.contrib.auth.models import User; u = User.objects.get(username='{username}'); u.is_staff = True; u.is_superuser = True; u.save(); print('Admin created')\""
    subprocess.run(cmd, shell=True, capture_output=True)

def test_create_subscription_plan(token, plan_data):
    """Test creating a subscription plan (Admin only)"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{AUTH_URL}/admin/subscription-plans/",
        headers=headers,
        json=plan_data
    )

    passed = response.status_code == 201
    test_name = f"Create subscription plan: {plan_data['name']}"

    if passed:
        data = response.json()
        print_test(test_name, True, f"Plan ID: {data.get('id')}")
        return data
    else:
        print_test(test_name, False, f"Status: {response.status_code}", response.json())
        return None

def test_list_plans_admin(token):
    """Test listing all plans (Admin only)"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{AUTH_URL}/admin/subscription-plans/list/",
        headers=headers
    )

    passed = response.status_code == 200
    test_name = "List all subscription plans (Admin)"

    if passed:
        data = response.json()
        print_test(test_name, True, f"Found {len(data)} plans")
        return data
    else:
        print_test(test_name, False, f"Status: {response.status_code}", response.json())
        return None

def test_update_plan(token, plan_id, update_data):
    """Test updating a subscription plan (Admin only)"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.patch(
        f"{AUTH_URL}/admin/subscription-plans/{plan_id}/",
        headers=headers,
        json=update_data
    )

    passed = response.status_code == 200
    test_name = f"Update subscription plan ID {plan_id}"

    if passed:
        data = response.json()
        print_test(test_name, True)
        return data
    else:
        print_test(test_name, False, f"Status: {response.status_code}", response.json())
        return None

def test_list_active_plans():
    """Test listing active plans (Public endpoint)"""
    response = requests.get(f"{AUTH_URL}/subscription-plans/")

    passed = response.status_code == 200
    test_name = "List active subscription plans (Public)"

    if passed:
        data = response.json()
        print_test(test_name, True, f"Found {len(data)} active plans")
        return data
    else:
        print_test(test_name, False, f"Status: {response.status_code}", response.json())
        return None

def test_get_plan_details(plan_id):
    """Test getting specific plan details (Public endpoint)"""
    response = requests.get(f"{AUTH_URL}/subscription-plans/{plan_id}/")

    passed = response.status_code == 200
    test_name = f"Get plan details (ID: {plan_id})"

    if passed:
        data = response.json()
        print_test(test_name, True, f"Plan: {data.get('name')}")
        return data
    else:
        print_test(test_name, False, f"Status: {response.status_code}", response.json())
        return None

def test_get_my_subscription(token):
    """Test getting user's subscription status"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{AUTH_URL}/my-subscription/",
        headers=headers
    )

    test_name = "Get my subscription status"

    if response.status_code == 200:
        data = response.json()
        print_test(test_name, True, f"Status: {data.get('status')}")
        return data
    elif response.status_code == 404:
        print_test(test_name, True, "No subscription found (expected)")
        return None
    else:
        print_test(test_name, False, f"Status: {response.status_code}", response.json())
        return None

def test_initialize_subscription(token, plan_id):
    """Test initializing a subscription payment"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{AUTH_URL}/subscribe/",
        headers=headers,
        json={"plan_id": plan_id}
    )

    passed = response.status_code == 200
    test_name = f"Initialize subscription (Plan ID: {plan_id})"

    if passed:
        data = response.json()
        print_test(test_name, True)
        print(f"   → Payment URL: {data.get('data', {}).get('payment_url')}")
        print(f"   → Order Tracking ID: {data.get('data', {}).get('order_tracking_id')}")
        return data
    else:
        print_test(test_name, False, f"Status: {response.status_code}", response.json())
        return None

def test_verify_payment(token, order_tracking_id):
    """Test verifying a payment"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{AUTH_URL}/payment/verify/{order_tracking_id}/",
        headers=headers
    )

    test_name = f"Verify payment (Order: {order_tracking_id})"

    if response.status_code == 200:
        data = response.json()
        print_test(test_name, True, f"Payment status: {data.get('payment', {}).get('status')}")
        return data
    elif response.status_code == 400:
        data = response.json()
        print_test(test_name, True, f"Payment not completed (expected for sandbox)")
        return data
    else:
        print_test(test_name, False, f"Status: {response.status_code}", response.json())
        return None

def test_payment_history(token):
    """Test getting payment history"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{AUTH_URL}/payment/history/",
        headers=headers
    )

    passed = response.status_code == 200
    test_name = "Get payment history"

    if passed:
        data = response.json()
        print_test(test_name, True, f"Found {len(data)} payments")
        return data
    else:
        print_test(test_name, False, f"Status: {response.status_code}", response.json())
        return None

def test_cancel_subscription(token):
    """Test cancelling a subscription"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{AUTH_URL}/subscription/cancel/",
        headers=headers
    )

    test_name = "Cancel subscription"

    if response.status_code == 200:
        data = response.json()
        print_test(test_name, True, f"Subscription cancelled")
        return data
    elif response.status_code == 404:
        print_test(test_name, True, "No subscription to cancel (expected)")
        return None
    else:
        print_test(test_name, False, f"Status: {response.status_code}", response.json())
        return None

def test_delete_plan(token, plan_id):
    """Test deleting a subscription plan (Admin only)"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(
        f"{AUTH_URL}/admin/subscription-plans/{plan_id}/delete/",
        headers=headers
    )

    passed = response.status_code == 204
    test_name = f"Delete subscription plan (ID: {plan_id})"

    if passed:
        print_test(test_name, True)
        return True
    else:
        print_test(test_name, False, f"Status: {response.status_code}", response.json())
        return False

# ============ Main Test Flow ============

def run_all_tests():
    """Run all subscription API tests"""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "SUBSCRIPTION API TEST SUITE" + " " * 31 + "║")
    print("╚" + "=" * 78 + "╝")

    # Step 1: Register users
    print_section("Step 1: User Registration")
    admin_data = test_register_user(ADMIN_USER, is_admin=True)
    time.sleep(0.5)
    user_data = test_register_user(REGULAR_USER)

    if not admin_data or not user_data:
        print("\n❌ Failed to register users. Exiting.")
        return

    # Make the admin user an actual admin
    print("\n→ Promoting admin_test to superuser...")
    make_admin(ADMIN_USER["username"])
    time.sleep(1)

    # Re-login admin to get new token with admin permissions
    admin_login = login_user(ADMIN_USER["username"], ADMIN_USER["password"])
    if admin_login:
        admin_token = admin_login["access_token"]
        print("✓ Admin logged in with admin permissions")
    else:
        print("❌ Failed to login admin")
        return

    user_token = user_data["access_token"]

    # Step 2: Test Admin Plan Management
    print_section("Step 2: Admin Subscription Plan Management")

    # Create plans
    basic_plan = test_create_subscription_plan(admin_token, {
        "name": "Basic Plan",
        "description": "Basic subscription with standard features",
        "amount": 999.00,
        "period": "monthly",
        "period_count": 1,
        "is_active": True,
        "features": ["Feature 1", "Feature 2", "Basic Support"]
    })
    time.sleep(0.5)

    premium_plan = test_create_subscription_plan(admin_token, {
        "name": "Premium Plan",
        "description": "Premium subscription with all features",
        "amount": 2499.00,
        "period": "monthly",
        "period_count": 3,
        "is_active": True,
        "features": ["All Features", "Priority Support", "Custom Reports"]
    })
    time.sleep(0.5)

    # List all plans (Admin)
    all_plans = test_list_plans_admin(admin_token)
    time.sleep(0.5)

    # Update a plan
    if basic_plan:
        test_update_plan(admin_token, basic_plan['id'], {
            "amount": 899.00,
            "description": "Updated basic plan with new pricing"
        })
        time.sleep(0.5)

    # Step 3: Test Public Plan Endpoints
    print_section("Step 3: Public Subscription Plan Endpoints")

    active_plans = test_list_active_plans()
    time.sleep(0.5)

    if active_plans and len(active_plans) > 0:
        test_get_plan_details(active_plans[0]['id'])
        time.sleep(0.5)

    # Step 4: Test User Subscription Flow
    print_section("Step 4: User Subscription Flow")

    # Check initial subscription status
    test_get_my_subscription(user_token)
    time.sleep(0.5)

    # Initialize subscription
    if basic_plan:
        subscription_init = test_initialize_subscription(user_token, basic_plan['id'])
        time.sleep(0.5)

        # Test payment verification
        if subscription_init:
            order_tracking_id = subscription_init.get('data', {}).get('order_tracking_id')
            if order_tracking_id:
                test_verify_payment(user_token, order_tracking_id)
                time.sleep(0.5)

    # Step 5: Test Payment Endpoints
    print_section("Step 5: Payment Endpoints")

    test_payment_history(user_token)
    time.sleep(0.5)

    # Check subscription status again
    test_get_my_subscription(user_token)
    time.sleep(0.5)

    # Step 6: Test Subscription Cancellation
    print_section("Step 6: Subscription Cancellation")

    test_cancel_subscription(user_token)
    time.sleep(0.5)

    # Step 7: Test Plan Deletion (cleanup)
    print_section("Step 7: Cleanup - Delete Test Plans")

    if basic_plan:
        test_delete_plan(admin_token, basic_plan['id'])
        time.sleep(0.5)

    if premium_plan:
        test_delete_plan(admin_token, premium_plan['id'])
        time.sleep(0.5)

    # Print summary
    print_section("Test Summary")

    total_tests = len(test_results["passed"]) + len(test_results["failed"])
    pass_rate = (len(test_results["passed"]) / total_tests * 100) if total_tests > 0 else 0

    print(f"Total Tests: {total_tests}")
    print(f"Passed: {len(test_results['passed'])} ({pass_rate:.1f}%)")
    print(f"Failed: {len(test_results['failed'])}")
    print(f"Warnings: {len(test_results['warnings'])}")

    if test_results["failed"]:
        print("\n" + "─" * 80)
        print("Failed Tests:")
        for failure in test_results["failed"]:
            print(f"  • {failure['test']}")
            print(f"    → {failure['message']}")

    if test_results["warnings"]:
        print("\n" + "─" * 80)
        print("Warnings:")
        for warning in test_results["warnings"]:
            print(f"  • {warning}")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
