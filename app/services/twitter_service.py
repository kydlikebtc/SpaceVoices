from typing import Optional
from datetime import datetime
import os
import tweepy
from dotenv import load_dotenv

load_dotenv()

class TwitterSpacesError(Exception):
    """Custom exception for Twitter Spaces operations."""
    pass

class TwitterSpacesService:
    def __init__(self):
        self.api_key = os.getenv("TWITTER_API_KEY")
        self.api_secret = os.getenv("TWITTER_API_SECRET")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            raise ValueError("Missing required Twitter API credentials in environment variables")
        
        # Initialize Twitter client
        self.client = tweepy.Client(
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret
        )
        
        # Initialize API v1.1 for some Spaces features not available in v2
        auth = tweepy.OAuth1UserHandler(
            self.api_key,
            self.api_secret,
            self.access_token,
            self.access_token_secret
        )
        self.api = tweepy.API(auth)
    
    async def create_space(
        self,
        title: str,
        scheduled_start: Optional[datetime] = None,
        description: Optional[str] = None
    ) -> str:
        """
        Create a Twitter Space.
        
        Args:
            title: Title of the Space
            scheduled_start: Optional scheduled start time
            description: Optional Space description
            
        Returns:
            str: Space ID
        """
        try:
            # Add AI disclosure to description
            ai_disclosure = "[AI-GENERATED CONTENT] This Space features AI-generated voices and content."
            full_description = f"{ai_disclosure}\n\n{description}" if description else ai_disclosure
            
            # Create the Space
            space = self.client.create_space(
                title=title,
                scheduled_start=scheduled_start,
                topic_ids=None  # Optional: Add relevant topic IDs
            )
            
            if not space.data:
                raise TwitterSpacesError("Failed to create Space")
            
            space_id = space.data['id']
            
            # Update Space with description (using v1.1 API)
            self.api.update_space(space_id, description=full_description)
            
            return space_id
            
        except tweepy.TweepyException as e:
            raise TwitterSpacesError(f"Twitter API error: {str(e)}")
        except Exception as e:
            raise TwitterSpacesError(f"Unexpected error: {str(e)}")
    
    async def start_space(self, space_id: str) -> bool:
        """Start a created Space."""
        try:
            self.api.start_space(space_id)
            return True
        except tweepy.TweepyException as e:
            raise TwitterSpacesError(f"Failed to start Space: {str(e)}")
    
    async def end_space(self, space_id: str) -> bool:
        """End an active Space."""
        try:
            self.api.end_space(space_id)
            return True
        except tweepy.TweepyException as e:
            raise TwitterSpacesError(f"Failed to end Space: {str(e)}")
    
    async def get_space_status(self, space_id: str) -> dict:
        """Get current status of a Space."""
        try:
            space = self.client.get_space(space_id)
            return space.data
        except tweepy.TweepyException as e:
            raise TwitterSpacesError(f"Failed to get Space status: {str(e)}")
