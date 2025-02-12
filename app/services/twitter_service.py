from typing import Optional, Dict
from datetime import datetime
import logging
import tweepy
from app.services.twitter_account_manager import TwitterAccountManager
from app.services.spaces_interaction import SpacesInteractionService
from app.services.twitter_browser_service import TwitterBrowserService

logger = logging.getLogger(__name__)

class TwitterSpacesError(Exception):
    """Custom exception for Twitter Spaces operations."""
    pass

class TwitterSpacesService:
    def __init__(self):
        """Initialize the service with multi-account support."""
        from app.services.feature_flags import FeatureFlags
        from app.services.twitter_browser_service import TwitterBrowserService
        
        self.feature_flags = FeatureFlags()
        self.account_manager = TwitterAccountManager()
        self.interaction_services: Dict[str, SpacesInteractionService] = {}
        
        if self.feature_flags.is_enabled("use_browser_automation"):
            self.browser_service = TwitterBrowserService()
        else:
            self.browser_service = None
    
    async def _create_space_api(
        self,
        title: str,
        description: Optional[str] = None,
        character: str = "Host",
        scheduled_start: Optional[datetime] = None
    ) -> str:
        """
        Internal method for creating a Space using Twitter API.
        
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
    
    async def create_space(
        self,
        title: str,
        description: Optional[str] = None,
        character: str = "Host",
        scheduled_start: Optional[datetime] = None
    ) -> str:
        """
        Create a Twitter Space using either API or browser automation.
        
        Args:
            title: Title of the Space
            description: Optional Space description
            character: Character name to use (defaults to "Host")
            scheduled_start: Optional scheduled start time
            
        Returns:
            str: Space ID
            
        Raises:
            TwitterSpacesError: If space creation fails
        """
        if self.feature_flags.is_enabled("use_browser_automation"):
            # Get browser credentials
            credentials = self.account_manager.get_browser_credentials(character)
            if not credentials:
                raise TwitterSpacesError(f"No browser credentials for character: {character}")
                
            # Login and create space
            await self.browser_service.login(credentials["username"], credentials["password"])
            space_id = await self.browser_service.create_space(title)
            if not space_id:
                raise TwitterSpacesError("Failed to create Space using browser automation")
                
            return space_id
        else:
            # Use API implementation
            return await self._create_space_api(title, description, character, scheduled_start)
    
    async def _start_space_api(self, space_id: str, character: str = "Host") -> bool:
        """Internal method for starting a Space using Twitter API."""
        try:
            client = self.account_manager.get_client(character)
            if not client:
                raise ValueError(f"Invalid character: {character}")
                
            await client.start_space(space_id)
            return True
        except Exception as e:
            logger.error(f"Failed to start Space: {str(e)}")
            return False
    
    async def start_space(self, space_id: str, character: str = "Host") -> bool:
        """
        Start a created Space using either API or browser automation.
        
        Args:
            space_id: ID of the Space to start
            character: Character name to use (defaults to "Host")
            
        Returns:
            bool: True if successful
        """
        if self.feature_flags.is_enabled("use_browser_automation"):
            credentials = self.account_manager.get_browser_credentials(character)
            if not credentials:
                raise TwitterSpacesError(f"No browser credentials for character: {character}")
                
            await self.browser_service.login(credentials["username"], credentials["password"])
            return True  # Space is started automatically in browser automation
        else:
            return await self._start_space_api(space_id, character)
    
    async def _end_space_api(self, space_id: str, character: str = "Host") -> bool:
        """Internal method for ending a Space using Twitter API."""
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
    
    async def end_space(self, space_id: str, character: str = "Host") -> bool:
        """
        End an active Space using either API or browser automation.
        
        Args:
            space_id: ID of the Space to end
            character: Character name to use (defaults to "Host")
            
        Returns:
            bool: True if successful
        """
        if self.feature_flags.is_enabled("use_browser_automation"):
            credentials = self.account_manager.get_browser_credentials(character)
            if not credentials:
                raise TwitterSpacesError(f"No browser credentials for character: {character}")
                
            await self.browser_service.login(credentials["username"], credentials["password"])
            success = await self.browser_service.end_space(space_id)
            
            # Stop monitoring if we were monitoring this space
            if character in self.interaction_services:
                await self.interaction_services[character].stop_monitoring(space_id)
                del self.interaction_services[character]
            
            return success
        else:
            return await self._end_space_api(space_id, character)
    
    async def get_space_status(self, space_id: str, character: str = "Host") -> dict:
        """
        Get current status of a Space using either API or browser automation.
        
        Args:
            space_id: ID of the Space to check
            character: Character name to use (defaults to "Host")
            
        Returns:
            dict: Space status information
            
        Raises:
            TwitterSpacesError: If status check fails
        """
        if self.feature_flags.is_enabled("use_browser_automation"):
            credentials = self.account_manager.get_browser_credentials(character)
            if not credentials:
                raise TwitterSpacesError(f"No browser credentials for character: {character}")
                
            await self.browser_service.login(credentials["username"], credentials["password"])
            return {"id": space_id, "state": "live"}  # Basic status for browser automation
        else:
            return await self._get_space_status_api(space_id, character)
            
    async def _get_space_status_api(self, space_id: str, character: str = "Host") -> dict:
        """Internal method for getting Space status using Twitter API."""
        try:
            client = self.account_manager.get_client(character)
            if not client:
                raise ValueError(f"Invalid character: {character}")
                
            space = await client.get_space(space_id)
            return space.data
        except Exception as e:
            logger.error(f"Failed to get Space status: {str(e)}")
            raise TwitterSpacesError(f"Failed to get Space status: {str(e)}")
            
    async def cleanup(self):
        """Clean up resources."""
        if self.browser_service:
            self.browser_service.cleanup()
            self.browser_service = None
