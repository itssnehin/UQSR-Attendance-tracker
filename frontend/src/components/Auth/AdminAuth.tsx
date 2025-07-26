import React, { useState } from 'react';

interface AdminAuthProps {
  onAuthenticated: () => void;
}

const AdminAuth: React.FC<AdminAuthProps> = ({ onAuthenticated }) => {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Simple password check - in production, this should be more secure
  const ADMIN_PASSWORD = 'admin123'; // You can change this

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    // Simulate a small delay
    await new Promise(resolve => setTimeout(resolve, 500));

    if (password === ADMIN_PASSWORD) {
      // Store auth status in localStorage
      localStorage.setItem('isAdmin', 'true');
      onAuthenticated();
    } else {
      setError('Invalid password. Please try again.');
    }
    
    setIsLoading(false);
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#f8f9fa',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem'
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        padding: '3rem',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
        maxWidth: '400px',
        width: '100%'
      }}>
        <div style={{
          textAlign: 'center',
          marginBottom: '2rem'
        }}>
          <h1 style={{
            color: '#2c3e50',
            fontSize: '2rem',
            marginBottom: '0.5rem'
          }}>
            🔐 Admin Access
          </h1>
          <p style={{
            color: '#7f8c8d',
            fontSize: '1rem'
          }}>
            Enter the admin password to access the dashboard
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{
              display: 'block',
              marginBottom: '0.5rem',
              fontWeight: 'bold',
              color: '#2c3e50'
            }}>
              Password:
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                width: '100%',
                padding: '0.75rem',
                fontSize: '1rem',
                border: error ? '2px solid #e74c3c' : '2px solid #ced4da',
                borderRadius: '4px',
                outline: 'none',
                transition: 'border-color 0.2s'
              }}
              placeholder="Enter admin password"
              disabled={isLoading}
              onFocus={(e) => e.target.style.borderColor = '#007bff'}
              onBlur={(e) => {
                if (!error) e.target.style.borderColor = '#ced4da';
              }}
            />
            {error && (
              <div style={{
                color: '#e74c3c',
                fontSize: '0.875rem',
                marginTop: '0.25rem'
              }}>
                {error}
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading || !password.trim()}
            style={{
              width: '100%',
              padding: '0.75rem',
              fontSize: '1rem',
              fontWeight: 'bold',
              color: 'white',
              backgroundColor: isLoading || !password.trim() ? '#6c757d' : '#3498db',
              border: 'none',
              borderRadius: '4px',
              cursor: isLoading || !password.trim() ? 'not-allowed' : 'pointer',
              transition: 'background-color 0.2s'
            }}
            onMouseOver={(e) => {
              if (!isLoading && password.trim()) {
                e.currentTarget.style.backgroundColor = '#2980b9';
              }
            }}
            onMouseOut={(e) => {
              if (!isLoading && password.trim()) {
                e.currentTarget.style.backgroundColor = '#3498db';
              }
            }}
          >
            {isLoading ? '🔄 Checking...' : '🚀 Access Dashboard'}
          </button>
        </form>

        <div style={{
          marginTop: '2rem',
          padding: '1rem',
          backgroundColor: '#fff3cd',
          border: '1px solid #ffeaa7',
          borderRadius: '4px',
          fontSize: '0.85rem',
          color: '#856404'
        }}>
          <strong>Demo Password:</strong> admin123
        </div>
      </div>
    </div>
  );
};

export default AdminAuth;