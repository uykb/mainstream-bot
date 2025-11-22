import requests
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_fixed, RetryError
from config_loader import cfg
from logger import log

BASE_URL = "https://fapi.binance.com"
TIMEFRAME = cfg['trading']['timeframe']
DATA_FETCH_LIMIT = cfg['trading']['data_fetch_limit']

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
def _make_request(url: str, params: dict):
    """Makes a request with retry logic."""
    response = requests.get(url, params=params)
    response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
    return response.json()


def get_binance_data(symbol: str):
    """获取一个币种的所有相关数据：K-line, OI, L/S Ratio"""
    log.debug(f"Fetching data for {symbol}")
    try:
        # 1. 获取K线数据 (价格, 成交量)
        klines_url = f"{BASE_URL}/fapi/v1/klines"
        params = {'symbol': symbol, 'interval': TIMEFRAME, 'limit': DATA_FETCH_LIMIT}
        klines_data = _make_request(klines_url, params=params)
        
        df = pd.DataFrame(klines_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        if df.empty:
            log.warning(f"No klines data returned for {symbol}")
            return pd.DataFrame()

        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'taker_buy_base_asset_volume']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric)

        # 4. 计算 CVD (Cumulative Volume Delta)
        volume_delta = df['taker_buy_base_asset_volume'] - (df['volume'] - df['taker_buy_base_asset_volume'])
        df['cvd'] = volume_delta.cumsum()
        
        # 2. 获取持仓量 (OI)
        oi_df = pd.DataFrame()
        try:
            oi_url = f"{BASE_URL}/futures/data/openInterestHist"
            oi_params = {'symbol': symbol, 'period': TIMEFRAME, 'limit': DATA_FETCH_LIMIT}
            oi_data = _make_request(oi_url, params=oi_params)
            oi_df = pd.DataFrame(oi_data)
            if not oi_df.empty:
                oi_df['timestamp'] = pd.to_datetime(oi_df['timestamp'], unit='ms')
                oi_df.set_index('timestamp', inplace=True)
                df['oi'] = pd.to_numeric(oi_df['sumOpenInterestValue'])
        except Exception as e:
            log.warning(f"Could not fetch Open Interest data for {symbol}: {e}")

        # 3. 获取多空比
        ls_df = pd.DataFrame()
        try:
            ls_url = f"{BASE_URL}/futures/data/globalLongShortAccountRatio"
            ls_params = {'symbol': symbol, 'period': TIMEFRAME, 'limit': DATA_FETCH_LIMIT}
            ls_data = _make_request(ls_url, params=ls_params)
            ls_df = pd.DataFrame(ls_data)
            if not ls_df.empty:
                ls_df['timestamp'] = pd.to_datetime(ls_df['timestamp'], unit='ms')
                ls_df.set_index('timestamp', inplace=True)
                df['ls_ratio'] = pd.to_numeric(ls_df['longShortRatio'])
        except Exception as e:
            log.warning(f"Could not fetch Long/Short Ratio data for {symbol}: {e}")
        
        # 数据对齐与填充
        all_indices = df.index
        if not oi_df.empty:
            all_indices = all_indices.union(oi_df.index)
        if not ls_df.empty:
            all_indices = all_indices.union(ls_df.index)
        
        df = df.reindex(all_indices).interpolate(method='time').bfill().ffill()
        log.debug(f"Successfully fetched and processed data for {symbol}")
        return df

    except RetryError as e:
        log.error(f"Error fetching data for {symbol} after multiple retries: {e}")
        return pd.DataFrame()
    except Exception as e:
        log.error(f"An unexpected error occurred while fetching data for {symbol}: {e}", exc_info=True)
        return pd.DataFrame()