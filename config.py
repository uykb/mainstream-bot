# config.py
import os
from dotenv import load_dotenv
load_dotenv()
# --- API Keys & Webhooks ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LARK_WEBHOOK_URL = os.getenv("LARK_WEBHOOK_URL")

# --- Gemini Model Settings ---
# 默认模型名称
GEMINI_MODEL_NAME = "gemini-2.5-flash" 
# 代理或自定义API地址 (如果使用官方API，请留空或注释掉)
GEMINI_API_BASE_URL = "https://api.uykb.eu.org/v1" 
# --- Monitoring Settings ---
# 静态币种列表 (当 DYNAMIC_SYMBOLS = False 时生效，或作为动态获取失败时的备用列表)
SYMBOLS = ['BTCUSDT','ETHUSDT','SOLUSDT','DOGEUSDT'] # 要监控的币种列表
TIMEFRAME = '15m'                # K线周期
DATA_FETCH_LIMIT = 200           # 每次获取数据条数

# --- Indicator Thresholds ---
# Default thresholds used for any symbol not specified in SYMBOL_THRESHOLDS
DEFAULT_THRESHOLDS = {
    'VOLUME_Z_SCORE_THRESHOLD': 2.5,
    'OI_SUDDEN_CHANGE_THRESHOLD': 0.05,
    'OI_24H_CHANGE_THRESHOLD': 0.15,
    'LS_RATIO_Z_SCORE_THRESHOLD': 2.5
}

# Symbol-specific threshold overrides
SYMBOL_THRESHOLDS = {
    'BTCUSDT': {
        'VOLUME_Z_SCORE_THRESHOLD': 3.0,
        'OI_SUDDEN_CHANGE_THRESHOLD': 0.03,
        'OI_24H_CHANGE_THRESHOLD': 0.10,
        'LS_RATIO_Z_SCORE_THRESHOLD': 3.0
    },
    'ETHUSDT': {
        'VOLUME_Z_SCORE_THRESHOLD': 3.0,
        'OI_SUDDEN_CHANGE_THRESHOLD': 0.04,
        'OI_24H_CHANGE_THRESHOLD': 0.12,
        'LS_RATIO_Z_SCORE_THRESHOLD': 3.0
    },
    'SOLUSDT': {
        'VOLUME_Z_SCORE_THRESHOLD': 2.0,
        'OI_SUDDEN_CHANGE_THRESHOLD': 0.06,
        'OI_24H_CHANGE_THRESHOLD': 0.20,
        'LS_RATIO_Z_SCORE_THRESHOLD': 2.5
    },
    'DOGEUSDT': {
        'VOLUME_Z_SCORE_THRESHOLD': 2.0,
        'OI_SUDDEN_CHANGE_THRESHOLD': 0.08,
        'OI_24H_CHANGE_THRESHOLD': 0.25,
        'LS_RATIO_Z_SCORE_THRESHOLD': 2.5
    }
}

def get_threshold(symbol, key):
    """Gets the threshold for a specific symbol, falling back to the default if not specified."""
    return SYMBOL_THRESHOLDS.get(symbol, {}).get(key, DEFAULT_THRESHOLDS[key])

# --- Other settings that are not symbol-specific ---
VOLUME_LOOKBACK_PERIOD = 96      # 回看周期 (15m * 96 = 24 hours)
OI_LOOKBACK_PERIOD = 96          # OI回看周期
OI_CONTINUOUS_RISE_PERIODS = 4   # OI连续上涨N个周期则触发
LS_RATIO_LOOKBACK_PERIOD = 96    # 多空比回看周期

# Z-Score 类信号的显著变化阈值
# 只有当新的 Z-Score 与上次发送的 Z-Score 差值的绝对值大于此阈值时，才被视为新信号
Z_SCORE_CHANGE_THRESHOLD = 0.5

# 百分比类信号的显著变化阈值 (例如 OI 变化)
# 只有当新的百分比与上次发送的百分比差值的绝对值大于此阈值时，才被视为新信号
PERCENTAGE_CHANGE_THRESHOLD = 0.05 # 5%
