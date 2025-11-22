import requests
import json
from datetime import datetime
from config_loader import cfg
from logger import log

# --- 使用新的配置 ---
LARK_WEBHOOK_URL = cfg['lark']['webhook_url']

def send_lark_alert(symbol: str, signal_data: dict, ai_interpretation: str):
    """
    构建并发送一个精美的 Lark 卡片消息
    """
    webhook_url = LARK_WEBHOOK_URL
    if not webhook_url or webhook_url == "YOUR_LARK_WEBHOOK_URL":
        log.warning("Lark webhook URL not set or is a placeholder. Skipping alert.")
        return

    primary_signal = signal_data.get('primary_signal', {})
    indicator_name = primary_signal.get('indicator', 'N/A')
    
    color_map = {
        "Volume": "orange",
        "Open Interest": "blue",
        "Long/Short Ratio": "red"
    }
    
    details_list = []
    for key, value in primary_signal.items():
        if key not in ['indicator', 'signal_type']:
            details_list.append(f"**{key.replace('_', ' ').title()}:** {value}")
    details_string = "\n".join(details_list)

    fields = []
    sections = ai_interpretation.split('【')
    for section in sections:
        if '】' in section:
            parts = section.split('】', 1)
            title = "🤖 " + parts[0]
            content = parts[1].strip()
            if content:
                fields.append({
                    "is_short": False,
                    "text": {
                        "content": f"**{title}**\n{content}",
                        "tag": "lark_md"
                    }
                })

    card = {
        "config": {
            "wide_screen_mode": True
        },
        "header": {
            "template": color_map.get(indicator_name, "grey"),
            "title": {
                "content": f"🚨 {symbol} 市场异动告警 🚨",
                "tag": "plain_text"
            }
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "content": details_string,
                    "tag": "lark_md"
                }
            },
            {
                "tag": "hr"
            },
            *fields,
            {
                "tag": "note",
                "elements": [
                    {
                        "content": f"Data from Binance Futures | Bot by uyzing | {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
                        "tag": "plain_text"
                    }
                ]
            }
        ]
    }

    payload = {
        "msg_type": "interactive",
        "card": card
    }

    try:
        response = requests.post(webhook_url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        response.raise_for_status()
        log.info(f"Lark alert for {symbol} sent successfully.")
    except requests.exceptions.RequestException as e:
        log.error(f"Error sending Lark alert for {symbol}: {e}")
