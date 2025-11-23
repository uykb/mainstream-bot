import warnings
warnings.filterwarnings("ignore", category=UserWarning, message=".*pkg_resources is deprecated.*")

import time
import schedule
from logger import log # 导入 log
from config_loader import cfg
from data_fetcher import get_binance_data
from indicators import VolumeSignal, OpenInterestSignal, LSRatioSignal
from ai_interpreter import get_gemini_interpretation
from alerter import send_lark_alert
from state_manager import SignalStateManager

# --- 使用新的配置 ---
symbols_to_check = cfg['trading']['symbols']
timeframe = cfg['trading']['timeframe']
check_interval_minutes = cfg['schedule']['check_interval_minutes']

# 初始化状态管理器
state_manager = SignalStateManager()

def run_check():
    log.info(f"开始执行检查，目标币种: {', '.join(symbols_to_check)}...")
    
    # 初始化所有指标检查器
    indicator_checkers = [VolumeSignal(), OpenInterestSignal(), LSRatioSignal()]
    
    for symbol in symbols_to_check:
        log.info(f"--- 正在检查 {symbol} ---")
        df = get_binance_data(symbol)
        
        if df.empty:
            log.warning(f"未能获取 {symbol} 的数据，跳过。")
            continue
            
        for checker in indicator_checkers:
            signal = checker.check(df, symbol)
            if signal:
                # 发现信号时，使用 warning 级别记录，以便引起注意
                log.warning(f"为 {symbol} 找到潜在信号: {signal['primary_signal']}")
                
                # 检查是否应该发送警报
                should_send, prev_signal = state_manager.should_send_alert(symbol, signal)
                if should_send:
                    # 获取 AI 解读
                    ai_insight = get_gemini_interpretation(symbol, timeframe, signal, previous_signal=prev_signal)
                    # 发送通知
                    send_lark_alert(symbol, signal, ai_insight)
                    # 防止短时间重复发送同一个信号
                    time.sleep(2)
    
    log.info("检查完成。")

if __name__ == "__main__":
    log.info("启动加密货币指标监控器...")
    # 首次启动立即执行一次
    run_check()
    
    # 设置定时任务
    schedule.every(check_interval_minutes).minutes.do(run_check)
    log.info(f"定时任务已设置，程序将每 {check_interval_minutes} 分钟运行一次检查。")
    
    while True:
        schedule.run_pending()
        time.sleep(1)
