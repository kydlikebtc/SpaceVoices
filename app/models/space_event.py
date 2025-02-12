from pydantic import BaseModel
from typing import Dict, Any
import time

class SpaceEvent(BaseModel):
    """Model for Twitter Spaces events."""
    type: str = "space_update"  # Default event type
    data: Dict[str, Any]
    timestamp: float = time.time()  # Default to current time
