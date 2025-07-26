"""
WebSocket Service for real-time attendance updates
"""
import socketio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from fastapi import FastAPI

logger = logging.getLogger(__name__)


class WebSocketService:
    """Service for handling real-time WebSocket connections and attendance updates"""
    
    def __init__(self):
        # Create Socket.IO server with CORS configuration
        allowed_origins = [
            "http://localhost:3000",
            "http://localhost:3001",
            "https://srcatttrackerbeta.vercel.app",
            "https://srcatttrackerbeta-*.vercel.app",
            "https://*.vercel.app",
            "https://srcatttrackerbeta-np15pmt84-itssnehins-projects.vercel.app",
            "https://srcatttrackerbeta-ars678kvf-itssnehins-projects.vercel.app",
            "https://srcatttrackerbeta-yhg2lz99t-itssnehins-projects.vercel.app"
        ]
        
        self.sio = socketio.AsyncServer(
            cors_allowed_origins="*",  # Temporarily allow all origins
            logger=True,
            engineio_logger=True,
            async_mode='asgi'
        )
        
        # In-memory session management
        self.connected_clients: Dict[str, Dict[str, Any]] = {}
        self.room_sessions: Dict[str, List[str]] = {}  # session_id -> list of client_ids
        
        # Set up event handlers
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Set up Socket.IO event handlers"""
        
        @self.sio.event
        async def connect(sid, environ, auth):
            """Handle client connection"""
            try:
                logger.info(f"Client {sid} connected")
                
                # Store client info
                self.connected_clients[sid] = {
                    "connected_at": datetime.utcnow().isoformat(),
                    "session_id": None,
                    "client_type": None  # 'admin' or 'runner'
                }
                
                # Send connection confirmation
                await self.sio.emit('connection_confirmed', {
                    'status': 'connected',
                    'client_id': sid,
                    'timestamp': datetime.utcnow().isoformat()
                }, room=sid)
                
                logger.info(f"Total connected clients: {len(self.connected_clients)}")
                
            except Exception as e:
                logger.error(f"Error handling connection for {sid}: {str(e)}")
        
        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection"""
            try:
                logger.info(f"Client {sid} disconnected")
                
                # Remove from session rooms
                if sid in self.connected_clients:
                    session_id = self.connected_clients[sid].get('session_id')
                    if session_id and session_id in self.room_sessions:
                        if sid in self.room_sessions[session_id]:
                            self.room_sessions[session_id].remove(sid)
                        
                        # Clean up empty rooms
                        if not self.room_sessions[session_id]:
                            del self.room_sessions[session_id]
                    
                    # Remove client info
                    del self.connected_clients[sid]
                
                logger.info(f"Total connected clients: {len(self.connected_clients)}")
                
            except Exception as e:
                logger.error(f"Error handling disconnection for {sid}: {str(e)}")
        
        @self.sio.event
        async def join_session(sid, data):
            """Handle client joining a session room"""
            try:
                session_id = data.get('session_id')
                client_type = data.get('client_type', 'runner')  # 'admin' or 'runner'
                
                if not session_id:
                    await self.sio.emit('error', {
                        'message': 'Session ID is required'
                    }, room=sid)
                    return
                
                logger.info(f"Client {sid} joining session {session_id} as {client_type}")
                
                # Update client info
                if sid in self.connected_clients:
                    self.connected_clients[sid]['session_id'] = session_id
                    self.connected_clients[sid]['client_type'] = client_type
                
                # Add to session room
                await self.sio.enter_room(sid, session_id)
                
                # Track room membership
                if session_id not in self.room_sessions:
                    self.room_sessions[session_id] = []
                if sid not in self.room_sessions[session_id]:
                    self.room_sessions[session_id].append(sid)
                
                # Confirm room join
                await self.sio.emit('session_joined', {
                    'session_id': session_id,
                    'client_type': client_type,
                    'timestamp': datetime.utcnow().isoformat()
                }, room=sid)
                
                logger.info(f"Client {sid} successfully joined session {session_id}")
                
            except Exception as e:
                logger.error(f"Error handling join_session for {sid}: {str(e)}")
                await self.sio.emit('error', {
                    'message': 'Failed to join session'
                }, room=sid)
        
        @self.sio.event
        async def leave_session(sid, data):
            """Handle client leaving a session room"""
            try:
                session_id = data.get('session_id')
                
                if not session_id:
                    return
                
                logger.info(f"Client {sid} leaving session {session_id}")
                
                # Remove from session room
                await self.sio.leave_room(sid, session_id)
                
                # Update tracking
                if session_id in self.room_sessions and sid in self.room_sessions[session_id]:
                    self.room_sessions[session_id].remove(sid)
                    
                    # Clean up empty rooms
                    if not self.room_sessions[session_id]:
                        del self.room_sessions[session_id]
                
                # Update client info
                if sid in self.connected_clients:
                    self.connected_clients[sid]['session_id'] = None
                
                await self.sio.emit('session_left', {
                    'session_id': session_id,
                    'timestamp': datetime.utcnow().isoformat()
                }, room=sid)
                
            except Exception as e:
                logger.error(f"Error handling leave_session for {sid}: {str(e)}")
        
        @self.sio.event
        async def ping(sid, data):
            """Handle ping for connection health check"""
            try:
                await self.sio.emit('pong', {
                    'timestamp': datetime.utcnow().isoformat(),
                    'client_id': sid
                }, room=sid)
            except Exception as e:
                logger.error(f"Error handling ping for {sid}: {str(e)}")
    
    async def broadcast_attendance_update(self, session_id: str, attendance_data: Dict[str, Any]):
        """
        Broadcast attendance update to all clients in a session
        
        Requirements:
        - 3.2: Real-time updates without page refresh
        - 4.1: Handle up to 100 concurrent users
        
        Args:
            session_id: Session ID to broadcast to
            attendance_data: Attendance data to broadcast
        """
        try:
            logger.info(f"Broadcasting attendance update to session {session_id}")
            
            # Prepare broadcast data
            broadcast_data = {
                'type': 'attendance_update',
                'session_id': session_id,
                'data': attendance_data,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Broadcast to all clients in the session room
            await self.sio.emit('attendance_update', broadcast_data, room=session_id)
            
            # Log broadcast stats
            client_count = len(self.room_sessions.get(session_id, []))
            logger.info(f"Attendance update broadcasted to {client_count} clients in session {session_id}")
            
        except Exception as e:
            logger.error(f"Error broadcasting attendance update: {str(e)}")
    
    async def broadcast_registration_success(self, session_id: str, registration_data: Dict[str, Any]):
        """
        Broadcast successful registration to all clients in a session
        
        Args:
            session_id: Session ID to broadcast to
            registration_data: Registration data to broadcast
        """
        try:
            logger.info(f"Broadcasting registration success to session {session_id}")
            
            broadcast_data = {
                'type': 'registration_success',
                'session_id': session_id,
                'data': registration_data,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            await self.sio.emit('registration_success', broadcast_data, room=session_id)
            
            client_count = len(self.room_sessions.get(session_id, []))
            logger.info(f"Registration success broadcasted to {client_count} clients in session {session_id}")
            
        except Exception as e:
            logger.error(f"Error broadcasting registration success: {str(e)}")
    
    async def send_error_to_client(self, client_id: str, error_message: str):
        """
        Send error message to specific client
        
        Args:
            client_id: Client ID to send error to
            error_message: Error message to send
        """
        try:
            await self.sio.emit('error', {
                'message': error_message,
                'timestamp': datetime.utcnow().isoformat()
            }, room=client_id)
            
        except Exception as e:
            logger.error(f"Error sending error to client {client_id}: {str(e)}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get current connection statistics
        
        Returns:
            Dict with connection statistics
        """
        try:
            total_clients = len(self.connected_clients)
            active_sessions = len(self.room_sessions)
            
            session_stats = {}
            for session_id, clients in self.room_sessions.items():
                session_stats[session_id] = len(clients)
            
            return {
                'total_connected_clients': total_clients,
                'active_sessions': active_sessions,
                'session_client_counts': session_stats,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting connection stats: {str(e)}")
            return {
                'total_connected_clients': 0,
                'active_sessions': 0,
                'session_client_counts': {},
                'error': str(e)
            }
    
    def get_socketio_app(self):
        """Get the Socket.IO ASGI app for mounting"""
        return socketio.ASGIApp(self.sio)


# Global WebSocket service instance
websocket_service = WebSocketService()