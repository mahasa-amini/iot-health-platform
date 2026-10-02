from fastapi import APIRouter, HTTPException
from datetime import datetime
from src.core.config_loader import load_config

router = APIRouter()


@router.get("/")
def get_services():
    try:
        data = load_config("services.json")
        return {
            "status": "success",
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
