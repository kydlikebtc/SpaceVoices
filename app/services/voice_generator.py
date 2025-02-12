from abc import ABC, abstractmethod
from typing import BinaryIO, Optional
import os
import aiohttp
from dotenv import load_dotenv

load_dotenv()

class VoiceGenerationError(Exception):
    """Custom exception for voice generation failures."""
    pass

class VoiceGenerator(ABC):
    @abstractmethod
    async def generate_voice(
        self,
        text: str,
        voice_profile: str
    ) -> BinaryIO:
        """Generate voice audio from text using specified voice profile."""
        pass

class ElevenLabsGenerator(VoiceGenerator):
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY environment variable is not set")
        self.base_url = "https://api.elevenlabs.io/v1"
        
    async def generate_voice(
        self,
        text: str,
        voice_profile: str
    ) -> BinaryIO:
        """Generate voice using ElevenLabs API."""
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.75,
                "similarity_boost": 0.75
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/text-to-speech/{voice_profile}"
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise VoiceGenerationError(
                            f"ElevenLabs API error: {response.status} - {error_text}"
                        )
                    
                    # Create a temporary file to store the audio
                    import tempfile
                    temp_file = tempfile.TemporaryFile()
                    temp_file.write(await response.read())
                    temp_file.seek(0)
                    return temp_file
                    
        except aiohttp.ClientError as e:
            raise VoiceGenerationError(f"Network error: {str(e)}")
        except Exception as e:
            raise VoiceGenerationError(f"Unexpected error: {str(e)}")
