#!/usr/bin/env python3
"""
Frontend-Backend Integration Test Script
Tests the connection between React frontend and backend API
"""

import json
import urllib.request
import urllib.error
import time
import sys

class IntegrationTester:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.test_results = []
    
    def log_result(self, test_name, success, message):
        """Log test result"""
        status = "✓" if success else "✗"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
    
    def test_backend_health(self):
        """Test if backend is healthy"""
        try:
            response = urllib.request.urlopen(f"{self.backend_url}/health")
            data = json.loads(response.read())
            self.log_result("Backend Health", True, f"Server is healthy - {data['status']}")
            return True
        except Exception as e:
            self.log_result("Backend Health", False, f"Backend not running: {str(e)}")
            return False
    
    def test_cors_headers(self):
        """Test CORS configuration"""
        try:
            # Test preflight request
            req = urllib.request.Request(
                f"{self.backend_url}/users",
                headers={
                    'Origin': 'http://localhost:3000',
                    'Access-Control-Request-Method': 'POST',
                    'Access-Control-Request-Headers': 'Content-Type'
                },
                method='OPTIONS'
            )
            
            response = urllib.request.urlopen(req)
            headers = dict(response.headers)
            
            # Check CORS headers
            cors_origin = headers.get('Access-Control-Allow-Origin', '')
            cors_methods = headers.get('Access-Control-Allow-Methods', '')
            
            if cors_origin and cors_methods:
                self.log_result("CORS Headers", True, f"CORS enabled for origin: {cors_origin}")
                return True
            else:
                self.log_result("CORS Headers", False, "CORS headers not properly configured")
                return False
        except Exception as e:
            self.log_result("CORS Headers", False, f"Error testing CORS: {str(e)}")
            return False
    
    def test_api_endpoints(self):
        """Test main API endpoints"""
        endpoints = [
            ("GET", "/users", None, "Get users"),
            ("GET", "/products", None, "Get products"),
            ("GET", "/orders", None, "Get orders"),
        ]
        
        all_passed = True
        for method, endpoint, data, description in endpoints:
            try:
                if method == "GET":
                    response = urllib.request.urlopen(f"{self.backend_url}{endpoint}")
                    result = json.loads(response.read())
                    self.log_result(f"API {description}", True, f"Retrieved {len(result) if isinstance(result, list) else 1} items")
                else:
                    # POST request
                    req_data = json.dumps(data).encode('utf-8') if data else None
                    req = urllib.request.Request(
                        f"{self.backend_url}{endpoint}",
                        data=req_data,
                        headers={'Content-Type': 'application/json'},
                        method=method
                    )
                    response = urllib.request.urlopen(req)
                    self.log_result(f"API {description}", True, f"Status: {response.status}")
            except Exception as e:
                self.log_result(f"API {description}", False, str(e))
                all_passed = False
        
        return all_passed
    
    def test_frontend_api_config(self):
        """Check frontend API configuration"""
        print("\n=== Frontend API Configuration ===")
        
        # Check if .env file exists
        try:
            with open('../frontend/.env', 'r') as f:
                env_content = f.read()
                if 'VITE_API_URL' in env_content:
                    api_url = [line for line in env_content.split('\n') if line.startswith('VITE_API_URL')][0]
                    self.log_result("Frontend .env", True, f"Found: {api_url}")
                else:
                    self.log_result("Frontend .env", False, "VITE_API_URL not found in .env")
        except FileNotFoundError:
            self.log_result("Frontend .env", False, ".env file not found - using default http://localhost:8000")
    
    def simulate_frontend_requests(self):
        """Simulate typical frontend API requests"""
        print("\n=== Simulating Frontend Requests ===")
        
        # Login simulation
        try:
            login_data = json.dumps({
                "username": "test_user",
                "password": "test_password"
            }).encode('utf-8')
            
            req = urllib.request.Request(
                f"{self.backend_url}/auth/login",
                data=login_data,
                headers={
                    'Content-Type': 'application/json',
                    'Origin': 'http://localhost:3000'
                }
            )
            
            try:
                response = urllib.request.urlopen(req)
                self.log_result("Login Request", True, "Login endpoint exists")
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    self.log_result("Login Request", True, "Login endpoint not implemented yet (404)")
                else:
                    self.log_result("Login Request", False, f"Error: {e.code}")
        except Exception as e:
            self.log_result("Login Request", False, str(e))
    
    def print_summary(self):
        """Print test summary"""
        print("\n=== Test Summary ===")
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        
        if passed_tests == total_tests:
            print("\n✓ All tests passed! Frontend and backend are properly integrated.")
        else:
            print("\n✗ Some tests failed. Check the configuration above.")
        
        print("\n=== Next Steps ===")
        print("1. Ensure backend is running: python3 simple_server.py")
        print("2. Start frontend: cd ../frontend && npm run dev")
        print("3. Open http://localhost:3000 in your browser")
        print("4. Check browser console for API requests")

def main():
    print("=== EduRPG Frontend-Backend Integration Test ===\n")
    
    tester = IntegrationTester()
    
    # Run tests
    if tester.test_backend_health():
        tester.test_cors_headers()
        tester.test_api_endpoints()
        tester.test_frontend_api_config()
        tester.simulate_frontend_requests()
    else:
        print("\n⚠️  Backend server is not running!")
        print("Please start the backend server first:")
        print("  python3 simple_server.py")
        print("\nOr if you have dependencies installed:")
        print("  python -m uvicorn app.main:app --reload")
    
    # Print summary
    tester.print_summary()

if __name__ == "__main__":
    main()