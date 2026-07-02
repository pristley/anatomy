from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get('/')
def monitoring_snapshot():
    # return a simple simulated snapshot for polling clients
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "timeseries": [],
        "timeline": [],
        "tools": [],
    }


@router.get('/timeline')
def monitoring_timeline(limit: int = 50):
    return {"timeline": [], "limit": limit}
