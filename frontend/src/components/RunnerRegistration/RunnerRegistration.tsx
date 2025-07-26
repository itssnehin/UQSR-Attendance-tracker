import React, { useState, useEffect, useRef } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { useAppContext } from '../../context/AppContext';
import { validateRunnerName, validateSessionId, sanitizeInput } from '../../utils/validationUtils';
import apiService from '../../services/apiService';
import { RegistrationRequest, AttendanceResponse } from '../../types';
// import './RunnerRegistration.css'; // Temporarily disabled

interface FormData {
  runnerName: string;
  sessionId: string;
}

interface FormErrors {
  runnerName?: string;
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
    runnerName: '',
    sessionId: urlSessionId || searchParams.get('session') || ''
  });
  
  const [errors, setErrors] = useState<FormErrors>({});
  const [registrationState, setRegistrationState] = useState<RegistrationState>({
    isSubmitting: false,
    isSuccess: false,
    message: '',
    currentCount: 0
  });
  
  // QR Scanner state
  const [showScanner, setShowScanner] = useState(false);
  const [cameraError, setCameraError] = useState<string>('');
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Initialize session ID from URL or QR scan
  useEffect(() => {
    const sessionFromUrl = urlSessionId || searchParams.get('session') || searchParams.get('token');
    if (sessionFromUrl) {
      setFormData(prev => ({ ...prev, sessionId: sessionFromUrl }));
      validateSessionIdField(sessionFromUrl);
    }
  }, [urlSessionId, searchParams]);

  // Cleanup camera stream on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

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

  const validateRunnerNameField = (name: string) => {
    const validation = validateRunnerName(name);
    if (!validation.isValid) {
      setErrors(prev => ({ ...prev, runnerName: validation.error }));
      return false;
    } else {
      setErrors(prev => ({ ...prev, runnerName: undefined }));
      return true;
    }
  };

  const handleInputChange = (field: keyof FormData, value: string) => {
    const sanitizedValue = sanitizeInput(value);
    setFormData(prev => ({ ...prev, [field]: sanitizedValue }));
    
    // Clear previous errors and validate
    setErrors(prev => ({ ...prev, [field]: undefined, general: undefined }));
    
    if (field === 'runnerName') {
      validateRunnerNameField(sanitizedValue);
    } else if (field === 'sessionId') {
      validateSessionIdField(sanitizedValue);
    }
  };

  const validateForm = (): boolean => {
    const nameValid = validateRunnerNameField(formData.runnerName);
    const sessionValid = validateSessionIdField(formData.sessionId);
    return nameValid && sessionValid;
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
        runnerName: formData.runnerName,
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
        setFormData(prev => ({ ...prev, runnerName: '' }));
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

  const startCamera = async () => {
    try {
      setCameraError('');
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'environment' } // Use back camera on mobile
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
        setShowScanner(true);
      }
    } catch (error) {
      console.error('Camera access failed:', error);
      setCameraError('Camera access denied or not available. Please enter the session ID manually.');
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setShowScanner(false);
    setCameraError('');
  };

  const handleManualTokenInput = () => {
    const token = prompt('Enter the QR code token or session ID:');
    if (token) {
      handleInputChange('sessionId', token);
    }
  };

  return (
    <div className="runner-registration">
      <div className="registration-container">
        <header className="registration-header">
          <h1>Runner Registration</h1>
          <p className="subtitle">Register for today's social run</p>
        </header>

        {/* Connection Status */}
        <div className={`connection-status ${state.isConnected ? 'connected' : 'disconnected'}`}>
          <span className="status-indicator"></span>
          {state.isConnected ? 'Connected' : 'Disconnected'}
        </div>

        {/* Success Message */}
        {registrationState.isSuccess && (
          <div className="success-message">
            <div className="success-icon">✓</div>
            <h2>Registration Successful!</h2>
            <p>{registrationState.message}</p>
            <p className="attendance-count">
              Current attendance: <strong>{registrationState.currentCount}</strong>
            </p>
          </div>
        )}

        {/* Registration Form */}
        {!registrationState.isSuccess && (
          <form onSubmit={handleSubmit} className="registration-form">
            {/* Session ID Input */}
            <div className="form-group">
              <label htmlFor="sessionId">Session ID</label>
              <div className="session-input-group">
                <input
                  type="text"
                  id="sessionId"
                  value={formData.sessionId}
                  onChange={(e) => handleInputChange('sessionId', e.target.value)}
                  placeholder="Enter session ID or scan QR code"
                  className={errors.sessionId ? 'error' : ''}
                  disabled={registrationState.isSubmitting}
                />
                <div className="session-actions">
                  <button
                    type="button"
                    onClick={startCamera}
                    className="scan-button"
                    disabled={registrationState.isSubmitting}
                    title="Scan QR Code"
                  >
                    📷
                  </button>
                  <button
                    type="button"
                    onClick={handleManualTokenInput}
                    className="manual-button"
                    disabled={registrationState.isSubmitting}
                    title="Enter manually"
                  >
                    ⌨️
                  </button>
                </div>
              </div>
              {errors.sessionId && <span className="error-text">{errors.sessionId}</span>}
            </div>

            {/* Runner Name Input */}
            <div className="form-group">
              <label htmlFor="runnerName">Your Name</label>
              <input
                type="text"
                id="runnerName"
                value={formData.runnerName}
                onChange={(e) => handleInputChange('runnerName', e.target.value)}
                placeholder="Enter your full name"
                className={errors.runnerName ? 'error' : ''}
                disabled={registrationState.isSubmitting}
                autoComplete="name"
              />
              {errors.runnerName && <span className="error-text">{errors.runnerName}</span>}
            </div>

            {/* General Error */}
            {errors.general && (
              <div className="error-message">
                <span className="error-icon">⚠️</span>
                {errors.general}
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              className="submit-button"
              disabled={registrationState.isSubmitting || !formData.runnerName || !formData.sessionId}
            >
              {registrationState.isSubmitting ? (
                <>
                  <span className="loading-spinner"></span>
                  Registering...
                </>
              ) : (
                'Register Attendance'
              )}
            </button>
          </form>
        )}

        {/* QR Scanner Modal */}
        {showScanner && (
          <div className="scanner-modal">
            <div className="scanner-content">
              <div className="scanner-header">
                <h3>Scan QR Code</h3>
                <button onClick={stopCamera} className="close-button">×</button>
              </div>
              <div className="scanner-body">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  className="scanner-video"
                />
                <div className="scanner-overlay">
                  <div className="scanner-frame"></div>
                </div>
                <p className="scanner-instructions">
                  Position the QR code within the frame
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Camera Error */}
        {cameraError && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {cameraError}
          </div>
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
            className="try-again-button"
          >
            Register Another Runner
          </button>
        )}
      </div>
    </div>
  );
};

export default RunnerRegistration;