# Performance Optimization Recommendations

## Current Capacity: ~20-30 Concurrent Users
## Target Capacity: 100+ Concurrent Users

### 1. Backend Optimizations (Railway)

#### A. Multi-Worker Configuration
```python
# Update Procfile
web: python -m gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --max-requests 1000 --max-requests-jitter 100 --preload
```

#### B. Connection Pool Optimization
```python
# In database/connection.py
if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=5,          # Reduced for free tier
        max_overflow=10,      # Reduced for free tier  
        pool_pre_ping=True,
        pool_recycle=300,
        pool_timeout=10,      # Reduced timeout
        echo=False,
    )
```

#### C. Add Request Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/attendance/register")
@limiter.limit("10/minute")  # Limit registrations per IP
async def register_attendance(request: Request, ...):
    pass
```

### 2. Frontend Optimizations (Vercel)

#### A. Static Site Generation
- Pre-build admin dashboard as static pages
- Use client-side routing to reduce function calls

#### B. Request Batching
```typescript
// Batch multiple requests
const batchRequests = async (requests: Promise<any>[]) => {
  return Promise.allSettled(requests);
};
```

#### C. Caching Strategy
```typescript
// Add service worker for caching
// Cache API responses for 30 seconds
const CACHE_DURATION = 30000;
```

### 3. Database Optimizations

#### A. Add Database Indexes
```sql
CREATE INDEX idx_attendance_run_id ON attendances(run_id);
CREATE INDEX idx_attendance_registered_at ON attendances(registered_at);
CREATE INDEX idx_runs_date_active ON runs(date, is_active);
```

#### B. Connection Pooling
```python
# Use connection pooling service like PgBouncer
DATABASE_URL = "postgresql://user:pass@host:port/db?pgbouncer=true"
```

### 4. Architecture Changes for Scale

#### A. Move to Paid Tiers
- **Railway Pro**: $5/month - 8GB RAM, 8 vCPU
- **Vercel Pro**: $20/month - Unlimited functions, higher limits

#### B. Alternative Free Solutions
- **Backend**: Render.com (512MB free), Fly.io (256MB free)
- **Database**: Supabase (500MB free), PlanetScale (5GB free)
- **Frontend**: Netlify (100GB bandwidth free)

#### C. Microservices Split
```
┌─────────────────┐    ┌─────────────────┐
│   Registration  │    │   Admin Panel   │
│   Service       │    │   Service       │
│   (High Load)   │    │   (Low Load)    │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────────────────┘
                     │
         ┌─────────────────┐
         │   Database      │
         │   Service       │
         └─────────────────┘
```

### 5. Immediate Quick Fixes

#### A. Add Gunicorn Workers
```bash
pip install gunicorn
# Update Procfile
web: gunicorn app.main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
```

#### B. Optimize Database Queries
```python
# Use bulk operations
session.bulk_insert_mappings(Attendance, attendance_data)
session.commit()
```

#### C. Add Response Compression
```python
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### 6. Monitoring & Alerts

#### A. Add Performance Monitoring
```python
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

#### B. Health Check Endpoints
```python
@app.get("/health/detailed")
async def detailed_health():
    return {
        "database": db_manager.check_health(),
        "memory_usage": get_memory_usage(),
        "active_connections": db_manager.get_pool_status(),
    }
```

## Estimated Capacity After Optimizations

### With Current Free Tiers + Optimizations:
- **Concurrent Users**: 40-50
- **Peak Load**: 60-70 users for short periods

### With Paid Tiers:
- **Railway Pro + Vercel Pro**: 200+ concurrent users
- **Cost**: ~$25/month total

### Alternative Free Stack:
- **Render + Supabase + Netlify**: 80-100 concurrent users
- **Cost**: $0/month