from typing import Optional, Dict
from datetime import datetime
import logging
import tweepy
from app.services.twitter_account_manager import TwitterAccountManager
from app.services.spaces_interaction import SpacesInteractionService

logger = logging.getLogger(__name__)

class TwitterSpacesError(Exception):
    """Custom exception for Twitter Spaces operations."""
    pass

class TwitterSpacesService:
    def __init__(self):
        """Initialize the service with multi-account support."""
        self.account_manager = TwitterAccountManager()
        self.interaction_services: Dict[str, SpacesInteractionService] = {}
    
    async def create_space(
        self,
        title: str,
        description: Optional[str] = None,
        character: str = "Host",
        scheduled_start: Optional[datetime] = None
    ) -> str:
        """
        Create a Twitter Space using a specific character's account.
        
        Args:
            title: Title of the Space
            description: Optional Space description
            character: Character name to use (defaults to "Host")
            scheduled_start: Optional scheduled start time
            
        Returns:
            str: Space ID
            
        Raises:
            ValueError: If character is invalid
            TwitterSpacesError: If space creation fails
        """
        try:
            # Get client for character
            client = self.account_manager.get_client(character)
            if not client:
                raise TwitterSpacesError(f"Invalid character: {character}")
            
            # Add AI disclosure to description
            ai_disclosure = "[AI-GENERATED CONTENT] This Space features AI-generated voices and content."
            full_description = f"{ai_disclosure}\n\n{description}" if description else ai_disclosure
            
            # Create the Space using create_tweet endpoint
            space = client.create_tweet(
                text=title,
                card_uri="twitter://spaces",
                scheduled_start=scheduled_start
            )
            
            if not space.data:
                raise TwitterSpacesError("Failed to create Space")
            
            space_id = space.data['id']
            
            # Create interaction service for this space
            interaction_service = SpacesInteractionService(client)
            self.interaction_services[character] = interaction_service
            
            # Start monitoring the space
            await interaction_service.start_monitoring(space_id)
            
            return space_id
            
        except tweepy.TweepyException as e:
            raise TwitterSpacesError(f"Twitter API error: {str(e)}")
        except Exception as e:
            raise TwitterSpacesError(f"Unexpected error: {str(e)}")
    
    async def start_space(self, space_id: str, character: str = "Host") -> bool:
        """Start a created Space using a specific character's account."""
        try:
            client = self.account_manager.get_client(character)
            if not client:
                raise ValueError(f"Invalid character: {character}")
                
            await client.start_space(space_id)
            return True
        except Exception as e:
            logger.error(f"Failed to start Space: {str(e)}")
            return False
    
    async def end_space(self, space_id: str, character: str = "Host") -> bool:
        """End an active Space using a specific character's account."""
        try:
            client = self.account_manager.get_client(character)
            if not client:
                raise ValueError(f"Invalid character: {character}")
            
            await client.end_space(space_id)
            
            # Stop monitoring if we were monitoring this space
            if character in self.interaction_services:
                await self.interaction_services[character].stop_monitoring(space_id)
                del self.interaction_services[character]
            
            return True
        except Exception as e:
            logger.error(f"Failed to end Space: {str(e)}")
            return False
    
    async def get_space_status(self, space_id: str, character: str = "Host") -> dict:
        """Get current status of a Space using a specific character's account."""
        try:
            client = self.account_manager.get_client(character)
            if not client:
                raise ValueError(f"Invalid character: {character}")
                
            space = await client.get_space(space_id)
            return space.data
        except Exception as e:
            logger.error(f"Failed to get Space status: {str(e)}")
            raise TwitterSpacesError(f"Failed to get Space status: {str(e)}")
