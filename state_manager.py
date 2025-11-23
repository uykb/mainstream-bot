import time
import json
from pathlib import Path
from config_loader import cfg
from logger import log

# --- 使用新的配置 ---
Z_SCORE_CHANGE_THRESHOLD = cfg['trading']['thresholds']['z_score_change']
PERCENTAGE_CHANGE_THRESHOLD = cfg['trading']['thresholds']['percentage_change']
RESEND_INTERVAL_MINUTES = cfg['schedule']['resend_interval_minutes']
STATE_FILE_PATH = cfg['state_file_path']

class SignalStateManager:
    def __init__(self, state_file=STATE_FILE_PATH):
        self.state_file = Path(state_file)
        self.last_triggered_signals = self._load_state()

    def _load_state(self):
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    log.info("Loading previous state from file.")
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                log.error(f"Error loading state file: {e}. Starting with a fresh state.")
                return {}
        log.info("No state file found. Starting with a fresh state.")
        return {}

    def _save_state(self):
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.last_triggered_signals, f, indent=4)
                log.debug("Successfully saved state to file.")
        except IOError as e:
            log.error(f"Error saving state file: {e}")

    def _get_unique_key(self, symbol, signal):
        indicator = signal['primary_signal'].get('indicator', 'UnknownIndicator')
        signal_type = signal['primary_signal'].get('signal_type', 'UnknownType')
        return f"{symbol}-{indicator}-{signal_type}"

    def should_send_alert(self, symbol, signal):
        unique_key = self._get_unique_key(symbol, signal)
        last_signal_info = self.last_triggered_signals.get(unique_key)

        if not last_signal_info:
            log.info(f"New signal type {unique_key}, allowing send.")
            self._update_state(unique_key, signal)
            return True, None

        last_signal_data = last_signal_info['signal_data']['primary_signal']
        last_timestamp = last_signal_info.get('timestamp', 0)
        current_signal_data = signal['primary_signal']

        # 检查是否超过了强制重发时间
        time_since_last_alert = (time.time() - last_timestamp) / 60
        if time_since_last_alert > RESEND_INTERVAL_MINUTES:
            log.info(f"Signal {unique_key} has persisted for {time_since_last_alert:.1f} minutes. Resending.")
            self._update_state(unique_key, signal)
            return True, last_signal_data

        is_significant_change = False

        # 检查 Z-Score 变化
        if 'z_score' in current_signal_data:
            try:
                last_z = float(last_signal_data.get('z_score', 0))
                current_z = float(current_signal_data.get('z_score', 0))
                if abs(current_z - last_z) > Z_SCORE_CHANGE_THRESHOLD:
                    log.info(f"Significant Z-Score change for {unique_key} ({last_z:.2f} -> {current_z:.2f}), allowing send.")
                    is_significant_change = True
            except (ValueError, TypeError):
                pass
        
        # 检查百分比变化 (例如 OI 变化)
        elif 'change_1_period' in current_signal_data: # 假设这是百分比变化的字段
            try:
                last_change_str = last_signal_data.get('change_1_period', '0%').strip('%')
                current_change_str = current_signal_data.get('change_1_period', '0%').strip('%')
                last_change = float(last_change_str) / 100
                current_change = float(current_change_str) / 100
                if abs(current_change - last_change) > PERCENTAGE_CHANGE_THRESHOLD:
                    log.info(f"Significant percentage change for {unique_key} ({last_change:.2%} -> {current_change:.2%}), allowing send.")
                    is_significant_change = True
            except (ValueError, TypeError):
                pass

        if is_significant_change:
            self._update_state(unique_key, signal)
            return True, last_signal_data

        log.info(f"Signal {unique_key} has not changed significantly. Suppressed.")
        return False, last_signal_data

    def _update_state(self, unique_key, signal):
        self.last_triggered_signals[unique_key] = {
            "timestamp": time.time(),
            "signal_data": signal
        }
        self._save_state()
