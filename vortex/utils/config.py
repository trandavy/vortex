import yaml
import os

def load_config(filepath: str) -> dict:
    """
    Loads a YAML configuration file.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Configuration file not found: {filepath}")
        
    with open(filepath, 'r') as f:
        config = yaml.safe_load(f)
        
    return config
