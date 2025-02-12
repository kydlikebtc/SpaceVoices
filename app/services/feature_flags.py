from typing import Dict
import os
import logging

logger = logging.getLogger(__name__)

class FeatureFlags:
    """Service for managing feature flags."""
    
    def __init__(self):
        """Initialize feature flags from environment variables."""
        self.flags = {
            "enable_nlp_optimization": self._parse_bool_env("ENABLE_NLP_OPTIMIZATION", True),
            "enable_real_time_monitoring": self._parse_bool_env("ENABLE_REAL_TIME_MONITORING", True),
            "enable_rate_limiting": self._parse_bool_env("ENABLE_RATE_LIMITING", True),
            "enable_heartbeat": self._parse_bool_env("ENABLE_HEARTBEAT", True),
            "enable_resource_monitoring": self._parse_bool_env("ENABLE_RESOURCE_MONITORING", True),
            "use_browser_automation": self._parse_bool_env("USE_BROWSER_AUTOMATION", False),
            "browser_auto_retry": self._parse_bool_env("BROWSER_AUTO_RETRY", True)
        }
        logger.info(f"Feature flags initialized: {self.flags}")
    
    def is_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled."""
        enabled = self.flags.get(feature, False)
        logger.debug(f"Feature flag check: {feature} = {enabled}")
        return enabled
    
    @staticmethod
    def _parse_bool_env(key: str, default: bool) -> bool:
        """Parse boolean value from environment variable."""
        value = os.getenv(key, str(default))
        return value.lower() in ('true', '1', 'yes', 'on')
    
    def get_all_flags(self) -> Dict[str, bool]:
        """Get all feature flags and their states."""
        return self.flags.copy()
