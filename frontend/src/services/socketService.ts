import { io, Socket } from 'socket.io-client';

class SocketService {
  private socket: Socket | null = null;
  private baseUrl: string;

  constructor() {
    // Use production backend URL
    this.baseUrl = process.env.REACT_APP_API_URL || 'https://talented-intuition-production.up.railway.app';
  }

  connect(): void {
    if (!this.socket) {
      this.socket = io(this.baseUrl, {
        path: '/socket.io', // Explicitly set the path
        transports: ['websocket', 'polling'], // Add polling as fallback
        autoConnect: true,
        timeout: 10000, // 10 second timeout
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 2000,
        forceNew: true, // Force new connection
      });

      this.socket.on('connect', () => {
        console.log('Socket connected to:', this.baseUrl);
      });

      this.socket.on('disconnect', (reason) => {
        console.log('Socket disconnected:', reason);
      });

      this.socket.on('connect_error', (error) => {
        console.error('Socket connection error:', error);
      });

      this.socket.on('error', (error) => {
        console.error('Socket error:', error);
      });
    }
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  on(event: string, callback: (...args: any[]) => void): void {
    if (this.socket) {
      this.socket.on(event, callback);
    }
  }

  off(event: string, callback?: (...args: any[]) => void): void {
    if (this.socket) {
      this.socket.off(event, callback);
    }
  }

  emit(event: string, data?: any): void {
    if (this.socket && this.socket.connected) {
      this.socket.emit(event, data);
    }
  }

  reconnect(): void {
    if (this.socket) {
      this.socket.connect();
    } else {
      this.connect();
    }
  }

  getConnectionState(): string {
    if (!this.socket) return 'not_initialized';
    if (this.socket.connected) return 'connected';
    if (this.socket.disconnected) return 'disconnected';
    return 'connecting';
  }
}

export default new SocketService();