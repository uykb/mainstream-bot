import yaml
from pathlib import Path

_config = None

def load_config():
    global _config
    if _config is None:
        config_path = Path(__file__).parent / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            _config = yaml.safe_load(f)
    return _config

# Load on module import
cfg = load_config()
