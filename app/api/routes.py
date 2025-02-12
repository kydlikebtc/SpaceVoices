from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict
from app.models.script import Script
from app.services.script_parser import ScriptParser
from app.services.voice_generator import ElevenLabsGenerator, VoiceGenerationError
from app.services.audio_processor import AudioProcessor, AudioProcessingError
from app.services.twitter_service import TwitterSpacesService, TwitterSpacesError

router = APIRouter()

# In-memory storage for demo purposes
scripts_db = {}
podcasts_db = {}

@router.post("/scripts", response_model=Dict[str, int])
async def create_script(script: Script):
    """Create a new script."""
    try:
        # Validate characters in dialogue
        if not ScriptParser.validate_characters(script):
            raise HTTPException(
                status_code=400,
                detail="All dialogue lines must reference existing characters"
            )
        
        # Store script (using simple incremental ID for demo)
        script_id = len(scripts_db) + 1
        scripts_db[script_id] = script
        
        return {"script_id": script_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate/{script_id}", response_model=Dict[str, int])
async def generate_podcast(script_id: int, background_tasks: BackgroundTasks):
    """Generate podcast from script."""
    try:
        script = scripts_db.get(script_id)
        if not script:
            raise HTTPException(status_code=404, detail="Script not found")
        
        # Initialize services
        voice_generator = ElevenLabsGenerator()
        audio_processor = AudioProcessor()
        
        # Get character voice mapping
        voice_map = ScriptParser.get_character_voice_map(script)
        
        # Generate voice for each dialogue line
        voice_tracks = []
        for line in script.dialogue:
            voice_profile = voice_map[line.character]
            audio = await voice_generator.generate_voice(line.text, voice_profile)
            voice_tracks.append(audio)
        
        # Process audio
        final_audio = await audio_processor.merge_audio_tracks(voice_tracks)
        
        # Store podcast (using simple incremental ID for demo)
        podcast_id = len(podcasts_db) + 1
        podcasts_db[podcast_id] = final_audio
        
        return {"podcast_id": podcast_id}
        
    except VoiceGenerationError as e:
        raise HTTPException(status_code=500, detail=f"Voice generation failed: {str(e)}")
    except AudioProcessingError as e:
        raise HTTPException(status_code=500, detail=f"Audio processing failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/publish/{podcast_id}", response_model=Dict[str, str])
async def publish_to_spaces(podcast_id: int):
    """Publish podcast to Twitter Spaces."""
    try:
        podcast = podcasts_db.get(podcast_id)
        if not podcast:
            raise HTTPException(status_code=404, detail="Podcast not found")
        
        # Initialize Twitter service
        twitter_service = TwitterSpacesService()
        
        # Create and start space
        space_id = await twitter_service.create_space(
            title=f"AI Podcast #{podcast_id}",
            description="An AI-generated podcast episode"
        )
        
        await twitter_service.start_space(space_id)
        
        return {"space_id": space_id}
        
    except TwitterSpacesError as e:
        raise HTTPException(status_code=500, detail=f"Twitter Spaces error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
