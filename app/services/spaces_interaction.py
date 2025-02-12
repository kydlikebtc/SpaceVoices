import asyncio
import logging
from typing import Dict, List, Callable, Optional
import time
import tweepy
from app.models.space_event import SpaceEvent

logger = logging.getLogger(__name__)

class SpacesInteractionService:
    """Service for managing Twitter Spaces interactions."""
    
    def __init__(self, twitter_client: tweepy.Client):
        """Initialize the service with a Twitter client."""
        self.client = twitter_client
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.active_spaces: Dict[str, asyncio.Task] = {}
        self.backoff_delay = 5  # Initial backoff delay in seconds
    
    def register_handler(self, event_type: str, handler: Callable):
        """Register an event handler for a specific event type."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def start_monitoring(self, space_id: str):
        """Start monitoring a Space."""
        if space_id in self.active_spaces:
            return
        task = asyncio.create_task(self._monitor_space(space_id))
        self.active_spaces[space_id] = task
    
    async def stop_monitoring(self, space_id: str):
        """Stop monitoring a Space."""
        if space_id in self.active_spaces:
            self.active_spaces[space_id].cancel()
            del self.active_spaces[space_id]
    
    async def _monitor_space(self, space_id: str):
        """Monitor a Space for events."""
        while True:
            try:
                # Get space info from Twitter
                space = await self._get_space_info(space_id)
                
                if not space:
                    logger.warning(f"Space {space_id} not found")
                    await self.stop_monitoring(space_id)
                    break
                
                # Create and emit event
                event = SpaceEvent(
                    type="space_update",
                    data={
                        "space_id": space_id,
                        "state": space.state,
                        "participant_count": space.participant_count
                    }
                )
                await self._emit_event(event)
                
                # Break if space is ended
                if space.state == "ended":
                    await self.stop_monitoring(space_id)
                    break
                
                # Reset backoff on successful request
                self.backoff_delay = 5
                
                # Wait before next poll
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error monitoring space {space_id}: {str(e)}")
                # Exponential backoff
                await asyncio.sleep(self.backoff_delay)
                self.backoff_delay = min(self.backoff_delay * 2, 60)
    
    async def _get_space_info(self, space_id: str) -> Optional[Dict]:
        """Get Space information from Twitter."""
        try:
            return await asyncio.to_thread(
                self.client.get_space,
                space_id,
                space_fields=["state", "participant_count"]
            )
        except Exception as e:
            logger.error(f"Error getting space info: {str(e)}")
            return None
    
    async def _emit_event(self, event: SpaceEvent):
        """Emit an event to registered handlers."""
        handlers = self.event_handlers.get(event.type, [])
        for handler in handlers:
            try:
                await asyncio.to_thread(handler, event)
            except Exception as e:
                logger.error(f"Error in event handler: {str(e)}")
