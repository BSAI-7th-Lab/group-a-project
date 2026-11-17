from fastapi import FastAPI
import redis
import os

app = FastAPI(title="SwarmDining Backend", version="1.0.0")

# Redis connection 
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL)

@app.get("/")
def read_root():
    return {"message": "Welcome to SwarmDining Backend API!"}

@app.get("/health")
def health_check():
    try:
        # Check if Redis is responding
        redis_client.ping()
        redis_status = "connected"
    except Exception as e:
        redis_status = f"disconnected: {str(e)}"
        
    return {
        "status": "healthy",
        "system": "SwarmDining State Blackboard Active",
        "redis": redis_status
    }