#!/usr/bin/env python3
"""
Simple test runner script
"""
import subprocess
import sys
import os

def run_tests():
    """Run pytest tests"""
    # Change to backend directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Run pytest
    cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short"]
    
    # Add coverage if requested
    if "--coverage" in sys.argv:
        cmd.extend(["--cov=app", "--cov-report=term-missing"])
    
    # Add specific test file if provided
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        cmd.append(sys.argv[1])
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Tests failed with return code: {e.returncode}")
        return e.returncode
    except FileNotFoundError:
        print("pytest not found. Please install it with: pip install pytest pytest-cov")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())