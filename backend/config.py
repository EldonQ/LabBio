"""
Configuration Loader
====================
Loads the global config.yaml from the project root.
"""

import yaml
import os
from pathlib import Path

def load_config() -> dict:
    """
    Load the global configuration file.
    Returns:
        dict: Configuration dictionary
    """
    # Find project root (2 levels up from backend/)
    # e:\LabBio\backend\config.py -> e:\LabBio
    root_dir = Path(__file__).parent.parent
    config_path = root_dir / "config.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at: {config_path}")
        
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    return config

# Global config instance
config = load_config()
