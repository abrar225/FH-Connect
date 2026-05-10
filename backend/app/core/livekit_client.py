import os
from typing import Optional
from contextlib import asynccontextmanager

from livekit import api
from app.core.logging import get_logger

logger = get_logger("livekit_client")


class LiveKitClient:
    """Singleton LiveKit client to avoid repeated instantiation."""
    
    _instance: Optional[api.LiveKitAPI] = None
    
    @classmethod
    def get_client(cls) -> api.LiveKitAPI:
        """Get or create the LiveKit API client."""
        if cls._instance is None:
            livekit_url = os.getenv("LIVEKIT_URL")
            api_key = os.getenv("LIVEKIT_API_KEY")
            api_secret = os.getenv("LIVEKIT_API_SECRET")
            
            if not livekit_url or not api_key or not api_secret:
                raise RuntimeError("LiveKit configuration missing")
            
            cls._instance = api.LiveKitAPI(livekit_url, api_key, api_secret)
            logger.info("LiveKit client initialized")
        
        return cls._instance
    
    @classmethod
    async def close(cls):
        """Close the client connection."""
        if cls._instance:
            await cls._instance.aclose()
            cls._instance = None
            logger.info("LiveKit client closed")


@asynccontextmanager
async def get_livekit():
    """Context manager for LiveKit client with automatic cleanup."""
    client = LiveKitClient.get_client()
    try:
        yield client
    finally:
        pass  # Client managed as singleton, no per-request cleanup