from typing import Dict, Optional
import psutil
import asyncio
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ResourceMetrics:
    """Resource usage metrics."""
    memory_percent: float
    cpu_percent: float
    process_count: int

class ResourceError(Exception):
    """Custom exception for resource-related errors."""
    pass

class ResourceManager:
    """Service for monitoring and managing system resources."""
    
    def __init__(
        self,
        max_memory_percent: float = 80.0,
        max_cpu_percent: float = 70.0,
        max_processes: int = 100
    ):
        """Initialize the resource manager with configurable limits."""
        self.max_memory_percent = max_memory_percent
        self.max_cpu_percent = max_cpu_percent
        self.max_processes = max_processes
        self.metrics: Dict[str, ResourceMetrics] = {}
    
    async def check_resources(self, operation_id: str = "default") -> bool:
        """
        Check if system resources are within acceptable limits.
        
        Args:
            operation_id: Identifier for the operation being monitored
            
        Returns:
            bool: True if resources are available, False otherwise
            
        Raises:
            ResourceError: If resource metrics cannot be collected
        """
        try:
            metrics = await self._collect_metrics()
            self.metrics[operation_id] = metrics
            
            # Check against thresholds
            if metrics.memory_percent >= self.max_memory_percent:
                logger.warning(f"Memory usage ({metrics.memory_percent}%) exceeds threshold ({self.max_memory_percent}%)")
                return False
                
            if metrics.cpu_percent >= self.max_cpu_percent:
                logger.warning(f"CPU usage ({metrics.cpu_percent}%) exceeds threshold ({self.max_cpu_percent}%)")
                return False
                
            if metrics.process_count >= self.max_processes:
                logger.warning(f"Process count ({metrics.process_count}) exceeds threshold ({self.max_processes})")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to check resources: {str(e)}")
            raise ResourceError(f"Resource check failed: {str(e)}")
    
    async def _collect_metrics(self) -> ResourceMetrics:
        """Collect current system resource metrics."""
        try:
            return ResourceMetrics(
                memory_percent=psutil.virtual_memory().percent,
                cpu_percent=psutil.cpu_percent(interval=0.1),
                process_count=len(psutil.Process().children())
            )
        except Exception as e:
            logger.error(f"Failed to collect metrics: {str(e)}")
            raise ResourceError(f"Metrics collection failed: {str(e)}")
    
    def get_metrics(self, operation_id: str = "default") -> Optional[ResourceMetrics]:
        """Get the latest metrics for an operation."""
        return self.metrics.get(operation_id)
