from typing import Dict, Optional
import os
from dotenv import load_dotenv
import tweepy
from app.models.twitter_account import TwitterAccount

class TwitterAccountManager:
    """Service for managing multiple Twitter accounts."""
    
    def __init__(self):
        """Initialize the account manager and load accounts from environment."""
        self.accounts: Dict[str, TwitterAccount] = {}
        self._load_accounts()
    
    def _load_accounts(self):
        """Load accounts from environment variables."""
        load_dotenv()
        account_prefix = "TWITTER_ACCOUNT_"
        i = 1
        while True:
            base_key = f"{account_prefix}{i}"
            if not os.getenv(f"{base_key}_CHARACTER"):
                break
                
            self.accounts[os.getenv(f"{base_key}_CHARACTER")] = TwitterAccount(
                character_name=os.getenv(f"{base_key}_CHARACTER"),
                api_key=os.getenv(f"{base_key}_API_KEY"),
                api_secret=os.getenv(f"{base_key}_API_SECRET"),
                access_token=os.getenv(f"{base_key}_ACCESS_TOKEN"),
                access_token_secret=os.getenv(f"{base_key}_ACCESS_TOKEN_SECRET")
            )
            i += 1
    
    def get_account(self, character_name: str) -> Optional[TwitterAccount]:
        """Get Twitter account by character name."""
        return self.accounts.get(character_name)
    
    def get_client(self, character_name: str) -> Optional[tweepy.Client]:
        """Get Tweepy client for a character's account."""
        account = self.get_account(character_name)
        if not account:
            return None
            
        return tweepy.Client(
            consumer_key=account.api_key,
            consumer_secret=account.api_secret,
            access_token=account.access_token,
            access_token_secret=account.access_token_secret
        )
