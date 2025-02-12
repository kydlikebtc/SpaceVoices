from typing import List, Dict
from app.models.script import Script, Character, DialogueLine

class ScriptParser:
    @staticmethod
    def validate_characters(script: Script) -> bool:
        """Validate that all dialogue lines reference existing characters."""
        character_names = {char.name for char in script.characters}
        for line in script.dialogue:
            if line.character not in character_names:
                return False
        return True

    @staticmethod
    def get_character_voice_map(script: Script) -> Dict[str, str]:
        """Create a mapping of character names to their voice profiles."""
        return {char.name: char.voice_profile for char in script.characters}

    @staticmethod
    def get_total_duration(script: Script) -> float:
        """Calculate approximate total duration based on pauses."""
        return sum(line.pause_before + line.pause_after for line in script.dialogue)
