from typing import List, Dict, Optional
import re
from textblob import TextBlob

class ContentModerator:
    """Service for content moderation and compliance."""
    
    def __init__(self):
        """Initialize the content moderator."""
        self.ai_disclosure_text = "[AI-GENERATED CONTENT] This content is generated using artificial intelligence."
        self.tos_compliance_text = "This Space complies with Twitter's Terms of Service."
    
    async def moderate_script(self, text: str) -> Dict[str, any]:
        """
        Moderate script content for compliance and safety.
        
        Args:
            text: The script text to moderate
            
        Returns:
            Dict containing moderation results and recommendations
        """
        results = {
            "is_safe": True,
            "warnings": [],
            "recommendations": []
        }
        
        # Check content safety
        if await self._contains_sensitive_content(text):
            results["is_safe"] = False
            results["warnings"].append("Content may contain sensitive material")
        
        # Check for proper AI disclosure
        if not await self._has_ai_disclosure(text):
            results["recommendations"].append("Add AI content disclosure")
        
        # Check for ToS compliance
        tos_issues = await self._check_tos_compliance(text)
        if tos_issues:
            results["warnings"].extend(tos_issues)
        
        return results
    
    async def _contains_sensitive_content(self, text: str) -> bool:
        """Check for potentially sensitive content."""
        # Basic sentiment analysis for extreme negativity
        blob = TextBlob(text)
        # Lower threshold to catch more sensitive content
        if blob.sentiment.polarity < -0.3:
            return True
            
        # Check for concerning keywords
        concerning_words = {
            'terrible', 'hopeless', 'meaningless', 'awful',
            'suicide', 'depression', 'anxiety', 'crisis'
        }
        
        text_words = set(text.lower().split())
        if any(word in text_words for word in concerning_words):
            return True
            
        return False
    
    async def _has_ai_disclosure(self, text: str) -> bool:
        """Check if content includes AI disclosure."""
        return "AI-GENERATED" in text.upper() or "ARTIFICIAL INTELLIGENCE" in text.upper()
    
    async def _check_tos_compliance(self, text: str) -> List[str]:
        """Check for Twitter Terms of Service compliance."""
        issues = []
        
        # Check for common ToS violations
        if len(text) > 25000:  # Example limit
            issues.append("Content length exceeds Twitter's limits")
        
        # Add more ToS compliance checks here
        return issues
    
    def get_required_disclosures(self) -> Dict[str, str]:
        """Get required disclosure texts."""
        return {
            "ai_disclosure": self.ai_disclosure_text,
            "tos_compliance": self.tos_compliance_text
        }
