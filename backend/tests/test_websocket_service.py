"""
Integration tests for WebSocket functionality
"""
import pytest
import asyncio
import socketio
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, date
import json

from app.main import app
from app.services.websocket_service import WebSocketService, websocket_service
from app.services.registration_service import RegistrationService
from app.models.run import Run
from app.models.attendance import Attendance
from app.schemas import RegistrationRequest
from .conftest import test_engine


class TestWebSocketService:
    """Test WebSocket service functionality"""
    
    @pytest.fixture
    def ws_service(self):
        """Create a fresh WebSocket service for testing"""
        return WebSocketService()
    
    @pytest.fixture
    def mock_client_data(self):
        """Mock client connection data"""
        return {
            'session_id': 'test-session-123',
            'client_type': 'admin'
        }
    
    def test_websocket_service_initialization(self, ws_service):
        """Test WebSocket service initializes correctly"""
        assert ws_service.sio is not None
        assert ws_service.connected_clients == {}
        assert ws_service.room_sessions == {}
    
    def test_get_connection_stats_empty(self, ws_service):
        """Test connection stats when no clients connected"""
        stats = ws_service.get_connection_stats()
        
        assert stats['total_connected_clients'] == 0
        assert stats['active_sessions'] == 0
        assert stats['session_client_counts'] == {}
        assert 'timestamp' in stats
    
    def test_get_connection_stats_with_clients(self, ws_service):
        """Test connection stats with mock clients"""
        # Mock some connected clients
        ws_service.connected_clients = {
            'client1': {'session_id': 'session1', 'client_type': 'admin'},
            'client2': {'session_id': 'session1', 'client_type': 'runner'},
            'client3': {'session_id': 'session2', 'client_type': 'admin'}
        }
        ws_service.room_sessions = {
            'session1': ['client1', 'client2'],
            'session2': ['client3']
        }
        
        stats = ws_service.get_connection_stats()
        
        assert stats['total_connected_clients'] == 3
        assert stats['active_sessions'] == 2
        assert stats['session_client_counts']['session1'] == 2
        assert stats['session_client_counts']['session2'] == 1
    
    @pytest.mark.asyncio
    async def test_broadcast_attendance_update(self, ws_service):
        """Test broadcasting attendance updates"""
        # Mock room sessions
        ws_service.room_sessions = {'test-session': ['client1', 'client2']}
        
        attendance_data = {
            'runner_name': 'Test Runner',
            'current_count': 5,
            'registered_at': datetime.utcnow().isoformat()
        }
        
        # This should not raise an exception
        await ws_service.broadcast_attendance_update('test-session', attendance_data)
    
    @pytest.mark.asyncio
    async def test_broadcast_registration_success(self, ws_service):
        """Test broadcasting registration success"""
        # Mock room sessions
        ws_service.room_sessions = {'test-session': ['client1']}
        
        registration_data = {
            'runner_name': 'Test Runner',
            'current_count': 3,
            'message': 'Registration successful!'
        }
        
        # This should not raise an exception
        await ws_service.broadcast_registration_success('test-session', registration_data)
    
    @pytest.mark.asyncio
    async def test_send_error_to_client(self, ws_service):
        """Test sending error to specific client"""
        # This should not raise an exception
        await ws_service.send_error_to_client('client1', 'Test error message')


