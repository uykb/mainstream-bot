import yaml
import os
from pathlib import Path

_config = None

def load_config():
    global _config
    if _config is None:
        config_path = Path(__file__).parent / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            _config = yaml.safe_load(f)

        # 优先从环境变量中读取敏感信息
        _config['binance']['api_key'] = os.getenv('BINANCE_API_KEY', _config['binance']['api_key'])
        _config['binance']['api_secret'] = os.getenv('BINANCE_API_SECRET', _config['binance']['api_secret'])
        _config['lark']['webhook_url'] = os.getenv('LARK_WEBHOOK_URL', _config['lark']['webhook_url'])
        _config['gemini']['api_key'] = os.getenv('GEMINI_API_KEY', _config['gemini']['api_key'])

    return _config

# Load on module import
cfg = load_config()
