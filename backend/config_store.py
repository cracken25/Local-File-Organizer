"""
Simple configuration storage for user preferences.
"""
import json
import os
from pathlib import Path


CONFIG_FILE = "user_config.json"


def get_config_path():
    """Get the path to the config file."""
    return os.path.join(os.path.dirname(__file__), "..", CONFIG_FILE)


def load_config():
    """Load configuration from file."""
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
    return {}


def save_config(config):
    """Save configuration to file."""
    config_path = get_config_path()
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False


def get_last_paths():
    """Get the last used input/output paths."""
    config = load_config()
    return {
        'input_path': config.get('last_input_path', ''),
        'output_path': config.get('last_output_path', ''),
        'mode': config.get('last_mode', 'content')
    }


def save_last_paths(input_path=None, output_path=None, mode=None):
    """Save the last used paths."""
    config = load_config()
    
    if input_path is not None:
        config['last_input_path'] = input_path
    if output_path is not None:
        config['last_output_path'] = output_path
    if mode is not None:
        config['last_mode'] = mode
    
    return save_config(config)




