from typing import Optional
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def sample_script():
    return {
        "title": "Test Script",
        "characters": [
            {"name": "Alice", "voice_profile": "voice_1"},
            {"name": "Bob", "voice_profile": "voice_2"}
        ],
        "dialogue": [
            {
                "character": "Alice",
                "text": "Hello, how are you?",
                "pause_before": 0.0,
                "pause_after": 0.5
            },
            {
                "character": "Bob",
                "text": "I'm doing great, thanks!",
                "pause_before": 0.0,
                "pause_after": 0.5
            }
        ],
        "background_music": None
    }

@pytest.fixture
def mock_voice_generator(monkeypatch):
    class MockVoiceGenerator:
        async def generate_voice(self, text: str, voice_profile: str):
            import tempfile
            temp = tempfile.TemporaryFile()
            temp.write(b"mock audio data")
            temp.seek(0)
            return temp
    
    from app.services.voice_generator import ElevenLabsGenerator
    def mock_init(self):
        pass
    
    mock_gen = MockVoiceGenerator()
    monkeypatch.setattr(ElevenLabsGenerator, "__init__", mock_init)
    monkeypatch.setattr(ElevenLabsGenerator, "generate_voice", mock_gen.generate_voice)
    return mock_gen

@pytest.fixture
def mock_audio_processor(monkeypatch):
    class MockAudioProcessor:
        async def merge_audio_tracks(self, voice_tracks, background_music=None):
            import tempfile
            temp = tempfile.TemporaryFile()
            temp.write(b"mock merged audio data")
            temp.seek(0)
            return temp
        
        def __init__(self):
            pass
    
    from app.services.audio_processor import AudioProcessor
    mock_processor = MockAudioProcessor()
    monkeypatch.setattr(AudioProcessor, "__init__", MockAudioProcessor.__init__)
    monkeypatch.setattr(AudioProcessor, "merge_audio_tracks", mock_processor.merge_audio_tracks)
    return mock_processor

@pytest.fixture
def mock_twitter_service(monkeypatch):
    class MockTwitterService:
        async def create_space(self, title: str, description: Optional[str] = None):
            return "mock_space_id"
            
        async def start_space(self, space_id: str):
            return True
            
    from app.services.twitter_service import TwitterSpacesService
    def mock_init(self):
        pass
    
    mock_service = MockTwitterService()
    monkeypatch.setattr(TwitterSpacesService, "__init__", mock_init)
    monkeypatch.setattr(TwitterSpacesService, "create_space", mock_service.create_space)
    monkeypatch.setattr(TwitterSpacesService, "start_space", mock_service.start_space)
    return mock_service
