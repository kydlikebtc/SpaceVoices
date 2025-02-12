import pytest
from unittest.mock import Mock, patch
from app.services.nlp_optimizer import NLPOptimizer
from app.services.resource_manager import ResourceError
from app.models.script import DialogueLine

@pytest.fixture
def nlp_optimizer():
    return NLPOptimizer()

@pytest.mark.asyncio
async def test_optimize_dialogue_with_available_resources(nlp_optimizer):
    with patch('app.services.resource_manager.ResourceManager.check_resources', return_value=True):
        lines = [
            DialogueLine(
                character="Alice",
                text="Hello! How are you?",
                pause_before=0.5,
                pause_after=0.5
            )
        ]
        
        # Should not raise ResourceError
        result = await nlp_optimizer.optimize_dialogue(lines)
        assert len(result) == 1
        assert result[0].text == "Hello! How are you?"

@pytest.mark.asyncio
async def test_optimize_dialogue_with_exceeded_resources(nlp_optimizer):
    with patch('app.services.resource_manager.ResourceManager.check_resources', return_value=False):
        lines = [
            DialogueLine(
                character="Alice",
                text="Hello! How are you?",
                pause_before=0.5,
                pause_after=0.5
            )
        ]
        
        # Should raise ResourceError
        with pytest.raises(ResourceError, match="System resources exceeded limits"):
            await nlp_optimizer.optimize_dialogue(lines)
