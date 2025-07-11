"""
Test script for error handling and logging system
"""
import requests
import json
from datetime import datetime

# Base URL
BASE_URL = "http://localhost:8000/api/v1"

# Test endpoints
TEST_ENDPOINTS = [
    ("GET", "/test/test-success", None, "Success test"),
    ("GET", "/test/test-authentication-error", None, "Authentication error"),
    ("GET", "/test/test-authorization-error", None, "Authorization error"),
    ("GET", "/test/test-not-found?resource_id=123", None, "Not found error"),
    ("GET", "/test/test-validation-error", None, "Validation error"),
    ("GET", "/test/test-conflict-error", None, "Conflict error"),
    ("GET", "/test/test-business-logic-error", None, "Business logic error"),
    ("GET", "/test/test-database-error", None, "Database error"),
    ("GET", "/test/test-external-service-error", None, "External service error"),
    ("GET", "/test/test-rate-limit-error", None, "Rate limit error"),
    ("GET", "/test/test-unhandled-error", None, "Unhandled error"),
    ("GET", "/test/test-logging?param1=test&param2=123", None, "Logging test"),
    ("GET", "/test/test-slow-endpoint?delay=0.5", None, "Slow endpoint test"),
]


def test_endpoint(method: str, endpoint: str, data: dict = None, description: str = ""):
    """Test a single endpoint"""
    print(f"\n{'='*50}")
    print(f"Testing: {description}")
    print(f"{method} {BASE_URL}{endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}")
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", json=data)
        else:
            response = requests.request(method, f"{BASE_URL}{endpoint}", json=data)
        
        print(f"Status: {response.status_code}")
        
        # Print headers
        if "X-Request-ID" in response.headers:
            print(f"Request ID: {response.headers['X-Request-ID']}")
        if "X-Response-Time" in response.headers:
            print(f"Response Time: {response.headers['X-Response-Time']}")
        
        # Print response body
        try:
            response_json = response.json()
            print(f"Response: {json.dumps(response_json, indent=2)}")
        except:
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")


def test_validation_error():
    """Test validation error with invalid data"""
    print(f"\n{'='*50}")
    print("Testing: Validation error with invalid POST data")
    
    # Missing required fields
    invalid_data = {
        "username": "test"  # Missing email and password
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=invalid_data)
        print(f"Status: {response.status_code}")
        
        if "X-Request-ID" in response.headers:
            print(f"Request ID: {response.headers['X-Request-ID']}")
        
        response_json = response.json()
        print(f"Response: {json.dumps(response_json, indent=2)}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")


def test_rate_limiting():
    """Test rate limiting by making many requests"""
    print(f"\n{'='*50}")
    print("Testing: Rate limiting")
    
    # Make 10 requests quickly
    for i in range(10):
        try:
            response = requests.get(f"{BASE_URL}/test/test-success")
            print(f"Request {i+1}: Status {response.status_code}", end="")
            
            if "X-RateLimit-Remaining" in response.headers:
                print(f" - Remaining: {response.headers['X-RateLimit-Remaining']}")
            else:
                print()
                
            if response.status_code == 429:
                print(f"Rate limit hit! Retry after: {response.headers.get('Retry-After', 'N/A')}")
                break
                
        except requests.exceptions.RequestException as e:
            print(f"Request {i+1} failed: {e}")


def check_logs():
    """Check if logs are being created"""
    print(f"\n{'='*50}")
    print("Checking log files:")
    
    import os
    log_dir = "logs"
    
    if os.path.exists(log_dir):
        for file in os.listdir(log_dir):
            file_path = os.path.join(log_dir, file)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                print(f"- {file}: {size} bytes")
                
                # Show last few lines of each log
                if size > 0:
                    print(f"  Last entry:")
                    try:
                        with open(file_path, 'r') as f:
                            lines = f.readlines()
                            if lines:
                                last_line = lines[-1].strip()
                                if last_line:
                                    log_entry = json.loads(last_line)
                                    print(f"    Time: {log_entry.get('timestamp', 'N/A')}")
                                    print(f"    Level: {log_entry.get('level', 'N/A')}")
                                    print(f"    Message: {log_entry.get('message', 'N/A')}")
                    except Exception as e:
                        print(f"    Error reading log: {e}")
    else:
        print(f"Log directory '{log_dir}' not found")


def main():
    """Run all tests"""
    print("Starting Error Handling and Logging Tests")
    print(f"Timestamp: {datetime.now()}")
    
    # Test all error endpoints
    for method, endpoint, data, description in TEST_ENDPOINTS:
        test_endpoint(method, endpoint, data, description)
    
    # Test validation error
    test_validation_error()
    
    # Test rate limiting
    test_rate_limiting()
    
    # Check logs
    check_logs()
    
    print(f"\n{'='*50}")
    print("Tests completed!")


if __name__ == "__main__":
    main()