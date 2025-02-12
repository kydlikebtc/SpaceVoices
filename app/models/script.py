from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Character(BaseModel):
    name: str = Field(..., description="Name of the character in the script")
    voice_profile: str = Field(..., description="Voice profile identifier for the character")

class DialogueLine(BaseModel):
    character: str = Field(..., description="Name of the character speaking this line")
    text: str = Field(..., description="The actual dialogue text")
    pause_before: float = Field(default=0.0, description="Pause duration in seconds before this line")
    pause_after: float = Field(default=0.5, description="Pause duration in seconds after this line")

class Script(BaseModel):
    title: str = Field(..., description="Title of the script/episode")
    characters: List[Character] = Field(..., description="List of characters in the script")
    dialogue: List[DialogueLine] = Field(..., description="List of dialogue lines in order")
    background_music: Optional[str] = Field(None, description="Optional background music track identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
