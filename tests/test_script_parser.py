import pytest
from app.models.script import Script, Character, DialogueLine
from app.services.script_parser import ScriptParser

def test_validate_characters_valid():
    script = Script(
        title="Test Script",
        characters=[
            Character(name="Alice", voice_profile="voice_1"),
            Character(name="Bob", voice_profile="voice_2")
        ],
        dialogue=[
            DialogueLine(character="Alice", text="Hello"),
            DialogueLine(character="Bob", text="Hi")
        ]
    )
    assert ScriptParser.validate_characters(script) is True

def test_validate_characters_invalid():
    script = Script(
        title="Test Script",
        characters=[
            Character(name="Alice", voice_profile="voice_1")
        ],
        dialogue=[
            DialogueLine(character="Alice", text="Hello"),
            DialogueLine(character="Bob", text="Hi")  # Bob is not defined
        ]
    )
    assert ScriptParser.validate_characters(script) is False

def test_get_character_voice_map():
    script = Script(
        title="Test Script",
        characters=[
            Character(name="Alice", voice_profile="voice_1"),
            Character(name="Bob", voice_profile="voice_2")
        ],
        dialogue=[]
    )
    voice_map = ScriptParser.get_character_voice_map(script)
    assert voice_map == {"Alice": "voice_1", "Bob": "voice_2"}

def test_get_total_duration():
    script = Script(
        title="Test Script",
        characters=[Character(name="Alice", voice_profile="voice_1")],
        dialogue=[
            DialogueLine(
                character="Alice",
                text="Hello",
                pause_before=1.0,
                pause_after=0.5
            ),
            DialogueLine(
                character="Alice",
                text="World",
                pause_before=0.5,
                pause_after=1.0
            )
        ]
    )
    total_duration = ScriptParser.get_total_duration(script)
    assert total_duration == 3.0  # 1.0 + 0.5 + 0.5 + 1.0
