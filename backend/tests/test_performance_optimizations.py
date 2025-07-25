"""
Performance optimization tests for Runner Attendance Tracker
Tests system performance under various load conditions and validates optimization measures
"""

import pytest
import asyncio
import time
import concurrent.futures
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch

from app.main import app
from app.database.connection import get_db
from app.models.database import Run, Attendance, CalendarConfig
from app.services.cache_service import CacheService
from tests.conftest import override_get_db


class TestPerformanceOptimizations:
    """Test performance optimizations and system limits"""
    
    @pytest.fixture
    def client(self):
        """Create test client with database override"""
        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as client:
            yield client
        app.dependency_overrides.clear()
    
    @pytest.fixture
    def db_session(self):
        """Create test database session"""
        db = next(override_get_db())
        yield db
        db.close()
    
    @pytest.fixture
    def setup_run_day(self, db_session: Session):
        """Set up a run day for testing"""
        today = date.today()
        
        # Create calendar config
        calendar_config = CalendarConfig(date=today, has_run=True)
        db_session.add(calendar_config)
        
        # Create run
        run = Run(
            date=today,
            session_id=f"perf-test-session-{today.isoformat()}",
            is_active=True
        )
        db_session.add(run)
        db_session.commit()
        
        return run
    
    def test_concurrent_registration_performance(self, client, setup_run_day):
        """Test system performance with concurrent registrations"""
        run = setup_run_day
        
        def register_runner(runner_id):
            """Register a single runner"""
            start_time = time.time()
            response = client.post("/api/register", json={
                "session_id": run.session_id,
                "runner_name": f"Concurrent Runner {runner_id}"
            })
            end_time = time.time()
            
            return {
                "success": response.status_code == 200,
                "response_time": end_time - start_time,
                "status_code": response.status_code
            }
        
        # Test with 50 concurrent registrations
        num_concurrent = 50
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(register_runner, i) 
                for i in range(num_concurrent)
            ]
            
            results = [
                future.result() 
                for future in concurrent.futures.as_completed(futures)
            ]
        
        # Analyze results
        successful_registrations = [r for r in results if r["success"]]
        response_times = [r["response_time"] for r in results]
        
        # Performance requirements
        assert len(successful_registrations) >= num_concurrent * 0.95  # 95% success rate
        assert max(response_times) < 5.0  # Max 5 seconds per requirement
        assert sum(response_times) / len(response_times) < 2.0  # Average < 2 seconds
    
    def test_database_query_performance(self, client, db_session, setup_run_day):
        """Test database query performance with large datasets"""
        run = setup_run_day
        
        # Create large dataset
        attendances = []
        for i in range(1000):
            attendance = Attendance(
                run_id=run.id,
                runner_name=f"Performance Test Runner {i}",
                registered_at=datetime.utcnow()
            )
            attendances.append(attendance)
        
        db_session.add_all(attendances)
        db_session.commit()
        
        # Test query performance
        start_time = time.time()
        response = client.get("/api/attendance/today")
        end_time = time.time()
        
        query_time = end_time - start_time
        
        assert response.status_code == 200
        assert query_time < 1.0  # Should be fast even with 1000 records
        
        data = response.json()
        assert data["count"] == 1000
    
    def test_cache_performance(self, client, setup_run_day):
        """Test caching performance improvements"""
        run = setup_run_day
        
        # First request (cache miss)
        start_time = time.time()
        response1 = client.get("/api/attendance/today")
        first_request_time = time.time() - start_time
        
        assert response1.status_code == 200
        
        # Second request (cache hit)
        start_time = time.time()
        response2 = client.get("/api/attendance/today")
        second_request_time = time.time() - start_time
        
        assert response2.status_code == 200
        assert response1.json() == response2.json()
        
        # Cache hit should be significantly faster
        # Allow some variance for test environment
        assert second_request_time < first_request_time * 0.8
    
    def test_rate_limiting_effectiveness(self, client, setup_run_day):
        """Test rate limiting prevents abuse"""
        run = setup_run_day
        
        # Make rapid requests from same client
        responses = []
        
        for i in range(100):  # Rapid fire requests
            response = client.post("/api/register", json={
                "session_id": run.session_id,
                "runner_name": f"Rate Limit Test {i}"
            })
            responses.append(response.status_code)
            
            if i < 10:
                time.sleep(0.01)  # Small delay for first few requests
        
        # Should have some rate limited responses (429)
        rate_limited_count = responses.count(429)
        successful_count = responses.count(200)
        duplicate_count = responses.count(409)
        
        # Rate limiting should kick in
        assert rate_limited_count > 0, "Rate limiting not working"
        assert successful_count > 0, "No successful requests"
        
        # Total should not exceed reasonable limits
        assert successful_count + duplicate_count < 50, "Too many requests allowed"
    
    def test_memory_usage_under_load(self, client, setup_run_day):
        """Test memory usage remains stable under load"""
        run = setup_run_day
        
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Generate load
        for batch in range(10):  # 10 batches of requests
            for i in range(20):  # 20 requests per batch
                client.post("/api/register", json={
                    "session_id": run.session_id,
                    "runner_name": f"Memory Test Batch {batch} Runner {i}"
                })
            
            # Check memory after each batch
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = current_memory - initial_memory
            
            # Memory should not grow excessively (allow 50MB increase)
            assert memory_increase < 50, f"Memory usage increased by {memory_increase:.2f}MB"
    
    def test_database_connection_pooling(self, client, setup_run_day):
        """Test database connection pooling efficiency"""
        run = setup_run_day
        
        def make_request():
            return client.get("/api/attendance/today")
        
        # Make many concurrent requests to test connection pooling
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            futures = [executor.submit(make_request) for _ in range(100)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        success_count = sum(1 for r in results if r.status_code == 200)
        assert success_count == 100, f"Only {success_count}/100 requests succeeded"
    
    def test_qr_code_generation_performance(self, client, setup_run_day):
        """Test QR code generation performance"""
        run = setup_run_day
        
        # Test single QR generation time
        start_time = time.time()
        response = client.get(f"/api/qr/{run.session_id}")
        single_generation_time = time.time() - start_time
        
        assert response.status_code == 200
        assert single_generation_time < 1.0, f"QR generation too slow: {single_generation_time:.2f}s"
        
        # Test concurrent QR generation
        def generate_qr():
            start = time.time()
            resp = client.get(f"/api/qr/{run.session_id}")
            return time.time() - start, resp.status_code == 200
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(generate_qr) for _ in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        times, successes = zip(*results)
        
        # All should succeed and be reasonably fast
        assert all(successes), "Some QR generations failed"
        assert max(times) < 2.0, f"Slowest QR generation: {max(times):.2f}s"
        assert sum(times) / len(times) < 1.0, f"Average QR generation: {sum(times)/len(times):.2f}s"
    
    def test_websocket_performance_under_load(self, client, setup_run_day):
        """Test WebSocket performance with many connections"""
        # This is a simplified test - full WebSocket testing would require
        # actual WebSocket client connections
        
        run = setup_run_day
        
        # Simulate load by making many registration requests
        # which should trigger WebSocket broadcasts
        
        start_time = time.time()
        
        for i in range(50):
            response = client.post("/api/register", json={
                "session_id": run.session_id,
                "runner_name": f"WebSocket Load Test {i}"
            })
            # Allow duplicates for this test
            assert response.status_code in [200, 409]
        
        total_time = time.time() - start_time
        
        # Should handle 50 registrations (with WebSocket broadcasts) quickly
        assert total_time < 10.0, f"WebSocket load test took too long: {total_time:.2f}s"
    
    def test_data_export_performance(self, client, db_session, setup_run_day):
        """Test data export performance with large datasets"""
        run = setup_run_day
        
        # Create large dataset for export
        attendances = []
        for i in range(500):
            attendance = Attendance(
                run_id=run.id,
                runner_name=f"Export Test Runner {i}",
                registered_at=datetime.utcnow() - timedelta(minutes=i)
            )
            attendances.append(attendance)
        
        db_session.add_all(attendances)
        db_session.commit()
        
        # Test export performance
        start_time = time.time()
        response = client.get(f"/api/attendance/export?start_date={run.date}&end_date={run.date}")
        export_time = time.time() - start_time
        
        assert response.status_code == 200
        assert export_time < 5.0, f"Export took too long: {export_time:.2f}s"
        
        # Verify export content
        assert "text/csv" in response.headers["content-type"]
        csv_content = response.content.decode()
        lines = csv_content.strip().split('\n')
        
        # Should have header + 500 data rows
        assert len(lines) >= 500, f"Expected 500+ lines, got {len(lines)}"
    
    def test_system_recovery_after_overload(self, client, setup_run_day):
        """Test system recovery after being overloaded"""
        run = setup_run_day
        
        # Overload the system
        overload_responses = []
        for i in range(200):  # Heavy load
            response = client.post("/api/register", json={
                "session_id": run.session_id,
                "runner_name": f"Overload Test {i}"
            })
            overload_responses.append(response.status_code)
        
        # Wait for system to recover
        time.sleep(2)
        
        # Test normal operation after overload
        recovery_responses = []
        for i in range(10):
            response = client.get("/api/attendance/today")
            recovery_responses.append(response.status_code)
            time.sleep(0.1)
        
        # System should recover and handle normal requests
        successful_recovery = recovery_responses.count(200)
        assert successful_recovery >= 8, f"System didn't recover properly: {successful_recovery}/10 successful"
    
    def test_database_optimization_indexes(self, db_session, setup_run_day):
        """Test that database indexes are working effectively"""
        run = setup_run_day
        
        # Create test data
        attendances = []
        for i in range(1000):
            attendance = Attendance(
                run_id=run.id,
                runner_name=f"Index Test Runner {i}",
                registered_at=datetime.utcnow() - timedelta(minutes=i)
            )
            attendances.append(attendance)
        
        db_session.add_all(attendances)
        db_session.commit()
        
        # Test indexed queries
        start_time = time.time()
        
        # Query by run_id (should be indexed)
        result = db_session.query(Attendance).filter(Attendance.run_id == run.id).count()
        
        query_time = time.time() - start_time
        
        assert result == 1000
        assert query_time < 0.5, f"Indexed query too slow: {query_time:.3f}s"
        
        # Test date-based query (should be indexed)
        start_time = time.time()
        
        recent_attendances = db_session.query(Attendance).filter(
            Attendance.registered_at >= datetime.utcnow() - timedelta(hours=1)
        ).count()
        
        date_query_time = time.time() - start_time
        
        assert recent_attendances >= 0
        assert date_query_time < 0.5, f"Date query too slow: {date_query_time:.3f}s"