class TestWebSocketIntegration:
    """Test WebSocket integration with FastAPI and registration service"""
    
    def test_websocket_status_endpoint(self, client):
        """Test WebSocket status endpoint"""
        response = client.get("/api/websocket/status")
        assert response.status_code == 200
        
        data = response.json()
        assert 'total_connected_clients' in data
        assert 'active_sessions' in data
        assert 'session_client_counts' in data
        assert 'timestamp' in data
    
    def test_registration_with_websocket_integration(self, test_session):
        """Test registration service with WebSocket integration"""
        # Create a test run
        run = Run(
            date=date.today(),
            session_id='test-session-integration',
            is_active=True
        )
        test_session.add(run)
        test_session.commit()
        test_session.refresh(run)
        
        # Create registration service with WebSocket service
        registration_service = RegistrationService(test_session, websocket_service)
        
        # Create registration request
        registration = RegistrationRequest(
            session_id=run.session_id,
            runner_name='Test Runner WebSocket'
        )
        
        # Register attendance
        result = registration_service.register_attendance(registration)
        
        # Verify registration was successful
        assert result.success is True
        assert result.current_count == 1
        assert result.runner_name == 'Test Runner WebSocket'
        assert 'Registration successful!' in result.message
        
        # Verify attendance was recorded in database
        attendance = test_session.query(Attendance).filter(
            Attendance.run_id == run.id,
            Attendance.runner_name == 'Test Runner WebSocket'
        ).first()
        
        assert attendance is not None
        assert attendance.runner_name == 'Test Runner WebSocket'
    
    def test_duplicate_registration_with_websocket(self, test_session):
        """Test duplicate registration prevention with WebSocket integration"""
        # Create a test run
        run = Run(
            date=date.today(),
            session_id='test-session-duplicate',
            is_active=True
        )
        test_session.add(run)
        test_session.commit()
        test_session.refresh(run)
        
        registration_service = RegistrationService(test_session, websocket_service)
        
        registration = RegistrationRequest(
            session_id=run.session_id,
            runner_name='Duplicate Test Runner'
        )
        
        # First registration should succeed
        result1 = registration_service.register_attendance(registration)
        assert result1.success is True
        assert result1.current_count == 1
        
        # Second registration should fail
        result2 = registration_service.register_attendance(registration)
        assert result2.success is False
        assert 'already registered' in result2.message.lower()
        assert result2.current_count == 1  # Count should remain the same
    
    def test_registration_with_invalid_session(self, test_session):
        """Test registration with invalid session ID"""
        registration_service = RegistrationService(test_session, websocket_service)
        
        registration = RegistrationRequest(
            session_id='invalid-session-id',
            runner_name='Test Runner Invalid'
        )
        
        result = registration_service.register_attendance(registration)
        
        assert result.success is False
        assert 'invalid session' in result.message.lower()
        assert result.current_count == 0
    



class TestWebSocketErrorHandling:
    """Test WebSocket error handling and connection management"""
    
    @pytest.fixture
    def ws_service(self):
        """Create WebSocket service for error testing"""
        return WebSocketService()
    
    @pytest.mark.asyncio
    async def test_broadcast_with_no_clients(self, ws_service):
        """Test broadcasting when no clients are connected"""
        attendance_data = {'runner_name': 'Test', 'current_count': 1}
        
        # Should not raise exception even with no clients
        await ws_service.broadcast_attendance_update('empty-session', attendance_data)
        await ws_service.broadcast_registration_success('empty-session', attendance_data)
    
    @pytest.mark.asyncio
    async def test_error_handling_in_broadcast(self, ws_service):
        """Test error handling during broadcast operations"""
        # Mock a problematic session
        ws_service.room_sessions = {'problem-session': ['nonexistent-client']}
        
        attendance_data = {'runner_name': 'Test', 'current_count': 1}
        
        # Should handle errors gracefully
        await ws_service.broadcast_attendance_update('problem-session', attendance_data)
    
    def test_connection_stats_error_handling(self, ws_service):
        """Test connection stats error handling"""
        # Corrupt the data structures to trigger error handling
        ws_service.connected_clients = None
        
        stats = ws_service.get_connection_stats()
        
        # Should return error information instead of crashing
        assert 'error' in stats or stats['total_connected_clients'] == 0


