# Runner Attendance Tracker - Deployment Guide

## Overview

This guide covers the complete deployment process for the Runner Attendance Tracker application, including both backend (Python/FastAPI) and frontend (React) components.

## Architecture

- **Backend**: Python/FastAPI with SQLite database hosted on Railway
- **Frontend**: React application hosted on Vercel
- **Database**: SQLite with persistent storage on Railway
- **Real-time**: WebSocket connections for live updates

## Prerequisites

- GitHub account with repository access
- Railway account (free tier available)
- Vercel account (free tier available)
- Domain names (optional, can use provided subdomains)

## Backend Deployment (Railway)

### 1. Prepare Repository

Ensure your repository has the following files in the `backend/` directory:
- `requirements.txt` - Python dependencies
- `railway.toml` - Railway configuration
- `nixpacks.toml` - Build configuration
- `Procfile` - Process configuration
- `alembic/` - Database migrations
- `app/` - Application code

### 2. Deploy to Railway

1. **Connect Repository**:
   - Go to [Railway](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Choose the `backend` directory as the root

2. **Configure Environment Variables**:
   Set these variables in Railway dashboard:
   ```bash
   DATABASE_URL=sqlite:///./data/runner_attendance.db
   ENVIRONMENT=production
   LOG_LEVEL=INFO
   DEBUG=false
   QR_CODE_EXPIRY_HOURS=24
   CACHE_TTL=300
   MAX_CONCURRENT_REQUESTS=100
   FRONTEND_URL=https://your-frontend-domain.vercel.app
   ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app
   SECRET_KEY=your-secure-secret-key-here
   JWT_SECRET_KEY=your-jwt-secret-key-here
   ```

3. **Deploy**:
   - Railway will automatically build and deploy
   - Monitor logs for any issues
   - Note your Railway domain (e.g., `https://your-app.railway.app`)

### 3. Database Setup

The deployment automatically:
- Creates the `data/` directory for SQLite
- Runs Alembic migrations
- Sets up performance indexes
- Configures SQLite optimizations

## Frontend Deployment (Vercel)

### 1. Configure Environment Variables

In Vercel dashboard, set these variables:
```bash
REACT_APP_API_URL=https://your-backend-domain.railway.app
REACT_APP_WS_URL=https://your-backend-domain.railway.app
REACT_APP_ENVIRONMENT=production
```

### 2. Deploy to Vercel

1. **Connect Repository**:
   - Go to [Vercel](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repository
   - Set root directory to `frontend`

2. **Configure Build Settings**:
   - Build Command: `npm run build`
   - Output Directory: `build`
   - Install Command: `npm install`

3. **Deploy**:
   - Vercel will automatically build and deploy
   - Note your Vercel domain (e.g., `https://your-app.vercel.app`)

### 3. Update Backend CORS

After getting your Vercel domain:
1. Go back to Railway environment variables
2. Update `FRONTEND_URL` and `ALLOWED_ORIGINS` with your Vercel domain
3. Redeploy backend

## Post-Deployment Configuration

### 1. Test Deployment

1. **Backend Health Check**:
   ```bash
   curl https://your-backend-domain.railway.app/health
   ```

2. **Frontend Access**:
   - Visit your Vercel domain
   - Test admin dashboard functionality
   - Test runner registration flow

3. **WebSocket Connection**:
   - Check real-time updates work
   - Monitor browser console for errors

### 2. Monitoring Setup

The application includes built-in monitoring:

- **Health Endpoint**: `/health`
- **Metrics Endpoint**: `/api/monitoring/metrics`
- **Performance Stats**: `/api/performance/stats`

### 3. Logging

Production logs are available:
- **Railway**: View logs in Railway dashboard
- **Vercel**: View function logs in Vercel dashboard
- **Application**: Structured JSON logging enabled

## Security Configuration

### 1. Environment Variables

Generate secure keys:
```python
import secrets
print("SECRET_KEY:", secrets.token_urlsafe(32))
print("JWT_SECRET_KEY:", secrets.token_urlsafe(32))
```

### 2. CORS Configuration

- Never use `*` for ALLOWED_ORIGINS in production
- Specify exact domains
- Include both www and non-www if needed

### 3. Database Security

- SQLite file stored in Railway's persistent volume
- Not publicly accessible
- Automatic backups by Railway

## Scaling Considerations

### Free Tier Limits

**Railway Free Tier**:
- 500 hours/month execution time
- $5/month for additional resources
- Persistent storage included

**Vercel Free Tier**:
- 100GB bandwidth/month
- Unlimited deployments
- Custom domains supported

### Performance Optimization

The application includes:
- Database connection pooling
- Request rate limiting
- Caching strategies
- Performance monitoring
- Automatic cleanup of old data

## Troubleshooting

### Common Issues

1. **CORS Errors**:
   - Check ALLOWED_ORIGINS matches frontend domain exactly
   - Ensure no trailing slashes

2. **Database Errors**:
   - Check data directory permissions
   - Verify migrations ran successfully
   - Monitor Railway logs

3. **WebSocket Issues**:
   - Verify WS_URL matches API_URL
   - Check firewall/proxy settings

4. **Build Failures**:
   - Check all environment variables are set
   - Verify dependencies in requirements.txt/package.json

### Debug Commands

**Railway**:
```bash
# View logs
railway logs

# Check environment
railway run env

# Test database
railway run python -c "from app.database.connection import db_manager; print(db_manager.check_health())"
```

**Vercel**:
```bash
# Local build test
npm run build

# Check environment variables
vercel env ls
```

## Maintenance

### Regular Tasks

1. **Monitor Performance**:
   - Check `/api/monitoring/health` endpoint
   - Review Railway/Vercel dashboards
   - Monitor error rates

2. **Database Maintenance**:
   - Old logs automatically cleaned up
   - Performance metrics rotated
   - Monitor database size

3. **Updates**:
   - Keep dependencies updated
   - Monitor security advisories
   - Test updates in staging first

### Backup Strategy

- Railway provides automatic backups
- SQLite database persists across deployments
- Export attendance data regularly via CSV

## Support

For deployment issues:
1. Check Railway/Vercel status pages
2. Review application logs
3. Test health endpoints
4. Monitor performance metrics

## Cost Estimation

**Free Tier Usage**:
- Railway: Free for small university club usage
- Vercel: Free for typical traffic levels
- Total: $0/month for basic usage

**Paid Tier** (if needed):
- Railway: $5/month for additional resources
- Vercel: $20/month for pro features
- Total: $25/month maximum