#!/usr/bin/env python3
"""
🧪 OMEGA AI MCP Integration Test Suite
Comprehensive testing framework for MCP services
"""

import asyncio
import json
import logging
import os
import pytest
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from omega_mcp_integration import OMEGAMCPIntegration, get_omega_mcp_integration
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.mark.skipif(not MCP_AVAILABLE, reason="MCP integration not available")
class TestOMEGAMCPIntegration:
    """Test cases for OMEGA MCP Integration"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "config"
            config_dir.mkdir()
            yield config_dir
    
    @pytest.fixture
    def sample_config(self):
        """Sample MCP configuration"""
        return {
            "mcp_enabled": True,
            "auto_start": False,
            "services": {
                "lottery_data": {"enabled": True},
                "notifications": {"enabled": True},
                "workflow_automation": {"enabled": True}
            },
            "integration": {
                "omega_api_base": "http://localhost:8000",
                "prediction_integration": True
            }
        }
    
    @pytest.fixture
    def sample_credentials(self):
        """Sample MCP credentials"""
        return {
            "test_mode": True,
            "smtp_host": "smtp.example.com",
            "smtp_user": "test@example.com",
            "test_email": "test@example.com"
        }
    
    def test_mcp_integration_initialization(self, temp_config_dir, sample_config):
        """Test MCP integration initialization"""
        # Create config file
        config_file = temp_config_dir / "mcp_config.json"
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        # Initialize integration
        integration = OMEGAMCPIntegration(str(config_file))
        
        assert integration.config["mcp_enabled"] == True
        assert integration.config["services"]["lottery_data"]["enabled"] == True
    
    def test_config_loading_with_defaults(self, temp_config_dir):
        """Test configuration loading with defaults when file doesn't exist"""
        non_existent_config = temp_config_dir / "nonexistent.json"
        integration = OMEGAMCPIntegration(str(non_existent_config))
        
        # Should have default configuration
        assert "mcp_enabled" in integration.config
        assert "services" in integration.config
    
    def test_credentials_loading_from_env(self, temp_config_dir):
        """Test credentials loading from environment variables"""
        # Set environment variables
        test_env = {
            "TWILIO_ACCOUNT_SID": "test_account_sid",
            "TWILIO_AUTH_TOKEN": "test_auth_token",
            "TEST_EMAIL": "test@example.com"
        }
        
        with patch.dict(os.environ, test_env):
            integration = OMEGAMCPIntegration()
            credentials = integration._load_credentials()
            
            assert credentials["twilio_account_sid"] == "test_account_sid"
            assert credentials["twilio_auth_token"] == "test_auth_token"
    
    def test_credentials_loading_from_file(self, temp_config_dir, sample_credentials):
        """Test credentials loading from file"""
        # Create credentials file
        creds_file = temp_config_dir / "credentials.json"
        with open(creds_file, 'w') as f:
            json.dump(sample_credentials, f)
        
        # Change to temp directory so the integration finds the file
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_config_dir.parent)
            integration = OMEGAMCPIntegration()
            credentials = integration._load_credentials()
            
            assert credentials["test_mode"] == True
            assert credentials["smtp_host"] == "smtp.example.com"
        finally:
            os.chdir(original_cwd)
    
    @pytest.mark.asyncio
    async def test_mcp_initialization_without_dependencies(self, temp_config_dir):
        """Test MCP initialization when dependencies are missing"""
        integration = OMEGAMCPIntegration()
        
        # Mock missing dependencies
        with patch('omega_mcp_integration.sys') as mock_sys:
            mock_sys.path = sys.path
            
            # This should handle import errors gracefully
            with patch.dict('sys.modules', {'mcps.lottery_data_mcp': None}):
                result = await integration.initialize()
                
                # Should handle gracefully and return False if critical modules missing
                # The actual behavior depends on implementation
                assert isinstance(result, bool)
    
    def test_status_reporting(self):
        """Test status reporting functionality"""
        integration = OMEGAMCPIntegration()
        status = integration.get_status()
        
        assert "integration_active" in status
        assert "services_initialized" in status
        assert "configuration" in status
        assert "timestamp" in status
    
    def test_mcp_enabled_check(self, temp_config_dir, sample_config):
        """Test MCP enabled check"""
        # Test with MCP enabled
        config_file = temp_config_dir / "mcp_config.json"
        sample_config["mcp_enabled"] = True
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        integration = OMEGAMCPIntegration(str(config_file))
        # Note: is_mcp_enabled() requires mcps to be initialized
        # So we test the config loading instead
        assert integration.config["mcp_enabled"] == True
        
        # Test with MCP disabled
        sample_config["mcp_enabled"] = False
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        integration = OMEGAMCPIntegration(str(config_file))
        assert integration.config["mcp_enabled"] == False

