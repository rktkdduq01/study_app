"""
Run all tests with a summary report
"""
import subprocess
import sys
import os
import json
from datetime import datetime


def run_all_tests():
    """Run all test suites and generate a report"""
    print("=" * 80)
    print("Running All Tests")
    print(f"Started at: {datetime.now()}")
    print("=" * 80)
    
    # Test categories
    test_suites = [
        {
            "name": "Unit Tests - Security",
            "file": "tests/test_security.py",
            "markers": "unit"
        },
        {
            "name": "Unit Tests - Authentication",
            "file": "tests/test_auth.py",
            "markers": "unit"
        },
        {
            "name": "Unit Tests - Error Handling",
            "file": "tests/test_error_handling.py",
            "markers": "unit"
        },
        {
            "name": "Unit Tests - Gamification",
            "file": "tests/test_gamification.py",
            "markers": "unit"
        },
        {
            "name": "Integration Tests - Authentication",
            "file": "tests/test_integration_auth.py",
            "markers": "integration"
        },
        {
            "name": "Integration Tests - Gamification",
            "file": "tests/test_integration_gamification.py",
            "markers": "integration"
        }
    ]
    
    results = []
    total_passed = 0
    total_failed = 0
    total_skipped = 0
    
    for suite in test_suites:
        print(f"\n{'=' * 80}")
        print(f"Running: {suite['name']}")
        print(f"File: {suite['file']}")
        print("=" * 80)
        
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            suite["file"],
            "-v",
            "--tb=short",
            "--no-header"
        ]
        
        if suite.get("markers"):
            cmd.extend(["-m", suite["markers"]])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            # Parse output for results
            output_lines = result.stdout.split('\n')
            suite_result = {
                "name": suite["name"],
                "file": suite["file"],
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "errors": []
            }
            
            for line in output_lines:
                if " PASSED" in line:
                    suite_result["passed"] += 1
                    total_passed += 1
                elif " FAILED" in line:
                    suite_result["failed"] += 1
                    total_failed += 1
                elif " SKIPPED" in line:
                    suite_result["skipped"] += 1
                    total_skipped += 1
                elif " ERROR" in line:
                    suite_result["errors"].append(line.strip())
            
            results.append(suite_result)
            
            # Print summary for this suite
            print(f"\nResults for {suite['name']}:")
            print(f"  Passed:  {suite_result['passed']}")
            print(f"  Failed:  {suite_result['failed']}")
            print(f"  Skipped: {suite_result['skipped']}")
            
            if suite_result["errors"]:
                print(f"  Errors:")
                for error in suite_result["errors"]:
                    print(f"    - {error}")
            
        except Exception as e:
            print(f"Error running {suite['name']}: {e}")
            results.append({
                "name": suite["name"],
                "file": suite["file"],
                "error": str(e)
            })
    
    # Generate final report
    print("\n" + "=" * 80)
    print("FINAL TEST REPORT")
    print("=" * 80)
    print(f"Total Tests Run: {total_passed + total_failed + total_skipped}")
    print(f"Total Passed:    {total_passed}")
    print(f"Total Failed:    {total_failed}")
    print(f"Total Skipped:   {total_skipped}")
    print(f"Success Rate:    {total_passed / (total_passed + total_failed) * 100:.1f}%" if (total_passed + total_failed) > 0 else "N/A")
    
    # Detailed results by suite
    print("\nDetailed Results by Suite:")
    for result in results:
        if "error" in result:
            print(f"\n{result['name']}: ERROR - {result['error']}")
        else:
            print(f"\n{result['name']}:")
            print(f"  File: {result['file']}")
            print(f"  Passed: {result['passed']}, Failed: {result['failed']}, Skipped: {result['skipped']}")
    
    # Save report to file
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_tests": total_passed + total_failed + total_skipped,
            "passed": total_passed,
            "failed": total_failed,
            "skipped": total_skipped,
            "success_rate": total_passed / (total_passed + total_failed) * 100 if (total_passed + total_failed) > 0 else 0
        },
        "suites": results
    }
    
    with open("test_report.json", "w") as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\nDetailed report saved to: test_report.json")
    print(f"Completed at: {datetime.now()}")
    
    # Return exit code based on failures
    return 1 if total_failed > 0 else 0


if __name__ == "__main__":
    sys.exit(run_all_tests())