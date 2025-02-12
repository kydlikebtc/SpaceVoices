from pydantic import BaseModel, Field

class TwitterAccount(BaseModel):
    """Model for storing Twitter account credentials."""
    character_name: str = Field(..., description="Name of the character this account represents")
    api_key: str = Field(..., description="Twitter API key")
    api_secret: str = Field(..., description="Twitter API secret")
    access_token: str = Field(..., description="Twitter access token")
    access_token_secret: str = Field(..., description="Twitter access token secret")
