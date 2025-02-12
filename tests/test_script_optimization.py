import pytest
from app.models.script import Script, Character, DialogueLine
from app.services.script_parser import ScriptParser

@pytest.mark.asyncio
async def test_optimize_script():
    parser = ScriptParser()
    
    # Create a test script
    script = Script(
        title="Test Script",
        characters=[
            Character(name="Alice", voice_profile="voice_1"),
            Character(name="Bob", voice_profile="voice_2")
        ],
        dialogue=[
            DialogueLine(
                character="Alice",
                text="Hello! How are you today?",
                pause_before=0.5,
                pause_after=0.5
            ),
            DialogueLine(
                character="Bob",
                text="I'm feeling terrible.",
                pause_before=0.5,
                pause_after=0.5
            ),
            DialogueLine(
                character="Alice",
                text="What's your favorite color?",
                pause_before=0.5,
                pause_after=0.5
            )
        ]
    )
    
    # Optimize the script
    optimized = await parser.optimize_script(script)
    
    # Check that optimization didn't change basic structure
    assert len(optimized.dialogue) == len(script.dialogue)
    assert optimized.title == script.title
    assert optimized.characters == script.characters
    
    # Check that pauses were adjusted based on sentiment and coherence
    # First line (greeting) should have short pause
    assert optimized.dialogue[0].pause_after <= 0.3
    
    # Second line (negative sentiment) should have longer pause
    assert optimized.dialogue[1].pause_after >= 1.0
    
    # Third line (topic change) should have longer pause before
    assert optimized.dialogue[2].pause_before >= 1.0
