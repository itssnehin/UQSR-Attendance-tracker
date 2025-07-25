"""
Load testing scenarios for Runner Attendance Tracker
Simulates peak usage with up to 100 concurrent users
"""

import json
import random
import string
from datetime import datetime, date
from locust import HttpUser, task, between, events
from locust.exception import RescheduleTask


class RunnerUser(HttpUser):
    """Simulates a runner registering for attendance"""
    wait_time = between(1, 3)
    
    def on_start(self):
        """Set up test data when user starts"""
        self.session_id = None
        self.runner_name = f"TestRunner_{random.randint(1000, 9999)}"
        
        # Ensure today is configured as a run day
        today = date.today().isoformat()
        response = self.client.post("/api/calendar/configure", json={
            "date": today,
            "has_run": True
        })
        
        if response.status_code == 200:
            # Get session ID for today
            today_response = self.client.get("/api/calendar/today")
            if today_response.status_code == 200:
                data = today_response.json()
                self.session_id = data.get("session_id")
    
    @task(10)
    def register_attendance(self):
        """Register attendance - main user action"""
        if not self.session_id:
            raise RescheduleTask()
            
        # Generate unique runner name for each registration attempt
        unique_name = f"{self.runner_name}_{random.randint(1, 10000)}"
        
        with self.client.post("/api/register", json={
            "session_id": self.session_id,
            "runner_name": unique_name
        }, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 409:  # Duplicate registration
                response.success()  # This is expected behavior
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
    
    @task(2)
    def check_attendance_count(self):
        """Check current attendance count"""
        with self.client.get("/api/attendance/today", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to get attendance count: {response.status_code}")


class AdminUser(HttpUser):
    """Simulates an admin user monitoring the system"""
    wait_time = between(2, 5)
    
    @task(5)
    def view_attendance_dashboard(self):
        """View current attendance"""
        self.client.get("/api/attendance/today")
    
    @task(3)
    def check_calendar_config(self):
        """Check calendar configuration"""
        self.client.get("/api/calendar")
    
    @task(2)
    def view_attendance_history(self):
        """View attendance history"""
        # Get last 7 days of data
        end_date = date.today().isoformat()
        start_date = date.today().replace(day=1).isoformat()  # First day of month
        
        self.client.get(f"/api/attendance/history?start_date={start_date}&end_date={end_date}")
    
    @task(1)
    def export_attendance_data(self):
        """Export attendance data"""
        end_date = date.today().isoformat()
        start_date = date.today().replace(day=1).isoformat()
        
        with self.client.get(f"/api/attendance/export?start_date={start_date}&end_date={end_date}", 
                           catch_response=True) as response:
            if response.status_code == 200 and 'text/csv' in response.headers.get('content-type', ''):
                response.success()
            else:
                response.failure(f"Export failed: {response.status_code}")


class QRCodeUser(HttpUser):
    """Simulates users accessing QR codes"""
    wait_time = between(1, 2)
    
    def on_start(self):
        """Set up session ID"""
        today = date.today().isoformat()
        response = self.client.post("/api/calendar/configure", json={
            "date": today,
            "has_run": True
        })
        
        if response.status_code == 200:
            today_response = self.client.get("/api/calendar/today")
            if today_response.status_code == 200:
                data = today_response.json()
                self.session_id = data.get("session_id")
    
    @task(8)
    def generate_qr_code(self):
        """Generate QR code for session"""
        if self.session_id:
            self.client.get(f"/api/qr/{self.session_id}")
    
    @task(2)
    def validate_qr_token(self):
        """Validate QR code token"""
        if self.session_id:
            # This would normally be a token from the QR code
            # For testing, we'll use the session_id as a mock token
            self.client.get(f"/api/qr/validate/{self.session_id}")


# Custom load test scenarios
class PeakRegistrationScenario(HttpUser):
    """Simulates peak registration scenario - first day of semester"""
    wait_time = between(0.5, 1.5)  # Faster registration attempts
    
    def on_start(self):
        """Set up for peak scenario"""
        self.session_id = None
        self.runner_name = f"PeakUser_{random.randint(10000, 99999)}"
        
        # Ensure today is configured
        today = date.today().isoformat()
        response = self.client.post("/api/calendar/configure", json={
            "date": today,
            "has_run": True
        })
        
        if response.status_code == 200:
            today_response = self.client.get("/api/calendar/today")
            if today_response.status_code == 200:
                data = today_response.json()
                self.session_id = data.get("session_id")
    
    @task
    def rapid_registration(self):
        """Rapid registration attempts"""
        if not self.session_id:
            raise RescheduleTask()
            
        unique_name = f"{self.runner_name}_{random.randint(1, 100000)}"
        
        start_time = datetime.now()
        
        with self.client.post("/api/register", json={
            "session_id": self.session_id,
            "runner_name": unique_name
        }, catch_response=True) as response:
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            # Requirement: Registration should complete within 5 seconds under peak load
            if response_time > 5.0:
                response.failure(f"Registration took too long: {response_time:.2f}s")
            elif response.status_code == 200:
                response.success()
            elif response.status_code == 409:  # Duplicate
                response.success()
            else:
                response.failure(f"Registration failed: {response.status_code}")


# Event handlers for custom metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize test metrics"""
    print("Starting load test for Runner Attendance Tracker")
    print(f"Target URL: {environment.host}")
    print("Simulating peak usage scenario with up to 100 concurrent users")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print test summary"""
    print("\nLoad test completed")
    print("Key metrics to verify:")
    print("- Registration response time < 5 seconds under peak load")
    print("- System handles 100 concurrent users without failures")
    print("- Real-time updates continue to function under load")
    print("- Database integrity maintained during concurrent access")


# WebSocket load testing (requires additional setup)
class WebSocketUser(HttpUser):
    """Simulates WebSocket connections for real-time updates"""
    
    def on_start(self):
        """Connect to WebSocket"""
        # Note: This is a simplified example
        # Full WebSocket testing would require python-socketio client
        pass
    
    @task
    def maintain_connection(self):
        """Maintain WebSocket connection"""
        # Simulate keeping connection alive
        self.client.get("/api/attendance/today")  # Fallback to HTTP polling