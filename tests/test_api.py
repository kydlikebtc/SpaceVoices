import pytest
from fastapi.testclient import TestClient

def test_create_script(client, sample_script):
    response = client.post("/api/v1/scripts", json=sample_script)
    assert response.status_code == 200
    assert "script_id" in response.json()

def test_create_script_invalid_character(client, sample_script):
    # Modify script to include invalid character
    sample_script["dialogue"].append({
        "character": "Charlie",  # Character not defined
        "text": "Hello there!",
        "pause_before": 0.0,
        "pause_after": 0.5
    })
    
    response = client.post("/api/v1/scripts", json=sample_script)
    assert response.status_code == 400
    assert "must reference existing characters" in response.json()["detail"]

@pytest.mark.asyncio
async def test_generate_podcast(client, sample_script, mock_voice_generator, mock_audio_processor):
    # First create a script
    response = client.post("/api/v1/scripts", json=sample_script)
    script_id = response.json()["script_id"]
    
    # Then generate podcast
    response = client.post(f"/api/v1/generate/{script_id}")
    assert response.status_code == 200
    assert "podcast_id" in response.json()

@pytest.mark.asyncio
async def test_publish_to_spaces(client, sample_script, mock_voice_generator, mock_audio_processor, mock_twitter_service):
    # Create script and generate podcast first
    response = client.post("/api/v1/scripts", json=sample_script)
    script_id = response.json()["script_id"]
    
    response = client.post(f"/api/v1/generate/{script_id}")
    podcast_id = response.json()["podcast_id"]
    
    # Then publish to spaces
    response = client.post(f"/api/v1/publish/{podcast_id}")
    assert response.status_code == 200
    assert "space_id" in response.json()
    assert response.json()["space_id"] == "mock_space_id"
