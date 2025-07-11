#!/usr/bin/env python3
"""
Test backend server without dependencies
This script tests the basic functionality that doesn't require external packages
"""

import json
import urllib.request
import urllib.error
import subprocess
import time
import sys
import os

class BackendTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.server_process = None
    
    def test_connection(self):
        """Test if server is running"""
        try:
            response = urllib.request.urlopen(f"{self.base_url}/health")
            data = json.loads(response.read())
            print(f"✓ Server is healthy: {data}")
            return True
        except urllib.error.URLError:
            print("✗ Server is not running")
            return False
    
    def test_endpoints(self):
        """Test various endpoints"""
        endpoints = [
            ("/", "Root endpoint"),
            ("/health", "Health check"),
            ("/docs", "API documentation"),
        ]
        
        for endpoint, description in endpoints:
            try:
                response = urllib.request.urlopen(f"{self.base_url}{endpoint}")
                print(f"✓ {description}: {response.status} {response.reason}")
            except Exception as e:
                print(f"✗ {description}: {str(e)}")
    
    def test_mock_server(self):
        """Test the mock server directly"""
        print("\n=== Testing Mock Server ===")
        
        # Start mock server
        print("Starting mock server...")
        try:
            # Run the mock server directly with Python
            self.server_process = subprocess.Popen(
                [sys.executable, "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for server to start
            print("Waiting for server to start...")
            time.sleep(3)
            
            # Test endpoints
            self.test_connection()
            self.test_endpoints()
            
            # Test API functionality
            self.test_api_operations()
            
        except Exception as e:
            print(f"Error running mock server: {e}")
        finally:
            if self.server_process:
                print("\nStopping server...")
                self.server_process.terminate()
                self.server_process.wait()
    
    def test_api_operations(self):
        """Test CRUD operations"""
        print("\n=== Testing API Operations ===")
        
        # Test GET users
        try:
            response = urllib.request.urlopen(f"{self.base_url}/users")
            users = json.loads(response.read())
            print(f"✓ GET /users: Found {len(users)} users")
        except Exception as e:
            print(f"✗ GET /users: {e}")
        
        # Test POST user
        try:
            user_data = json.dumps({
                "username": "test_user",
                "email": "test@example.com",
                "full_name": "Test User"
            }).encode('utf-8')
            
            req = urllib.request.Request(
                f"{self.base_url}/users",
                data=user_data,
                headers={'Content-Type': 'application/json'}
            )
            response = urllib.request.urlopen(req)
            created_user = json.loads(response.read())
            print(f"✓ POST /users: Created user with ID {created_user.get('id')}")
        except Exception as e:
            print(f"✗ POST /users: {e}")

def main():
    print("=== EduRPG Backend Test Script ===\n")
    
    tester = BackendTester()
    
    # Check if server is already running
    print("Checking if server is already running...")
    if tester.test_connection():
        print("\nServer is already running. Testing endpoints...")
        tester.test_endpoints()
        tester.test_api_operations()
    else:
        print("\nServer not running. Testing mock server...")
        tester.test_mock_server()
    
    print("\n=== Frontend Integration Test ===")
    print("To test frontend integration:")
    print("1. Ensure backend is running on http://localhost:8000")
    print("2. Start frontend with: npm run dev")
    print("3. Check browser console for API calls")
    print("\nEnvironment variables in frontend:")
    print("VITE_API_URL=http://localhost:8000")

if __name__ == "__main__":
    main()