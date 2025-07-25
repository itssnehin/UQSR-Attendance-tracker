# Environment Variables Configuration Guide

## Railway Backend Environment Variables

Configure these environment variables in your Railway project dashboard:

### Required Variables
```bash
# Database Configuration
DATABASE_URL=sqlite:///./data/runner_attendance.db
DATABASE_ECHO=false

# Server Configuration
PORT=8000
ENVIRONMENT=production
WORKERS=1

# CORS Configuration (Update with your actual Vercel domain)
FRONTEND_URL=https://your-frontend-domain.vercel.app
ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app

# Application Configuration
DEBUG=false
LOG_LEVEL=INFO
LOG_FORMAT=json

# QR Code Configuration
QR_CODE_EXPIRY_HOURS=24

# Performance Configuration
CACHE_TTL=300
MAX_CONCURRENT_REQUESTS=100
CONNECTION_POOL_SIZE=5
CONNECTION_POOL_OVERFLOW=10

# WebSocket Configuration
WEBSOCKET_PING_INTERVAL=25
WEBSOCKET_PING_TIMEOUT=60

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Monitoring
HEALTH_CHECK_TIMEOUT=30
METRICS_ENABLED=true

# Feature Flags
ENABLE_PERFORMANCE_MONITORING=true
ENABLE_DETAILED_LOGGING=false
ENABLE_CACHE=true
```

### Security Variables (Set in Railway Dashboard)
```bash
# Generate a secure secret key for production
SECRET_KEY=your-secure-secret-key-here-minimum-32-characters

# JWT secret for QR code token generation
JWT_SECRET_KEY=your-jwt-secret-key-here-minimum-32-characters
```

## Vercel Frontend Environment Variables

Configure these in your Vercel project dashboard:

### Required Variables
```bash
# API Configuration (Update with your actual Railway domain)
REACT_APP_API_URL=https://your-backend-domain.railway.app
REACT_APP_WS_URL=https://your-backend-domain.railway.app

# Environment
REACT_APP_ENVIRONMENT=production

# Build Configuration
CI=false
```

## Setting Environment Variables

### Railway
1. Go to your Railway project dashboard
2. Navigate to Variables tab
3. Add each variable with its value
4. Deploy to apply changes

### Vercel
1. Go to your Vercel project dashboard
2. Navigate to Settings → Environment Variables
3. Add each variable for Production, Preview, and Development
4. Redeploy to apply changes

## Domain Configuration Steps

### 1. Deploy Backend to Railway
1. Connect your GitHub repository to Railway
2. Set all backend environment variables
3. Note your Railway domain (e.g., `https://your-app.railway.app`)

### 2. Deploy Frontend to Vercel
1. Connect your GitHub repository to Vercel
2. Set `REACT_APP_API_URL` to your Railway domain
3. Set `REACT_APP_WS_URL` to your Railway domain
4. Note your Vercel domain (e.g., `https://your-app.vercel.app`)

### 3. Update CORS Configuration
1. Go back to Railway environment variables
2. Update `FRONTEND_URL` with your Vercel domain
3. Update `ALLOWED_ORIGINS` with your Vercel domain
4. Redeploy backend

## Security Considerations

### Secret Key Generation
Generate secure secret keys using Python:
```python
import secrets
print(secrets.token_urlsafe(32))
```

### CORS Security
- Never use `*` for ALLOWED_ORIGINS in production
- Always specify exact domains
- Include both www and non-www versions if needed

### Database Security
- SQLite file is stored in Railway's persistent volume
- Automatic backups are handled by Railway
- Database file is not publicly accessible

## Monitoring and Logging

### Railway Logs
- View logs in Railway dashboard
- Logs are automatically rotated
- Set LOG_LEVEL to control verbosity

### Health Checks
- Railway automatically monitors `/health` endpoint
- Configure HEALTH_CHECK_TIMEOUT as needed
- Monitor uptime in Railway dashboard

### Performance Monitoring
- Enable METRICS_ENABLED for performance tracking
- Monitor database performance through logs
- Use Railway's built-in metrics

## Troubleshooting

### Common Issues
1. **CORS errors**: Check ALLOWED_ORIGINS matches your frontend domain exactly
2. **Database errors**: Ensure data directory permissions are correct
3. **WebSocket issues**: Verify WS_URL matches API_URL
4. **Build failures**: Check all required environment variables are set

### Debug Commands
```bash
# Check environment variables in Railway
railway run env

# Test database connection
railway run python -c "from app.database.connection import db_manager; print(db_manager.check_health())"

# View logs
railway logs
```