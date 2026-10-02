# app/services/container.py
from functools import lru_cache
from app.services.rest_storage_client import RESTStorageClient
from app.services.storage import Storage

@lru_cache
def get_storage() -> Storage:
    """
    Returns a singleton-like instance of the storage layer.

    - Uses lazy initialization
    - Allows future replacement (e.g., PostgresStorage)
    - Avoids uncontrolled global state
    
    """
    return RESTStorageClient()
# ======================================================
