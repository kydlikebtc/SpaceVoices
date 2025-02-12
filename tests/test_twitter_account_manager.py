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

@pytest.fixture
def mock_browser_env(monkeypatch):
    """Set up mock environment variables for browser testing."""
    env_vars = {
        "TWITTER_BROWSER_1_CHARACTER": "Host",
        "TWITTER_BROWSER_1_USERNAME": "host_user",
        "TWITTER_BROWSER_1_PASSWORD": "host_pass",
        "TWITTER_BROWSER_2_CHARACTER": "Alice",
        "TWITTER_BROWSER_2_USERNAME": "alice_user",
        "TWITTER_BROWSER_2_PASSWORD": "alice_pass"
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars

def test_load_browser_accounts(mock_browser_env):
    manager = TwitterAccountManager()
    
    # Test browser accounts were loaded
    assert len(manager.browser_accounts) == 2
    assert "Host" in manager.browser_accounts
    assert "Alice" in manager.browser_accounts
    
    # Check account details
    host = manager.browser_accounts["Host"]
    assert host["username"] == "host_user"
    assert host["password"] == "host_pass"

def test_get_browser_credentials(mock_browser_env):
    manager = TwitterAccountManager()
    
    # Test getting existing account credentials
    creds = manager.get_browser_credentials("Host")
    assert creds is not None
    assert creds["username"] == "host_user"
    assert creds["password"] == "host_pass"
    
    # Test getting non-existent account credentials
    assert manager.get_browser_credentials("NonExistent") is None
