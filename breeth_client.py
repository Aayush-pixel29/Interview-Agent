import os
import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

BREETH_BASE_URL = "https://www.thebreeth.com/api"

async def sync_to_breeth(session_id: str, action: str, data: Dict[str, Any]):
    """
    Asynchronously syncs session state and turns to Breeth persistent memory.
    Dynamically fetches BREETH_API_KEY from environment to avoid import timing issues.
    Fails non-blockingly so API calls remain fast and resilient during evaluation.
    """
    api_key = os.getenv("BREETH_API_KEY")
    if not api_key:
        logger.debug("BREETH_API_KEY not found in environment. Skipping Breeth memory sync.")
        return
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "sessionId": session_id,
        "action": action,
        "data": data
    }
    
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            await client.post(f"{BREETH_BASE_URL}/memory", json=payload, headers=headers)
    except Exception as e:
        logger.warning(f"[Breeth Memory Sync Notice]: {e}")