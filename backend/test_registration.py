#!/usr/bin/env python3
"""
Test script for user registration and login flow
"""

import json
import urllib.request
import urllib.error
import urllib.parse

BASE_URL = "http://localhost:8000"

def test_registration():
    """Test user registration"""
    print("=== Testing User Registration ===")
    
    # Test data
    user_data = {
        "username": "testuser123",
        "email": "test123@example.com",
        "password": "password123",
        "full_name": "Test User",
        "role": "student"
    }
    
    try:
        # Create request
        data = json.dumps(user_data).encode('utf-8')
        req = urllib.request.Request(
            f"{BASE_URL}/api/v1/users/register",
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Send request
        response = urllib.request.urlopen(req)
        result = json.loads(response.read())
        
        print(f"✓ Registration successful!")
        print(f"  User ID: {result.get('id')}")
        print(f"  Username: {result.get('username')}")
        print(f"  Email: {result.get('email')}")
        
        return user_data['username'], user_data['password']
        
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"✗ Registration failed: {e.code} - {error_body}")
        return None, None
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None, None

def test_login(username, password):
    """Test user login"""
    print("\n=== Testing User Login ===")
    
    if not username or not password:
        print("✗ Skipping login test - no credentials")
        return None
    
    try:
        # Create form data
        form_data = urllib.parse.urlencode({
            'username': username,
            'password': password
        }).encode('utf-8')
        
        req = urllib.request.Request(
            f"{BASE_URL}/api/v1/auth/token",
            data=form_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        # Send request
        response = urllib.request.urlopen(req)
        result = json.loads(response.read())
        
        print(f"✓ Login successful!")
        print(f"  Token: {result.get('access_token')[:50]}...")
        print(f"  Token Type: {result.get('token_type')}")
        
        return result.get('access_token')
        
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"✗ Login failed: {e.code} - {error_body}")
        return None
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None

def test_get_current_user(token):
    """Test getting current user"""
    print("\n=== Testing Get Current User ===")
    
    if not token:
        print("✗ Skipping current user test - no token")
        return
    
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/api/v1/users/me",
            headers={'Authorization': f'Bearer {token}'}
        )
        
        response = urllib.request.urlopen(req)
        result = json.loads(response.read())
        
        print(f"✓ Got current user!")
        print(f"  User ID: {result.get('id')}")
        print(f"  Username: {result.get('username')}")
        print(f"  Role: {result.get('role')}")
        
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"✗ Failed to get current user: {e.code} - {error_body}")
    except Exception as e:
        print(f"✗ Error: {str(e)}")

def main():
    print("=== EduRPG Registration Test ===\n")
    
    # Check if server is running
    try:
        response = urllib.request.urlopen(f"{BASE_URL}/health")
        print("✓ Server is running\n")
    except:
        print("✗ Server is not running!")
        print("Please start the server first:")
        print("  python simple_server.py")
        return
    
    # Run tests
    username, password = test_registration()
    token = test_login(username, password)
    test_get_current_user(token)
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()