import pytest
from unittest.mock import Mock, patch
import psutil
from app.services.resource_manager import ResourceManager, ResourceError, ResourceMetrics

@pytest.fixture
def resource_manager():
    return ResourceManager(
        max_memory_percent=80.0,
        max_cpu_percent=70.0,
        max_processes=100
    )

@pytest.mark.asyncio
async def test_check_resources_within_limits(resource_manager):
    with patch('psutil.virtual_memory') as mock_memory, \
         patch('psutil.cpu_percent') as mock_cpu, \
         patch('psutil.Process') as mock_process:
        
        # Mock memory usage
        mock_memory_info = Mock()
        mock_memory_info.percent = 50.0
        mock_memory.return_value = mock_memory_info
        
        # Mock CPU usage
        mock_cpu.return_value = 30.0
        
        # Mock process count
        mock_process_instance = Mock()
        mock_process_instance.children.return_value = [Mock() for _ in range(5)]
        mock_process.return_value = mock_process_instance
        
        # Check resources
        result = await resource_manager.check_resources("test_op")
        assert result == True
        
        # Verify metrics were collected
        metrics = resource_manager.get_metrics("test_op")
        assert metrics is not None
        assert metrics.memory_percent == 50.0
        assert metrics.cpu_percent == 30.0
        assert metrics.process_count == 5

@pytest.mark.asyncio
async def test_check_resources_memory_exceeded(resource_manager):
    with patch('psutil.virtual_memory') as mock_memory, \
         patch('psutil.cpu_percent') as mock_cpu, \
         patch('psutil.Process') as mock_process:
        
        # Mock high memory usage
        mock_memory_info = Mock()
        mock_memory_info.percent = 90.0
        mock_memory.return_value = mock_memory_info
        
        # Mock normal CPU usage
        mock_cpu.return_value = 30.0
        
        # Mock process count
        mock_process_instance = Mock()
        mock_process_instance.children.return_value = [Mock() for _ in range(5)]
        mock_process.return_value = mock_process_instance
        
        # Check resources
        result = await resource_manager.check_resources("test_op")
        assert result == False
        
        # Verify metrics were collected
        metrics = resource_manager.get_metrics("test_op")
        assert metrics is not None
        assert metrics.memory_percent == 90.0

@pytest.mark.asyncio
async def test_check_resources_error_handling(resource_manager):
    with patch('psutil.virtual_memory', side_effect=Exception("Test error")):
        with pytest.raises(ResourceError, match="Resource check failed"):
            await resource_manager.check_resources("test_op")