class TestWebSocketPerformance:
    """Test WebSocket performance under load conditions"""
    
    @pytest.fixture
    def ws_service(self):
        """Create WebSocket service for performance testing"""
        return WebSocketService()
    
    def test_multiple_client_tracking(self, ws_service):
        """Test tracking multiple clients (simulating peak load)"""
        # Simulate 100 concurrent clients (requirement 4.1)
        for i in range(100):
            client_id = f'client_{i}'
            session_id = f'session_{i % 10}'  # 10 different sessions
            
            ws_service.connected_clients[client_id] = {
                'session_id': session_id,
                'client_type': 'runner',
                'connected_at': datetime.utcnow().isoformat()
            }
            
            if session_id not in ws_service.room_sessions:
                ws_service.room_sessions[session_id] = []
            ws_service.room_sessions[session_id].append(client_id)
        
        # Verify tracking
        stats = ws_service.get_connection_stats()
        assert stats['total_connected_clients'] == 100
        assert stats['active_sessions'] == 10
        
        # Each session should have 10 clients
        for session_id, count in stats['session_client_counts'].items():
            assert count == 10
    
    @pytest.mark.asyncio
    async def test_concurrent_broadcasts(self, ws_service):
        """Test concurrent broadcast operations"""
        # Set up multiple sessions with clients
        for i in range(5):
            session_id = f'concurrent_session_{i}'
            ws_service.room_sessions[session_id] = [f'client_{i}_1', f'client_{i}_2']
        
        # Create multiple broadcast tasks
        tasks = []
        for i in range(5):
            session_id = f'concurrent_session_{i}'
            attendance_data = {
                'runner_name': f'Runner {i}',
                'current_count': i + 1,
                'registered_at': datetime.utcnow().isoformat()
            }
            
            task = ws_service.broadcast_attendance_update(session_id, attendance_data)
            tasks.append(task)
        
        # Execute all broadcasts concurrently
        await asyncio.gather(*tasks)
        
        # If we get here without exceptions, concurrent broadcasts work


class TestWebSocketEndToEnd:
    """End-to-end tests for WebSocket functionality"""
    
    def test_full_registration_flow_with_websocket(self, client, test_session):
        """Test complete registration flow with WebSocket integration"""
        # Create a test run
        run = Run(
            date=date.today(),
            session_id='e2e-test-session',
            is_active=True
        )
        test_session.add(run)
        test_session.commit()
        test_session.refresh(run)
        
        # Test registration endpoint
        registration_data = {
            'session_id': run.session_id,
            'runner_name': 'E2E Test Runner'
        }
        
        response = client.post('/api/register', json=registration_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result['success'] is True
        assert result['current_count'] == 1
        assert result['runner_name'] == 'E2E Test Runner'
        
        # Test WebSocket status endpoint
        ws_status = client.get('/api/websocket/status')
        assert ws_status.status_code == 200
        
        # Test today's attendance endpoint
        today_response = client.get('/api/attendance/today')
        assert today_response.status_code == 200
        
        today_data = today_response.json()
        assert today_data['success'] is True
        assert today_data['count'] == 1
        assert today_data['has_run_today'] is True
    
    def test_websocket_status_after_multiple_registrations(self, client, test_session):
        """Test WebSocket status tracking after multiple registrations"""
        # Create a test run
        run = Run(
            date=date.today(),
            session_id='e2e-multi-test-session',
            is_active=True
        )
        test_session.add(run)
        test_session.commit()
        test_session.refresh(run)
        
        # Register multiple runners
        runners = ['Runner A', 'Runner B', 'Runner C']
        
        for runner_name in runners:
            registration_data = {
                'session_id': run.session_id,
                'runner_name': runner_name
            }
            
            response = client.post('/api/register', json=registration_data)
            assert response.status_code == 200
        
        # Check final attendance count
        today_response = client.get('/api/attendance/today')
        today_data = today_response.json()
        assert today_data['count'] == 3
        
        # Check WebSocket status
        ws_status = client.get('/api/websocket/status')
        assert ws_status.status_code == 200
        
        ws_data = ws_status.json()
        assert 'total_connected_clients' in ws_data
        assert 'active_sessions' in ws_data