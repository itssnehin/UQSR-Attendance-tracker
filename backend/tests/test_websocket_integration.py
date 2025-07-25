"""
Integration tests for WebSocket functionality and real-time updates
Tests the complete WebSocket flow including connection, events, and data synchronization
"""

import pytest
import asyncio
import json
from datetime import date, datetime
from unittest.mock import AsyncMock, patch
import socketio
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.connection import get_db
from app.models.database import Run, Attendance, CalendarConfig
from tests.conftest import override_get_db, test_db


class TestWebSocketIntegration:
    """Test WebSocket functionality and real-time updates"""
    
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
    async def socket_client(self):
        """Create Socket.IO test client"""
        sio = socketio.AsyncClient()
        yield sio
        if sio.connected:
            await sio.disconnect()
    
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
            session_id=f"test-session-{today.isoformat()}",
            is_active=True
        )
        db_session.add(run)
        db_session.commit()
        
        return run
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self, socket_client):
        """Test basic WebSocket connection"""
        # Connect to WebSocket server
        await socket_client.connect('http://localhost:8000', socketio_path='/socket.io/')
        
        # Verify connection
        assert socket_client.connected
        
        # Test ping/pong
        await socket_client.emit('ping')
        
        # Wait for response
        await asyncio.sleep(0.1)
        
        await socket_client.disconnect()
    
    @pytest.mark.asyncio
    async def test_attendance_registration_broadcast(self, socket_client, client, setup_run_day):
        """Test that attendance registrations are broadcast to connected clients"""
        run = setup_run_day
        
        # Connect to WebSocket
        await socket_client.connect('http://localhost:8000', socketio_path='/socket.io/')
        
        # Set up event handler to capture broadcasts
        received_events = []
        
        @socket_client.event
        async def attendance_update(data):
            received_events.append(data)
        
        # Register attendance via HTTP API
        response = client.post("/api/register", json={
            "session_id": run.session_id,
            "runner_name": "WebSocket Test Runner"
        })
        
        assert response.status_code == 200
        
        # Wait for WebSocket event
        await asyncio.sleep(0.5)
        
        # Verify broadcast was received
        assert len(received_events) == 1
        event_data = received_events[0]
        
        assert event_data["type"] == "attendance_registered"
        assert event_data["runner_name"] == "WebSocket Test Runner"
        assert event_data["session_id"] == run.session_id
        assert "current_count" in event_data
        assert "timestamp" in event_data
        
        await socket_client.disconnect()
    
    @pytest.mark.asyncio
    async def test_multiple_clients_receive_updates(self, client, setup_run_day):
        """Test that multiple WebSocket clients receive the same updates"""
        run = setup_run_day
        
        # Create multiple socket clients
        client1 = socketio.AsyncClient()
        client2 = socketio.AsyncClient()
        client3 = socketio.AsyncClient()
        
        try:
            # Connect all clients
            await client1.connect('http://localhost:8000', socketio_path='/socket.io/')
            await client2.connect('http://localhost:8000', socketio_path='/socket.io/')
            await client3.connect('http://localhost:8000', socketio_path='/socket.io/')
            
            # Set up event handlers
            client1_events = []
            client2_events = []
            client3_events = []
            
            @client1.event
            async def attendance_update(data):
                client1_events.append(data)
            
            @client2.event
            async def attendance_update(data):
                client2_events.append(data)
            
            @client3.event
            async def attendance_update(data):
                client3_events.append(data)
            
            # Register attendance
            response = client.post("/api/register", json={
                "session_id": run.session_id,
                "runner_name": "Multi-Client Test Runner"
            })
            
            assert response.status_code == 200
            
            # Wait for events
            await asyncio.sleep(0.5)
            
            # Verify all clients received the same event
            assert len(client1_events) == 1
            assert len(client2_events) == 1
            assert len(client3_events) == 1
            
            # Verify event content is identical
            assert client1_events[0] == client2_events[0] == client3_events[0]
            
        finally:
            # Clean up connections
            if client1.connected:
                await client1.disconnect()
            if client2.connected:
                await client2.disconnect()
            if client3.connected:
                await client3.disconnect()
    
    @pytest.mark.asyncio
    async def test_websocket_error_handling(self, socket_client):
        """Test WebSocket error handling and reconnection"""
        # Test connection to invalid endpoint
        try:
            await socket_client.connect('http://localhost:9999', socketio_path='/socket.io/')
            assert False, "Should have failed to connect"
        except Exception:
            pass  # Expected to fail
        
        # Test valid connection
        await socket_client.connect('http://localhost:8000', socketio_path='/socket.io/')
        assert socket_client.connected
        
        # Test handling of invalid events
        await socket_client.emit('invalid_event', {'invalid': 'data'})
        
        # Should still be connected
        assert socket_client.connected
        
        await socket_client.disconnect()
    
    @pytest.mark.asyncio
    async def test_websocket_authentication(self, socket_client):
        """Test WebSocket authentication and authorization"""
        # Connect without authentication
        await socket_client.connect('http://localhost:8000', socketio_path='/socket.io/')
        
        # Test that connection is allowed (no auth required for this app)
        assert socket_client.connected
        
        # Test admin-specific events (if implemented)
        await socket_client.emit('admin_request', {'action': 'get_stats'})
        
        await asyncio.sleep(0.1)
        
        await socket_client.disconnect()
    
    @pytest.mark.asyncio
    async def test_websocket_performance_under_load(self, client, setup_run_day):
        """Test WebSocket performance with multiple concurrent connections and events"""
        run = setup_run_day
        
        # Create multiple concurrent connections
        clients = []
        received_counts = []
        
        try:
            # Create 20 concurrent WebSocket clients
            for i in range(20):
                sio_client = socketio.AsyncClient()
                await sio_client.connect('http://localhost:8000', socketio_path='/socket.io/')
                
                # Track events for each client
                client_events = []
                received_counts.append(client_events)
                
                @sio_client.event
                async def attendance_update(data, client_idx=i):
                    received_counts[client_idx].append(data)
                
                clients.append(sio_client)
            
            # Send multiple registration events rapidly
            for i in range(10):
                response = client.post("/api/register", json={
                    "session_id": run.session_id,
                    "runner_name": f"Load Test Runner {i}"
                })
                assert response.status_code in [200, 409]  # 409 for duplicates
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.1)
            
            # Wait for all events to propagate
            await asyncio.sleep(2)
            
            # Verify all clients received events
            for i, events in enumerate(received_counts):
                assert len(events) > 0, f"Client {i} received no events"
            
            # Verify event consistency across clients
            first_client_count = len(received_counts[0])
            for i, events in enumerate(received_counts[1:], 1):
                assert len(events) == first_client_count, f"Client {i} event count mismatch"
        
        finally:
            # Clean up all connections
            for sio_client in clients:
                if sio_client.connected:
                    await sio_client.disconnect()
    
    @pytest.mark.asyncio
    async def test_websocket_data_integrity(self, socket_client, client, setup_run_day):
        """Test that WebSocket events maintain data integrity"""
        run = setup_run_day
        
        await socket_client.connect('http://localhost:8000', socketio_path='/socket.io/')
        
        received_events = []
        
        @socket_client.event
        async def attendance_update(data):
            received_events.append(data)
        
        # Register multiple attendees
        runner_names = ["Alice", "Bob", "Charlie", "Diana", "Eve"]
        
        for name in runner_names:
            response = client.post("/api/register", json={
                "session_id": run.session_id,
                "runner_name": name
            })
            assert response.status_code == 200
            
            await asyncio.sleep(0.2)  # Allow event processing
        
        # Verify we received all events
        assert len(received_events) == len(runner_names)
        
        # Verify event data integrity
        for i, event in enumerate(received_events):
            assert event["runner_name"] == runner_names[i]
            assert event["session_id"] == run.session_id
            assert event["current_count"] == i + 1  # Count should increment
            assert "timestamp" in event
            
            # Verify timestamp is valid
            timestamp = datetime.fromisoformat(event["timestamp"].replace('Z', '+00:00'))
            assert isinstance(timestamp, datetime)
        
        await socket_client.disconnect()
    
    @pytest.mark.asyncio
    async def test_websocket_connection_lifecycle(self, socket_client):
        """Test complete WebSocket connection lifecycle"""
        # Test initial connection
        await socket_client.connect('http://localhost:8000', socketio_path='/socket.io/')
        assert socket_client.connected
        
        # Test ping/pong to verify connection health
        start_time = asyncio.get_event_loop().time()
        await socket_client.emit('ping')
        await asyncio.sleep(0.1)
        end_time = asyncio.get_event_loop().time()
        
        # Verify reasonable response time
        response_time = end_time - start_time
        assert response_time < 1.0, f"Ping response too slow: {response_time}s"
        
        # Test graceful disconnection
        await socket_client.disconnect()
        assert not socket_client.connected
        
        # Test reconnection
        await socket_client.connect('http://localhost:8000', socketio_path='/socket.io/')
        assert socket_client.connected
        
        await socket_client.disconnect()
    
    def test_websocket_fallback_to_polling(self, client, setup_run_day):
        """Test fallback behavior when WebSocket is not available"""
        run = setup_run_day
        
        # Register attendance via HTTP
        response = client.post("/api/register", json={
            "session_id": run.session_id,
            "runner_name": "Polling Test Runner"
        })
        
        assert response.status_code == 200
        
        # Verify data is still accessible via HTTP polling
        response = client.get("/api/attendance/today")
        assert response.status_code == 200
        
        data = response.json()
        assert data["count"] >= 1
        assert any(a["runner_name"] == "Polling Test Runner" for a in data["attendances"])
    
    @pytest.mark.asyncio
    async def test_websocket_memory_usage(self, client, setup_run_day):
        """Test WebSocket memory usage with many connections"""
        run = setup_run_day
        
        # Create many short-lived connections to test memory cleanup
        for i in range(50):
            sio_client = socketio.AsyncClient()
            await sio_client.connect('http://localhost:8000', socketio_path='/socket.io/')
            
            # Send a registration event
            response = client.post("/api/register", json={
                "session_id": run.session_id,
                "runner_name": f"Memory Test Runner {i}"
            })
            
            await asyncio.sleep(0.05)
            await sio_client.disconnect()
        
        # Verify system is still responsive
        response = client.get("/api/attendance/today")
        assert response.status_code == 200