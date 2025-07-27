import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { useAppContext } from '../../context/AppContext';
import { validateSessionId, sanitizeInput } from '../../utils/validationUtils';
import apiService from '../../services/apiService';
import { RegistrationRequest, AttendanceResponse } from '../../types';
// import './RunnerRegistration.css'; // Temporarily disabled

interface FormData {
  studentNumber: string;
  sessionId: string;
}

interface FormErrors {
  studentNumber?: string;
  sessionId?: string;
  general?: string;
}

interface RegistrationState {
  isSubmitting: boolean;
  isSuccess: boolean;
  message: string;
  currentCount: number;
}

const RunnerRegistration: React.FC = () => {
  const { sessionId: urlSessionId } = useParams<{ sessionId?: string }>();
  const [searchParams] = useSearchParams();
  const { state } = useAppContext();

  // Form state
  const [formData, setFormData] = useState<FormData>({
    studentNumber: '',
    sessionId: urlSessionId || searchParams.get('session') || ''
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [registrationState, setRegistrationState] = useState<RegistrationState>({
    isSubmitting: false,
    isSuccess: false,
    message: '',
    currentCount: 0
  });



  // Initialize session ID from URL or QR scan
  useEffect(() => {
    const sessionFromUrl = urlSessionId || searchParams.get('session') || searchParams.get('token');
    if (sessionFromUrl) {
      setFormData(prev => ({ ...prev, sessionId: sessionFromUrl }));
      validateSessionIdField(sessionFromUrl);
    }
  }, [urlSessionId, searchParams]);



  const validateSessionIdField = (sessionId: string) => {
    const validation = validateSessionId(sessionId);
    if (!validation.isValid) {
      setErrors(prev => ({ ...prev, sessionId: validation.error }));
      return false;
    } else {
      setErrors(prev => ({ ...prev, sessionId: undefined }));
      return true;
    }
  };

  const validateStudentNumberField = (studentNumber: string) => {
    // Student number validation: exactly 8 digits
    if (!studentNumber) {
      setErrors(prev => ({ ...prev, studentNumber: 'Student number is required' }));
      return false;
    }
    if (!/^\d{8}$/.test(studentNumber)) {
      setErrors(prev => ({ ...prev, studentNumber: 'Student number must be exactly 8 digits' }));
      return false;
    }
    setErrors(prev => ({ ...prev, studentNumber: undefined }));
    return true;
  };

  const handleInputChange = (field: keyof FormData, value: string) => {
    const sanitizedValue = sanitizeInput(value);
    setFormData(prev => ({ ...prev, [field]: sanitizedValue }));

    // Clear previous errors and validate
    setErrors(prev => ({ ...prev, [field]: undefined, general: undefined }));

    if (field === 'studentNumber') {
      validateStudentNumberField(sanitizedValue);
    } else if (field === 'sessionId') {
      validateSessionIdField(sanitizedValue);
    }
  };

  const validateForm = (): boolean => {
    const studentNumberValid = validateStudentNumberField(formData.studentNumber);
    const sessionValid = validateSessionIdField(formData.sessionId);
    return studentNumberValid && sessionValid;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setRegistrationState(prev => ({ ...prev, isSubmitting: true, message: '' }));
    setErrors(prev => ({ ...prev, general: undefined }));

    try {
      const registrationData: RegistrationRequest = {
        sessionId: formData.sessionId,
        runnerName: formData.studentNumber, // Backend still expects runnerName field
        timestamp: new Date()
      };

      const response: AttendanceResponse = await apiService.registerAttendance(registrationData);

      setRegistrationState({
        isSubmitting: false,
        isSuccess: response.success,
        message: response.message,
        currentCount: response.current_count
      });

      if (response.success) {
        // Clear form on success
        setFormData(prev => ({ ...prev, studentNumber: '' }));
      }
    } catch (error) {
      console.error('Registration failed:', error);
      setRegistrationState({
        isSubmitting: false,
        isSuccess: false,
        message: 'Registration failed. Please try again.',
        currentCount: 0
      });
      setErrors(prev => ({
        ...prev,
        general: error instanceof Error ? error.message : 'Registration failed. Please try again.'
      }));
    }
  };



  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '1rem'
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '20px',
        padding: '2.5rem',
        boxShadow: '0 20px 40px rgba(0,0,0,0.1)',
        maxWidth: '500px',
        width: '100%',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Decorative Background Elements */}
        <div style={{
          position: 'absolute',
          top: '-50px',
          right: '-50px',
          width: '100px',
          height: '100px',
          background: 'linear-gradient(45deg, #667eea, #764ba2)',
          borderRadius: '50%',
          opacity: '0.1'
        }}></div>
        <div style={{
          position: 'absolute',
          bottom: '-30px',
          left: '-30px',
          width: '60px',
          height: '60px',
          background: 'linear-gradient(45deg, #764ba2, #667eea)',
          borderRadius: '50%',
          opacity: '0.1'
        }}></div>

        <header style={{
          textAlign: 'center',
          marginBottom: '2rem',
          position: 'relative',
          zIndex: 1
        }}>
          <div style={{
            fontSize: '3rem',
            marginBottom: '1rem'
          }}>🏃‍♂️</div>
          <h1 style={{
            color: '#2c3e50',
            fontSize: '2rem',
            fontWeight: 'bold',
            marginBottom: '0.5rem',
            background: 'linear-gradient(135deg, #667eea, #764ba2)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text'
          }}>
            Runner Registration
          </h1>
          <p style={{
            color: '#7f8c8d',
            fontSize: '1.1rem',
            margin: 0
          }}>
            Register for today's social run
          </p>
        </header>

        {/* Connection Status */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '2rem',
          padding: '0.75rem 1rem',
          backgroundColor: state.isConnected ? '#d4edda' : '#f8d7da',
          color: state.isConnected ? '#155724' : '#721c24',
          borderRadius: '10px',
          fontSize: '0.9rem',
          fontWeight: '500'
        }}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: state.isConnected ? '#28a745' : '#dc3545',
            marginRight: '0.5rem',
            animation: state.isConnected ? 'none' : 'pulse 1.5s infinite'
          }}></span>
          {state.isConnected ? '✅ Connected' : '🔄 Reconnecting...'}
        </div>

        {/* Success Message */}
        {registrationState.isSuccess && (
          <div style={{
            textAlign: 'center',
            padding: '2rem',
            backgroundColor: '#d4edda',
            borderRadius: '15px',
            border: '2px solid #c3e6cb',
            marginBottom: '2rem',
            animation: 'slideIn 0.5s ease-out'
          }}>
            <div style={{
              fontSize: '4rem',
              color: '#28a745',
              marginBottom: '1rem',
              animation: 'bounce 0.6s ease-out'
            }}>✓</div>
            <h2 style={{
              color: '#155724',
              fontSize: '1.5rem',
              fontWeight: 'bold',
              marginBottom: '1rem'
            }}>Registration Successful!</h2>
            <p style={{
              color: '#155724',
              fontSize: '1.1rem',
              marginBottom: '1rem'
            }}>{registrationState.message}</p>
            <div style={{
              display: 'inline-block',
              backgroundColor: '#28a745',
              color: 'white',
              padding: '0.75rem 1.5rem',
              borderRadius: '25px',
              fontSize: '1rem',
              fontWeight: 'bold'
            }}>
              Current attendance: {registrationState.currentCount}
            </div>
          </div>
        )}

        {/* Registration Form */}
        {!registrationState.isSuccess && (
          <form onSubmit={handleSubmit} style={{ position: 'relative', zIndex: 1 }}>
            {/* Session ID Input */}
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{
                display: 'block',
                marginBottom: '0.5rem',
                fontWeight: '600',
                color: '#2c3e50',
                fontSize: '1rem'
              }}>
                📱 Session ID
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  type="text"
                  id="sessionId"
                  value={formData.sessionId}
                  onChange={(e) => handleInputChange('sessionId', e.target.value)}
                  placeholder="Enter 5-digit session code"
                  disabled={registrationState.isSubmitting}
                  maxLength={5}
                  style={{
                    width: '100%',
                    padding: '1rem',
                    border: errors.sessionId ? '2px solid #e74c3c' : '2px solid #e9ecef',
                    borderRadius: '12px',
                    outline: 'none',
                    transition: 'all 0.3s ease',
                    backgroundColor: registrationState.isSubmitting ? '#f8f9fa' : 'white',
                    fontFamily: 'monospace',
                    letterSpacing: '2px',
                    textAlign: 'center',
                    fontSize: '1.5rem',
                    fontWeight: 'bold'
                  }}
                  onFocus={(e) => {
                    if (!errors.sessionId) {
                      e.target.style.borderColor = '#667eea';
                      e.target.style.boxShadow = '0 0 0 3px rgba(102, 126, 234, 0.1)';
                    }
                  }}
                  onBlur={(e) => {
                    if (!errors.sessionId) {
                      e.target.style.borderColor = '#e9ecef';
                      e.target.style.boxShadow = 'none';
                    }
                  }}
                />

              </div>
              {errors.sessionId && (
                <div style={{
                  color: '#e74c3c',
                  fontSize: '0.875rem',
                  marginTop: '0.5rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem'
                }}>
                  <span>⚠️</span>
                  {errors.sessionId}
                </div>
              )}
            </div>

            {/* Student Number Input */}
            <div style={{ marginBottom: '2rem' }}>
              <label style={{
                display: 'block',
                marginBottom: '0.5rem',
                fontWeight: '600',
                color: '#2c3e50',
                fontSize: '1rem'
              }}>
                🎓 Student Number
              </label>
              <input
                type="text"
                id="studentNumber"
                value={formData.studentNumber}
                onChange={(e) => {
                  // Only allow numbers and limit to 8 digits
                  const value = e.target.value.replace(/\D/g, '').slice(0, 8);
                  handleInputChange('studentNumber', value);
                }}
                placeholder="Enter your 8-digit student number"
                disabled={registrationState.isSubmitting}
                maxLength={8}
                style={{
                  width: '100%',
                  padding: '1rem',
                  border: errors.studentNumber ? '2px solid #e74c3c' : '2px solid #e9ecef',
                  borderRadius: '12px',
                  outline: 'none',
                  transition: 'all 0.3s ease',
                  backgroundColor: registrationState.isSubmitting ? '#f8f9fa' : 'white',
                  fontFamily: 'monospace',
                  letterSpacing: '1px',
                  textAlign: 'center',
                  fontSize: '1.3rem',
                  fontWeight: 'bold'
                }}
                onFocus={(e) => {
                  if (!errors.studentNumber) {
                    e.target.style.borderColor = '#667eea';
                    e.target.style.boxShadow = '0 0 0 3px rgba(102, 126, 234, 0.1)';
                  }
                }}
                onBlur={(e) => {
                  if (!errors.studentNumber) {
                    e.target.style.borderColor = '#e9ecef';
                    e.target.style.boxShadow = 'none';
                  }
                }}
              />
              {errors.studentNumber && (
                <div style={{
                  color: '#e74c3c',
                  fontSize: '0.875rem',
                  marginTop: '0.5rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem'
                }}>
                  <span>⚠️</span>
                  {errors.studentNumber}
                </div>
              )}
            </div>

            {/* General Error */}
            {errors.general && (
              <div style={{
                backgroundColor: '#f8d7da',
                color: '#721c24',
                padding: '1rem',
                borderRadius: '10px',
                border: '1px solid #f5c6cb',
                marginBottom: '1.5rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                <span style={{ fontSize: '1.2rem' }}>⚠️</span>
                {errors.general}
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={registrationState.isSubmitting || !formData.studentNumber || !formData.sessionId}
              style={{
                width: '100%',
                padding: '1.25rem',
                fontSize: '1.1rem',
                fontWeight: 'bold',
                color: 'white',
                background: (registrationState.isSubmitting || !formData.studentNumber || !formData.sessionId)
                  ? 'linear-gradient(135deg, #95a5a6, #7f8c8d)'
                  : 'linear-gradient(135deg, #667eea, #764ba2)',
                border: 'none',
                borderRadius: '12px',
                cursor: (registrationState.isSubmitting || !formData.studentNumber || !formData.sessionId)
                  ? 'not-allowed'
                  : 'pointer',
                transition: 'all 0.3s ease',
                position: 'relative',
                overflow: 'hidden',
                boxShadow: '0 4px 15px rgba(102, 126, 234, 0.3)'
              }}
              onMouseOver={(e) => {
                if (!registrationState.isSubmitting && formData.studentNumber && formData.sessionId) {
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.4)';
                }
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 4px 15px rgba(102, 126, 234, 0.3)';
              }}
            >
              {registrationState.isSubmitting ? (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                  <div style={{
                    width: '20px',
                    height: '20px',
                    border: '2px solid transparent',
                    borderTop: '2px solid white',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                  }}></div>
                  Registering...
                </div>
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                  <span style={{ fontSize: '1.2rem' }}>🏃‍♂️</span>
                  Register Attendance
                </div>
              )}
            </button>
          </form>
        )}



        {/* Registration Error */}
        {!registrationState.isSuccess && registrationState.message && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {registrationState.message}
          </div>
        )}

        {/* Try Again Button */}
        {registrationState.isSuccess && (
          <button
            onClick={() => setRegistrationState({
              isSubmitting: false,
              isSuccess: false,
              message: '',
              currentCount: 0
            })}
            style={{
              width: '100%',
              padding: '1rem',
              fontSize: '1rem',
              fontWeight: '600',
              color: '#667eea',
              backgroundColor: 'transparent',
              border: '2px solid #667eea',
              borderRadius: '12px',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              marginTop: '1rem'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.backgroundColor = '#667eea';
              e.currentTarget.style.color = 'white';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.color = '#667eea';
            }}
          >
            ➕ Register Another Runner
          </button>
        )}

        {/* Registration Error */}
        {!registrationState.isSuccess && registrationState.message && (
          <div style={{
            backgroundColor: '#f8d7da',
            color: '#721c24',
            padding: '1rem',
            borderRadius: '10px',
            border: '1px solid #f5c6cb',
            marginTop: '1rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <span style={{ fontSize: '1.2rem' }}>⚠️</span>
            {registrationState.message}
          </div>
        )}
      </div>

      {/* Add CSS animations */}
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        
        @keyframes slideIn {
          0% { 
            opacity: 0; 
            transform: translateY(-20px); 
          }
          100% { 
            opacity: 1; 
            transform: translateY(0); 
          }
        }
        
        @keyframes bounce {
          0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
          40% { transform: translateY(-10px); }
          60% { transform: translateY(-5px); }
        }
      `}</style>
    </div>
  );
};

export default RunnerRegistration;