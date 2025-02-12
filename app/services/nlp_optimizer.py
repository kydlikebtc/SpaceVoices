from typing import List, Dict
from textblob import TextBlob
from app.models.script import DialogueLine

class NLPOptimizer:
    """Service for optimizing dialogue using NLP techniques."""
    
    def __init__(self):
        """Initialize NLP optimizer."""
        pass
    
    async def optimize_dialogue(self, lines: List[DialogueLine]) -> List[DialogueLine]:
        """
        Optimize dialogue flow using NLP analysis.
        
        Args:
            lines: List of dialogue lines to optimize
            
        Returns:
            Optimized list of dialogue lines with adjusted pauses
        """
        optimized_lines = []
        
        for i, line in enumerate(lines):
            # Analyze sentiment for appropriate pauses
            sentiment_score = await self._analyze_sentiment(line.text)
            
            # Adjust pauses based on sentiment
            if sentiment_score < 0.3:  # Negative sentiment
                line.pause_after = max(1.0, line.pause_after)
            elif sentiment_score > 0.7:  # Positive sentiment
                line.pause_after = min(0.3, line.pause_after)
            
            # Check coherence with previous line if not first line
            if i > 0:
                coherence_score = await self._check_coherence(
                    optimized_lines[-1].text,
                    line.text
                )
                
                # Add longer pause if coherence is low
                if coherence_score < 0.5:
                    line.pause_before = max(1.0, line.pause_before)
            
            optimized_lines.append(line)
        
        return optimized_lines
    
    async def _analyze_sentiment(self, text: str) -> float:
        """
        Analyze sentiment of text and return score between -1 and 1.
        -1 = very negative, 1 = very positive
        """
        blob = TextBlob(text)
        # Convert from [-1, 1] to [0, 1] range
        return (blob.sentiment.polarity + 1) / 2
    
    async def _check_coherence(self, prev_text: str, curr_text: str) -> float:
        """
        Check coherence between two pieces of text using word overlap.
        Returns score between 0 and 1 where 1 is most coherent.
        """
        prev_blob = TextBlob(prev_text)
        curr_blob = TextBlob(curr_text)
        
        # Simple word overlap similarity
        prev_words = set(prev_blob.words)
        curr_words = set(curr_blob.words)
        
        if not prev_words or not curr_words:
            return 1.0
            
        overlap = len(prev_words.intersection(curr_words))
        total = len(prev_words.union(curr_words))
        return overlap / total