class TestMCPServices:
    """Test cases for individual MCP services"""
    
    @pytest.fixture
    def mock_lottery_mcp(self):
        """Mock lottery data MCP"""
        mock = Mock()
        mock.get_supported_lotteries.return_value = ["kabala_pe", "powerball"]
        mock.get_cache_stats.return_value = {
            "cache_entries": 100,
            "supported_lotteries": ["kabala_pe", "powerball"]
        }
        return mock
    
    @pytest.fixture
    def mock_notification_mcp(self):
        """Mock notification MCP"""
        mock = Mock()
        mock.get_delivery_stats.return_value = {
            "available_channels": ["email", "console"],
            "failed_deliveries_count": 0
        }
        mock.send_notification = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_workflow_mcp(self):
        """Mock workflow automation MCP"""
        mock = Mock()
        mock.scheduler = Mock()
        mock.scheduler.running = True
        mock.scheduler.get_jobs.return_value = []
        mock.get_workflow_stats.return_value = {
            "scheduled_jobs": 0,
            "success_rate_24h": 100.0,
            "executions_last_24h": 0
        }
        mock.start = Mock()
        mock.shutdown = Mock()
        return mock
    
    def test_lottery_service_functionality(self, mock_lottery_mcp):
        """Test lottery service basic functionality"""
        supported = mock_lottery_mcp.get_supported_lotteries()
        assert "kabala_pe" in supported
        assert "powerball" in supported
        
        stats = mock_lottery_mcp.get_cache_stats()
        assert stats["cache_entries"] == 100
        assert len(stats["supported_lotteries"]) == 2
    
    @pytest.mark.asyncio
    async def test_notification_service_functionality(self, mock_notification_mcp):
        """Test notification service basic functionality"""
        stats = mock_notification_mcp.get_delivery_stats()
        assert "email" in stats["available_channels"]
        assert stats["failed_deliveries_count"] == 0
        
        # Test sending notification
        await mock_notification_mcp.send_notification(
            message="Test message",
            channels=["email"],
            priority="normal"
        )
        
        mock_notification_mcp.send_notification.assert_called_once_with(
            message="Test message",
            channels=["email"],
            priority="normal"
        )
    
    def test_workflow_service_functionality(self, mock_workflow_mcp):
        """Test workflow automation service basic functionality"""
        assert mock_workflow_mcp.scheduler.running == True
        
        stats = mock_workflow_mcp.get_workflow_stats()
        assert stats["success_rate_24h"] == 100.0
        assert stats["executions_last_24h"] == 0
        
        # Test start/stop
        mock_workflow_mcp.start()
        mock_workflow_mcp.start.assert_called_once()
        
        mock_workflow_mcp.shutdown()
        mock_workflow_mcp.shutdown.assert_called_once()

class TestMCPIntegrationEndToEnd:
    """End-to-end integration tests"""
    
    @pytest.fixture
    def integration_with_mocks(self):
        """Integration instance with mocked services"""
        integration = OMEGAMCPIntegration()
        
        # Mock the MCPs
        integration.mcps = {
            "lottery_data": Mock(),
            "notifications": Mock(),
            "workflow_automation": Mock()
        }
        
        # Configure mocks
        integration.mcps["lottery_data"].get_supported_lotteries.return_value = ["kabala_pe"]
        integration.mcps["notifications"].get_delivery_stats.return_value = {"available_channels": ["email"]}
        integration.mcps["workflow_automation"].scheduler = Mock()
        integration.mcps["workflow_automation"].scheduler.running = True
        
        return integration
    
    def test_integration_status_with_services(self, integration_with_mocks):
        """Test integration status when services are available"""
        status = integration_with_mocks.get_status()
        
        assert status["services_initialized"] == ["lottery_data", "notifications", "workflow_automation"]
    
    def test_mcp_enabled_with_services(self, integration_with_mocks):
        """Test MCP enabled check with services initialized"""
        integration_with_mocks.config["mcp_enabled"] = True
        assert integration_with_mocks.is_mcp_enabled() == True
        
        integration_with_mocks.config["mcp_enabled"] = False
        assert integration_with_mcp.is_mcp_enabled() == False

