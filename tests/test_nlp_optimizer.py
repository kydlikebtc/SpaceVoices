import pytest
from app.models.script import DialogueLine
from app.services.nlp_optimizer import NLPOptimizer

@pytest.mark.asyncio
async def test_analyze_sentiment():
    optimizer = NLPOptimizer()
    
    # Test positive sentiment
    positive_text = "I'm so happy and excited!"
    score = await optimizer._analyze_sentiment(positive_text)
    assert score > 0.7  # Should be very positive
    
    # Test negative sentiment
    negative_text = "This is terrible and disappointing."
    score = await optimizer._analyze_sentiment(negative_text)
    assert score < 0.3  # Should be very negative

@pytest.mark.asyncio
async def test_check_coherence():
    optimizer = NLPOptimizer()
    
    # Test coherent dialogue with common important words
    prev_text = "How are you doing today?"
    curr_text = "I'm doing great, thanks!"
    score = await optimizer._check_coherence(prev_text, curr_text)
    assert score > 0.2  # Should have moderate coherence due to common dialogue words
    
    # Test greeting coherence
    prev_text = "Hello! How are you?"
    curr_text = "Hi there! I'm good, thanks!"
    score = await optimizer._check_coherence(prev_text, curr_text)
    assert score > 0.5  # Should be coherent (greetings, thanks)
    
    # Test low coherence
    prev_text = "What's the weather like?"
    curr_text = "I love playing basketball."
    score = await optimizer._check_coherence(prev_text, curr_text)
    assert score < 0.3  # Should have low coherence

@pytest.mark.asyncio
async def test_optimize_dialogue():
    optimizer = NLPOptimizer()
    
    lines = [
        DialogueLine(
            character="Alice",
            text="I'm so excited to see you!",
            pause_before=0.5,
            pause_after=0.5
        ),
        DialogueLine(
            character="Bob",
            text="That's terrible news.",
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
    
    optimized = await optimizer.optimize_dialogue(lines)
    
    # Check that we got the right number of lines back
    assert len(optimized) == len(lines)
    
    # The first line should have a short pause (positive sentiment)
    assert optimized[0].pause_after <= 0.3
    
    # The second line should have a longer pause (negative sentiment)
    assert optimized[1].pause_after >= 1.0
    
    # The third line should have a longer pause_before (low coherence with previous)
    assert optimized[2].pause_before >= 1.0
