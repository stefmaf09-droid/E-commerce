"""
Health Check Endpoints for Production Monitoring

Provides health, readiness, and liveness endpoints for load balancers and monitoring.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
import psycopg2
import redis
import os
import psutil

app = FastAPI(title="Agent IA Recouvrement - Health Checks")


@app.get("/health")
def health_check():
    """
    Basic health check - returns 200 if service is up.
    
    Use this for simple uptime monitoring.
    """
    return {
        "status": "healthy",
        "service": "agent-ia-recouvrement",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.get("/health/live")
def liveness_check():
    """
    Liveness probe - checks if the application is alive.
    
    Returns 200 if process is running.
    Kubernetes uses this to restart unhealthy containers.
    """
    return {
        "status": "alive",
        "pid": os.getpid(),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health/ready")
async def readiness_check():
    """
    Readiness probe - checks if service is ready to accept traffic.
    
    Verifies all dependencies are available:
    - Database connection
    - Redis connection
    - Disk space
    
    Returns 200 if ready, 503 if not.
    """
    checks = {}
    all_ready = True
    
    # Check database
    try:
        db_status = await check_database()
        checks['database'] = db_status
        if db_status['status'] != 'healthy':
            all_ready = False
    except Exception as e:
        checks['database'] = {'status': 'unhealthy', 'error': str(e)}
        all_ready = False
    
    # Check Redis
    try:
        redis_status = await check_redis()
        checks['redis'] = redis_status
        if redis_status['status'] != 'healthy':
            all_ready = False
    except Exception as e:
        checks['redis'] = {'status': 'unhealthy', 'error': str(e)}
        all_ready = False
    
    # Check disk space (need at least 10% free)
    try:
        disk_status = check_disk_space()
        checks['disk'] = disk_status
        if disk_status['percent_free'] < 10:
            all_ready = False
    except Exception as e:
        checks['disk'] = {'status': 'unknown', 'error': str(e)}
    
    # Check memory (warn if > 90%)
    try:
        memory = psutil.virtual_memory()
        checks['memory'] = {
            'percent_used': memory.percent,
            'status': 'healthy' if memory.percent < 90 else 'warning'
        }
    except:
        pass
    
    response = {
        "ready": all_ready,
        "timestamp": datetime.now().isoformat(),
        "checks": checks
    }
    
    status_code = 200 if all_ready else 503
    return JSONResponse(content=response, status_code=status_code)


async def check_database():
    """Check PostgreSQL database connection."""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        return {
            'status': 'unconfigured',
            'message': 'DATABASE_URL not set'
        }
    
    try:
        import time
        start_time = time.time()
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        cursor.close()
        conn.close()
        
        latency_ms = round((time.time() - start_time) * 1000, 2)
        
        return {
            'status': 'healthy',
            'latency_ms': latency_ms
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }


async def check_redis():
    """Check Redis connection."""
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    try:
        r = redis.from_url(redis_url)
        r.ping()
        r.close()
        
        return {
            'status': 'healthy'
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }


def check_disk_space():
    """Check available disk space."""
    disk = psutil.disk_usage('/')
    
    return {
        'total_gb': round(disk.total / (1024**3), 2),
        'used_gb': round(disk.used / (1024**3), 2),
        'free_gb': round(disk.free / (1024**3), 2),
        'percent_free': round((disk.free / disk.total) * 100, 2),
        'status': 'healthy' if (disk.free / disk.total) > 0.1 else 'critical'
    }


@app.get("/metrics")
def metrics():
    """
    Prometheus-compatible metrics endpoint.
    
    Returns metrics in Prometheus text format.
    """
    # Basic metrics (expand as needed)
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    metrics_text = f"""
# HELP system_cpu_percent CPU usage percentage
# TYPE system_cpu_percent gauge
system_cpu_percent {cpu_percent}

# HELP system_memory_percent Memory usage percentage
# TYPE system_memory_percent gauge
system_memory_percent {memory.percent}

# HELP system_disk_percent Disk usage percentage
# TYPE system_disk_percent gauge
system_disk_percent {disk.percent}
"""
    
    return Response(content=metrics_text.strip(), media_type="text/plain")


# Run with: uvicorn src.health_check:app --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