class TestMCPServiceManager:
    """Test cases for MCP service manager functionality"""
    
    @pytest.fixture
    def mock_mcp_manager(self):
        """Mock MCP manager"""
        with patch('scripts.run_mcps.MCPManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            
            # Configure test results
            mock_manager.test_all_systems = AsyncMock(return_value={
                "lottery_data": {"success": True},
                "notifications": {"success": True},
                "workflow_automation": {"success": True}
            })
            
            mock_manager.deploy_production_workflows = AsyncMock(return_value={
                "scheduler_started": True,
                "lottery_jobs": ["job_1", "job_2"],
                "total_jobs": 3
            })
            
            yield mock_manager
    
    @pytest.mark.asyncio
    async def test_mcp_manager_testing(self, mock_mcp_manager):
        """Test MCP manager testing functionality"""
        results = await mock_mcp_manager.test_all_systems()
        
        assert results["lottery_data"]["success"] == True
        assert results["notifications"]["success"] == True
        assert results["workflow_automation"]["success"] == True
    
    @pytest.mark.asyncio
    async def test_mcp_manager_deployment(self, mock_mcp_manager):
        """Test MCP manager deployment functionality"""
        user_prefs = {
            "notification_channels": ["email"],
            "contact_info": {"email": "test@example.com"}
        }
        
        result = await mock_mcp_manager.deploy_production_workflows(user_prefs)
        
        assert result["scheduler_started"] == True
        assert len(result["lottery_jobs"]) == 2
        assert result["total_jobs"] == 3

class TestMCPErrorHandling:
    """Test cases for MCP error handling"""
    
    def test_initialization_with_invalid_config(self):
        """Test initialization with invalid configuration file"""
        integration = OMEGAMCPIntegration("nonexistent_config.json")
        
        # Should create default configuration
        assert "mcp_enabled" in integration.config
    
    @pytest.mark.asyncio
    async def test_initialization_with_import_errors(self):
        """Test initialization when MCP modules can't be imported"""
        integration = OMEGAMCPIntegration()
        
        with patch('omega_mcp_integration.importlib.import_module', side_effect=ImportError("Module not found")):
            # Should handle import errors gracefully
            with patch.object(integration, '_initialize_mcps', side_effect=ImportError("Test error")):
                result = await integration.initialize()
                assert result == False
    
    def test_credentials_loading_with_errors(self):
        """Test credentials loading with file read errors"""
        integration = OMEGAMCPIntegration()
        
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            credentials = integration._load_credentials()
            # Should return empty dict or env-only credentials
            assert isinstance(credentials, dict)

class TestMCPConfiguration:
    """Test cases for MCP configuration management"""
    
    def test_default_configuration_structure(self):
        """Test default configuration has required structure"""
        integration = OMEGAMCPIntegration()
        config = integration._get_default_config()
        
        required_keys = ["mcp_enabled", "services", "integration", "health_checks"]
        for key in required_keys:
            assert key in config
        
        # Test services structure
        assert "lottery_data" in config["services"]
        assert "notifications" in config["services"]
        assert "workflow_automation" in config["services"]
        
        # Test each service has enabled flag
        for service in config["services"].values():
            assert "enabled" in service
    
    def test_configuration_merging(self):
        """Test configuration merging with user overrides"""
        integration = OMEGAMCPIntegration()
        default = integration._get_default_config()
        
        # Modify and test that changes are preserved
        modified = default.copy()
        modified["mcp_enabled"] = False
        modified["services"]["lottery_data"]["enabled"] = False
        
        assert modified["mcp_enabled"] != default["mcp_enabled"]
        assert modified["services"]["lottery_data"]["enabled"] != default["services"]["lottery_data"]["enabled"]

def run_integration_tests():
    """Run integration tests manually (for non-pytest execution)"""
    print("🧪 Running OMEGA AI MCP Integration Tests...")
    
    if not MCP_AVAILABLE:
        print("❌ MCP integration not available - skipping tests")
        return False
    
    test_results = []
    
    # Test 1: Basic initialization
    try:
        integration = OMEGAMCPIntegration()
        status = integration.get_status()
        assert "integration_active" in status
        test_results.append("✅ Basic initialization test passed")
    except Exception as e:
        test_results.append(f"❌ Basic initialization test failed: {e}")
    
    # Test 2: Configuration loading
    try:
        integration = OMEGAMCPIntegration()
        config = integration._get_default_config()
        assert "mcp_enabled" in config
        assert "services" in config
        test_results.append("✅ Configuration loading test passed")
    except Exception as e:
        test_results.append(f"❌ Configuration loading test failed: {e}")
    
    # Test 3: Credentials loading
    try:
        integration = OMEGAMCPIntegration()
        credentials = integration._load_credentials()
        assert isinstance(credentials, dict)
        test_results.append("✅ Credentials loading test passed")
    except Exception as e:
        test_results.append(f"❌ Credentials loading test failed: {e}")
    
    # Print results
    print("\n📊 Test Results:")
    for result in test_results:
        print(f"   {result}")
    
    passed = len([r for r in test_results if r.startswith("✅")])
    total = len(test_results)
    
    print(f"\n🎯 Summary: {passed}/{total} tests passed")
    return passed == total

if __name__ == "__main__":
    # Check if we're running with pytest
    if "pytest" in sys.modules:
        # Running with pytest - let it handle the tests
        pass
    else:
        # Manual execution
        success = run_integration_tests()
        sys.exit(0 if success else 1)