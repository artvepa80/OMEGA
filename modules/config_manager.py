"""
OMEGA PRO AI v10.1 - A/B Testing Configuration Manager
====================================================

Centralized configuration management for A/B testing framework.
Handles test configurations, feature flag settings, and system parameters.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict, field
from pathlib import Path


@dataclass
class ABTestSystemConfig:
    """System-wide A/B testing configuration."""
    
    # Storage paths
    config_base_path: str = "config/ab_testing"
    results_base_path: str = "results/ab_testing" 
    logs_base_path: str = "logs/ab_testing"
    
    # Default test parameters
    default_significance_level: float = 0.05
    default_power: float = 0.8
    default_traffic_split: float = 0.5
    default_min_sample_size: int = 100
    default_max_duration_days: int = 30
    
    # Statistical analysis settings
    multiple_comparisons_method: str = "bonferroni"
    confidence_level: float = 0.95
    effect_size_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "small": 0.2,
        "medium": 0.5, 
        "large": 0.8
    })
    
    # Performance monitoring
    enable_performance_monitoring: bool = True
    metric_collection_interval_seconds: int = 60
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "performance_degradation": -0.05,  # 5% degradation
        "rare_number_improvement": 0.1,    # 10% improvement
        "latency_increase": 0.2            # 20% latency increase
    })
    
    # Feature flag settings
    feature_flag_config_path: str = "config/feature_flags.json"
    default_rollout_step_size: int = 10  # Percentage
    default_rollout_step_interval_hours: int = 24
    
    # Reporting settings
    auto_report_generation: bool = True
    report_formats: List[str] = field(default_factory=lambda: ["json", "html"])
    stakeholder_report_recipients: List[str] = field(default_factory=list)
    
    # Safety settings
    enable_auto_killswitch: bool = True
    killswitch_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "accuracy_drop": -0.1,      # 10% accuracy drop
        "error_rate_spike": 0.05,   # 5% error rate
        "latency_spike": 2.0        # 2x latency increase
    })
    
    # Integration settings  
    enable_prometheus_metrics: bool = False
    prometheus_port: int = 8080
    enable_grafana_dashboards: bool = False
    webhook_notifications: List[str] = field(default_factory=list)


@dataclass
class TestEnvironmentConfig:
    """Configuration for specific test environments."""
    
    environment_name: str
    description: str
    
    # Environment-specific overrides
    traffic_allocation: Dict[str, float] = field(default_factory=dict)  # {"control": 0.5, "treatment": 0.5}
    user_segments: List[str] = field(default_factory=list)
    geographic_restrictions: List[str] = field(default_factory=list)
    time_windows: List[Dict[str, str]] = field(default_factory=list)  # Active time windows
    
    # Resource limits
    max_concurrent_tests: int = 5
    max_samples_per_test: int = 10000
    max_test_duration_days: int = 60
    
    # Environment-specific metrics
    priority_metrics: List[str] = field(default_factory=lambda: [
        "accuracy", "rare_number_detection", "latency_ms"
    ])
    custom_metrics: Dict[str, str] = field(default_factory=dict)
    
    # Monitoring
    enable_alerts: bool = True
    alert_channels: List[str] = field(default_factory=list)
    
    # Data retention
    sample_retention_days: int = 90
    report_retention_days: int = 365


class ABTestConfigManager:
    """
    Centralized configuration manager for A/B testing framework.
    
    Manages:
    - System-wide A/B testing settings
    - Individual test configurations
    - Environment-specific settings
    - Feature flag configurations
    - Integration with OMEGA's existing configuration system
    """
    
    def __init__(self, config_path: str = "config/ab_testing_system.json"):
        self.config_path = config_path
        self.logger = self._setup_logging()
        
        # Load system configuration
        self.system_config = self._load_system_config()
        
        # Environment configurations
        self.environments: Dict[str, TestEnvironmentConfig] = {}
        self._load_environment_configs()
        
        # Test configurations cache
        self.test_configs: Dict[str, Dict[str, Any]] = {}
        
        # Ensure required directories exist
        self._ensure_directories()
        
        self.logger.info("A/B Test Config Manager initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for configuration manager."""
        logger = logging.getLogger("omega_ab_config_manager")
        logger.setLevel(logging.INFO)
        
        os.makedirs("logs/ab_testing", exist_ok=True)
        handler = logging.FileHandler("logs/ab_testing/config_manager.log")
        handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        return logger
    
    def get_system_config(self) -> ABTestSystemConfig:
        """Get system-wide A/B testing configuration."""
        return self.system_config
    
    def update_system_config(self, updates: Dict[str, Any]) -> bool:
        """
        Update system configuration.
        
        Args:
            updates: Dictionary of configuration updates
            
        Returns:
            bool: True if updated successfully
        """
        try:
            # Update system config
            for key, value in updates.items():
                if hasattr(self.system_config, key):
                    setattr(self.system_config, key, value)
            
            # Save updated configuration
            self._save_system_config()
            
            self.logger.info("System configuration updated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating system config: {str(e)}")
            return False
    
    def create_test_config_template(self, test_type: str = "prediction_improvement") -> Dict[str, Any]:
        """
        Create a test configuration template.
        
        Args:
            test_type: Type of A/B test to create template for
            
        Returns:
            Dict with test configuration template
        """
        base_template = {
            "test_id": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "name": "New A/B Test",
            "description": "A/B test description",
            "test_type": test_type,
            
            # Test parameters
            "traffic_split": self.system_config.default_traffic_split,
            "min_sample_size": self.system_config.default_min_sample_size,
            "max_duration_days": self.system_config.default_max_duration_days,
            "significance_level": self.system_config.default_significance_level,
            "power": self.system_config.default_power,
            
            # Configuration variants
            "control_config": {},
            "variant_config": {},
            
            # Metrics to track
            "metrics": ["accuracy", "rare_number_detection", "latency_ms", "confidence_score"],
            "primary_metric": "accuracy",
            
            # Targeting
            "user_segments": [],
            "geographic_restrictions": [],
            "time_windows": [],
            
            # Feature flags
            "feature_flags": [],
            
            # Monitoring
            "alerts_enabled": True,
            "alert_thresholds": dict(self.system_config.alert_thresholds),
            
            # Status
            "enabled": False,
            "created_at": datetime.now().isoformat(),
            "created_by": "system"
        }
        
        # Customize template based on test type
        if test_type == "prediction_improvement":
            base_template.update({
                "name": "Prediction Algorithm Improvement Test",
                "description": "A/B test to validate prediction algorithm improvements",
                "control_config": {
                    "algorithm_version": "current",
                    "use_enhanced_scoring": False,
                    "rare_number_boost": False
                },
                "variant_config": {
                    "algorithm_version": "enhanced",
                    "use_enhanced_scoring": True,
                    "rare_number_boost": True
                },
                "primary_metric": "accuracy"
            })
            
        elif test_type == "rare_number_detection":
            base_template.update({
                "name": "Rare Number Detection Enhancement Test", 
                "description": "A/B test focused on improving rare number prediction accuracy",
                "control_config": {
                    "rare_number_detection": "standard"
                },
                "variant_config": {
                    "rare_number_detection": "enhanced",
                    "exploratory_consensus_mode": True
                },
                "primary_metric": "rare_number_detection"
            })
            
        elif test_type == "performance_optimization":
            base_template.update({
                "name": "System Performance Optimization Test",
                "description": "A/B test to validate system performance improvements",
                "control_config": {
                    "optimization_level": "standard"
                },
                "variant_config": {
                    "optimization_level": "enhanced",
                    "caching_enabled": True,
                    "parallel_processing": True
                },
                "primary_metric": "latency_ms"
            })
        
        return base_template
    
    def validate_test_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate test configuration.
        
        Args:
            config: Test configuration to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Required fields
        required_fields = ["test_id", "name", "control_config", "variant_config"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
        
        # Validate traffic split
        traffic_split = config.get("traffic_split", 0.5)
        if not (0.01 <= traffic_split <= 0.99):
            errors.append("Traffic split must be between 0.01 and 0.99")
        
        # Validate sample size
        min_sample_size = config.get("min_sample_size", 0)
        if min_sample_size < 10:
            errors.append("Minimum sample size must be at least 10")
        
        # Validate duration
        max_duration = config.get("max_duration_days", 0)
        if max_duration < 1 or max_duration > 365:
            errors.append("Test duration must be between 1 and 365 days")
        
        # Validate significance level
        significance_level = config.get("significance_level", 0.05)
        if not (0.001 <= significance_level <= 0.1):
            errors.append("Significance level must be between 0.001 and 0.1")
        
        # Validate metrics
        metrics = config.get("metrics", [])
        if not metrics:
            errors.append("At least one metric must be specified")
        
        # Validate primary metric
        primary_metric = config.get("primary_metric")
        if primary_metric and primary_metric not in metrics:
            errors.append("Primary metric must be in the metrics list")
        
        # Check for conflicting tests
        test_id = config.get("test_id")
        if test_id and self._has_conflicting_test(test_id, config):
            errors.append(f"Test {test_id} conflicts with existing active tests")
        
        return len(errors) == 0, errors
    
    def save_test_config(self, config: Dict[str, Any]) -> bool:
        """
        Save test configuration.
        
        Args:
            config: Test configuration to save
            
        Returns:
            bool: True if saved successfully
        """
        try:
            # Validate configuration
            is_valid, errors = self.validate_test_config(config)
            if not is_valid:
                self.logger.error(f"Invalid test config: {errors}")
                return False
            
            test_id = config["test_id"]
            
            # Save to disk
            config_file = f"{self.system_config.config_base_path}/tests/{test_id}.json"
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2, default=str)
            
            # Cache configuration
            self.test_configs[test_id] = config
            
            self.logger.info(f"Saved test configuration: {test_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving test config: {str(e)}")
            return False
    
    def load_test_config(self, test_id: str) -> Optional[Dict[str, Any]]:
        """
        Load test configuration.
        
        Args:
            test_id: Test identifier
            
        Returns:
            Dict with test configuration or None if not found
        """
        try:
            # Check cache first
            if test_id in self.test_configs:
                return self.test_configs[test_id]
            
            # Load from disk
            config_file = f"{self.system_config.config_base_path}/tests/{test_id}.json"
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                # Cache configuration
                self.test_configs[test_id] = config
                return config
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error loading test config {test_id}: {str(e)}")
            return None
    
    def list_test_configs(self, status_filter: str = None) -> List[Dict[str, Any]]:
        """
        List all test configurations.
        
        Args:
            status_filter: Filter by status ("active", "completed", "paused")
            
        Returns:
            List of test configurations
        """
        try:
            configs = []
            
            # Scan test configuration directory
            tests_dir = f"{self.system_config.config_base_path}/tests"
            if os.path.exists(tests_dir):
                for config_file in os.listdir(tests_dir):
                    if config_file.endswith('.json'):
                        test_id = config_file[:-5]  # Remove .json extension
                        config = self.load_test_config(test_id)
                        
                        if config:
                            # Apply status filter if specified
                            if status_filter is None or config.get("status") == status_filter:
                                configs.append(config)
            
            return configs
            
        except Exception as e:
            self.logger.error(f"Error listing test configs: {str(e)}")
            return []
    
    def create_environment_config(self, environment_name: str, 
                                description: str = "") -> TestEnvironmentConfig:
        """
        Create a new environment configuration.
        
        Args:
            environment_name: Name of the environment
            description: Environment description
            
        Returns:
            TestEnvironmentConfig object
        """
        config = TestEnvironmentConfig(
            environment_name=environment_name,
            description=description or f"A/B testing environment: {environment_name}"
        )
        
        self.environments[environment_name] = config
        self._save_environment_config(environment_name)
        
        return config
    
    def get_environment_config(self, environment_name: str) -> Optional[TestEnvironmentConfig]:
        """Get environment configuration."""
        return self.environments.get(environment_name)
    
    def update_environment_config(self, environment_name: str, 
                                updates: Dict[str, Any]) -> bool:
        """
        Update environment configuration.
        
        Args:
            environment_name: Environment to update
            updates: Configuration updates
            
        Returns:
            bool: True if updated successfully
        """
        try:
            if environment_name not in self.environments:
                self.logger.error(f"Environment {environment_name} not found")
                return False
            
            config = self.environments[environment_name]
            
            # Update configuration
            for key, value in updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            # Save updated configuration
            self._save_environment_config(environment_name)
            
            self.logger.info(f"Updated environment config: {environment_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating environment config: {str(e)}")
            return False
    
    def get_test_config_for_environment(self, test_id: str, 
                                      environment: str) -> Optional[Dict[str, Any]]:
        """
        Get test configuration adapted for specific environment.
        
        Args:
            test_id: Test identifier
            environment: Environment name
            
        Returns:
            Dict with environment-adapted test configuration
        """
        try:
            # Load base test configuration
            base_config = self.load_test_config(test_id)
            if not base_config:
                return None
            
            # Get environment configuration
            env_config = self.get_environment_config(environment)
            if not env_config:
                return base_config  # Return base config if environment not found
            
            # Apply environment-specific overrides
            adapted_config = base_config.copy()
            
            # Override traffic allocation if specified
            if env_config.traffic_allocation:
                adapted_config["traffic_allocation"] = env_config.traffic_allocation
            
            # Override user segments
            if env_config.user_segments:
                adapted_config["user_segments"] = env_config.user_segments
            
            # Override geographic restrictions
            if env_config.geographic_restrictions:
                adapted_config["geographic_restrictions"] = env_config.geographic_restrictions
            
            # Override time windows
            if env_config.time_windows:
                adapted_config["time_windows"] = env_config.time_windows
            
            # Override priority metrics
            if env_config.priority_metrics:
                adapted_config["priority_metrics"] = env_config.priority_metrics
            
            # Add custom metrics
            if env_config.custom_metrics:
                adapted_config["custom_metrics"] = env_config.custom_metrics
            
            # Override sample and duration limits
            adapted_config["max_samples_per_test"] = env_config.max_samples_per_test
            adapted_config["max_test_duration_days"] = min(
                adapted_config.get("max_duration_days", env_config.max_test_duration_days),
                env_config.max_test_duration_days
            )
            
            return adapted_config
            
        except Exception as e:
            self.logger.error(f"Error adapting config for environment: {str(e)}")
            return base_config
    
    def generate_integration_config(self) -> Dict[str, Any]:
        """
        Generate configuration for integration with existing OMEGA systems.
        
        Returns:
            Dict with integration configuration
        """
        integration_config = {
            # Logging integration
            "logging": {
                "integrate_with_omega_logging": True,
                "log_level": "INFO",
                "log_format": "omega_ab_testing",
                "log_rotation": "daily"
            },
            
            # Metrics integration
            "metrics": {
                "integrate_with_prometheus": self.system_config.enable_prometheus_metrics,
                "prometheus_port": self.system_config.prometheus_port,
                "custom_metrics_prefix": "omega_ab_",
                "metric_labels": ["test_id", "variant", "environment"]
            },
            
            # Database integration
            "database": {
                "use_omega_database": True,
                "ab_testing_schema": "ab_testing",
                "data_retention_days": 90
            },
            
            # API integration
            "api": {
                "integrate_with_omega_api": True,
                "ab_testing_endpoints": [
                    "/api/ab/tests",
                    "/api/ab/results", 
                    "/api/ab/flags"
                ],
                "authentication_required": True
            },
            
            # Notification integration
            "notifications": {
                "webhook_urls": self.system_config.webhook_notifications,
                "email_recipients": self.system_config.stakeholder_report_recipients,
                "slack_integration": False,  # Can be enabled
                "teams_integration": False   # Can be enabled
            },
            
            # Security integration
            "security": {
                "inherit_omega_security": True,
                "require_authorization": True,
                "encrypt_sensitive_data": True,
                "audit_all_changes": True
            }
        }
        
        return integration_config
    
    def _load_system_config(self) -> ABTestSystemConfig:
        """Load system configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                
                # Handle nested dictionaries for dataclass fields
                if "effect_size_thresholds" in data:
                    data["effect_size_thresholds"] = dict(data["effect_size_thresholds"])
                if "alert_thresholds" in data:
                    data["alert_thresholds"] = dict(data["alert_thresholds"])
                if "killswitch_thresholds" in data:
                    data["killswitch_thresholds"] = dict(data["killswitch_thresholds"])
                
                return ABTestSystemConfig(**data)
            else:
                # Create default configuration
                default_config = ABTestSystemConfig()
                self._save_system_config_obj(default_config)
                return default_config
                
        except Exception as e:
            self.logger.error(f"Error loading system config: {str(e)}")
            return ABTestSystemConfig()
    
    def _save_system_config(self):
        """Save current system configuration to file."""
        self._save_system_config_obj(self.system_config)
    
    def _save_system_config_obj(self, config: ABTestSystemConfig):
        """Save system configuration object to file."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(asdict(config), f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Error saving system config: {str(e)}")
    
    def _load_environment_configs(self):
        """Load environment configurations."""
        try:
            env_configs_dir = f"{self.system_config.config_base_path}/environments"
            if os.path.exists(env_configs_dir):
                for config_file in os.listdir(env_configs_dir):
                    if config_file.endswith('.json'):
                        env_name = config_file[:-5]  # Remove .json extension
                        
                        config_path = os.path.join(env_configs_dir, config_file)
                        with open(config_path, 'r') as f:
                            data = json.load(f)
                        
                        config = TestEnvironmentConfig(**data)
                        self.environments[env_name] = config
                        
        except Exception as e:
            self.logger.error(f"Error loading environment configs: {str(e)}")
    
    def _save_environment_config(self, environment_name: str):
        """Save environment configuration to file."""
        try:
            if environment_name not in self.environments:
                return
            
            config = self.environments[environment_name]
            
            env_configs_dir = f"{self.system_config.config_base_path}/environments"
            os.makedirs(env_configs_dir, exist_ok=True)
            
            config_file = f"{env_configs_dir}/{environment_name}.json"
            with open(config_file, 'w') as f:
                json.dump(asdict(config), f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Error saving environment config: {str(e)}")
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        directories = [
            self.system_config.config_base_path,
            self.system_config.results_base_path,
            self.system_config.logs_base_path,
            f"{self.system_config.config_base_path}/tests",
            f"{self.system_config.config_base_path}/environments"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def _has_conflicting_test(self, test_id: str, config: Dict[str, Any]) -> bool:
        """Check if test configuration conflicts with existing tests."""
        try:
            # Simple check: test ID collision
            if test_id in self.test_configs:
                return True
            
            # Could add more sophisticated conflict detection here
            # (e.g., overlapping user segments, conflicting feature flags)
            
            return False
            
        except Exception:
            return False