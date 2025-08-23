"""
OMEGA PRO AI v10.1 - Feature Flag Management
==========================================

Safe feature rollout system for A/B testing and gradual deployment.
Provides consistent user assignment and rollback capabilities.
"""

import os
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, asdict
from threading import RLock


@dataclass
class FeatureFlag:
    """Configuration for a feature flag."""
    name: str
    description: str
    enabled: bool = False
    rollout_percentage: int = 0  # 0-100
    user_whitelist: Set[str] = None
    user_blacklist: Set[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.user_whitelist is None:
            self.user_whitelist = set()
        if self.user_blacklist is None:
            self.user_blacklist = set()
        if self.metadata is None:
            self.metadata = {}


class FeatureFlagManager:
    """
    Feature flag management system for safe A/B testing rollouts.
    
    Provides:
    - Consistent user assignment based on hashing
    - Gradual rollout capabilities 
    - User whitelist/blacklist support
    - Time-based activation/deactivation
    - Safe rollback mechanisms
    """
    
    def __init__(self, config_path: str = "config/feature_flags.json"):
        self.config_path = config_path
        self.flags: Dict[str, FeatureFlag] = {}
        self._lock = RLock()
        self.logger = self._setup_logging()
        
        # Load existing flags
        self._load_flags()
        
        self.logger.info("Feature Flag Manager initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for feature flags."""
        logger = logging.getLogger("omega_feature_flags")
        logger.setLevel(logging.INFO)
        
        # Create file handler
        os.makedirs("logs/ab_testing", exist_ok=True)
        handler = logging.FileHandler("logs/ab_testing/feature_flags.log")
        handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        return logger
    
    def create_flag(self, name: str, description: str = "", 
                   enabled: bool = False, rollout_percentage: int = 0,
                   user_whitelist: Set[str] = None, 
                   user_blacklist: Set[str] = None,
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   metadata: Dict[str, Any] = None) -> bool:
        """
        Create a new feature flag.
        
        Args:
            name: Unique flag name
            description: Human-readable description
            enabled: Whether flag is globally enabled
            rollout_percentage: Percentage of users to include (0-100)
            user_whitelist: Always include these users
            user_blacklist: Never include these users
            start_date: When to start the flag
            end_date: When to end the flag
            metadata: Additional metadata
            
        Returns:
            bool: True if created successfully
        """
        with self._lock:
            try:
                if name in self.flags:
                    self.logger.warning(f"Flag {name} already exists")
                    return False
                
                flag = FeatureFlag(
                    name=name,
                    description=description,
                    enabled=enabled,
                    rollout_percentage=max(0, min(100, rollout_percentage)),
                    user_whitelist=user_whitelist or set(),
                    user_blacklist=user_blacklist or set(),
                    start_date=start_date,
                    end_date=end_date,
                    metadata=metadata or {}
                )
                
                self.flags[name] = flag
                self._save_flags()
                
                self.logger.info(f"Created feature flag: {name}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error creating flag {name}: {str(e)}")
                return False
    
    def is_enabled(self, flag_name: str, user_id: str = None,
                  context: Dict[str, Any] = None) -> bool:
        """
        Check if a feature flag is enabled for a user.
        
        Args:
            flag_name: Name of the flag to check
            user_id: User identifier for consistent assignment
            context: Additional context for evaluation
            
        Returns:
            bool: True if flag is enabled for this user
        """
        with self._lock:
            if flag_name not in self.flags:
                return False
            
            flag = self.flags[flag_name]
            
            # Check if flag is globally disabled
            if not flag.enabled:
                return False
            
            # Check date constraints
            now = datetime.now()
            if flag.start_date and now < flag.start_date:
                return False
            if flag.end_date and now > flag.end_date:
                return False
            
            # If no user_id provided, use global flag state
            if user_id is None:
                return flag.rollout_percentage >= 100
            
            # Check blacklist first
            if user_id in flag.user_blacklist:
                return False
            
            # Check whitelist
            if user_id in flag.user_whitelist:
                return True
            
            # Use consistent hashing for rollout percentage
            return self._is_user_in_rollout(user_id, flag_name, flag.rollout_percentage)
    
    def enable_flag(self, flag_name: str) -> bool:
        """Enable a feature flag globally."""
        return self.update_flag(flag_name, enabled=True)
    
    def disable_flag(self, flag_name: str) -> bool:
        """Disable a feature flag globally."""
        return self.update_flag(flag_name, enabled=False)
    
    def update_rollout_percentage(self, flag_name: str, percentage: int) -> bool:
        """Update rollout percentage for a flag."""
        return self.update_flag(flag_name, rollout_percentage=percentage)
    
    def update_flag(self, flag_name: str, **kwargs) -> bool:
        """
        Update feature flag configuration.
        
        Args:
            flag_name: Name of flag to update
            **kwargs: Fields to update
            
        Returns:
            bool: True if updated successfully
        """
        with self._lock:
            if flag_name not in self.flags:
                self.logger.error(f"Flag {flag_name} not found")
                return False
            
            try:
                flag = self.flags[flag_name]
                
                # Update allowed fields
                for key, value in kwargs.items():
                    if hasattr(flag, key):
                        if key == 'rollout_percentage':
                            value = max(0, min(100, value))
                        setattr(flag, key, value)
                
                self._save_flags()
                self.logger.info(f"Updated feature flag: {flag_name}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error updating flag {flag_name}: {str(e)}")
                return False
    
    def add_to_whitelist(self, flag_name: str, user_ids: List[str]) -> bool:
        """Add users to flag whitelist."""
        with self._lock:
            if flag_name not in self.flags:
                return False
            
            self.flags[flag_name].user_whitelist.update(user_ids)
            self._save_flags()
            self.logger.info(f"Added {len(user_ids)} users to {flag_name} whitelist")
            return True
    
    def remove_from_whitelist(self, flag_name: str, user_ids: List[str]) -> bool:
        """Remove users from flag whitelist."""
        with self._lock:
            if flag_name not in self.flags:
                return False
            
            for user_id in user_ids:
                self.flags[flag_name].user_whitelist.discard(user_id)
            
            self._save_flags()
            self.logger.info(f"Removed {len(user_ids)} users from {flag_name} whitelist")
            return True
    
    def add_to_blacklist(self, flag_name: str, user_ids: List[str]) -> bool:
        """Add users to flag blacklist."""
        with self._lock:
            if flag_name not in self.flags:
                return False
            
            self.flags[flag_name].user_blacklist.update(user_ids)
            self._save_flags()
            self.logger.info(f"Added {len(user_ids)} users to {flag_name} blacklist")
            return True
    
    def remove_from_blacklist(self, flag_name: str, user_ids: List[str]) -> bool:
        """Remove users from flag blacklist."""
        with self._lock:
            if flag_name not in self.flags:
                return False
            
            for user_id in user_ids:
                self.flags[flag_name].user_blacklist.discard(user_id)
            
            self._save_flags()
            self.logger.info(f"Removed {len(user_ids)} users from {flag_name} blacklist")
            return True
    
    def get_flag_info(self, flag_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a flag."""
        with self._lock:
            if flag_name not in self.flags:
                return None
            
            flag = self.flags[flag_name]
            return {
                "name": flag.name,
                "description": flag.description,
                "enabled": flag.enabled,
                "rollout_percentage": flag.rollout_percentage,
                "whitelist_count": len(flag.user_whitelist),
                "blacklist_count": len(flag.user_blacklist),
                "start_date": flag.start_date.isoformat() if flag.start_date else None,
                "end_date": flag.end_date.isoformat() if flag.end_date else None,
                "metadata": flag.metadata
            }
    
    def list_flags(self) -> List[Dict[str, Any]]:
        """List all feature flags with basic info."""
        with self._lock:
            return [self.get_flag_info(name) for name in self.flags.keys()]
    
    def delete_flag(self, flag_name: str) -> bool:
        """Delete a feature flag."""
        with self._lock:
            if flag_name not in self.flags:
                return False
            
            del self.flags[flag_name]
            self._save_flags()
            self.logger.info(f"Deleted feature flag: {flag_name}")
            return True
    
    def get_user_flags(self, user_id: str) -> Dict[str, bool]:
        """Get all flags and their status for a specific user."""
        with self._lock:
            return {
                name: self.is_enabled(name, user_id)
                for name in self.flags.keys()
            }
    
    def bulk_rollout(self, flag_name: str, target_percentage: int, 
                    step_size: int = 10, step_interval_hours: int = 1) -> bool:
        """
        Gradually roll out a flag to target percentage.
        
        Args:
            flag_name: Name of flag to roll out
            target_percentage: Target rollout percentage
            step_size: Percentage increase per step
            step_interval_hours: Hours between each step
            
        Returns:
            bool: True if rollout plan created successfully
        """
        if flag_name not in self.flags:
            return False
        
        current_percentage = self.flags[flag_name].rollout_percentage
        if current_percentage >= target_percentage:
            return True  # Already at or above target
        
        # Create rollout plan in metadata
        rollout_plan = {
            "target_percentage": target_percentage,
            "step_size": step_size,
            "step_interval_hours": step_interval_hours,
            "start_time": datetime.now().isoformat(),
            "current_step": current_percentage,
            "next_step_time": (datetime.now() + timedelta(hours=step_interval_hours)).isoformat()
        }
        
        self.update_flag(flag_name, metadata={
            **self.flags[flag_name].metadata,
            "rollout_plan": rollout_plan
        })
        
        self.logger.info(f"Created rollout plan for {flag_name}: {current_percentage}% -> {target_percentage}%")
        return True
    
    def process_rollout_schedules(self):
        """Process any scheduled rollout increases."""
        now = datetime.now()
        
        with self._lock:
            for flag_name, flag in self.flags.items():
                rollout_plan = flag.metadata.get("rollout_plan")
                if not rollout_plan:
                    continue
                
                next_step_time = datetime.fromisoformat(rollout_plan["next_step_time"])
                if now >= next_step_time:
                    current = rollout_plan["current_step"]
                    target = rollout_plan["target_percentage"]
                    step_size = rollout_plan["step_size"]
                    
                    if current < target:
                        new_percentage = min(current + step_size, target)
                        
                        # Update flag
                        self.update_rollout_percentage(flag_name, new_percentage)
                        
                        # Update rollout plan
                        rollout_plan["current_step"] = new_percentage
                        rollout_plan["next_step_time"] = (
                            now + timedelta(hours=rollout_plan["step_interval_hours"])
                        ).isoformat()
                        
                        # Clean up if completed
                        if new_percentage >= target:
                            del flag.metadata["rollout_plan"]
                        
                        self.logger.info(f"Rollout step for {flag_name}: {current}% -> {new_percentage}%")
    
    def _is_user_in_rollout(self, user_id: str, flag_name: str, 
                           rollout_percentage: int) -> bool:
        """
        Determine if user should be included in rollout based on consistent hashing.
        
        This ensures the same user gets consistent results across calls.
        """
        if rollout_percentage <= 0:
            return False
        if rollout_percentage >= 100:
            return True
        
        # Create deterministic hash from user_id and flag_name
        hash_input = f"{user_id}:{flag_name}".encode('utf-8')
        hash_digest = hashlib.sha256(hash_input).hexdigest()
        
        # Convert first 8 chars to int and get percentage
        hash_int = int(hash_digest[:8], 16)
        user_percentage = hash_int % 100
        
        return user_percentage < rollout_percentage
    
    def _load_flags(self):
        """Load feature flags from disk."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    
                for flag_data in data.get('flags', []):
                    # Handle datetime fields
                    if flag_data.get('start_date'):
                        flag_data['start_date'] = datetime.fromisoformat(flag_data['start_date'])
                    if flag_data.get('end_date'):
                        flag_data['end_date'] = datetime.fromisoformat(flag_data['end_date'])
                    
                    # Handle sets
                    flag_data['user_whitelist'] = set(flag_data.get('user_whitelist', []))
                    flag_data['user_blacklist'] = set(flag_data.get('user_blacklist', []))
                    
                    flag = FeatureFlag(**flag_data)
                    self.flags[flag.name] = flag
                    
        except Exception as e:
            self.logger.error(f"Error loading feature flags: {str(e)}")
    
    def _save_flags(self):
        """Save feature flags to disk."""
        try:
            flags_data = []
            
            for flag in self.flags.values():
                flag_dict = asdict(flag)
                
                # Handle datetime serialization
                if flag_dict['start_date']:
                    flag_dict['start_date'] = flag.start_date.isoformat()
                if flag_dict['end_date']:
                    flag_dict['end_date'] = flag.end_date.isoformat()
                
                # Handle sets
                flag_dict['user_whitelist'] = list(flag.user_whitelist)
                flag_dict['user_blacklist'] = list(flag.user_blacklist)
                
                flags_data.append(flag_dict)
            
            data = {'flags': flags_data}
            
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Error saving feature flags: {str(e)}")
    
    def emergency_killswitch(self, flag_name: str, reason: str = "Emergency stop") -> bool:
        """
        Emergency disable a feature flag immediately.
        
        Args:
            flag_name: Name of flag to disable
            reason: Reason for emergency stop
            
        Returns:
            bool: True if disabled successfully
        """
        with self._lock:
            if flag_name not in self.flags:
                return False
            
            # Immediately disable
            self.flags[flag_name].enabled = False
            self.flags[flag_name].rollout_percentage = 0
            
            # Log emergency stop
            self.logger.critical(f"EMERGENCY KILLSWITCH: {flag_name} - {reason}")
            
            # Add to metadata for tracking
            self.flags[flag_name].metadata['emergency_stops'] = (
                self.flags[flag_name].metadata.get('emergency_stops', []) + 
                [{
                    'timestamp': datetime.now().isoformat(),
                    'reason': reason
                }]
            )
            
            self._save_flags()
            return True