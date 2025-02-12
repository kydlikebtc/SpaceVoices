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
                line.pause_after = 1.0
            elif sentiment_score > 0.7:  # Positive sentiment
                line.pause_after = 0.3
            
            # For greetings and positive interactions, use shorter pauses
            if any(word in line.text.lower() for word in {'hello', 'hi', 'hey', 'good'}):
                line.pause_after = 0.3
            
            # Check coherence with previous line if not first line
            if i > 0:
                coherence_score = await self._check_coherence(
                    optimized_lines[-1].text,
                    line.text
                )
                
                # Add longer pause if coherence is low (strict threshold)
                if coherence_score < 0.5:
                    line.pause_before = max(1.0, line.pause_before)
                else:
                    # Keep original pause for coherent dialogue
                    line.pause_before = min(0.5, line.pause_before)
            
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
        # Normalize text: lowercase and handle contractions
        prev_text = prev_text.lower().replace("'m", " am").replace("'re", " are").replace("'s", " is")
        curr_text = curr_text.lower().replace("'m", " am").replace("'re", " are").replace("'s", " is")
        
        # Simple word tokenization
        prev_words = set(prev_text.split())
        curr_words = set(curr_text.split())
        
        if not prev_words or not curr_words:
            return 1.0
        
        # Calculate weighted score based on common words
        common_words = prev_words.intersection(curr_words)
        
        # Define word categories with different weights
        dialogue_words = {'i', 'you', 'am', 'are', 'is', 'doing', 'thanks', 'please', 'good', 'great'}  # Weight: 4
        question_words = {'how', 'what', 'why', 'when', 'where', 'who'}  # Weight: 3
        greeting_words = {'hello', 'hi', 'hey', 'bye', 'goodbye', 'there', 'morning', 'afternoon', 'evening'}  # Weight: 3
        
        # Calculate weighted overlap
        def get_word_weight(word: str) -> int:
            if word in dialogue_words:
                return 4
            if word in question_words or word in greeting_words:
                return 3
            return 1
        
        # Calculate weighted scores with emphasis on dialogue patterns
        def get_dialogue_bonus(words: set[str]) -> float:
            # Give bonus for question-answer patterns and greetings
            has_question = any(w in question_words for w in words)
            has_response = any(w in {'yes', 'no', 'thanks', 'thank', 'good', 'great', 'ok', 'okay'} for w in words)
            has_greeting = any(w in greeting_words for w in words)
            
            bonus = 0.0
            if has_question and has_response:
                bonus += 0.3
            if has_greeting:
                bonus += 0.3
            return min(0.6, bonus)
        
        # Base score from weighted word overlap
        overlap_weight = sum(get_word_weight(w) for w in common_words)
        max_weight = max(
            sum(get_word_weight(w) for w in prev_words),
            sum(get_word_weight(w) for w in curr_words)
        )
        
        if max_weight == 0:
            return 1.0 if not (prev_words or curr_words) else 0.0
        
        # Calculate final score with dialogue pattern bonus
        base_score = overlap_weight / max_weight
        dialogue_bonus = get_dialogue_bonus(prev_words.union(curr_words))
        
        return min(1.0, base_score + dialogue_bonus)
