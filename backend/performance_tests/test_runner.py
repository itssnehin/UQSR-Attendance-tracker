#!/usr/bin/env python3
"""
Test runner for performance and load testing scenarios
"""

import subprocess
import sys
import time
import requests
from pathlib import Path


def wait_for_server(url, timeout=60):
    """Wait for server to be ready"""
    print(f"Waiting for server at {url}...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/docs")
            if response.status_code == 200:
                print(f"Server is ready at {url}")
                return True
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    
    print(f"Server at {url} did not start within {timeout} seconds")
    return False


def run_load_test(scenario="basic", users=10, spawn_rate=2, duration="60s"):
    """Run load test with specified parameters"""
    
    backend_url = "http://localhost:8000"
    
    # Check if server is running
    if not wait_for_server(backend_url, timeout=30):
        print("Backend server is not running. Please start it first.")
        return False
    
    # Determine which user class to use
    user_classes = {
        "basic": "RunnerUser",
        "admin": "AdminUser", 
        "qr": "QRCodeUser",
        "peak": "PeakRegistrationScenario",
        "websocket": "WebSocketUser"
    }
    
    user_class = user_classes.get(scenario, "RunnerUser")
    
    # Build locust command
    cmd = [
        "locust",
        "-f", "locustfile.py",
        "--host", backend_url,
        "--users", str(users),
        "--spawn-rate", str(spawn_rate),
        "--run-time", duration,
        "--headless",
        "--html", f"load_test_report_{scenario}_{users}users.html",
        user_class
    ]
    
    print(f"Running load test: {scenario} scenario with {users} users")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        # Run in the performance_tests directory
        result = subprocess.run(cmd, cwd=Path(__file__).parent, capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"Load test completed successfully. Report saved as load_test_report_{scenario}_{users}users.html")
            return True
        else:
            print(f"Load test failed with return code {result.returncode}")
            return False
            
    except FileNotFoundError:
        print("Locust not found. Please install it with: pip install locust")
        return False
    except Exception as e:
        print(f"Error running load test: {e}")
        return False


def run_peak_scenario():
    """Run the peak usage scenario (100 concurrent users)"""
    print("Running peak usage scenario...")
    print("This simulates the first day of semester with 100 concurrent registrations")
    
    return run_load_test(
        scenario="peak",
        users=100,
        spawn_rate=10,
        duration="300s"  # 5 minutes
    )


def run_stress_test():
    """Run stress test to find breaking point"""
    print("Running stress test to find system limits...")
    
    # Gradually increase load
    user_counts = [10, 25, 50, 75, 100, 150, 200]
    
    for users in user_counts:
        print(f"\nTesting with {users} users...")
        success = run_load_test(
            scenario="basic",
            users=users,
            spawn_rate=5,
            duration="120s"
        )
        
        if not success:
            print(f"System failed at {users} users")
            break
        
        # Brief pause between tests
        time.sleep(10)


def run_endurance_test():
    """Run endurance test for extended period"""
    print("Running endurance test...")
    print("This tests system stability over extended period")
    
    return run_load_test(
        scenario="basic",
        users=50,
        spawn_rate=5,
        duration="1800s"  # 30 minutes
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_runner.py <scenario>")
        print("Scenarios:")
        print("  basic     - Basic load test with runner registrations")
        print("  admin     - Admin dashboard load test")
        print("  qr        - QR code generation load test")
        print("  peak      - Peak usage scenario (100 users)")
        print("  stress    - Stress test to find limits")
        print("  endurance - Long-running stability test")
        sys.exit(1)
    
    scenario = sys.argv[1]
    
    if scenario == "peak":
        success = run_peak_scenario()
    elif scenario == "stress":
        success = run_stress_test()
    elif scenario == "endurance":
        success = run_endurance_test()
    else:
        # Custom parameters if provided
        users = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        duration = sys.argv[3] if len(sys.argv) > 3 else "60s"
        success = run_load_test(scenario, users=users, duration=duration)
    
    sys.exit(0 if success else 1)