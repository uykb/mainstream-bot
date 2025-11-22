import pandas as pd
import pandas_ta as ta
from config_loader import cfg

# --- 使用新的配置 ---
VOLUME_LOOKBACK_PERIOD = cfg['trading']['volume_lookback_period']
LS_RATIO_LOOKBACK_PERIOD = cfg['trading']['ls_ratio_lookback_period']
THRESHOLDS = cfg['trading']['thresholds']

def _create_market_snapshot(df: pd.DataFrame, primary_signal: dict):
    """
    创建一个包含主要信号和市场背景快照的丰富数据包。
    """
    # 1. 提取最近16条K线数据
    recent_klines = df.tail(16).copy()
    klines_data = recent_klines[['open', 'high', 'low', 'close', 'volume']].to_dict(orient='records')

    # 2. 提取关键指标的最新值
    latest_indicators = df.tail(1).copy()
    context_indicators = {
        "oi": f"${latest_indicators['oi'].iloc[0]:,.0f}" if 'oi' in latest_indicators else "N/A",
        "price": f"{latest_indicators['close'].iloc[0]:.2f}",
        "volume": f"{latest_indicators['volume'].iloc[0]:,.0f}",
        "cvd": f"{latest_indicators['cvd'].iloc[0]:,.0f}" if 'cvd' in latest_indicators else "N/A",
        "long_short_ratio": f"{latest_indicators['ls_ratio'].iloc[0]:.3f}" if 'ls_ratio' in latest_indicators else "N/A"
    }
    
    # 3. 计算额外的技术指标 (RSI, EMA)
    df.ta.rsi(length=14, append=True)
    df.ta.ema(length=12, append=True)
    df.ta.ema(length=26, append=True)
    
    latest_tech_indicators = df.tail(1)
    tech_indicators = {
        "rsi_14": f"{latest_tech_indicators.get('RSI_14', pd.Series([pd.NA])).iloc[0]:.2f}",
        "ema_12": f"{latest_tech_indicators.get('EMA_12', pd.Series([pd.NA])).iloc[0]:.2f}",
        "ema_26": f"{latest_tech_indicators.get('EMA_26', pd.Series([pd.NA])).iloc[0]:.2f}",
    }

    return {
        "primary_signal": primary_signal,
        "market_context": {
            "recent_klines": klines_data,
            "key_indicators": context_indicators,
            "technical_indicators": tech_indicators
        }
    }

def calculate_z_score(series: pd.Series, lookback: int):
    """计算 Z-Score"""
    mean = series.rolling(window=lookback, min_periods=lookback // 2).mean()
    std = series.rolling(window=lookback, min_periods=lookback // 2).std()
    # Avoid division by zero
    std[std == 0] = 1
    return (series - mean) / std

class VolumeSignal:
    def check(self, df: pd.DataFrame, symbol: str):
        df['volume_z_score'] = calculate_z_score(df['volume'], VOLUME_LOOKBACK_PERIOD)
        latest = df.iloc[-1]
        
        volume_z_score_threshold = THRESHOLDS['volume_z_score']
        
        if pd.notna(latest['volume_z_score']) and abs(latest['volume_z_score']) > volume_z_score_threshold:
            signal = {
                "indicator": "Volume",
                "signal_type": "Spike Alert",
                "value": f"{latest['volume']:,.0f}",
                "z_score": f"{latest['volume_z_score']:.2f}",
                "price_change": f"{(latest['close']/df.iloc[-2]['close'] - 1):.2%}"
            }
            return _create_market_snapshot(df, signal)
        return None

class OpenInterestSignal:
    def check(self, df: pd.DataFrame, symbol: str):
        if 'oi' not in df.columns or df['oi'].isnull().all():
            return None
            
        latest = df.iloc[-1]
        oi_sudden_change_threshold = THRESHOLDS['oi_sudden_change']
        
        # 突然剧烈变化
        oi_pct_change = df['oi'].pct_change()
        if pd.notna(oi_pct_change.iloc[-1]) and abs(oi_pct_change.iloc[-1]) > oi_sudden_change_threshold:
            signal = {
                "indicator": "Open Interest",
                "signal_type": "Sudden Change Alert",
                "value": f"${latest['oi']:,.0f}",
                "change_1_period": f"{oi_pct_change.iloc[-1]:+.2%}",
                "price": f"{latest['close']:.2f}"
            }
            return _create_market_snapshot(df, signal)
            
        return None

class LSRatioSignal:
    def check(self, df: pd.DataFrame, symbol: str):
        if 'ls_ratio' not in df.columns or df['ls_ratio'].isnull().all():
            return None

        df['ls_z_score'] = calculate_z_score(df['ls_ratio'], LS_RATIO_LOOKBACK_PERIOD)
        latest = df.iloc[-1]
        
        ls_ratio_z_score_threshold = THRESHOLDS['ls_ratio_z_score']
        
        if pd.notna(latest['ls_z_score']) and abs(latest['ls_z_score']) > ls_ratio_z_score_threshold:
            sentiment = "Extremely Bullish (Contrarian Bearish)" if latest['ls_z_score'] > 0 else "Extremely Bearish (Contrarian Bullish)"
            signal = {
                "indicator": "Long/Short Ratio",
                "signal_type": "Sentiment Extreme Alert",
                "value": f"{latest['ls_ratio']:.3f}",
                "z_score": f"{latest['ls_z_score']:.2f}",
                "sentiment": sentiment
            }
            return _create_market_snapshot(df, signal)
        return None
