import os
import pytest
import tweepy
from app.services.twitter_account_manager import TwitterAccountManager

@pytest.fixture
def mock_env(monkeypatch):
    """Set up mock environment variables for testing."""
    env_vars = {
        "TWITTER_ACCOUNT_1_CHARACTER": "Alice",
        "TWITTER_ACCOUNT_1_API_KEY": "key1",
        "TWITTER_ACCOUNT_1_API_SECRET": "secret1",
        "TWITTER_ACCOUNT_1_ACCESS_TOKEN": "token1",
        "TWITTER_ACCOUNT_1_ACCESS_TOKEN_SECRET": "token_secret1",
        "TWITTER_ACCOUNT_2_CHARACTER": "Bob",
        "TWITTER_ACCOUNT_2_API_KEY": "key2",
        "TWITTER_ACCOUNT_2_API_SECRET": "secret2",
        "TWITTER_ACCOUNT_2_ACCESS_TOKEN": "token2",
        "TWITTER_ACCOUNT_2_ACCESS_TOKEN_SECRET": "token_secret2"
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

def test_load_accounts(mock_env):
    manager = TwitterAccountManager()
    
    # Check that both accounts were loaded
    assert len(manager.accounts) == 2
    assert "Alice" in manager.accounts
    assert "Bob" in manager.accounts
    
    # Check account details
    alice = manager.accounts["Alice"]
    assert alice.character_name == "Alice"
    assert alice.api_key == "key1"
    assert alice.api_secret == "secret1"
    assert alice.access_token == "token1"
    assert alice.access_token_secret == "token_secret1"

def test_get_account(mock_env):
    manager = TwitterAccountManager()
    
    # Test getting existing account
    alice = manager.get_account("Alice")
    assert alice is not None
    assert alice.character_name == "Alice"
    
    # Test getting non-existent account
    assert manager.get_account("Charlie") is None

def test_get_client(mock_env):
    manager = TwitterAccountManager()
    
    # Test getting client for existing account
    client = manager.get_client("Alice")
    assert client is not None
    assert isinstance(client, tweepy.Client)
    
    # Test getting client for non-existent account
    assert manager.get_client("Charlie") is None
