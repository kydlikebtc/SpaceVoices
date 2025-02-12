import pytest
from app.services.content_moderator import ContentModerator

@pytest.fixture
def moderator():
    return ContentModerator()

@pytest.mark.asyncio
async def test_moderate_safe_content(moderator):
    text = """
    [AI-GENERATED CONTENT]
    Alice: Hello! How are you today?
    Bob: I'm doing great, thanks for asking!
    """
    
    results = await moderator.moderate_script(text)
    assert results["is_safe"] == True
    assert len(results["warnings"]) == 0

@pytest.mark.asyncio
async def test_moderate_missing_disclosure(moderator):
    text = """
    Alice: Hello! How are you today?
    Bob: I'm doing great, thanks for asking!
    """
    
    results = await moderator.moderate_script(text)
    assert "Add AI content disclosure" in results["recommendations"]

@pytest.mark.asyncio
async def test_moderate_sensitive_content(moderator):
    text = """
    [AI-GENERATED CONTENT]
    Alice: I'm feeling absolutely terrible and hopeless.
    Bob: Everything is going wrong and it's all meaningless.
    """
    
    results = await moderator.moderate_script(text)
    assert results["is_safe"] == False
    assert "sensitive material" in results["warnings"][0].lower()

@pytest.mark.asyncio
async def test_tos_compliance(moderator):
    # Create a very long text that exceeds limits
    long_text = "A" * 30000
    
    results = await moderator.moderate_script(long_text)
    assert any("limit" in warning.lower() for warning in results["warnings"])

@pytest.mark.asyncio
async def test_get_required_disclosures(moderator):
    disclosures = moderator.get_required_disclosures()
    assert "ai_disclosure" in disclosures
    assert "tos_compliance" in disclosures
    assert "AI-GENERATED CONTENT" in disclosures["ai_disclosure"]
