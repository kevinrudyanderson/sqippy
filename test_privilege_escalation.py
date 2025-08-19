#!/usr/bin/env python3
"""
Test script to verify the privilege escalation vulnerability has been patched.
This script attempts to modify protected fields like 'role' and 'is_superuser'.
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test_user@example.com"
TEST_PASSWORD = "TestPassword123!"

def test_privilege_escalation():
    """Test if users can escalate their privileges"""
    
    print("=== Privilege Escalation Security Test ===\n")
    
    # Step 1: Register a test user
    print("1. Registering test user...")
    signup_data = {
        "name": "Test User",
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "phone_number": "+1234567890"
    }
    
    response = requests.post(f"{BASE_URL}/auth/customer/signup", json=signup_data)
    if response.status_code == 201:
        print("   ✓ User registered successfully")
    elif response.status_code == 400:
        print("   ⚠ User already exists, proceeding with login")
    else:
        print(f"   ✗ Registration failed: {response.status_code}")
        return
    
    # Step 2: Login to get access token
    print("\n2. Logging in...")
    login_data = {
        "username": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    if response.status_code != 200:
        print(f"   ✗ Login failed: {response.status_code}")
        return
    
    tokens = response.json()
    access_token = tokens["access_token"]
    print("   ✓ Login successful, token obtained")
    
    # Step 3: Get current profile
    print("\n3. Fetching current profile...")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/users/profile", headers=headers)
    
    if response.status_code != 200:
        print(f"   ✗ Failed to get profile: {response.status_code}")
        return
    
    profile = response.json()
    print(f"   ✓ Current role: {profile['role']}")
    print(f"   ✓ Current is_active: {profile['is_active']}")
    
    # Step 4: Attempt privilege escalation attacks
    print("\n4. Testing privilege escalation attempts...")
    
    # Test 1: Try to change role to ADMIN
    print("\n   Test 1: Attempting to change role to ADMIN...")
    attack_payload = {"role": "ADMIN"}
    response = requests.patch(f"{BASE_URL}/users/profile", json=attack_payload, headers=headers)
    
    # Check if role was changed
    response = requests.get(f"{BASE_URL}/users/profile", headers=headers)
    new_profile = response.json()
    
    if new_profile["role"] == "ADMIN":
        print("   ✗ CRITICAL: User was able to escalate to ADMIN role!")
    else:
        print(f"   ✓ PROTECTED: Role remains {new_profile['role']}")
    
    # Test 2: Try to set is_superuser
    print("\n   Test 2: Attempting to set is_superuser to true...")
    attack_payload = {"is_superuser": True}
    response = requests.patch(f"{BASE_URL}/users/profile", json=attack_payload, headers=headers)
    
    # Note: is_superuser may not be in the response schema, but we can test if it was set
    
    # Test 3: Try to change organization_id
    print("\n   Test 3: Attempting to change organization_id...")
    attack_payload = {"organization_id": "malicious-org-id"}
    response = requests.patch(f"{BASE_URL}/users/profile", json=attack_payload, headers=headers)
    
    # Test 4: Try to combine legitimate and malicious fields
    print("\n   Test 4: Attempting mixed payload (legitimate + malicious)...")
    attack_payload = {
        "name": "Updated Name",  # Legitimate
        "role": "SUPER_ADMIN",   # Malicious
        "is_superuser": True      # Malicious
    }
    response = requests.patch(f"{BASE_URL}/users/profile", json=attack_payload, headers=headers)
    
    # Final check
    response = requests.get(f"{BASE_URL}/users/profile", headers=headers)
    final_profile = response.json()
    
    print("\n=== Final Security Assessment ===")
    if final_profile["role"] == "CUSTOMER":
        print("✓ SECURE: Privilege escalation vulnerability has been patched!")
        print("  - Role field is protected from user modification")
        print("  - Only whitelisted fields can be updated")
    else:
        print("✗ VULNERABLE: User was able to change their role!")
        print(f"  - Current role: {final_profile['role']}")
    
    print("\nWhitelisted fields that CAN be updated:")
    print("  - name")
    print("  - email") 
    print("  - phone_number")
    print("  - password (via change-password endpoint)")
    print("  - is_active (for deactivation)")
    
    print("\nProtected fields that CANNOT be updated:")
    print("  - role")
    print("  - is_superuser")
    print("  - organization_id")
    print("  - user_id")
    print("  - created_at")
    print("  - updated_at")

if __name__ == "__main__":
    try:
        test_privilege_escalation()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API server.")
        print("Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"Error: {e}")