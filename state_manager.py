import time
from config import Z_SCORE_CHANGE_THRESHOLD, PERCENTAGE_CHANGE_THRESHOLD

class SignalStateManager:
    def __init__(self):
        self.last_triggered_signals = {}

    def _get_unique_key(self, symbol, signal):
        indicator = signal['primary_signal'].get('indicator', 'UnknownIndicator')
        signal_type = signal['primary_signal'].get('signal_type', 'UnknownType')
        return f"{symbol}-{indicator}-{signal_type}"

    def should_send_alert(self, symbol, signal):
        unique_key = self._get_unique_key(symbol, signal)
        last_signal_info = self.last_triggered_signals.get(unique_key)

        if not last_signal_info:
            print(f"[State Manager] 新的信号类型 {unique_key}，允许发送。")
            self._update_state(unique_key, signal)
            return True, None

        last_signal_data = last_signal_info['signal_data']['primary_signal']
        current_signal_data = signal['primary_signal']

        if 'z_score' in current_signal_data:
            try:
                last_z = float(last_signal_data.get('z_score', 0))
                current_z = float(current_signal_data.get('z_score', 0))
                if abs(current_z - last_z) > Z_SCORE_CHANGE_THRESHOLD:
                    print(f"[State Manager] 信号 {unique_key} 的 Z-Score 变化显著 ({last_z:.2f} -> {current_z:.2f})，允许发送。")
                    self._update_state(unique_key, signal)
                    return True, last_signal_data
            except (ValueError, TypeError):
                pass

        if 'change_24h' in current_signal_data:
            try:
                last_change_str = last_signal_data.get('change_24h', '0%').strip('%')
                current_change_str = current_signal_data.get('change_24h', '0%').strip('%')
                last_change = float(last_change_str) / 100
                current_change = float(current_change_str) / 100
                if abs(current_change - last_change) > PERCENTAGE_CHANGE_THRESHOLD:
                    print(f"[State Manager] 信号 {unique_key} 的百分比变化显著 ({last_change:.2%} -> {current_change:.2%})，允许发送。")
                    self._update_state(unique_key, signal)
                    return True, last_signal_data
            except (ValueError, TypeError):
                pass

        print(f"[State Manager] 信号 {unique_key} 无显著变化，已抑制。")
        return False, last_signal_data

    def _update_state(self, unique_key, signal):
        self.last_triggered_signals[unique_key] = {
            "timestamp": time.time(),
            "signal_data": signal
        }